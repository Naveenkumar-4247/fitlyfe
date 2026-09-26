import json
import os
import re
import random
from typing import Any, Dict


try:
    from google import genai
    from google.genai import types
except ImportError:
    genai = None
    types = None


# ============================================================
# ACTIVITY FACTORS
# ============================================================

ACTIVITY_FACTORS = {
    "sedentary": 1.20,
    "light": 1.375,
    "moderate": 1.55,
    "active": 1.725,
    "very_active": 1.90,
}


# ============================================================
# GOAL CALORIE ADJUSTMENTS
# ============================================================

GOAL_ADJUSTMENTS = {
    "weight_loss": -400,
    "weight_gain": 300,
    "muscle_gain": 250,
    "maintenance": 0,
    "general_fitness": 0,
    "endurance": 150,
}


# ============================================================
# AI RESPONSE SCHEMA
# ============================================================

PLAN_SCHEMA = {
    "type": "object",
    "properties": {
        "title": {
            "type": "string"
        },

        "summary": {
            "type": "string"
        },

        "nutrition": {
            "type": "object",
            "properties": {
                "calories": {
                    "type": "integer"
                },
                "protein_g": {
                    "type": "number"
                },
                "carbs_g": {
                    "type": "number"
                },
                "fat_g": {
                    "type": "number"
                },
                "water_l": {
                    "type": "number"
                }
            },
            "required": [
                "calories",
                "protein_g",
                "carbs_g",
                "fat_g",
                "water_l"
            ]
        },

        "meals": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string"
                    },

                    "time": {
                        "type": "string"
                    },

                    "foods": {
                        "type": "array",
                        "description": (
                            "List of individual food items. Every item must "
                            "include a specific quantity and measurement. "
                            "Examples: Oats - 50 g; Milk - 200 ml; "
                            "Banana - 1 medium (120 g); "
                            "Olive oil - 5 ml (1 tsp)."
                        ),
                        "items": {
                            "type": "string"
                        }
                    },

                    "calories": {
                        "type": "integer"
                    },

                    "protein_g": {
                        "type": "number"
                    }
                },

                "required": [
                    "name",
                    "time",
                    "foods",
                    "calories",
                    "protein_g"
                ]
            }
        },

        "hydration": {
            "type": "string"
        },

        "tips": {
            "type": "array",
            "items": {
                "type": "string"
            }
        },

        "safety_note": {
            "type": "string"
        }
    },

    "required": [
        "title",
        "summary",
        "nutrition",
        "meals",
        "hydration",
        "tips",
        "safety_note"
    ]
}


# ============================================================
# SAFE NUMBER CONVERSION
# ============================================================

def _number(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


# ============================================================
# GOAL ALIASES
# ============================================================

GOAL_ALIASES = {
    "lose weight": "weight_loss",
    "lose_weight": "weight_loss",
    "weight loss": "weight_loss",
    "weight-loss": "weight_loss",
    "fat loss": "weight_loss",
    "fat_loss": "weight_loss",

    "maintain": "maintenance",
    "maintenance": "maintenance",
    "maintain weight": "maintenance",
    "weight maintenance": "maintenance",

    "build muscle": "muscle_gain",
    "build_muscle": "muscle_gain",
    "muscle gain": "muscle_gain",
    "muscle-gain": "muscle_gain",
    "gain muscle": "muscle_gain",

    "improve endurance": "endurance",
    "improve_endurance": "endurance",
    "endurance": "endurance",
    "cardio": "endurance",

    "general fitness": "general_fitness",
    "general_fitness": "general_fitness",
    "fitness": "general_fitness",

    "weight gain": "weight_gain",
    "weight_gain": "weight_gain",
    "weight-gain": "weight_gain",
    "gain weight": "weight_gain",
}


# ============================================================
# NORMALIZE GOAL
# ============================================================

def normalize_goal(value: Any) -> str:
    """
    Normalize legacy/display goal values to the canonical AI goal key.
    """

    if value is None:
        return "maintenance"

    raw = str(value).strip().lower()
    raw = re.sub(r"[^a-z0-9]+", "_", raw).strip("_")

    canonical = {
        "weight_loss": "weight_loss",
        "lose_weight": "weight_loss",
        "loseweight": "weight_loss",
        "weightloss": "weight_loss",
        "fat_loss": "weight_loss",
        "fatloss": "weight_loss",

        "maintenance": "maintenance",
        "maintain": "maintenance",
        "maintain_weight": "maintenance",
        "weight_maintenance": "maintenance",

        "muscle_gain": "muscle_gain",
        "build_muscle": "muscle_gain",
        "buildmuscle": "muscle_gain",
        "gain_muscle": "muscle_gain",

        "endurance": "endurance",
        "improve_endurance": "endurance",
        "improveendurance": "endurance",
        "cardio": "endurance",

        "general_fitness": "general_fitness",
        "generalfitness": "general_fitness",
        "fitness": "general_fitness",

        "weight_gain": "weight_gain",
        "gain_weight": "weight_gain",
        "gainweight": "weight_gain",
    }

    if raw in canonical:
        return canonical[raw]

    if any(token in raw for token in ("lose", "loss", "fat")):
        return "weight_loss"

    if any(token in raw for token in ("muscle", "build")):
        return "muscle_gain"

    if any(token in raw for token in ("endurance", "cardio", "stamina")):
        return "endurance"

    if any(token in raw for token in ("gain", "bulk")):
        return "weight_gain"

    if any(token in raw for token in ("maintain", "maintenance")):
        return "maintenance"

    if "fitness" in raw:
        return "general_fitness"

    return "maintenance"


# ============================================================
# CALCULATE PERSONALIZED NUTRITION
# ============================================================

def calculate_nutrition(
    profile: Dict[str, Any],
    sex: str = "prefer_not_to_say"
) -> Dict[str, Any]:

    age = int(
        _number(
            profile.get("age"),
            25
        )
    )

    height = _number(
        profile.get("height"),
        170
    )

    weight = _number(
        profile.get("weight"),
        70
    )

    activity_level = str(
        profile.get(
            "activity_level",
            "moderate"
        )
    ).strip().lower()

    goal = normalize_goal(
        profile.get(
            "goal",
            "maintenance"
        )
    )

    # --------------------------------------------------------
    # SAFETY FALLBACKS
    # --------------------------------------------------------

    if activity_level not in ACTIVITY_FACTORS:
        activity_level = "moderate"

    if goal not in GOAL_ADJUSTMENTS:
        goal = "maintenance"

    if age < 13:
        age = 13

    if height <= 0:
        height = 170

    if weight <= 0:
        weight = 70

    # --------------------------------------------------------
    # BMI
    # --------------------------------------------------------

    height_m = height / 100

    bmi = weight / (
        height_m * height_m
    )

    # --------------------------------------------------------
    # BMR
    # Mifflin-St Jeor equation
    # --------------------------------------------------------

    if sex == "male":

        bmr = (
            10 * weight
            + 6.25 * height
            - 5 * age
            + 5
        )

    elif sex == "female":

        bmr = (
            10 * weight
            + 6.25 * height
            - 5 * age
            - 161
        )

    else:

        bmr = (
            10 * weight
            + 6.25 * height
            - 5 * age
            - 78
        )

    # --------------------------------------------------------
    # TDEE
    # --------------------------------------------------------

    activity_factor = ACTIVITY_FACTORS[
        activity_level
    ]

    tdee = bmr * activity_factor

    # --------------------------------------------------------
    # GOAL ADJUSTMENT
    # --------------------------------------------------------

    adjustment = GOAL_ADJUSTMENTS.get(
        goal,
        0
    )

    target_calories = (
        tdee
        + adjustment
    )

    # --------------------------------------------------------
    # SAFETY RANGE
    # --------------------------------------------------------

    target_calories = max(
        1200,
        min(
            target_calories,
            4500
        )
    )

    target_calories = round(
        target_calories
    )

    # --------------------------------------------------------
    # PROTEIN
    # --------------------------------------------------------

    if goal == "muscle_gain":

        protein_g = weight * 1.8

    elif goal == "weight_loss":

        protein_g = weight * 1.6

    elif goal == "weight_gain":

        protein_g = weight * 1.5

    else:

        protein_g = weight * 1.4

    protein_g = max(
        45,
        min(
            protein_g,
            220
        )
    )

    protein_g = round(
        protein_g,
        1
    )

    # --------------------------------------------------------
    # FAT
    # --------------------------------------------------------

    fat_g = (
        target_calories * 0.25
    ) / 9

    fat_g = round(
        fat_g,
        1
    )

    # --------------------------------------------------------
    # CARBOHYDRATES
    # --------------------------------------------------------

    protein_calories = (
        protein_g * 4
    )

    fat_calories = (
        fat_g * 9
    )

    remaining_calories = (
        target_calories
        - protein_calories
        - fat_calories
    )

    carbs_g = (
        remaining_calories / 4
    )

    carbs_g = max(
        80,
        carbs_g
    )

    carbs_g = round(
        carbs_g,
        1
    )

    # --------------------------------------------------------
    # WATER
    # --------------------------------------------------------

    water_l = weight * 0.033

    water_l = max(
        1.5,
        min(
            water_l,
            5.0
        )
    )

    water_l = round(
        water_l,
        1
    )

    return {
        "bmi": round(
            bmi,
            1
        ),

        "bmr": round(
            bmr
        ),

        "tdee": round(
            tdee
        ),

        "calories": target_calories,

        "protein_g": protein_g,

        "carbs_g": carbs_g,

        "fat_g": fat_g,

        "water_l": water_l
    }


# ============================================================
# RESTRICTION HELPERS FOR LOCAL FALLBACK
# ============================================================

def _split_restrictions(value: str):
    """
    Convert allergy/dislike text into simple lowercase terms.
    Supports commas, semicolons, slashes and 'and'.
    """

    if not value:
        return []

    text = str(value).strip().lower()

    if not text:
        return []

    text = re.sub(
        r"\band\b",
        ",",
        text
    )

    parts = re.split(
        r"[,;/]+",
        text
    )

    result = []

    for part in parts:

        cleaned = part.strip()

        if cleaned:
            result.append(cleaned)

    return result


# ============================================================
# FOOD RESTRICTION KEYWORDS
# ============================================================

FOOD_GROUPS = {

    "fish": [
        "fish",
        "salmon",
        "tuna",
        "sardine",
        "mackerel",
        "rohu",
        "pomfret",
        "anchovy",
        "cod",
        "tilapia",
        "trout"
    ],

    "seafood": [
        "seafood",
        "fish",
        "prawn",
        "prawns",
        "shrimp",
        "crab",
        "lobster",
        "oyster",
        "squid",
        "mussel",
        "clam"
    ],

    "shellfish": [
        "prawn",
        "prawns",
        "shrimp",
        "crab",
        "lobster",
        "oyster",
        "mussel",
        "clam",
        "shellfish"
    ],

    "meat": [
        "meat",
        "chicken",
        "beef",
        "mutton",
        "lamb",
        "pork",
        "turkey",
        "ham",
        "bacon",
        "sausage"
    ],

    "chicken": [
        "chicken"
    ],

    "egg": [
        "egg",
        "eggs",
        "omelette",
        "omelet"
    ],

    "dairy": [
        "milk",
        "curd",
        "yogurt",
        "yoghurt",
        "paneer",
        "cheese",
        "butter",
        "ghee",
        "cream",
        "whey",
        "dairy"
    ],

    "milk": [
        "milk",
        "curd",
        "yogurt",
        "yoghurt",
        "paneer",
        "cheese",
        "butter",
        "ghee",
        "cream",
        "whey"
    ],

    "peanut": [
        "peanut",
        "peanuts",
        "groundnut",
        "groundnuts",
        "peanut butter"
    ],

    "nuts": [
        "almond",
        "almonds",
        "cashew",
        "cashews",
        "walnut",
        "walnuts",
        "pistachio",
        "pistachios",
        "peanut",
        "peanuts",
        "nut",
        "nuts"
    ],

    "soy": [
        "soy",
        "soya",
        "tofu",
        "soy chunks",
        "soy milk",
        "edamame"
    ],

    "gluten": [
        "wheat",
        "bread",
        "roti",
        "chapati",
        "naan",
        "pasta",
        "flour",
        "maida",
        "gluten"
    ]
}


# ============================================================
# EXPAND RESTRICTION TERMS
# ============================================================

def _expand_restriction_terms(
    restrictions
):
    expanded = set()

    for restriction in restrictions:

        restriction = restriction.lower().strip()

        if not restriction:
            continue

        expanded.add(
            restriction
        )

        for group_name, keywords in FOOD_GROUPS.items():

            if (
                restriction == group_name
                or restriction in keywords
                or group_name in restriction
            ):
                expanded.update(
                    keywords
                )

    return expanded


# ============================================================
# CHECK WHETHER FOOD IS ALLOWED
# ============================================================

def _food_is_allowed(
    food: str,
    diet_type: str,
    allergies,
    dislikes
) -> bool:

    food_lower = food.lower()

    allergy_terms = _expand_restriction_terms(
        allergies
    )

    dislike_terms = _expand_restriction_terms(
        dislikes
    )

    # --------------------------------------------------------
    # ALLERGIES ALWAYS TAKE PRIORITY
    # --------------------------------------------------------

    for term in allergy_terms:

        if term and term in food_lower:
            return False

    # --------------------------------------------------------
    # DISLIKES
    # --------------------------------------------------------

    for term in dislike_terms:

        if term and term in food_lower:
            return False

    # --------------------------------------------------------
    # DIET TYPE
    # --------------------------------------------------------

    if diet_type == "vegan":

        forbidden = (
            FOOD_GROUPS["meat"]
            + FOOD_GROUPS["fish"]
            + FOOD_GROUPS["seafood"]
            + FOOD_GROUPS["egg"]
            + FOOD_GROUPS["dairy"]
        )

        for term in forbidden:

            if term in food_lower:
                return False

    elif diet_type == "vegetarian":

        forbidden = (
            FOOD_GROUPS["meat"]
            + FOOD_GROUPS["fish"]
            + FOOD_GROUPS["seafood"]
            + FOOD_GROUPS["egg"]
        )

        for term in forbidden:

            if term in food_lower:
                return False

    elif diet_type == "eggetarian":

        forbidden = (
            FOOD_GROUPS["meat"]
            + FOOD_GROUPS["fish"]
            + FOOD_GROUPS["seafood"]
        )

        for term in forbidden:

            if term in food_lower:
                return False

    return True


# ============================================================
# FILTER A COMPLETE MEAL
# ============================================================

def _meal_is_allowed(
    meal,
    diet_type,
    allergies,
    dislikes
):

    for food in meal:

        if not _food_is_allowed(
            food,
            diet_type,
            allergies,
            dislikes
        ):
            return False

    return True


# ============================================================
# FALLBACK FOOD DATABASE
# ============================================================

BREAKFAST_OPTIONS = {

    "vegan": [
        [
            "Oats — 50 g",
            "Unsweetened soy milk — 250 ml",
            "Banana — 1 medium (120 g)",
            "Chia seeds — 10 g"
        ],
        [
            "Oats — 50 g",
            "Soy milk — 250 ml",
            "Apple — 1 medium (150 g)",
            "Peanut butter — 15 g"
        ],
        [
            "Tofu — 120 g",
            "Whole wheat bread — 2 slices (60 g)",
            "Tomato — 80 g",
            "Banana — 1 medium (120 g)"
        ]
    ],

    "vegetarian": [
        [
            "Oats — 50 g",
            "Milk — 200 ml",
            "Banana — 1 medium (120 g)",
            "Chia seeds — 10 g"
        ],
        [
            "Paneer — 80 g",
            "Whole wheat bread — 2 slices (60 g)",
            "Tomato — 80 g",
            "Apple — 1 medium (150 g)"
        ],
        [
            "Curd — 150 g",
            "Oats — 50 g",
            "Banana — 1 medium (120 g)",
            "Almonds — 15 g"
        ]
    ],

    "eggetarian": [
        [
            "Eggs — 3 whole eggs (150 g)",
            "Oats — 50 g",
            "Banana — 1 medium (120 g)",
            "Milk — 200 ml"
        ],
        [
            "Eggs — 2 whole eggs (100 g)",
            "Whole wheat bread — 2 slices (60 g)",
            "Apple — 1 medium (150 g)",
            "Curd — 100 g"
        ],
        [
            "Egg omelette — 3 eggs (150 g)",
            "Oats — 40 g",
            "Tomato — 80 g",
            "Banana — 1 medium (120 g)"
        ]
    ],

    "non_vegetarian": [
        [
            "Eggs — 3 whole eggs (150 g)",
            "Oats — 50 g",
            "Banana — 1 medium (120 g)",
            "Milk — 200 ml"
        ],
        [
            "Eggs — 2 whole eggs (100 g)",
            "Whole wheat bread — 2 slices (60 g)",
            "Apple — 1 medium (150 g)",
            "Curd — 100 g"
        ],
        [
            "Chicken breast — 100 g",
            "Whole wheat bread — 2 slices (60 g)",
            "Banana — 1 medium (120 g)",
            "Milk — 200 ml"
        ]
    ]
}


# ============================================================
# LUNCH OPTIONS
# ============================================================

LUNCH_OPTIONS = {

    "vegan": [
        [
            "Cooked rice — 180 g",
            "Moong dal — 150 g",
            "Tofu — 120 g",
            "Mixed vegetables — 150 g",
            "Olive oil — 5 ml (1 tsp)"
        ],
        [
            "Roti — 3 pieces (120 g)",
            "Chickpeas — 150 g",
            "Mixed vegetables — 150 g",
            "Tofu — 100 g",
            "Salad — 100 g"
        ],
        [
            "Cooked rice — 180 g",
            "Rajma — 150 g",
            "Tofu — 100 g",
            "Cucumber — 100 g",
            "Olive oil — 5 ml (1 tsp)"
        ]
    ],

    "vegetarian": [
        [
            "Cooked rice — 180 g",
            "Moong dal — 150 g",
            "Paneer — 100 g",
            "Mixed vegetables — 150 g",
            "Curd — 100 g"
        ],
        [
            "Roti — 3 pieces (120 g)",
            "Chickpeas — 150 g",
            "Paneer — 100 g",
            "Mixed vegetables — 150 g",
            "Salad — 100 g"
        ],
        [
            "Cooked rice — 180 g",
            "Rajma — 150 g",
            "Curd — 150 g",
            "Mixed vegetables — 150 g",
            "Paneer — 80 g"
        ]
    ],

    "eggetarian": [
        [
            "Cooked rice — 180 g",
            "Moong dal — 150 g",
            "Eggs — 2 whole eggs (100 g)",
            "Mixed vegetables — 150 g",
            "Curd — 100 g"
        ],
        [
            "Roti — 3 pieces (120 g)",
            "Chickpeas — 150 g",
            "Eggs — 2 whole eggs (100 g)",
            "Mixed vegetables — 150 g",
            "Salad — 100 g"
        ],
        [
            "Cooked rice — 180 g",
            "Rajma — 150 g",
            "Eggs — 2 whole eggs (100 g)",
            "Curd — 100 g",
            "Cucumber — 100 g"
        ]
    ],

    "non_vegetarian": [
        [
            "Cooked rice — 180 g",
            "Chicken breast — 150 g",
            "Mixed vegetables — 150 g",
            "Curd — 100 g",
            "Olive oil — 5 ml (1 tsp)"
        ],
        [
            "Roti — 3 pieces (120 g)",
            "Chicken breast — 150 g",
            "Mixed vegetables — 150 g",
            "Salad — 100 g",
            "Curd — 100 g"
        ],
        [
            "Cooked rice — 180 g",
            "Eggs — 2 whole eggs (100 g)",
            "Chicken breast — 100 g",
            "Vegetables — 150 g",
            "Curd — 100 g"
        ]
    ]
}


# ============================================================
# SNACK OPTIONS
# ============================================================

SNACK_OPTIONS = {

    "vegan": [
        [
            "Apple — 1 medium (150 g)",
            "Peanut butter — 20 g",
            "Roasted chickpeas — 40 g"
        ],
        [
            "Banana — 1 medium (120 g)",
            "Peanuts — 20 g",
            "Soy milk — 200 ml"
        ],
        [
            "Orange — 1 large (180 g)",
            "Roasted chickpeas — 50 g",
            "Pumpkin seeds — 15 g"
        ]
    ],

    "vegetarian": [
        [
            "Apple — 1 medium (150 g)",
            "Curd — 150 g",
            "Almonds — 15 g"
        ],
        [
            "Banana — 1 medium (120 g)",
            "Paneer — 60 g",
            "Almonds — 10 g"
        ],
        [
            "Orange — 1 large (180 g)",
            "Curd — 150 g",
            "Roasted chickpeas — 30 g"
        ]
    ],

    "eggetarian": [
        [
            "Apple — 1 medium (150 g)",
            "Boiled eggs — 2 whole eggs (100 g)",
            "Almonds — 10 g"
        ],
        [
            "Banana — 1 medium (120 g)",
            "Boiled egg — 1 whole egg (50 g)",
            "Curd — 150 g"
        ],
        [
            "Orange — 1 large (180 g)",
            "Boiled eggs — 2 whole eggs (100 g)",
            "Curd — 100 g"
        ]
    ],

    "non_vegetarian": [
        [
            "Apple — 1 medium (150 g)",
            "Boiled eggs — 2 whole eggs (100 g)",
            "Almonds — 10 g"
        ],
        [
            "Banana — 1 medium (120 g)",
            "Boiled egg — 1 whole egg (50 g)",
            "Curd — 150 g"
        ],
        [
            "Orange — 1 large (180 g)",
            "Chicken breast — 80 g",
            "Whole wheat bread — 1 slice (30 g)"
        ]
    ]
}


# ============================================================
# DINNER OPTIONS
# ============================================================

DINNER_OPTIONS = {

    "vegan": [
        [
            "Roti — 3 pieces (120 g)",
            "Tofu — 150 g",
            "Mixed vegetables — 180 g",
            "Dal — 120 g",
            "Olive oil — 5 ml (1 tsp)"
        ],
        [
            "Cooked rice — 180 g",
            "Chickpeas — 150 g",
            "Tofu — 100 g",
            "Vegetables — 180 g",
            "Salad — 100 g"
        ],
        [
            "Roti — 3 pieces (120 g)",
            "Soy chunks — 60 g dry weight",
            "Mixed vegetables — 180 g",
            "Dal — 100 g",
            "Cucumber — 100 g"
        ]
    ],

    "vegetarian": [
        [
            "Roti — 3 pieces (120 g)",
            "Paneer — 120 g",
            "Mixed vegetables — 180 g",
            "Dal — 120 g",
            "Curd — 100 g"
        ],
        [
            "Cooked rice — 180 g",
            "Chickpeas — 150 g",
            "Paneer — 100 g",
            "Vegetables — 180 g",
            "Curd — 100 g"
        ],
        [
            "Roti — 3 pieces (120 g)",
            "Dal — 150 g",
            "Paneer — 100 g",
            "Mixed vegetables — 180 g",
            "Salad — 100 g"
        ]
    ],

    "eggetarian": [
        [
            "Roti — 3 pieces (120 g)",
            "Eggs — 3 whole eggs (150 g)",
            "Mixed vegetables — 180 g",
            "Dal — 120 g",
            "Curd — 100 g"
        ],
        [
            "Cooked rice — 180 g",
            "Eggs — 2 whole eggs (100 g)",
            "Chickpeas — 120 g",
            "Vegetables — 180 g",
            "Curd — 100 g"
        ],
        [
            "Roti — 3 pieces (120 g)",
            "Eggs — 3 whole eggs (150 g)",
            "Dal — 120 g",
            "Mixed vegetables — 180 g",
            "Salad — 100 g"
        ]
    ],

    "non_vegetarian": [
        [
            "Roti — 3 pieces (120 g)",
            "Chicken breast — 150 g",
            "Mixed vegetables — 180 g",
            "Dal — 100 g",
            "Curd — 100 g"
        ],
        [
            "Cooked rice — 180 g",
            "Chicken breast — 150 g",
            "Vegetables — 180 g",
            "Salad — 100 g",
            "Curd — 100 g"
        ],
        [
            "Roti — 3 pieces (120 g)",
            "Eggs — 2 whole eggs (100 g)",
            "Chicken breast — 100 g",
            "Mixed vegetables — 180 g",
            "Curd — 100 g"
        ]
    ]
}


# ============================================================
# SAFE EMERGENCY MEAL
# ============================================================

def _safe_emergency_meal(
    diet_type,
    allergies,
    dislikes
):

    candidates = {

        "vegan": [
            "Cooked rice — 150 g",
            "Moong dal — 150 g",
            "Banana — 1 medium (120 g)",
            "Mixed vegetables — 150 g"
        ],

        "vegetarian": [
            "Cooked rice — 150 g",
            "Moong dal — 150 g",
            "Curd — 100 g",
            "Mixed vegetables — 150 g"
        ],

        "eggetarian": [
            "Cooked rice — 150 g",
            "Moong dal — 150 g",
            "Eggs — 2 whole eggs (100 g)",
            "Mixed vegetables — 150 g"
        ],

        "non_vegetarian": [
            "Cooked rice — 150 g",
            "Chicken breast — 120 g",
            "Mixed vegetables — 150 g",
            "Salad — 100 g"
        ]
    }

    selected = []

    for food in candidates.get(
        diet_type,
        candidates["non_vegetarian"]
    ):

        if _food_is_allowed(
            food,
            diet_type,
            allergies,
            dislikes
        ):
            selected.append(food)

    if selected:
        return selected

    # Extremely restrictive case:
    # return simple foods that are checked again.

    neutral_foods = [
        "Cooked rice — 150 g",
        "Apple — 1 medium (150 g)",
        "Cucumber — 100 g"
    ]

    safe_neutral = []

    for food in neutral_foods:

        if _food_is_allowed(
            food,
            diet_type,
            allergies,
            dislikes
        ):
            safe_neutral.append(food)

    return safe_neutral or [
        "Plain cooked rice — 150 g"
    ]


# ============================================================
# CHOOSE SAFE MEAL
# ============================================================

def _choose_safe_meal(
    options,
    diet_type,
    allergies,
    dislikes,
    used_meals
):

    safe_options = []

    for meal in options:

        if _meal_is_allowed(
            meal,
            diet_type,
            allergies,
            dislikes
        ):

            meal_key = tuple(meal)

            if meal_key not in used_meals:
                safe_options.append(meal)

    # If every unique option has already been used,
    # allow a previously used safe option.

    if not safe_options:

        for meal in options:

            if _meal_is_allowed(
                meal,
                diet_type,
                allergies,
                dislikes
            ):
                safe_options.append(meal)

    if safe_options:

        selected = random.choice(
            safe_options
        )

        used_meals.add(
            tuple(selected)
        )

        return selected

    return _safe_emergency_meal(
        diet_type,
        allergies,
        dislikes
    )


# ============================================================
# FALLBACK PLAN
# ============================================================

def _fallback_plan(
    name,
    nutrition,
    diet_type,
    meals_per_day,
    cuisine,
    budget,
    allergies,
    dislikes,
    goal,
):
    """
    Reliable local wellness plan when Gemini is unavailable.

    This fallback:
    - respects diet type
    - respects allergies
    - respects dislikes
    - gives measured food quantities
    - varies meal combinations
    - keeps the requested meal count
    """

    # --------------------------------------------------------
    # NORMALIZE DIET TYPE
    # --------------------------------------------------------

    diet_type = str(
        diet_type or "non_vegetarian"
    ).strip().lower()

    valid_diets = {
        "vegan",
        "vegetarian",
        "eggetarian",
        "non_vegetarian"
    }

    if diet_type not in valid_diets:
        diet_type = "non_vegetarian"

    # --------------------------------------------------------
    # RESTRICTIONS
    # --------------------------------------------------------

    allergy_list = _split_restrictions(
        allergies
    )

    dislike_list = _split_restrictions(
        dislikes
    )

    # --------------------------------------------------------
    # MEAL COUNT
    # --------------------------------------------------------

    try:
        count = int(
            meals_per_day
        )
    except (
        TypeError,
        ValueError
    ):
        count = 4

    count = max(
        2,
        min(
            6,
            count
        )
    )

    # --------------------------------------------------------
    # MEAL NAMES
    # --------------------------------------------------------

    names = [
        "Breakfast",
        "Mid-morning",
        "Lunch",
        "Evening Snack",
        "Dinner",
        "Post-workout"
    ]

    times = [
        "07:30",
        "10:30",
        "13:00",
        "16:30",
        "20:00",
        "21:30"
    ]

    # --------------------------------------------------------
    # AVAILABLE OPTIONS
    # --------------------------------------------------------

    breakfast_options = BREAKFAST_OPTIONS[
        diet_type
    ]

    lunch_options = LUNCH_OPTIONS[
        diet_type
    ]

    snack_options = SNACK_OPTIONS[
        diet_type
    ]

    dinner_options = DINNER_OPTIONS[
        diet_type
    ]

    # --------------------------------------------------------
    # BUILD A VARIED MEAL SEQUENCE
    # --------------------------------------------------------

    meal_option_groups = []

    if count >= 1:

        meal_option_groups.append(
            breakfast_options
        )

    if count >= 2:

        meal_option_groups.append(
            snack_options
        )

    if count >= 3:

        meal_option_groups.append(
            lunch_options
        )

    if count >= 4:

        meal_option_groups.append(
            snack_options
        )

    if count >= 5:

        meal_option_groups.append(
            dinner_options
        )

    if count >= 6:

        meal_option_groups.append(
            snack_options
        )

    # --------------------------------------------------------
    # GENERATE MEALS
    # --------------------------------------------------------

    used_meals = set()

    meals = []

    each_cal = max(
        150,
        round(
            nutrition["calories"] / count
        )
    )

    each_protein = round(
        nutrition["protein_g"] / count,
        1
    )

    for index in range(count):

        options = meal_option_groups[index]

        selected_foods = _choose_safe_meal(
            options,
            diet_type,
            allergy_list,
            dislike_list,
            used_meals
        )

        meals.append(
            {
                "name": names[index],
                "time": times[index],
                "foods": selected_foods,
                "calories": each_cal,
                "protein_g": each_protein
            }
        )

    # --------------------------------------------------------
    # SAFETY CHECK
    # --------------------------------------------------------

    # Final verification:
    # every food returned by fallback must satisfy
    # the diet, allergy and dislike rules.

    for meal in meals:

        verified_foods = []

        for food in meal["foods"]:

            if _food_is_allowed(
                food,
                diet_type,
                allergy_list,
                dislike_list
            ):
                verified_foods.append(food)

        if not verified_foods:

            verified_foods = _safe_emergency_meal(
                diet_type,
                allergy_list,
                dislike_list
            )

        meal["foods"] = verified_foods

    # --------------------------------------------------------
    # RETURN FALLBACK PLAN
    # --------------------------------------------------------

    return {
        "title": (
            f"Personalized FitLyfe Plan for {name}"
        ),

        "summary": (
            f"A practical "
            f"{cuisine or 'balanced'} wellness plan "
            f"for your "
            f"{goal.replace('_', ' ')} goal."
        ),

        "nutrition": {
            "calories": nutrition["calories"],
            "protein_g": nutrition["protein_g"],
            "carbs_g": nutrition["carbs_g"],
            "fat_g": nutrition["fat_g"],
            "water_l": nutrition["water_l"],
        },

        "meals": meals,

        "hydration": (
            f"Target about "
            f"{nutrition['water_l']} L of water "
            f"throughout the day."
        ),

        "tips": [
            "Keep portions consistent with your calorie target.",
            "Include a protein source in each main meal.",
            "Prefer minimally processed foods most of the time.",
            f"Use sustainable {budget} food choices.",
            "Track your routine in FitLyfe so your insights improve over time."
        ],

        "safety_note": (
            "General wellness guidance only. "
            "For medical conditions, pregnancy, "
            "eating disorders or severe allergies, "
            "consult a qualified professional."
        )
    }


# ============================================================
# GENERATE AI DIET PLAN
# ============================================================

def generate_diet_plan(
    profile: Dict[str, Any],
    preferences: Dict[str, Any]
) -> Dict[str, Any]:

    # ========================================================
    # GEMINI API KEY
    # ========================================================

    api_key = os.getenv(
        "GEMINI_API_KEY"
    )

    client = None

    if api_key and genai is not None:

        client = genai.Client(
            api_key=api_key
        )

    # ========================================================
    # PROFILE
    # ========================================================

    name = str(
        profile.get(
            "name",
            "User"
        )
    )

    age = int(
        _number(
            profile.get(
                "age"
            ),
            25
        )
    )

    height = _number(
        profile.get(
            "height"
        ),
        170
    )

    weight = _number(
        profile.get(
            "weight"
        ),
        70
    )

    activity_level = str(
        profile.get(
            "activity_level",
            "moderate"
        )
    ).strip().lower()

    goal = normalize_goal(
        profile.get(
            "goal",
            "maintenance"
        )
    )

    # ========================================================
    # PREFERENCES
    # ========================================================

    diet_type = str(
        preferences.get(
            "diet_type",
            "non_vegetarian"
        )
    ).strip().lower()

    meals_per_day = int(
        _number(
            preferences.get(
                "meals_per_day",
                4
            ),
            4
        )
    )

    meals_per_day = max(
        2,
        min(
            6,
            meals_per_day
        )
    )

    sex = str(
        preferences.get(
            "sex",
            "prefer_not_to_say"
        )
    ).strip().lower()

    allergies = str(
        preferences.get(
            "allergies",
            ""
        )
    ).strip()

    dislikes = str(
        preferences.get(
            "dislikes",
            ""
        )
    ).strip()

    cuisine = str(
        preferences.get(
            "cuisine",
            ""
        )
    ).strip()

    budget = str(
        preferences.get(
            "budget",
            "moderate"
        )
    ).strip().lower()

    # ========================================================
    # CALCULATE NUTRITION TARGETS
    # ========================================================

    nutrition = calculate_nutrition(
        profile={
            "age": age,
            "height": height,
            "weight": weight,
            "activity_level": activity_level,
            "goal": goal
        },
        sex=sex
    )

    # ========================================================
    # DEBUG INFORMATION
    # ========================================================

    print(
        "\n"
        "============================================================"
    )

    print(
        "FITLYFE GEMINI DIET GENERATION"
    )

    print(
        "============================================================"
    )

    print(
        "Model:",
        os.getenv(
            "GEMINI_DIET_MODEL",
            "gemini-2.5-flash"
        )
    )

    print(
        "User:",
        name
    )

    print(
        "Age:",
        age
    )

    print(
        "Height:",
        height
    )

    print(
        "Weight:",
        weight
    )

    print(
        "Activity:",
        activity_level
    )

    print(
        "Goal:",
        goal
    )

    print(
        "Diet:",
        diet_type
    )

    print(
        "Meals:",
        meals_per_day
    )

    print(
        "Cuisine:",
        cuisine
    )

    print(
        "Budget:",
        budget
    )

    print(
        "Allergies:",
        allergies or "None"
    )

    print(
        "Dislikes:",
        dislikes or "None"
    )

    print(
        "Target Calories:",
        nutrition["calories"]
    )

    print(
        "Target Protein:",
        nutrition["protein_g"]
    )

    print(
        "============================================================"
    )

    # ========================================================
    # ALLERGY INSTRUCTION
    # ========================================================

    if allergies:

        allergy_instruction = (
            f"The user has the following allergies: "
            f"{allergies}. "
            f"DO NOT include any of these foods or "
            f"obvious ingredients containing them. "
            f"This rule is absolute."
        )

    else:

        allergy_instruction = (
            "The user has not listed any food allergies."
        )

    # ========================================================
    # DISLIKE INSTRUCTION
    # ========================================================

    if dislikes:

        dislike_instruction = (
            f"The user dislikes: {dislikes}. "
            f"Avoid these foods whenever reasonably possible."
        )

    else:

        dislike_instruction = (
            "The user has not listed any food dislikes."
        )

    # ========================================================
    # CUISINE INSTRUCTION
    # ========================================================

    if cuisine:

        cuisine_instruction = (
            f"Prefer foods and meal ideas from the "
            f"{cuisine} cuisine."
        )

    else:

        cuisine_instruction = (
            "Use practical foods commonly available "
            "to the user."
        )

    # ========================================================
    # PROMPT
    # ========================================================

    prompt = f"""
You are the AI nutrition planning assistant for FitLyfe,
a fitness and daily routine analytics website.

Create a personalized GENERAL-WELLNESS diet plan.

The plan must be based on the user's actual profile,
fitness goal and food preferences.

============================================================
USER PROFILE
============================================================

Name: {name}
Age: {age}
Height: {height} cm
Weight: {weight} kg
Activity Level: {activity_level}
Fitness Goal: {goal}
Sex Preference: {sex}

============================================================
FOOD PREFERENCES
============================================================

Diet Type: {diet_type}
Meals Per Day: {meals_per_day}
Budget: {budget}
Cuisine Preference: {cuisine or "No specific cuisine"}

Allergies:
{allergies or "None provided"}

Dislikes:
{dislikes or "None provided"}

============================================================
CALCULATED NUTRITION TARGETS
============================================================

Target Calories:
{nutrition["calories"]} kcal/day

Target Protein:
{nutrition["protein_g"]} g/day

Target Carbohydrates:
{nutrition["carbs_g"]} g/day

Target Fat:
{nutrition["fat_g"]} g/day

Target Water:
{nutrition["water_l"]} L/day

BMI Estimate:
{nutrition["bmi"]}

BMR Estimate:
{nutrition["bmr"]}

TDEE Estimate:
{nutrition["tdee"]}

============================================================
IMPORTANT REQUIREMENTS
============================================================

1. Generate EXACTLY {meals_per_day} meals.

2. The number of meals must be exactly {meals_per_day}.

3. Respect the selected diet type:

   - vegetarian = NO meat, fish, seafood or eggs
   - vegan = NO meat, fish, seafood, eggs or dairy
   - eggetarian = eggs allowed but NO meat, fish or seafood
   - non_vegetarian = meat, eggs and seafood may be used

4. {allergy_instruction}

5. {dislike_instruction}

6. {cuisine_instruction}

7. Respect the selected budget:

   - budget = affordable and common foods
   - moderate = balanced cost and variety
   - premium = more variety and premium food options

8. Use realistic food portions.

9. EVERY individual food item in the "foods" array MUST include
   a clear quantity and measurement.

   REQUIRED FORMAT EXAMPLES:

   - "Oats — 50 g"
   - "Cooked rice — 150 g"
   - "Chicken breast — 120 g"
   - "Milk — 200 ml"
   - "Curd — 150 g"
   - "Banana — 1 medium (120 g)"
   - "Eggs — 2 whole eggs (100 g)"
   - "Roti — 2 pieces (80 g)"
   - "Olive oil — 5 ml (1 tsp)"
   - "Almonds — 15 g (about 10 almonds)"

   Use practical units such as g, kg, ml, tsp, tbsp, cup,
   pieces, slices, or a count with an approximate gram/ml amount.

   Do NOT output vague entries such as:

   - "Vegetable omelette with oats and fruit"
   - "Rice with chicken and vegetables"
   - "Healthy snack"
   - "A bowl of salad"

   Instead, break the meal into individual measured food items.

10. Give practical meal times.

11. Include calories and protein for every meal.

12. Keep total daily calories reasonably close to:
    {nutrition["calories"]} kcal.

13. Keep total protein reasonably close to:
    {nutrition["protein_g"]} g.

14. Use common foods that a normal person can realistically prepare.

15. Do not recommend starvation diets.

16. Do not recommend extremely low calorie diets.

17. Do not diagnose diseases.

18. Do not prescribe medical treatment.

19. Do not claim that the diet can cure diseases.

20. This is a general wellness plan, not medical advice.

21. If the user has a medical condition, is pregnant,
    has an eating disorder, or has a severe food allergy,
    recommend consulting an appropriately qualified
    healthcare professional.

22. Make the plan useful, practical and easy to follow.

23. Return ONLY the requested structured JSON object.
"""

    # ========================================================
    # GEMINI MODEL
    # ========================================================

    model = os.getenv(
        "GEMINI_DIET_MODEL",
        "gemini-2.5-flash"
    )

    # ========================================================
    # GENERATE RESPONSE
    # ========================================================

    response_text = None

    if client is not None:

        try:

            response = client.models.generate_content(
                model=model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_json_schema=PLAN_SCHEMA
                )
            )

            response_text = getattr(
                response,
                "text",
                None
            )

        except Exception as exc:

            print(
                "GEMINI GENERATION WARNING:",
                exc
            )

    # ========================================================
    # FALLBACK
    # ========================================================

    if not response_text:

        print(
            "Using FitLyfe local diet fallback."
        )

        return _fallback_plan(
            name=name,
            nutrition=nutrition,
            diet_type=diet_type,
            meals_per_day=meals_per_day,
            cuisine=cuisine,
            budget=budget,
            allergies=allergies,
            dislikes=dislikes,
            goal=goal,
        )

    # ========================================================
    # READ RESPONSE
    # ========================================================

    response_text = response_text.strip()

    # ========================================================
    # REMOVE ACCIDENTAL MARKDOWN FENCES
    # ========================================================

    if response_text.startswith("```"):

        response_text = (
            response_text
            .replace(
                "```json",
                ""
            )
            .replace(
                "```",
                ""
            )
            .strip()
        )

    # ========================================================
    # PARSE JSON
    # ========================================================

    try:

        plan = json.loads(
            response_text
        )

    except json.JSONDecodeError as exc:

        print(
            "GEMINI RAW RESPONSE:"
        )

        print(
            response_text
        )

        raise RuntimeError(
            "Gemini returned invalid JSON."
        ) from exc

    # ========================================================
    # BASIC VALIDATION
    # ========================================================

    if not isinstance(
        plan,
        dict
    ):

        raise RuntimeError(
            "Gemini returned an invalid diet plan."
        )

    required_sections = [
        "title",
        "summary",
        "nutrition",
        "meals",
        "hydration",
        "tips",
        "safety_note"
    ]

    for section in required_sections:

        if section not in plan:

            raise RuntimeError(
                f"Gemini diet plan is missing: {section}"
            )

    # ========================================================
    # MEAL VALIDATION
    # ========================================================

    meals = plan.get(
        "meals",
        []
    )

    if not isinstance(
        meals,
        list
    ):

        raise RuntimeError(
            "Gemini returned an invalid meals list."
        )

    if len(meals) != meals_per_day:

        raise RuntimeError(
            "Gemini returned the wrong number of meals."
        )

    # ========================================================
    # NUTRITION VALIDATION
    # ========================================================

    plan_nutrition = plan.get(
        "nutrition"
    )

    if not isinstance(
        plan_nutrition,
        dict
    ):

        raise RuntimeError(
            "Gemini returned invalid nutrition information."
        )

    # ========================================================
    # ATTACH CALCULATED INFORMATION
    # ========================================================

    plan["_calculated"] = nutrition

    plan["_inputs"] = {
        "profile": {
            "name": name,
            "age": age,
            "height": height,
            "weight": weight,
            "activity_level": activity_level,
            "goal": goal
        },

        "preferences": {
            "diet_type": diet_type,
            "meals_per_day": meals_per_day,
            "sex": sex,
            "allergies": allergies,
            "dislikes": dislikes,
            "cuisine": cuisine,
            "budget": budget
        }
    }

    print(
        "FITLYFE GEMINI DIET PLAN GENERATED SUCCESSFULLY"
    )

    return plan