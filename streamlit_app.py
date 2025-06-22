import streamlit as st
import openai
import json
import os
from datetime import datetime, timedelta

# Load API keys from Streamlit Secrets
openai.api_key = st.secrets["OPENAI_API_KEY"]

# --- Load last week's meal data ---
with open("meals.json", "r") as f:
    meal_data = json.load(f)

# --- Format prompt for OpenAI ---
def generate_meal_summary_and_next_plan(meals):
    prompt = f"""
You are a weekly grocery planning assistant. Here's the meal plan from last week:

{json.dumps(meals, indent=2)}

1. Summarize the variety and nutritional balance across the week.
2. Recommend a meal plan for next week (Mon-Sat), with breakfast (B1, B2), lunch, and dinner.
3. Suggest a grocery list for the new plan assuming nothing is in the pantry.
4. Include estimated quantities for each item per meal.

Return your output in this structure:

### Summary of Last Week:
...

### Next Week's Meal Plan:
...

### Grocery List with Estimates:
- Item (Estimated total quantity)
"""

    response = openai.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7
    )
    return response.choices[0].message.content


# --- Streamlit UI ---
st.set_page_config(page_title="Weekly Grocery Assistant")
st.title("🛒 Weekly Grocery Assistant")
st.write("This tool generates a weekly meal plan and grocery list using your previous week's data.")

if st.button("Generate This Week's Plan"):
    with st.spinner("Thinking through your meals... 🍽️"):
        result = generate_meal_summary_and_next_plan(meal_data["meals"])
        st.text_area("📋 Grocery Plan Output", result, height=600)

        # Save result for future reference (optional)
        today = datetime.today().strftime("%Y-%m-%d")
        with open(f"summary_{today}.txt", "w") as f:
            f.write(result)
