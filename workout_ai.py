# ============================================================
# FITLYFE - AI WORKOUT GENERATOR
# Gemini-powered personalized workout generation
# ============================================================

import os
import json
import random
from datetime import datetime

try:
    from google import genai
except ImportError:
    genai = None


# ============================================================
# CONFIGURATION
# ============================================================

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
MODEL_NAME = os.getenv(
    "GEMINI_WORKOUT_MODEL",
    "gemini-2.5-flash"
)


# ============================================================
# LOCAL EXERCISE KNOWLEDGE
# Used only as reference in the AI prompt and emergency fallback.
# ============================================================

EXERCISES = {

    "chest": [
        "Barbell Bench Press",
        "Incline Dumbbell Press",
        "Machine Chest Press",
        "Cable Chest Fly",
        "Pec Deck Fly",
        "Incline Machine Press",
        "Dumbbell Bench Press",
        "Decline Bench Press",
        "Push-Ups",
    ],

    "back": [
        "Barbell Row",
        "Seated Cable Row",
        "Chest-Supported Row",
        "T-Bar Row",
        "Single-Arm Dumbbell Row",
        "Machine Row",
        "Back Extension",
    ],

    "lats": [
        "Lat Pulldown",
        "Wide-Grip Lat Pulldown",
        "Close-Grip Lat Pulldown",
        "Assisted Pull-Up",
        "Pull-Ups",
        "Single-Arm Lat Pulldown",
        "Straight-Arm Pulldown",
    ],

    "shoulders": [
        "Dumbbell Shoulder Press",
        "Machine Shoulder Press",
        "Arnold Press",
        "Cable Lateral Raise",
        "Dumbbell Lateral Raise",
        "Rear Delt Fly",
        "Face Pull",
        "Cable Front Raise",
    ],

    "biceps": [
        "Barbell Curl",
        "EZ-Bar Curl",
        "Incline Dumbbell Curl",
        "Hammer Curl",
        "Cable Curl",
        "Preacher Curl",
        "Concentration Curl",
    ],

    "triceps": [
        "Rope Triceps Pushdown",
        "Cable Triceps Pushdown",
        "Overhead Cable Extension",
        "Skull Crushers",
        "Close-Grip Bench Press",
        "Dumbbell Overhead Extension",
        "Bench Dips",
    ],

    "legs": [
        "Barbell Squat",
        "Leg Press",
        "Romanian Deadlift",
        "Walking Lunges",
        "Bulgarian Split Squat",
        "Leg Extension",
        "Leg Curl",
        "Standing Calf Raise",
        "Seated Calf Raise",
    ],

    "core": [
        "Cable Crunch",
        "Hanging Knee Raise",
        "Hanging Leg Raise",
        "Plank",
        "Ab Wheel Rollout",
        "Dead Bug",
        "Russian Twist",
        "Bicycle Crunch",
    ],

    "glutes": [
        "Barbell Hip Thrust",
        "Glute Bridge",
        "Bulgarian Split Squat",
        "Walking Lunges",
        "Cable Kickback",
        "Step-Ups",
        "Romanian Deadlift",
    ],

    "forearms": [
        "Wrist Curl",
        "Reverse Wrist Curl",
        "Farmer's Carry",
        "Reverse Curl",
        "Plate Pinch Hold",
    ],

    "push": [
        "Barbell Bench Press",
        "Incline Dumbbell Press",
        "Dumbbell Shoulder Press",
        "Dumbbell Lateral Raise",
        "Cable Chest Fly",
        "Rope Triceps Pushdown",
        "Overhead Triceps Extension",
    ],

    "pull": [
        "Lat Pulldown",
        "Seated Cable Row",
        "Single-Arm Dumbbell Row",
        "Face Pull",
        "Barbell Curl",
        "Hammer Curl",
        "Preacher Curl",
    ],
}


# ============================================================
# HELPERS
# ============================================================

def _safe_int(value, default=0):
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return default


def _safe_float(value, default=0):
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _clean_text(value, default=""):
    if value is None:
        return default

    return str(value).strip()


def _normalize_goal(value):

    raw = _clean_text(value).lower()

    aliases = {
        "lose weight": "weight_loss",
        "weight loss": "weight_loss",
        "fat loss": "weight_loss",
        "lose_weight": "weight_loss",
        "weight_loss": "weight_loss",

        "maintain": "maintenance",
        "maintenance": "maintenance",
        "maintain weight": "maintenance",

        "build muscle": "muscle_gain",
        "muscle gain": "muscle_gain",
        "gain muscle": "muscle_gain",
        "muscle_gain": "muscle_gain",

        "endurance": "endurance",
        "cardio": "endurance",

        "fitness": "general_fitness",
        "general fitness": "general_fitness",
        "general_fitness": "general_fitness",

        "weight gain": "weight_gain",
        "gain weight": "weight_gain",
        "weight_gain": "weight_gain",
    }

    return aliases.get(
        raw,
        raw.replace(" ", "_")
    )


def _normalize_activity(value):

    raw = _clean_text(value).lower()

    aliases = {
        "low": "sedentary",
        "sedentary": "sedentary",

        "light": "light",
        "lightly active": "light",

        "moderate": "moderate",
        "moderately active": "moderate",

        "active": "active",

        "very active": "very_active",
        "very_active": "very_active",
    }

    return aliases.get(raw, raw)


def _normalize_equipment(value):

    raw = _clean_text(value, "gym").lower()

    if raw in {
        "home",
        "bodyweight",
        "body weight",
        "no equipment"
    }:
        return "home/bodyweight"

    if raw in {
        "dumbbell",
        "dumbbells"
    }:
        return "dumbbells"

    if raw in {
        "gym",
        "full gym",
        "commercial gym"
    }:
        return "full gym"

    return raw


# ============================================================
# EXTRACT EXERCISES FROM ANY PLAN
# ============================================================

def _walk_plan_for_exercises(value, result):

    if isinstance(value, dict):

        for key, item in value.items():

            key_lower = str(key).lower()

            if key_lower in {
                "exercise",
                "exercise_name",
                "movement",
                "name"
            }:

                if isinstance(item, str):

                    name = item.strip()

                    if name:
                        result.append(name)

            _walk_plan_for_exercises(
                item,
                result
            )

    elif isinstance(value, list):

        for item in value:

            _walk_plan_for_exercises(
                item,
                result
            )


def _extract_previous_exercises(previous_workouts):

    names = []

    if not previous_workouts:
        return names

    for workout in previous_workouts:

        if isinstance(workout, dict):

            existing_names = workout.get(
                "exercise_names",
                []
            )

            if isinstance(
                existing_names,
                list
            ):

                names.extend(
                    existing_names
                )

            plan = workout.get(
                "plan"
            )

            if plan:
                _walk_plan_for_exercises(
                    plan,
                    names
                )

            workout_data = workout.get(
                "workout"
            )

            if workout_data:
                _walk_plan_for_exercises(
                    workout_data,
                    names
                )

        else:

            _walk_plan_for_exercises(
                workout,
                names
            )

    unique = []
    seen = set()

    for name in names:

        normalized = (
            str(name)
            .strip()
            .lower()
        )

        if (
            normalized
            and normalized not in seen
        ):

            seen.add(
                normalized
            )

            unique.append(
                str(name).strip()
            )

    return unique


# ============================================================
# EXERCISE DATABASE FOR PROMPT
# ============================================================

def _relevant_exercises(focus):

    focus_lower = _clean_text(
        focus
    ).lower()

    database = []

    if focus_lower in EXERCISES:

        database.extend(
            EXERCISES[focus_lower]
        )

    elif "chest" in focus_lower:

        database.extend(
            EXERCISES["chest"]
        )

    elif "back" in focus_lower:

        database.extend(
            EXERCISES["back"]
        )
        database.extend(
            EXERCISES["lats"]
        )

    elif "lat" in focus_lower:

        database.extend(
            EXERCISES["lats"]
        )

    elif "shoulder" in focus_lower:

        database.extend(
            EXERCISES["shoulders"]
        )

    elif "bicep" in focus_lower:

        database.extend(
            EXERCISES["biceps"]
        )

    elif "tricep" in focus_lower:

        database.extend(
            EXERCISES["triceps"]
        )

    elif "leg" in focus_lower:

        database.extend(
            EXERCISES["legs"]
        )

    elif "core" in focus_lower:

        database.extend(
            EXERCISES["core"]
        )

    elif "glute" in focus_lower:

        database.extend(
            EXERCISES["glutes"]
        )

    elif "forearm" in focus_lower:

        database.extend(
            EXERCISES["forearms"]
        )

    elif "push" in focus_lower:

        database.extend(
            EXERCISES["push"]
        )

    elif "pull" in focus_lower:

        database.extend(
            EXERCISES["pull"]
        )

    else:

        for items in EXERCISES.values():
            database.extend(items)

    # Remove duplicates.
    return list(
        dict.fromkeys(database)
    )


# ============================================================
# GEMINI CLIENT
# ============================================================

def _get_gemini_client():

    if genai is None:

        raise RuntimeError(
            "google-genai package is not installed."
        )

    if not GEMINI_API_KEY:

        raise RuntimeError(
            "GEMINI_API_KEY is not configured."
        )

    return genai.Client(
        api_key=GEMINI_API_KEY
    )


# ============================================================
# PROMPT
# ============================================================

def _build_prompt(
    profile,
    preferences,
    previous_workouts=None
):

    previous_workouts = (
        previous_workouts or []
    )

    generation_number = _safe_int(
        preferences.get(
            "generation_number",
            1
        ),
        1
    )

    focus = _clean_text(
        preferences.get(
            "focus",
            "Full Body"
        ),
        "Full Body"
    )

    duration = _safe_int(
        preferences.get(
            "duration_minutes",
            60
        ),
        60
    )

    equipment = _normalize_equipment(
        preferences.get(
            "equipment",
            "gym"
        )
    )

    fitness_level = _clean_text(
        preferences.get(
            "fitness_level",
            profile.get(
                "activity_level",
                "moderate"
            )
        ),
        "moderate"
    )

    goal = _normalize_goal(
        profile.get(
            "goal",
            "general_fitness"
        )
    )

    previous_exercises = (
        _extract_previous_exercises(
            previous_workouts
        )
    )

    relevant_database = (
        _relevant_exercises(focus)
    )

    # Random variation token means every request
    # receives a fresh generation context.
    variation_seed = random.randint(
        100000,
        999999999
    )

    previous_text = (
        ", ".join(previous_exercises)
        if previous_exercises
        else "None"
    )

    database_text = (
        ", ".join(relevant_database)
        if relevant_database
        else "Use appropriate standard gym exercises."
    )

    prompt = f"""
You are FitLyfe's professional AI workout coach.

Create a genuinely fresh workout plan for the user.

============================================================
USER
============================================================

Name: {profile.get("name", "User")}
Age: {profile.get("age", "Unknown")}
Height: {profile.get("height", "Unknown")} cm
Weight: {profile.get("weight", "Unknown")} kg
Gender: {profile.get("gender", "prefer_not_to_say")}
Activity Level: {profile.get("activity_level", "moderate")}
Fitness Goal: {goal}

============================================================
WORKOUT REQUEST
============================================================

Training Focus:
{focus}

Workout Type:
{preferences.get("workout_type", "gym")}

Equipment:
{equipment}

Fitness Level:
{fitness_level}

Target Duration:
{duration} minutes

Generation Number:
{generation_number}

Variation Seed:
{variation_seed}

============================================================
PREVIOUS EXERCISES
============================================================

{previous_text}

============================================================
IMPORTANT VARIATION RULES
============================================================

This is generation #{generation_number}.

The user specifically wants a NEW workout whenever
"Try Another Plan" is clicked.

DO NOT simply repeat the previous workout.

You MUST vary the workout by changing as many of these
as practical:

1. Exercise selection
2. Exercise order
3. Sets
4. Repetitions
5. Rest periods
6. Training emphasis
7. Exercise variation
8. Warm-up
9. Conditioning/core work
10. Workout structure

Avoid repeating exercises from the previous workouts
when practical.

Do NOT return the exact same exercise list.

If some exercise repetition is necessary because the
muscle group has limited exercise options, change the
order, sets, reps, rest, or training structure.

Keep the workout realistic and safe.

Do not recommend dangerous or extreme training.

============================================================
AVAILABLE EXERCISE REFERENCE
============================================================

{database_text}

You may use other standard exercises when appropriate.

============================================================
OUTPUT
============================================================

Return ONLY valid JSON.

Do not use markdown.
Do not use ```json.
Do not add explanations outside JSON.

Use exactly this general structure:

{{
  "title": "Workout title",
  "description": "Short description of this workout.",
  "focus": "{focus}",
  "generation_number": {generation_number},
  "duration_minutes": {duration},
  "intensity": "Moderate",
  "estimated_calories": 350,
  "warmup": [
    {{
      "exercise": "Warm-up movement",
      "duration": "5 minutes"
    }}
  ],
  "exercises": [
    {{
      "exercise": "Exercise name",
      "sets": 3,
      "reps": "8-12",
      "rest": "90 sec",
      "notes": "Short coaching instruction."
    }}
  ],
  "cooldown": [
    {{
      "exercise": "Stretch",
      "duration": "30 seconds"
    }}
  ]
}}

Generate approximately 5-8 main exercises depending on
the requested duration and training focus.

Make this generation meaningfully different from
previous generations.
"""

    return prompt


# ============================================================
# CLEAN GEMINI RESPONSE
# ============================================================

def _clean_ai_response(text):

    if not text:
        raise ValueError(
            "Gemini returned an empty response."
        )

    cleaned = str(text).strip()

    if cleaned.startswith("```"):

        cleaned = cleaned.replace(
            "```json",
            "",
            1
        )

        if cleaned.startswith("```"):

            cleaned = cleaned[3:]

        if cleaned.endswith("```"):

            cleaned = cleaned[:-3]

    return cleaned.strip()


# ============================================================
# VALIDATION
# ============================================================

def _validate_workout_plan(plan):

    if not isinstance(
        plan,
        dict
    ):

        raise ValueError(
            "Workout response must be a JSON object."
        )

    if not plan.get("title"):

        plan["title"] = (
            "AI Generated Workout"
        )

    if not plan.get("description"):

        plan["description"] = (
            "A personalized FitLyfe workout."
        )

    exercises = plan.get(
        "exercises",
        []
    )

    if not isinstance(
        exercises,
        list
    ):

        exercises = []

    cleaned_exercises = []

    for exercise in exercises:

        if not isinstance(
            exercise,
            dict
        ):
            continue

        name = (
            exercise.get("exercise")
            or exercise.get("exercise_name")
            or exercise.get("name")
            or exercise.get("movement")
        )

        if not name:
            continue

        cleaned_exercises.append({

            "exercise":
                str(name).strip(),

            "sets":
                _safe_int(
                    exercise.get(
                        "sets",
                        3
                    ),
                    3
                ),

            "reps":
                str(
                    exercise.get(
                        "reps",
                        "8-12"
                    )
                ).strip(),

            "rest":
                str(
                    exercise.get(
                        "rest",
                        "60-90 sec"
                    )
                ).strip(),

            "notes":
                str(
                    exercise.get(
                        "notes",
                        exercise.get(
                            "description",
                            "Perform with controlled form."
                        )
                    )
                ).strip(),
        })

    if not cleaned_exercises:

        raise ValueError(
            "Gemini returned no valid exercises."
        )

    plan["exercises"] = cleaned_exercises

    if not isinstance(
        plan.get("warmup"),
        list
    ):

        plan["warmup"] = []

    if not isinstance(
        plan.get("cooldown"),
        list
    ):

        plan["cooldown"] = []

    return plan


# ============================================================
# VARIATION CHECK
# ============================================================

def _plan_exercise_names(plan):

    names = []

    if not isinstance(
        plan,
        dict
    ):
        return names

    exercises = plan.get(
        "exercises",
        []
    )

    if not isinstance(
        exercises,
        list
    ):
        return names

    for exercise in exercises:

        if not isinstance(
            exercise,
            dict
        ):
            continue

        name = (
            exercise.get("exercise")
            or exercise.get("exercise_name")
            or exercise.get("name")
            or exercise.get("movement")
        )

        if name:

            names.append(
                str(name)
                .strip()
                .lower()
            )

    return names


def _is_too_similar(
    new_plan,
    previous_workouts
):

    if not previous_workouts:
        return False

    new_names = set(
        _plan_exercise_names(
            new_plan
        )
    )

    if not new_names:
        return True

    previous_names = set(
        _extract_previous_exercises(
            previous_workouts
        )
    )

    previous_names = {
        str(name).strip().lower()
        for name in previous_names
    }

    if not previous_names:
        return False

    overlap = (
        len(
            new_names
            & previous_names
        )
        /
        len(new_names)
    )

    # If almost everything is repeated,
    # ask Gemini again.
    return overlap >= 0.85


# ============================================================
# GEMINI GENERATION
# ============================================================

def _generate_with_gemini(
    profile,
    preferences,
    previous_workouts
):

    client = _get_gemini_client()

    prompt = _build_prompt(
        profile,
        preferences,
        previous_workouts
    )

    response = client.models.generate_content(
        model=MODEL_NAME,
        contents=prompt
    )

    raw = getattr(
        response,
        "text",
        None
    )

    cleaned = _clean_ai_response(
        raw
    )

    plan = json.loads(
        cleaned
    )

    return _validate_workout_plan(
        plan
    )


# ============================================================
# FALLBACK
# ============================================================

def _fallback_workout(
    profile,
    preferences,
    previous_workouts=None
):

    previous_workouts = (
        previous_workouts or []
    )

    focus = _clean_text(
        preferences.get(
            "focus",
            "Full Body"
        ),
        "Full Body"
    )

    duration = _safe_int(
        preferences.get(
            "duration_minutes",
            60
        ),
        60
    )

    database = (
        _relevant_exercises(
            focus
        )
    )

    previous = {
        name.lower()
        for name in _extract_previous_exercises(
            previous_workouts
        )
    }

    fresh = [
        exercise
        for exercise in database
        if exercise.lower()
        not in previous
    ]

    pool = (
        fresh
        if len(fresh) >= 5
        else database
    )

    random.shuffle(
        pool
    )

    count = min(
        max(
            5,
            duration // 10
        ),
        8,
        len(pool)
    )

    selected = pool[:count]

    exercises = []

    for exercise in selected:

        sets = random.choice(
            [3, 3, 4]
        )

        reps = random.choice(
            [
                "6-8",
                "8-10",
                "8-12",
                "10-12",
                "12-15"
            ]
        )

        rest = random.choice(
            [
                "45 sec",
                "60 sec",
                "75 sec",
                "90 sec"
            ]
        )

        exercises.append({

            "exercise":
                exercise,

            "sets":
                sets,

            "reps":
                reps,

            "rest":
                rest,

            "notes":
                "Use controlled form and stop if you experience pain.",
        })

    return {

        "title":
            f"{focus} Workout",

        "description":
            "A fresh FitLyfe workout variation.",

        "focus":
            focus,

        "generation_number":
            _safe_int(
                preferences.get(
                    "generation_number",
                    1
                ),
                1
            ),

        "duration_minutes":
            duration,

        "intensity":
            "Moderate",

        "estimated_calories":
            random.randint(
                250,
                550
            ),

        "warmup": [

            {
                "exercise":
                    "Light Cardio",

                "duration":
                    "5 minutes"
            }

        ],

        "exercises":
            exercises,

        "cooldown": [

            {
                "exercise":
                    "Full Body Stretch",

                "duration":
                    "5 minutes"
            }

        ],

    }


# ============================================================
# MAIN FUNCTION
# ============================================================

def generate_workout_plan(
    profile,
    preferences=None,
    previous_workouts=None
):

    preferences = (
        preferences or {}
    )

    previous_workouts = (
        previous_workouts or []
    )

    generation_number = _safe_int(
        preferences.get(
            "generation_number",
            len(previous_workouts) + 1
        ),
        len(previous_workouts) + 1
    )

    preferences = {
        **preferences,
        "generation_number":
            generation_number,
    }

    # --------------------------------------------------------
    # Gemini is the primary generator.
    # --------------------------------------------------------

    last_error = None

    for attempt in range(3):

        try:

            plan = _generate_with_gemini(
                profile,
                preferences,
                previous_workouts
            )

            # Ensure generation metadata.
            plan["generation_number"] = (
                generation_number
            )

            # ------------------------------------------------
            # Reject an almost identical generation.
            # ------------------------------------------------

            if (
                attempt < 2
                and _is_too_similar(
                    plan,
                    previous_workouts
                )
            ):

                print(
                    "WORKOUT AI: response too similar; "
                    "requesting another variation..."
                )

                # Add another random variation seed.
                preferences = {
                    **preferences,
                    "variation_retry":
                        random.randint(
                            100000,
                            999999999
                        ),
                }

                continue

            return plan

        except Exception as exc:

            last_error = exc

            print(
                f"WORKOUT AI ATTEMPT {attempt + 1} ERROR:",
                repr(exc)
            )

    # --------------------------------------------------------
    # Emergency fallback.
    # --------------------------------------------------------
    #
    # The Flask API will mark the response as fallback so
    # frontend can show that Gemini was unavailable.
    # --------------------------------------------------------

    fallback = _fallback_workout(
        profile,
        preferences,
        previous_workouts
    )

    fallback["_ai_error"] = str(
        last_error
    ) if last_error else ""

    fallback["_fallback"] = True

    return fallback


# ============================================================
# LOCAL TEST
# ============================================================

if __name__ == "__main__":

    test_profile = {

        "name":
            "FitLyfe User",

        "age":
            21,

        "height":
            178,

        "weight":
            75,

        "gender":
            "male",

        "activity_level":
            "moderate",

        "goal":
            "muscle_gain",
    }

    test_preferences = {

        "focus":
            "Chest",

        "workout_type":
            "gym",

        "equipment":
            "gym",

        "duration_minutes":
            60,

        "fitness_level":
            "moderate",

        "generation_number":
            1,
    }

    result = generate_workout_plan(
        test_profile,
        test_preferences,
        []
    )

    print(
        json.dumps(
            result,
            indent=2,
            ensure_ascii=False
        )
    )