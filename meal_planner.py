#!/usr/bin/env python3
"""
Interactive Meal Planner - minimizes unique ingredient purchases
by maximizing ingredient overlap across a multi-day plan.
"""
import sys
import io
if sys.stdout and hasattr(sys.stdout, 'buffer'):
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    except Exception:
        pass

import pandas as pd
import random
import re
from collections import defaultdict

# ─── Ingredient Normalization ────────────────────────────────────────────────

# Map messy ingredient strings → canonical names
CANONICAL = {
    "onion": "onion", "onions": "onion", "red onion": "onion",
    "tomato": "tomato", "tomatoes": "tomato", "cherry tomatoes": "tomato",
    "canned tomatoes": "canned tomatoes", "tomato sauce": "canned tomatoes",
    "garlic": "garlic", "ginger": "ginger",
    "ginger-garlic paste": "ginger-garlic paste",
    "green chili": "green chili", "green chilli": "green chili",
    "chili flakes": "chili flakes", "red chili": "red chili",
    "chili powder": "chili powder", "red chili powder": "chili powder",
    "oil": "oil", "olive oil": "olive oil", "vegetable oil": "oil",
    "butter": "butter", "ghee": "ghee",
    "salt": "salt", "pepper": "pepper", "black pepper": "black pepper",
    "cumin": "cumin", "cumin seeds": "cumin",
    "turmeric": "turmeric", "garam masala": "garam masala",
    "coriander": "fresh coriander", "coriander seeds": "coriander seeds",
    "curry leaves": "curry leaves", "mustard seeds": "mustard seeds",
    "chaat masala": "chaat masala", "tandoori masala": "tandoori masala",
    "kadai masala": "kadai masala", "korma paste": "korma paste",
    "curry powder": "curry powder", "sambar powder": "sambar powder",
    "paprika": "paprika", "nutmeg": "nutmeg", "cinnamon": "cinnamon",
    "cardamom": "cardamom", "bay leaf": "bay leaf", "cloves": "cloves",
    "rosemary": "rosemary", "thyme": "thyme", "basil": "basil",
    "dill": "dill", "parsley": "parsley", "mint": "mint",
    "oregano": "oregano", "marjoram": "marjoram", "chives": "chives",
    "lemon": "lemon", "lime": "lime", "tamarind": "tamarind",
    "balsamic vinegar": "balsamic vinegar",
    "eggs": "eggs", "egg": "eggs", "egg yolk": "eggs",
    "chicken breast": "chicken breast", "chicken thighs": "chicken thighs",
    "minced meat": "minced meat", "minced lamb": "minced lamb",
    "ham": "ham", "white sausage": "white sausage",
    "white fish fillets": "white fish", "cod fillet": "cod fillet",
    "salmon fillet": "salmon fillet", "shrimp": "shrimp",
    "canned tuna": "canned tuna", "smoked salmon": "smoked salmon",
    "smoked mackerel": "smoked mackerel",
    "paneer": "paneer", "cottage cheese": "cottage cheese",
    "twaróg (quark)": "twaróg", "twaróg": "twaróg", "cottage cheese (twaróg)": "twaróg",
    "feta cheese": "feta", "feta": "feta",
    "cheese": "cheese", "cheddar": "cheddar", "mozzarella": "mozzarella",
    "parmesan": "parmesan", "ricotta": "ricotta",
    "cream cheese": "cream cheese", "cream": "cream", "sour cream": "sour cream",
    "yogurt": "yogurt", "greek yogurt": "yogurt",
    "milk": "milk", "coconut milk": "coconut milk",
    "potato": "potato", "potatoes": "potato", "sweet potato": "sweet potato",
    "onion": "onion",
    "bell pepper": "bell pepper", "bell peppers": "bell pepper",
    "frozen spinach": "frozen spinach", "spinach": "spinach",
    "mixed greens": "mixed greens",
    "carrot": "carrot", "carrots": "carrot",
    "celery": "celery", "zucchini": "zucchini",
    "cucumber": "cucumber", "broccoli": "broccoli",
    "cauliflower": "cauliflower", "eggplant": "eggplant",
    "okra (fresh or frozen)": "okra", "green beans": "green beans",
    "mushrooms": "mushrooms", "kale": "kale",
    "beetroot": "beetroot", "cooked beetroot": "beetroot",
    "radishes": "radish",
    "green peas": "green peas", "peas": "green peas",
    "mixed vegetables": "mixed vegetables",
    "banana": "banana", "apple": "apple", "mango": "mango",
    "blueberries": "berries", "mixed berries": "berries",
    "avocado": "avocado",
    "basmati rice": "basmati rice", "rice": "basmati rice",
    "arborio rice": "arborio rice",
    "whole wheat flour": "whole wheat flour", "flour": "flour",
    "roti": "roti/whole wheat flour", "whole wheat paratha": "roti/whole wheat flour",
    "spaghetti": "spaghetti", "penne": "penne", "macaroni": "macaroni",
    "pasta": "pasta",
    "rye bread": "rye bread", "sourdough bread": "sourdough bread",
    "bread": "bread", "crusty bread": "bread",
    "english muffin": "english muffin", "croissant": "croissant",
    "tortilla": "tortilla", "baguette": "baguette",
    "pizza dough": "pizza dough", "pierogi dough": "pierogi dough",
    "rye crispbread": "rye crispbread", "whole wheat crackers": "whole wheat crackers",
    "rolled oats": "rolled oats", "oat flour": "oat flour",
    "semolina": "semolina", "couscous": "couscous", "quinoa": "quinoa",
    "pearl barley": "pearl barley",
    "kasha (roasted buckwheat)": "kasha (buckwheat)", "kasha": "kasha (buckwheat)",
    "rice flour": "rice flour", "gram flour": "gram flour",
    "moong dal flour": "moong dal flour",
    "broken wheat": "broken wheat", "flattened rice": "flattened rice",
    "rice vermicelli": "rice vermicelli", "idli rice": "idli rice",
    "tapioca pearls": "tapioca pearls",
    "ragi flour": "ragi flour", "roasted gram flour": "roasted gram flour",
    "breadcrumbs": "breadcrumbs",
    "toor dal": "toor dal", "moong dal": "moong dal", "urad dal": "urad dal",
    "chana dal": "chana dal", "red lentils": "red lentils",
    "kidney beans (canned)": "canned kidney beans",
    "canned chickpeas": "canned chickpeas",
    "cannellini beans": "canned cannellini beans",
    "canned white beans": "canned white beans",
    "mixed sprouts": "mixed sprouts", "dried chickpeas": "dried chickpeas",
    "flattened chickpeas": "flattened chickpeas",
    "whole green moong": "whole green moong",
    "peanuts": "peanuts", "peanut butter": "peanut butter",
    "almonds": "almonds", "walnuts": "walnuts", "cashews": "cashews",
    "pistachios": "pistachios", "pumpkin seeds": "pumpkin seeds",
    "chia seeds": "chia seeds",
    "granola": "granola", "honey": "honey", "jaggery": "jaggery",
    "dark chocolate chips": "dark chocolate chips",
    "dried cranberries": "dried cranberries", "raisins": "raisins",
    "nutritional yeast": "nutritional yeast",
    "tahini": "tahini", "basil pesto": "basil pesto",
    "soy sauce": "soy sauce", "white wine": "white wine",
    "baking powder": "baking powder", "vanilla": "vanilla",
    "sourdough starter (żur)": "żur starter",
    "fox nuts (makhana)": "makhana", "puffed rice": "puffed rice",
    "popcorn kernels": "popcorn kernels",
    "capers": "capers", "olives": "olives",
    "vegetable broth": "vegetable broth",
    "fenugreek leaves": "fenugreek leaves",
    "coconut": "desiccated coconut",
    "water": None, "salt": "salt",  # water is free
    "black salt": "black salt",
    "herbs": "mixed dried herbs",
}

# Non-veg indicators in ingredients
NON_VEG_KEYWORDS = {
    "chicken", "meat", "lamb", "fish", "salmon", "shrimp", "cod",
    "tuna", "mackerel", "ham", "sausage", "egg", "eggs",
}
# Dairy / animal-product indicators (not vegan)
DAIRY_KEYWORDS = {
    "paneer", "cheese", "cream", "yogurt", "milk", "butter", "ghee",
    "feta", "mozzarella", "parmesan", "ricotta", "cheddar", "twaróg",
    "cottage cheese", "cream cheese", "sour cream", "honey",
}

# Calorie estimates by category (rough kcal per serving)
CALORIE_ESTIMATES = {
    "Breakfast": 350,
    "Snack": 180,
    "Lunch": 550,
    "Dinner": 500,
}

# Aisle classification
AISLE_MAP = {
    "Produce": {
        "onion", "tomato", "garlic", "ginger", "green chili", "bell pepper",
        "spinach", "mixed greens", "carrot", "celery", "zucchini", "cucumber",
        "broccoli", "cauliflower", "eggplant", "okra", "green beans",
        "mushrooms", "kale", "beetroot", "radish", "green peas", "potato",
        "sweet potato", "banana", "apple", "mango", "avocado", "berries",
        "lemon", "lime", "fresh coriander", "mint", "chives", "dill",
        "parsley", "basil", "rosemary", "thyme", "fenugreek leaves",
        "curry leaves", "mixed vegetables",
    },
    "Dairy & Eggs": {
        "eggs", "paneer", "cottage cheese", "twaróg", "feta", "cheese",
        "cheddar", "mozzarella", "parmesan", "ricotta", "cream cheese",
        "cream", "sour cream", "yogurt", "milk", "butter",
        "coconut milk",
    },
    "Meat & Fish": {
        "chicken breast", "chicken thighs", "minced meat", "minced lamb",
        "ham", "white sausage", "white fish", "cod fillet", "salmon fillet",
        "shrimp", "canned tuna", "smoked salmon", "smoked mackerel",
    },
    "Dry Goods & Grains": {
        "basmati rice", "arborio rice", "whole wheat flour", "flour",
        "roti/whole wheat flour", "spaghetti", "penne", "macaroni", "pasta",
        "rye bread", "sourdough bread", "bread", "english muffin", "croissant",
        "tortilla", "baguette", "pizza dough", "pierogi dough",
        "rye crispbread", "whole wheat crackers",
        "rolled oats", "oat flour", "semolina", "couscous", "quinoa",
        "pearl barley", "kasha (buckwheat)", "rice flour", "gram flour",
        "moong dal flour", "broken wheat", "flattened rice", "rice vermicelli",
        "idli rice", "tapioca pearls", "ragi flour", "roasted gram flour",
        "breadcrumbs", "toor dal", "moong dal", "urad dal", "chana dal",
        "red lentils", "canned kidney beans", "canned chickpeas",
        "canned cannellini beans", "canned white beans",
        "mixed sprouts", "dried chickpeas", "flattened chickpeas",
        "whole green moong", "canned tomatoes", "vegetable broth",
        "peanuts", "peanut butter", "almonds", "walnuts", "cashews",
        "pistachios", "pumpkin seeds", "chia seeds", "granola",
        "dark chocolate chips", "dried cranberries", "raisins",
        "desiccated coconut", "tahini", "basil pesto",
        "puffed rice", "popcorn kernels", "makhana",
    },
    "Spices & Condiments": {
        "cumin", "turmeric", "garam masala", "coriander seeds", "chaat masala",
        "tandoori masala", "kadai masala", "korma paste", "curry powder",
        "sambar powder", "paprika", "nutmeg", "cinnamon", "cardamom",
        "bay leaf", "cloves", "mustard seeds", "chili flakes", "chili powder",
        "red chili", "black pepper", "oregano", "marjoram",
        "mixed dried herbs", "salt", "black salt", "tamarind",
        "honey", "jaggery", "soy sauce", "balsamic vinegar", "white wine",
        "baking powder", "vanilla", "nutritional yeast",
        "żur starter", "capers", "olives", "oil", "olive oil", "ghee",
    },
}


# ─── Helper Functions ────────────────────────────────────────────────────────

def parse_ingredients(raw: str) -> set[str]:
    """Split the CSV ingredient string and normalize each item."""
    items = [s.strip().lower() for s in raw.split(",")]
    normalized = set()
    for item in items:
        # Try direct lookup first
        if item in CANONICAL:
            canon = CANONICAL[item]
            if canon is not None:
                normalized.add(canon)
            continue
        # Remove quantity-like prefixes and parentheticals
        cleaned = re.sub(r"^\d[\d./]*\s*", "", item)
        cleaned = re.sub(r"\(.*?\)", "", cleaned).strip()
        cleaned = re.sub(r"\s*(chopped|sliced|diced|grated|crushed|fresh|frozen|dried|roasted|cooked|canned|boiled|mixed)\s*", " ", cleaned).strip()
        if cleaned in CANONICAL:
            canon = CANONICAL[cleaned]
            if canon is not None:
                normalized.add(canon)
        else:
            # Fallback: use the cleaned string as-is
            normalized.add(cleaned)
    return normalized


def classify_dietary(ingredients_raw: str) -> str:
    """Infer Veg / Non-Veg / Vegan from ingredient list."""
    lower = ingredients_raw.lower()
    for kw in NON_VEG_KEYWORDS:
        if kw in lower:
            return "Non-Veg"
    for kw in DAIRY_KEYWORDS:
        if kw in lower:
            return "Veg"
    return "Vegan"


def estimate_calories(category: str, ingredients_raw: str) -> int:
    """Rough calorie estimate based on category with small adjustments."""
    base = CALORIE_ESTIMATES.get(category, 400)
    lower = ingredients_raw.lower()
    # Bump up for calorie-dense ingredients
    if any(kw in lower for kw in ("cream", "cheese", "ghee", "butter", "peanut butter")):
        base += 60
    if any(kw in lower for kw in ("rice", "pasta", "spaghetti", "penne", "macaroni")):
        base += 40
    if "chicken" in lower or "meat" in lower or "lamb" in lower:
        base += 30
    return base


def ingredient_overlap(selected_ingredients: set[str], candidate_ingredients: set[str]) -> int:
    """Count how many ingredients the candidate shares with already-selected meals."""
    return len(selected_ingredients & candidate_ingredients)


def get_aisle(ingredient: str) -> str:
    for aisle, items in AISLE_MAP.items():
        if ingredient in items:
            return aisle
    return "Other"


# ─── Data Loading ────────────────────────────────────────────────────────────

def load_and_enrich(csv_path: str = "dishes.csv") -> pd.DataFrame:
    df = pd.read_csv(csv_path)
    df["Parsed_Ingredients"] = df["Ingredients"].apply(parse_ingredients)
    df["Dietary_Type"] = df["Ingredients"].apply(classify_dietary)
    df["Est_Calories"] = df.apply(lambda r: estimate_calories(r["Category"], r["Ingredients"]), axis=1)
    return df


# ─── Selection Algorithm ─────────────────────────────────────────────────────

def select_day_meals(pool: pd.DataFrame, global_ingredients: set[str],
                     calorie_target: int, used_dishes: set[str]) -> list[dict] | None:
    """
    Pick 4 meals (Breakfast, Snack, Lunch, Dinner) + Tea for one day.
    Maximize ingredient overlap with global_ingredients while hitting calorie target ±10%.
    """
    lo = calorie_target * 0.90
    hi = calorie_target * 1.10
    TEA_CALORIES = 30  # tea with a little milk/honey

    needed_categories = ["Breakfast", "Snack", "Lunch", "Dinner"]
    best_combo = None
    best_overlap = -1

    # Try multiple random seeds for variety, keep best overlap
    attempts = 300
    for _ in range(attempts):
        combo = []
        combo_ingredients = set()
        combo_calories = TEA_CALORIES

        valid = True
        for cat in needed_categories:
            cat_pool = pool[(pool["Category"] == cat) & (~pool["Dish_Name"].isin(used_dishes))]
            if cat_pool.empty:
                # Allow reuse if pool exhausted
                cat_pool = pool[pool["Category"] == cat]
            if cat_pool.empty:
                valid = False
                break

            # Score by overlap, pick from top candidates with some randomness
            scores = cat_pool["Parsed_Ingredients"].apply(
                lambda ing: ingredient_overlap(global_ingredients | combo_ingredients, ing)
            )
            cat_pool = cat_pool.copy()
            cat_pool["_score"] = scores.values

            # Pick from top 5 by overlap (with random tiebreak for variety)
            top = cat_pool.nlargest(min(5, len(cat_pool)), "_score")
            chosen = top.sample(1).iloc[0]

            combo.append(chosen)
            combo_ingredients |= chosen["Parsed_Ingredients"]
            combo_calories += chosen["Est_Calories"]

        if not valid:
            continue

        # Check calorie range
        if lo <= combo_calories <= hi:
            overlap = ingredient_overlap(global_ingredients, combo_ingredients)
            if overlap > best_overlap:
                best_overlap = overlap
                best_combo = combo

    # If no perfect calorie match, relax constraint and pick best overlap
    if best_combo is None:
        for _ in range(200):
            combo = []
            combo_ingredients = set()
            combo_calories = TEA_CALORIES

            valid = True
            for cat in needed_categories:
                cat_pool = pool[(pool["Category"] == cat) & (~pool["Dish_Name"].isin(used_dishes))]
                if cat_pool.empty:
                    cat_pool = pool[pool["Category"] == cat]
                if cat_pool.empty:
                    valid = False
                    break

                scores = cat_pool["Parsed_Ingredients"].apply(
                    lambda ing: ingredient_overlap(global_ingredients | combo_ingredients, ing)
                )
                cat_pool = cat_pool.copy()
                cat_pool["_score"] = scores.values
                top = cat_pool.nlargest(min(5, len(cat_pool)), "_score")
                chosen = top.sample(1).iloc[0]

                combo.append(chosen)
                combo_ingredients |= chosen["Parsed_Ingredients"]
                combo_calories += chosen["Est_Calories"]

            if not valid:
                continue

            overlap = ingredient_overlap(global_ingredients, combo_ingredients)
            if overlap > best_overlap:
                best_overlap = overlap
                best_combo = combo

    if best_combo is None:
        return None

    return best_combo


def generate_plan(df: pd.DataFrame, calorie_target: int, dietary_pref: str, num_days: int):
    """Generate the full meal plan."""
    # Filter by dietary preference
    if dietary_pref == "Vegan":
        pool = df[df["Dietary_Type"] == "Vegan"].copy()
    elif dietary_pref == "Veg":
        pool = df[df["Dietary_Type"].isin(["Veg", "Vegan"])].copy()
    else:  # Non-Veg: all dishes allowed
        pool = df.copy()

    if pool.empty:
        print("\n  No dishes match your dietary preference. Showing all dishes instead.")
        pool = df.copy()

    plan = {}  # day -> list of dish rows
    global_ingredients: set[str] = set()
    used_dishes: set[str] = set()

    for day in range(1, num_days + 1):
        day_meals = select_day_meals(pool, global_ingredients, calorie_target, used_dishes)
        if day_meals is None:
            print(f"\n  Warning: Could not find a valid combination for Day {day}. Using closest match.")
            # Fallback: just pick one from each category
            day_meals = []
            for cat in ["Breakfast", "Snack", "Lunch", "Dinner"]:
                cat_pool = pool[pool["Category"] == cat]
                if not cat_pool.empty:
                    day_meals.append(cat_pool.sample(1).iloc[0])

        plan[day] = day_meals
        for meal in day_meals:
            global_ingredients |= meal["Parsed_Ingredients"]
            used_dishes.add(meal["Dish_Name"])

    return plan, global_ingredients


# ─── Output Formatting ───────────────────────────────────────────────────────

def print_plan(plan: dict, calorie_target: int):
    TEA_CAL = 30
    print("\n" + "=" * 65)
    print("  WEEKLY MEAL PLAN")
    print("=" * 65)

    for day, meals in plan.items():
        day_cal = TEA_CAL
        print(f"\n{'-' * 65}")
        print(f"  DAY {day}")
        print(f"{'-' * 65}")
        for meal in meals:
            cal = meal["Est_Calories"]
            day_cal += cal
            print(f"  [{meal['Category']:<10}] {meal['Dish_Name']:<42} ~{cal} kcal")
            print(f"               {meal['Cuisine']} | Score: {meal['Nutrient_Score']}/10")
        print(f"  [{'Tea':<10}] {'Green/Herbal Tea with Honey':<42} ~{TEA_CAL} kcal")
        diff_pct = ((day_cal - calorie_target) / calorie_target) * 100
        marker = "OK" if abs(diff_pct) <= 10 else "~APPROX"
        print(f"\n  Day Total: ~{day_cal} kcal  (target: {calorie_target}, {diff_pct:+.1f}%) [{marker}]")


def print_shopping_list(plan: dict):
    # Collect all ingredients and which dishes use them
    ingredient_dishes: dict[str, list[str]] = defaultdict(list)
    for day, meals in plan.items():
        for meal in meals:
            for ing in meal["Parsed_Ingredients"]:
                if meal["Dish_Name"] not in ingredient_dishes[ing]:
                    ingredient_dishes[ing].append(meal["Dish_Name"])

    # Group by aisle
    aisle_items: dict[str, dict[str, list[str]]] = defaultdict(dict)
    for ing, dishes in sorted(ingredient_dishes.items()):
        aisle = get_aisle(ing)
        aisle_items[aisle][ing] = dishes

    # Add tea essentials
    aisle_items["Spices & Condiments"].setdefault("tea bags (green/herbal)", ["Daily Tea"])
    aisle_items["Spices & Condiments"].setdefault("honey", []).append("Daily Tea")

    print("\n" + "=" * 65)
    print("  CONSOLIDATED SHOPPING LIST")
    print("=" * 65)

    total_items = 0
    for aisle in ["Produce", "Dairy & Eggs", "Meat & Fish", "Dry Goods & Grains", "Spices & Condiments", "Other"]:
        items = aisle_items.get(aisle, {})
        if not items:
            continue
        print(f"\n  [{aisle}]")
        for ing in sorted(items.keys()):
            print(f"    • {ing}")
            total_items += 1

    print(f"\n  Total unique items: {total_items}")


def print_savings_summary(plan: dict):
    ingredient_usage: dict[str, int] = defaultdict(int)
    for day, meals in plan.items():
        for meal in meals:
            for ing in meal["Parsed_Ingredients"]:
                ingredient_usage[ing] += 1

    reused = {k: v for k, v in ingredient_usage.items() if v >= 2}
    reused_sorted = sorted(reused.items(), key=lambda x: -x[1])

    print("\n" + "=" * 65)
    print("  SAVINGS SUMMARY — Ingredient Reuse")
    print("=" * 65)

    if not reused_sorted:
        print("\n  No ingredients reused across meals.")
        return

    total_reuses = sum(v - 1 for _, v in reused_sorted)
    print(f"\n  {len(reused_sorted)} ingredients reused across multiple meals,")
    print(f"  saving ~{total_reuses} extra purchases.\n")

    print(f"  {'Ingredient':<30} {'Used in # meals':>15}")
    print(f"  {'-' * 30} {'-' * 15}")
    for ing, count in reused_sorted[:20]:
        print(f"  {ing:<30} {count:>15}x")
    if len(reused_sorted) > 20:
        print(f"  ... and {len(reused_sorted) - 20} more reused ingredients.")

    unique_count = len(ingredient_usage)
    naive_count = sum(ingredient_usage.values())
    print(f"\n  Without overlap optimization: ~{naive_count} ingredient-slots")
    print(f"  With overlap optimization:    ~{unique_count} unique items to buy")
    print(f"  Estimated reduction:           ~{naive_count - unique_count} fewer purchases")


# ─── User Questionnaire ─────────────────────────────────────────────────────

def get_user_input() -> tuple[int, str, int]:
    print("\n" + "=" * 65)
    print("  MEAL PLANNER — Minimal Ingredient Optimization")
    print("=" * 65)

    # Calorie goal
    while True:
        try:
            cal = int(input("\n  Daily calorie goal (e.g. 1800, 2000, 2500): ").strip())
            if 800 <= cal <= 5000:
                break
            print("  Please enter a value between 800 and 5000.")
        except ValueError:
            print("  Please enter a valid number.")

    # Dietary preference
    while True:
        pref = input("  Dietary preference [Veg / Vegan / Non-Veg]: ").strip().lower()
        mapping = {"veg": "Veg", "vegan": "Vegan", "non-veg": "Non-Veg", "nonveg": "Non-Veg"}
        if pref in mapping:
            pref = mapping[pref]
            break
        print("  Please enter Veg, Vegan, or Non-Veg.")

    # Duration
    while True:
        try:
            days = int(input("  Plan duration in days (e.g. 7): ").strip())
            if 1 <= days <= 30:
                break
            print("  Please enter a value between 1 and 30.")
        except ValueError:
            print("  Please enter a valid number.")

    return cal, pref, days


# ─── Main ────────────────────────────────────────────────────────────────────

def main():
    random.seed()
    cal_target, dietary, num_days = get_user_input()

    print(f"\n  Loading dishes and optimizing for ingredient overlap...")
    df = load_and_enrich("dishes.csv")

    plan, all_ingredients = generate_plan(df, cal_target, dietary, num_days)

    print_plan(plan, cal_target)
    print_shopping_list(plan)
    print_savings_summary(plan)

    print("\n" + "=" * 65)
    print("  Happy cooking! Smacznego!")
    print("=" * 65 + "\n")


if __name__ == "__main__":
    main()
