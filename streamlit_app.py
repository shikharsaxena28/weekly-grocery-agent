import streamlit as st
import openai
import json
import yagmail
import requests
from datetime import date

# --- Load Secrets ---
openai.api_key = st.secrets["OPENAI_API_KEY"]
GMAIL_USER = st.secrets["GMAIL_USER"]
GMAIL_APP_PASSWORD = st.secrets["GMAIL_APP_PASSWORD"]
GITHUB_TOKEN = st.secrets["GITHUB_TOKEN"]
GITHUB_REPO = st.secrets["GITHUB_REPO"]
GITHUB_BRANCH = st.secrets["GITHUB_BRANCH"]

# --- Load Last Week's Plan ---
with open("meals.json", "r") as f:
    meal_data = json.load(f)

# --- Generate Summary and Suggest New Plan ---
def generate_meal_summary_and_next_plan(data):
    prompt = f"""
    You are a smart meal planning assistant. The user had the following meal plan for last week:

    {json.dumps(data['schedule'], indent=2)}

    1. Summarize the last week's meals in 3-4 lines.
    2. Suggest a new meal plan for the next week (Mon–Sat), allowing for some repeat meals.
    3. Suggest a grocery list assuming nothing is in the pantry.

    Respond in structured JSON with keys: summary, next_plan, grocery_list.
    """

    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7
    )

    return json.loads(response.choices[0].message.content)

# --- Update meals.json on GitHub ---
def update_meals_json_on_github(new_schedule):
    api_url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/meals.json"

    # Get the current file's SHA
    get_resp = requests.get(api_url, headers={"Authorization": f"token {GITHUB_TOKEN}"})
    sha = get_resp.json().get("sha")

    # Prepare new file content
    new_data = meal_data.copy()
    new_data["week_start"] = str(date.today())
    new_data["meals"]["schedule"] = new_schedule
    new_content = json.dumps(new_data, indent=2)
    b64_content = new_content.encode("utf-8").decode("utf-8")

    # Update file
    commit_msg = f"Update meals.json for week starting {new_data['week_start']}"
    update_resp = requests.put(
        api_url,
        headers={"Authorization": f"token {GITHUB_TOKEN}"},
        json={
            "message": commit_msg,
            "content": new_content.encode("utf-8").decode("utf-8"),
            "sha": sha,
            "branch": GITHUB_BRANCH
        }
    )
    return update_resp.status_code == 200

# --- UI ---
st.title("🛒 Weekly Grocery Assistant")
st.markdown("This tool generates a weekly meal plan and grocery list using your previous week’s data.")

if st.button("Generate This Week's Plan"):
    result = generate_meal_summary_and_next_plan(meal_data["meals"])

    st.subheader("📌 Summary of Last Week")
    st.write(result['summary'])

    st.subheader("🗓️ Suggested Meal Plan for Next Week")
    st.json(result['next_plan'])

    st.subheader("🧾 Grocery List")
    st.json(result['grocery_list'])

    if st.button("✉️ Email This Plan To Me"):
        email_content = f"""
        Subject: Your Weekly Grocery Plan – {date.today()}

        📌 Summary of Last Week:
        {result['summary']}

        🗓️ Next Week Plan:
        {json.dumps(result['next_plan'], indent=2)}

        🧾 Grocery List:
        {json.dumps(result['grocery_list'], indent=2)}
        """
        try:
            yag = yagmail.SMTP(GMAIL_USER, GMAIL_APP_PASSWORD)
            yag.send(to=GMAIL_USER, subject="Your Weekly Grocery Plan", contents=email_content)
            st.success("Email sent successfully!")
        except Exception as e:
            st.error(f"Failed to send email: {e}")

    if st.button("✅ Approve and Save to GitHub"):
        success = update_meals_json_on_github(result['next_plan'])
        if success:
            st.success("meals.json updated on GitHub!")
        else:
            st.error("Failed to update meals.json on GitHub.")
