# NutriPlan — Smart Meal Planner

An interactive meal planner that builds a week of Indian/European/Fusion meals while **minimizing your grocery bill** through ingredient overlap optimization.

## Features

- **Linear programming-inspired selection** — every new meal maximizes shared ingredients with already-chosen meals, so you buy fewer unique items
- **Interactive web UI** — dark-themed single-page app with animated questionnaire → meal plan → grocery list flow
- **Dietary filtering** — Vegan / Vegetarian / Non-Veg, inferred automatically from ingredients
- **Cuisine filtering** — Indian, European, Fusion — mix and match
- **4 export formats** — plain text plan, shopping list, `.ics` calendar events, and a print-ready layout
- **Interactive grocery checklist** — tap items to check them off while shopping

## Project Structure

```
claude_nutrients/
├── dishes.csv          # 153 Indian/European/Fusion recipes
├── meal_planner.py     # Core logic: ingredient normalization, overlap algorithm, CLI
├── app.py              # Flask web server + API endpoints
├── templates/
│   └── index.html      # Single-page web app (questionnaire + results)
└── README.md
```

## Quick Start

### 1. Install dependencies

```bash
pip install flask pandas
```

### 2. Run the web app

```bash
python app.py
```

Then open **http://127.0.0.1:5000** in your browser.

### 3. Or use the CLI version

```bash
python meal_planner.py
```

Prompts for calorie goal, dietary preference, and duration, then prints the plan and shopping list to the terminal.

## How It Works

### Ingredient Overlap Algorithm

For each day, the planner:
1. Scores every candidate dish by how many ingredients it shares with meals already selected
2. Picks from the top-5 overlapping candidates (with randomness for variety)
3. Checks that the 4-meal combo (Breakfast + Snack + Lunch + Dinner + Tea) lands within ±10% of your calorie target
4. Repeats 300 attempts and keeps the combo with the highest overlap score

### Dietary Inference

The CSV has no `Dietary_Type` column, so it's inferred from ingredients:
- Contains chicken/fish/eggs/meat → **Non-Veg**
- Contains paneer/cheese/yogurt/cream → **Vegetarian**
- Neither → **Vegan**

### Calorie Estimation

Base estimates by category (Breakfast ~350, Snack ~180, Lunch ~550, Dinner ~500 kcal), adjusted upward for calorie-dense ingredients (cream, cheese, ghee, rice, pasta, meat).

## Web UI Screens

| Screen | Description |
|---|---|
| **Landing** | Sliders for calories & duration, pill-selectors for dietary and cuisine preferences |
| **Meal Plan tab** | Collapsible day cards; click any meal to expand its recipe and ingredients |
| **Grocery List tab** | Aisle-grouped items with tappable checkboxes for in-store use |
| **Savings tab** | Shows how many purchases were saved and which ingredients are reused most |

## Export Options

| Export | Format | Use |
|---|---|---|
| Download Plan | `.txt` | Read on your phone or print |
| Grocery List | `.txt` | Checkbox list for the supermarket |
| Calendar Events | `.ics` | Import into Google/Outlook/Apple Calendar — meals scheduled at realistic times |
| Print | Browser print | Clean black-on-white layout, no dark theme |

## Data

`dishes.csv` contains 153 recipes across:
- **Cuisines**: Indian, European, Fusion
- **Categories**: Breakfast, Snack, Lunch, Dinner
- **All ingredients** are staples available in Polish supermarkets (Biedronka / Lidl)

## Requirements

- Python 3.10+
- `pandas`
- `flask`
