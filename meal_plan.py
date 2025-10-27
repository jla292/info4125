import requests
from bs4 import BeautifulSoup
import json

# Cornell Dining Meal Plans URL
url = "https://scl.cornell.edu/residential-life/dining/meal-plans-rates/undergraduate-meal-plans"

response = requests.get(url)
response.raise_for_status()

soup = BeautifulSoup(response.text, "html.parser")

content_section = soup.find("div", class_="page-content") or soup.find("main")

meal_plans = []
if not content_section:
    print("❌ Could not find content section.")
else:
    current_plan = None

    for element in content_section.find_all(["h2", "p", "li"]):
        text = element.get_text(strip=True)
        if not text:
            continue

        if any(keyword in text for keyword in ["Unlimited", "Bear Traditional", "Bear Choice", "Meal Plan", "Just Bucks", "Debit", "House Plan", "Graduate Meal Plans"]):
            if current_plan:
                meal_plans.append(current_plan)
            current_plan = {"name": text, "details": []}
        elif current_plan:
            current_plan["details"].append(text)

    if current_plan:
        meal_plans.append(current_plan)

# ✅ Build JSON output (same format as finaid.json)
json_data = []
for plan in meal_plans:
    for detail in plan["details"]:
        json_data.append({
            "text": detail,
            "label": "1",
            "source": url,
            "date": "2025-26",
            "topic": plan["name"]
        })

# ✅ Save to file
output_file = "cornell_mealplans_2025.json"
with open(output_file, "w", encoding="utf-8") as f:
    json.dump(json_data, f, indent=4, ensure_ascii=False)

print(f"✅ Saved {len(json_data)} entries from {len(meal_plans)} plans to {output_file}")
