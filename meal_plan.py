import requests
from bs4 import BeautifulSoup
import json

# Cornell Dining Meal Plans URL
url = "https://scl.cornell.edu/residential-life/dining/meal-plans-rates/undergraduate-meal-plans"

# Send GET request
response = requests.get(url)
response.raise_for_status()

# Parse page
soup = BeautifulSoup(response.text, "html.parser")

# Find the main content section
content_section = soup.find("div", class_="page-content") or soup.find("main")

meal_plans = []
if not content_section:
    print("❌ Could not find content section.")
else:
    current_plan = None

    # Go through headers and paragraphs
    for element in content_section.find_all(["h2", "p", "li"]):
        text = element.get_text(strip=True)
        if not text:
            continue

        # Detect new meal plan titles
        if any(keyword in text for keyword in ["Unlimited", "Bear Traditional", "Bear Choice", "Meal Plan", "Just Bucks", "Debit", "House Plan"]):
            if current_plan:
                meal_plans.append(current_plan)
            current_plan = {"name": text, "details": []}
        elif current_plan:
            current_plan["details"].append(text)

    # Add last one
    if current_plan:
        meal_plans.append(current_plan)

# ✅ Build JSON output
source_url = url
json_data = []
entry_id = 1

for plan in meal_plans:
    plan_name = plan["name"]
    for detail in plan["details"]:
        json_data.append({
            "id": entry_id,
            "plan_name": plan_name,
            "text": detail,
            "source": source_url
        })
        entry_id += 1

# ✅ Save to file
output_file = "cornell_mealplans_2025.json"
with open(output_file, "w", encoding="utf-8") as f:
    json.dump(json_data, f, indent=4, ensure_ascii=False)

print(f"✅ Saved {len(json_data)} entries from {len(meal_plans)} plans to {output_file}")