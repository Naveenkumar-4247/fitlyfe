import json
import os
import re
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

def _number(
    value: Any,
    default: float = 0.0
) -> float:

    try:
        return float(value)

    except (TypeError, ValueError):
        return default


# ============================================================
# CALCULATE PERSONALIZED NUTRITION
# ============================================================

GOAL_ALIASES = {
    "lose weight": "weight_loss", "lose_weight": "weight_loss",
    "weight loss": "weight_loss", "weight-loss": "weight_loss",
    "fat loss": "weight_loss", "fat_loss": "weight_loss",
    "maintain": "maintenance", "maintenance": "maintenance",
    "maintain weight": "maintenance", "weight maintenance": "maintenance",
    "build muscle": "muscle_gain", "build_muscle": "muscle_gain",
    "muscle gain": "muscle_gain", "muscle-gain": "muscle_gain",
    "gain muscle": "muscle_gain",
    "improve endurance": "endurance", "improve_endurance": "endurance",
    "endurance": "endurance", "cardio": "endurance",
    "general fitness": "general_fitness", "general_fitness": "general_fitness",
    "fitness": "general_fitness",
    "weight gain": "weight_gain", "weight_gain": "weight_gain",
    "weight-gain": "weight_gain", "gain weight": "weight_gain",
}


def normalize_goal(value):
    """Normalize legacy/display goal values to the canonical AI goal key."""
    if value is None:
        return "maintenance"

    raw = str(value).strip().lower()
    raw = re.sub(r"[^a-z0-9]+", "_", raw).strip("_")

    canonical = {
        "weight_loss": "weight_loss", "lose_weight": "weight_loss",
        "loseweight": "weight_loss", "weightloss": "weight_loss",
        "fat_loss": "weight_loss", "fatloss": "weight_loss",
        "maintenance": "maintenance", "maintain": "maintenance",
        "maintain_weight": "maintenance", "weight_maintenance": "maintenance",
        "muscle_gain": "muscle_gain", "build_muscle": "muscle_gain",
        "buildmuscle": "muscle_gain", "gain_muscle": "muscle_gain",
        "endurance": "endurance", "improve_endurance": "endurance",
        "improveendurance": "endurance", "cardio": "endurance",
        "general_fitness": "general_fitness", "generalfitness": "general_fitness",
        "fitness": "general_fitness",
        "weight_gain": "weight_gain", "gain_weight": "weight_gain",
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
    #
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

        # Neutral estimate when sex
        # is not provided.

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
    #
    # General wellness estimate.
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
    #
    # Approximately 25% of calories.
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
    #
    # Remaining calories.
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
    #
    # General estimate based on body weight.
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
# GENERATE AI DIET PLAN
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
    """Reliable local wellness plan when Gemini is unavailable."""

    vegan = diet_type == "vegan"
    vegetarian = diet_type in {"vegetarian", "eggetarian"}

    if vegan:
        proteins = ["tofu", "soy chunks", "moong dal", "chickpeas", "peanuts"]
        breakfast = "Oats with banana, chia seeds and peanuts"
    elif vegetarian:
        proteins = ["paneer", "curd", "moong dal", "chickpeas", "eggs"]
        breakfast = "Vegetable oats with curd and fruit"
    else:
        proteins = ["eggs", "chicken", "fish", "curd", "dal"]
        breakfast = "Vegetable omelette with oats and fruit"

    foods = [
        breakfast,
        f"Rice or roti with dal, vegetables and {proteins[0]}",
        f"Fruit with {proteins[1]}",
        f"Balanced dinner with vegetables, rice/roti and {proteins[2]}",
        f"Light snack with {proteins[3]}",
        f"Protein-focused meal with {proteins[4]} and vegetables",
    ]
    names = ["Breakfast", "Mid-morning", "Lunch", "Evening snack", "Dinner", "Post-workout"]
    times = ["07:30", "10:30", "13:00", "16:30", "20:00", "21:30"]
    count = max(2, min(6, int(meals_per_day)))
    each_cal = max(150, round(nutrition["calories"] / count))
    each_protein = round(nutrition["protein_g"] / count, 1)

    meals = [
        {
            "name": names[i],
            "time": times[i],
            "foods": [foods[i]],
            "calories": each_cal,
            "protein_g": each_protein,
        }
        for i in range(count)
    ]

    return {
        "title": f"Personalized FitLyfe Plan for {name}",
        "summary": (
            f"A practical {cuisine or 'balanced'} wellness plan for your "
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
        "hydration": f"Target about {nutrition['water_l']} L of water throughout the day.",
        "tips": [
            "Keep portions consistent with your calorie target.",
            "Include a protein source in each main meal.",
            "Prefer minimally processed foods most of the time.",
            f"Use sustainable {budget} food choices.",
            "Track your routine in FitLyfe so your insights improve over time.",
        ],
        "safety_note": (
            "General wellness guidance only. For medical conditions, pregnancy, "
            "eating disorders or severe allergies, consult a qualified professional."
        ),
    }


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
        client = genai.Client(api_key=api_key)

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
            f"obvious ingredients containing them."
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
   - vegetarian = no meat, fish or seafood
   - vegan = no meat, fish, seafood, eggs or dairy
   - eggetarian = eggs allowed but no meat or seafood
   - non_vegetarian = meat, eggs and seafood may be used

4. {allergy_instruction}

5. {dislike_instruction}

6. {cuisine_instruction}

7. Respect the selected budget:
   - budget = affordable and common foods
   - moderate = balanced cost and variety
   - premium = more variety and premium food options

8. Use realistic food portions.

9. Give practical meal times.

10. Include calories and protein for every meal.

11. Keep total daily calories reasonably close to:
    {nutrition["calories"]} kcal.

12. Keep total protein reasonably close to:
    {nutrition["protein_g"]} g.

13. Use common foods that a normal person can realistically prepare.

14. Do not recommend starvation diets.

15. Do not recommend extremely low calorie diets.

16. Do not diagnose diseases.

17. Do not prescribe medical treatment.

18. Do not claim that the diet can cure diseases.

19. This is a general wellness plan, not medical advice.

20. If the user has a medical condition, is pregnant,
    has an eating disorder, or has a severe food allergy,
    recommend consulting an appropriately qualified
    healthcare professional.

21. Make the plan useful, practical and easy to follow.

22. Return ONLY the requested structured JSON object.
"""

    # ========================================================
    # GEMINI MODEL
    # ========================================================

    model = os.getenv(
        "GEMINI_DIET_MODEL",
        "gemini-2.5-flash"
    )

    # ========================================================
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
            response_text = getattr(response, "text", None)
        except Exception as exc:
            print("GEMINI GENERATION WARNING:", exc)

    if not response_text:
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