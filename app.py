#!/usr/bin/env python3
"""
Flask web server for the Meal Planner.
Serves a single-page app and exposes an API endpoint for plan generation.
"""

import json
import os
import random
from collections import defaultdict
from flask import Flask, render_template, request, jsonify

# Import core logic from meal_planner
from meal_planner import (
    load_and_enrich,
    generate_plan,
    get_aisle,
    AISLE_MAP,
)

app = Flask(__name__)

# Pre-load and enrich the dataset once at startup
CSV_PATH = os.path.join(os.path.dirname(__file__), "dishes.csv")
DF = load_and_enrich(CSV_PATH)

# Extract available cuisines and categories for the frontend filters
AVAILABLE_CUISINES = sorted(DF["Cuisine"].unique().tolist())
AVAILABLE_CATEGORIES = sorted(DF["Category"].unique().tolist())


def build_grocery_list(plan: dict) -> dict:
    """Build aisle-grouped grocery list with usage info."""
    ingredient_dishes: dict[str, list[str]] = defaultdict(list)
    for day, meals in plan.items():
        for meal in meals:
            for ing in meal["Parsed_Ingredients"]:
                if meal["Dish_Name"] not in ingredient_dishes[ing]:
                    ingredient_dishes[ing].append(meal["Dish_Name"])

    aisle_items: dict[str, dict[str, list[str]]] = defaultdict(dict)
    for ing, dishes in sorted(ingredient_dishes.items()):
        aisle = get_aisle(ing)
        aisle_items[aisle][ing] = dishes

    # Tea essentials
    aisle_items["Spices & Condiments"].setdefault("tea bags (green/herbal)", ["Daily Tea"])
    if "honey" in aisle_items.get("Spices & Condiments", {}):
        if "Daily Tea" not in aisle_items["Spices & Condiments"]["honey"]:
            aisle_items["Spices & Condiments"]["honey"].append("Daily Tea")
    else:
        aisle_items["Spices & Condiments"]["honey"] = ["Daily Tea"]

    result = {}
    aisle_order = ["Produce", "Dairy & Eggs", "Meat & Fish", "Dry Goods & Grains", "Spices & Condiments", "Other"]
    for aisle in aisle_order:
        items = aisle_items.get(aisle, {})
        if items:
            result[aisle] = {k: v for k, v in sorted(items.items())}
    return result


def build_savings(plan: dict) -> dict:
    """Build savings/reuse summary."""
    ingredient_usage: dict[str, int] = defaultdict(int)
    for day, meals in plan.items():
        for meal in meals:
            for ing in meal["Parsed_Ingredients"]:
                ingredient_usage[ing] += 1

    reused = {k: v for k, v in ingredient_usage.items() if v >= 2}
    reused_sorted = sorted(reused.items(), key=lambda x: -x[1])

    unique_count = len(ingredient_usage)
    naive_count = sum(ingredient_usage.values())

    return {
        "reused_ingredients": [{"name": k, "count": v} for k, v in reused_sorted],
        "unique_items": unique_count,
        "total_slots": naive_count,
        "saved": naive_count - unique_count,
    }


def serialize_plan(plan: dict, calorie_target: int) -> list[dict]:
    """Convert the plan dict into a JSON-serializable list."""
    TEA_CAL = 30
    days = []
    for day_num, meals in plan.items():
        day_cal = TEA_CAL
        meal_list = []
        for meal in meals:
            cal = int(meal["Est_Calories"])
            day_cal += cal
            meal_list.append({
                "category": meal["Category"],
                "name": meal["Dish_Name"],
                "cuisine": meal["Cuisine"],
                "ingredients": meal["Ingredients"],
                "recipe": meal["Recipe"],
                "nutrient_score": int(meal["Nutrient_Score"]),
                "nutrients": meal["Nutrients"],
                "calories": cal,
            })
        # Add tea
        meal_list.append({
            "category": "Tea",
            "name": "Green / Herbal Tea with Honey",
            "cuisine": "Universal",
            "ingredients": "tea bags, honey, water",
            "recipe": "Brew tea, add honey to taste.",
            "nutrient_score": 3,
            "nutrients": "Antioxidants, Hydration",
            "calories": TEA_CAL,
        })
        diff_pct = round(((day_cal - calorie_target) / calorie_target) * 100, 1)
        days.append({
            "day": day_num,
            "meals": meal_list,
            "total_calories": day_cal,
            "target": calorie_target,
            "diff_pct": diff_pct,
            "on_target": abs(diff_pct) <= 10,
        })
    return days


@app.route("/")
def index():
    return render_template(
        "index.html",
        cuisines=AVAILABLE_CUISINES,
        categories=AVAILABLE_CATEGORIES,
    )


@app.route("/api/generate", methods=["POST"])
def api_generate():
    data = request.get_json()
    calorie_target = int(data.get("calories", 2000))
    dietary_raw = data.get("dietary", ["Non-Veg"])
    num_days = int(data.get("days", 7))
    cuisine_filter = data.get("cuisines", [])  # empty = all

    # Accept both a single string and a list
    if isinstance(dietary_raw, str):
        dietary_prefs = [dietary_raw]
    else:
        dietary_prefs = dietary_raw or ["Non-Veg"]

    random.seed()

    # Apply cuisine filter if provided
    df = DF.copy()
    if cuisine_filter:
        df = df[df["Cuisine"].isin(cuisine_filter)]
        if df.empty:
            df = DF.copy()

    # Apply multi dietary filter:
    # Build the allowed set of Dietary_Type values
    allowed_types = set()
    for pref in dietary_prefs:
        if pref == "Non-Veg":
            allowed_types.update(["Non-Veg", "Veg", "Vegan"])
        elif pref == "Veg":
            allowed_types.update(["Veg", "Vegan"])
        elif pref == "Vegan":
            allowed_types.add("Vegan")

    filtered_df = df[df["Dietary_Type"].isin(allowed_types)].copy()
    if filtered_df.empty:
        filtered_df = df.copy()

    # Derive the most restrictive single preference for generate_plan's internal filter
    if "Vegan" in dietary_prefs:
        dietary_for_plan = "Vegan"
    elif "Veg" in dietary_prefs:
        dietary_for_plan = "Veg"
    else:
        dietary_for_plan = "Non-Veg"

    plan, all_ingredients = generate_plan(filtered_df, calorie_target, dietary_for_plan, num_days)

    return jsonify({
        "plan": serialize_plan(plan, calorie_target),
        "grocery": build_grocery_list(plan),
        "savings": build_savings(plan),
        "settings": {
            "calories": calorie_target,
            "dietary": dietary_prefs,
            "days": num_days,
            "cuisines": cuisine_filter if cuisine_filter else AVAILABLE_CUISINES,
        },
    })


if __name__ == "__main__":
    app.run(debug=True, port=5000)
