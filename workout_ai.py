# ============================================================
# FITLYFE - AI WORKOUT GENERATOR
# Gemini-powered personalized workout generation
# ============================================================

import os
import json
import random

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
# Used as reference in the AI prompt and emergency fallback.
# ============================================================

EXERCISES = {

    # --------------------------------------------------------
    # CHEST
    # --------------------------------------------------------

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

    # --------------------------------------------------------
    # BACK
    # --------------------------------------------------------

    "back": [
        "Barbell Row",
        "Seated Cable Row",
        "Chest-Supported Row",
        "T-Bar Row",
        "Single-Arm Dumbbell Row",
        "Machine Row",
        "Back Extension",
    ],

    # --------------------------------------------------------
    # LATS
    # --------------------------------------------------------

    "lats": [
        "Lat Pulldown",
        "Wide-Grip Lat Pulldown",
        "Close-Grip Lat Pulldown",
        "Assisted Pull-Up",
        "Pull-Ups",
        "Single-Arm Lat Pulldown",
        "Straight-Arm Pulldown",
    ],

    # --------------------------------------------------------
    # SHOULDERS
    # --------------------------------------------------------

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

    # --------------------------------------------------------
    # BICEPS
    # --------------------------------------------------------

    "biceps": [
        "Barbell Curl",
        "EZ-Bar Curl",
        "Incline Dumbbell Curl",
        "Hammer Curl",
        "Cable Curl",
        "Preacher Curl",
        "Concentration Curl",
    ],

    # --------------------------------------------------------
    # TRICEPS
    # --------------------------------------------------------

    "triceps": [
        "Rope Triceps Pushdown",
        "Cable Triceps Pushdown",
        "Overhead Cable Extension",
        "Skull Crushers",
        "Close-Grip Bench Press",
        "Dumbbell Overhead Extension",
        "Bench Dips",
    ],

    # --------------------------------------------------------
    # LEGS
    # --------------------------------------------------------

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

    # --------------------------------------------------------
    # CORE
    # --------------------------------------------------------

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

    # --------------------------------------------------------
    # GLUTES
    # --------------------------------------------------------

    "glutes": [
        "Barbell Hip Thrust",
        "Glute Bridge",
        "Bulgarian Split Squat",
        "Walking Lunges",
        "Cable Kickback",
        "Step-Ups",
        "Romanian Deadlift",
    ],

    # --------------------------------------------------------
    # FOREARMS
    # --------------------------------------------------------

    "forearms": [
        "Wrist Curl",
        "Reverse Wrist Curl",
        "Farmer's Carry",
        "Reverse Curl",
        "Plate Pinch Hold",
    ],

    # --------------------------------------------------------
    # PUSH
    # --------------------------------------------------------

    "push": [
        "Barbell Bench Press",
        "Incline Dumbbell Press",
        "Dumbbell Shoulder Press",
        "Dumbbell Lateral Raise",
        "Cable Chest Fly",
        "Rope Triceps Pushdown",
        "Overhead Triceps Extension",
    ],

    # --------------------------------------------------------
    # PULL
    # --------------------------------------------------------

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
# EXERCISE-SPECIFIC DESCRIPTIONS
#
# These descriptions are displayed on the workout cards.
# They replace the old generic:
#
# "Use controlled form and stop if you experience pain."
#
# ============================================================

EXERCISE_DESCRIPTIONS = {

    # --------------------------------------------------------
    # CHEST
    # --------------------------------------------------------

    "Barbell Bench Press":
        "Targets the chest while also engaging the triceps and shoulders.",

    "Incline Dumbbell Press":
        "Emphasizes the upper chest while also engaging the shoulders and triceps.",

    "Machine Chest Press":
        "Targets the chest with a stable pressing movement.",

    "Cable Chest Fly":
        "Focuses on the chest through a controlled squeezing movement.",

    "Pec Deck Fly":
        "Isolates the chest and emphasizes the contraction at the end of the movement.",

    "Incline Machine Press":
        "Targets the upper chest with a controlled pressing movement.",

    "Dumbbell Bench Press":
        "Targets the chest while allowing each side to work independently.",

    "Decline Bench Press":
        "Emphasizes the lower portion of the chest during the pressing movement.",

    "Push-Ups":
        "Targets the chest while also working the triceps and shoulders.",


    # --------------------------------------------------------
    # BACK
    # --------------------------------------------------------

    "Barbell Row":
        "Targets the upper and mid back to build pulling strength and back thickness.",

    "Seated Cable Row":
        "Targets the mid back while encouraging controlled scapular movement.",

    "Chest-Supported Row":
        "Targets the upper and mid back while reducing lower-back involvement.",

    "T-Bar Row":
        "Builds back thickness by targeting the upper and mid back.",

    "Single-Arm Dumbbell Row":
        "Targets the lats and upper back while allowing each side to work independently.",

    "Machine Row":
        "Targets the mid and upper back with a stable rowing movement.",

    "Back Extension":
        "Strengthens the lower back and posterior chain through controlled extension.",


    # --------------------------------------------------------
    # LATS
    # --------------------------------------------------------

    "Lat Pulldown":
        "Targets the lats to develop back width and pulling strength.",

    "Wide-Grip Lat Pulldown":
        "Emphasizes the lats and upper back with a wider pulling position.",

    "Close-Grip Lat Pulldown":
        "Targets the lats through a controlled close-grip pulling movement.",

    "Assisted Pull-Up":
        "Targets the lats and upper back while helping build pull-up strength.",

    "Pull-Ups":
        "Targets the lats and upper back while also engaging the biceps.",

    "Single-Arm Lat Pulldown":
        "Targets the lats individually and encourages controlled shoulder movement.",

    "Straight-Arm Pulldown":
        "Isolates the lats through a controlled straight-arm pulling movement.",


    # --------------------------------------------------------
    # SHOULDERS
    # --------------------------------------------------------

    "Dumbbell Shoulder Press":
        "Targets the shoulders while also engaging the triceps during the press.",

    "Machine Shoulder Press":
        "Builds shoulder strength with a stable overhead pressing movement.",

    "Arnold Press":
        "Targets the shoulders through a full-range rotational pressing movement.",

    "Cable Lateral Raise":
        "Targets the side delts to help develop shoulder width.",

    "Dumbbell Lateral Raise":
        "Emphasizes the side delts for improved shoulder width.",

    "Rear Delt Fly":
        "Targets the rear delts and supports balanced shoulder development.",

    "Face Pull":
        "Targets the rear delts and upper back while supporting shoulder stability.",

    "Cable Front Raise":
        "Targets the front delts through a controlled raising movement.",


    # --------------------------------------------------------
    # BICEPS
    # --------------------------------------------------------

    "Barbell Curl":
        "Targets the biceps for strength and muscle growth.",

    "EZ-Bar Curl":
        "Targets the biceps with a controlled curling movement.",

    "Incline Dumbbell Curl":
        "Emphasizes the biceps through a longer range of motion.",

    "Hammer Curl":
        "Targets the biceps and brachialis while using a neutral grip.",

    "Cable Curl":
        "Keeps consistent resistance on the biceps throughout the curl.",

    "Preacher Curl":
        "Isolates the biceps and helps reduce momentum during the curl.",

    "Concentration Curl":
        "Focuses on the biceps through a controlled single-arm curl.",


    # --------------------------------------------------------
    # TRICEPS
    # --------------------------------------------------------

    "Rope Triceps Pushdown":
        "Isolates the triceps with a controlled downward pressing movement.",

    "Cable Triceps Pushdown":
        "Targets the triceps through a stable and controlled pushdown.",

    "Overhead Cable Extension":
        "Emphasizes the triceps through an overhead extension position.",

    "Skull Crushers":
        "Targets the triceps through a controlled elbow-extension movement.",

    "Close-Grip Bench Press":
        "Targets the triceps while also working the chest and shoulders.",

    "Dumbbell Overhead Extension":
        "Targets the triceps through an overhead extension movement.",

    "Bench Dips":
        "Targets the triceps while also involving the chest and shoulders.",


    # --------------------------------------------------------
    # LEGS
    # --------------------------------------------------------

    "Barbell Squat":
        "Targets the quads and glutes while building overall lower-body strength.",

    "Leg Press":
        "Targets the quads and glutes with a stable lower-body pressing movement.",

    "Romanian Deadlift":
        "Targets the hamstrings and glutes while developing posterior-chain strength.",

    "Walking Lunges":
        "Works the quads and glutes while improving single-leg stability.",

    "Bulgarian Split Squat":
        "Targets the quads and glutes while challenging single-leg strength and balance.",

    "Leg Extension":
        "Isolates the quadriceps through controlled knee extension.",

    "Leg Curl":
        "Isolates the hamstrings through controlled knee flexion.",

    "Standing Calf Raise":
        "Targets the calf muscles through a standing calf-raise movement.",

    "Seated Calf Raise":
        "Emphasizes the calf muscles through a seated calf-raise movement.",


    # --------------------------------------------------------
    # CORE
    # --------------------------------------------------------

    "Cable Crunch":
        "Targets the abdominal muscles through controlled spinal flexion.",

    "Hanging Knee Raise":
        "Targets the core with emphasis on controlled knee elevation.",

    "Hanging Leg Raise":
        "Challenges the core and lower abdominal muscles through leg elevation.",

    "Plank":
        "Builds core stability by resisting movement through the trunk.",

    "Ab Wheel Rollout":
        "Challenges the entire core while developing trunk stability.",

    "Dead Bug":
        "Builds core stability while training controlled movement of the limbs.",

    "Russian Twist":
        "Works the core with emphasis on controlled rotational movement.",

    "Bicycle Crunch":
        "Targets the abdominal muscles through a controlled alternating movement.",


    # --------------------------------------------------------
    # GLUTES
    # --------------------------------------------------------

    "Barbell Hip Thrust":
        "Targets the glutes with a strong hip-extension movement.",

    "Glute Bridge":
        "Activates the glutes through controlled hip extension.",

    "Cable Kickback":
        "Isolates the glutes through a controlled hip-extension movement.",

    "Step-Ups":
        "Targets the glutes and quads while developing single-leg strength.",


    # --------------------------------------------------------
    # FOREARMS
    # --------------------------------------------------------

    "Wrist Curl":
        "Targets the forearm flexor muscles and improves grip-related strength.",

    "Reverse Wrist Curl":
        "Targets the forearm extensor muscles through controlled wrist extension.",

    "Farmer's Carry":
        "Builds grip, forearm and core strength while carrying a controlled load.",

    "Reverse Curl":
        "Targets the forearms and brachialis with an overhand curling grip.",

    "Plate Pinch Hold":
        "Builds finger, grip and forearm strength through an isometric hold.",
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
        "no equipment",
    }:
        return "home/bodyweight"

    if raw in {
        "dumbbell",
        "dumbbells",
    }:
        return "dumbbells"

    if raw in {
        "gym",
        "full gym",
        "commercial gym",
    }:
        return "full gym"

    return raw


# ============================================================
# EXERCISE DESCRIPTION HELPER
# ============================================================

def _exercise_description(name, fallback=None):
    """
    Return a specific description for a known exercise.

    If Gemini generates an exercise that is not present in the
    local database, its generated notes are kept as fallback.
    """

    clean_name = _clean_text(name)

    if clean_name in EXERCISE_DESCRIPTIONS:
        return EXERCISE_DESCRIPTIONS[clean_name]

    normalized = clean_name.lower()

    for exercise_name, description in EXERCISE_DESCRIPTIONS.items():
        if exercise_name.lower() == normalized:
            return description

    if fallback:
        return str(fallback).strip()

    return (
        "Perform this exercise with controlled technique "
        "and appropriate form."
    )


# ============================================================
# FOCUS PARSER
#
# Supports:
# Chest
# Chest + Triceps
# Chest and Triceps
# Chest Triceps
# Back + Biceps
# Shoulders + Triceps
# Legs + Core
# Push
# Pull
# ============================================================

def _focus_groups(focus):

    text = _clean_text(focus).lower()

    text = text.replace("&", " and ")
    text = text.replace("+", " and ")
    text = text.replace("/", " and ")

    text = " ".join(text.split())

    # --------------------------------------------------------
    # Full body
    # --------------------------------------------------------

    if (
        "full body" in text
        or "whole body" in text
        or "fullbody" in text
    ):
        return ["full_body"]

    # --------------------------------------------------------
    # Push
    # --------------------------------------------------------

    if text.strip() in {
        "push",
        "push day",
        "push workout",
    }:
        return ["push"]

    # --------------------------------------------------------
    # Pull
    # --------------------------------------------------------

    if text.strip() in {
        "pull",
        "pull day",
        "pull workout",
    }:
        return ["pull"]

    groups = []

    def add(group):
        if group not in groups:
            groups.append(group)

    # --------------------------------------------------------
    # Chest
    # --------------------------------------------------------

    if any(
        word in text
        for word in [
            "chest",
            "pec",
            "pecs",
            "pectoral",
            "pectorals",
        ]
    ):
        add("chest")

    # --------------------------------------------------------
    # Back
    # --------------------------------------------------------

    if "back" in text:
        add("back")

    # --------------------------------------------------------
    # Lats
    # --------------------------------------------------------

    if any(
        word in text
        for word in [
            "lat",
            "lats",
            "latissimus",
        ]
    ):
        add("lats")

    # --------------------------------------------------------
    # Shoulders
    # --------------------------------------------------------

    if any(
        word in text
        for word in [
            "shoulder",
            "shoulders",
            "delt",
            "delts",
            "deltoid",
            "deltoids",
        ]
    ):
        add("shoulders")

    # --------------------------------------------------------
    # Biceps
    #
    # Short aliases are deliberately checked only as complete
    # words to avoid accidental matches.
    # --------------------------------------------------------

    words = set(text.replace(",", " ").split())

    if (
        "bicep" in words
        or "biceps" in words
        or "bi" in words
        or "bis" in words
    ):
        add("biceps")

    # --------------------------------------------------------
    # Triceps
    # --------------------------------------------------------

    if (
        "tricep" in words
        or "triceps" in words
        or "tri" in words
        or "tris" in words
    ):
        add("triceps")

    # --------------------------------------------------------
    # Legs
    # --------------------------------------------------------

    if any(
        word in text
        for word in [
            "leg",
            "legs",
            "lower body",
            "lowerbody",
            "quad",
            "quads",
        ]
    ):
        add("legs")

    # --------------------------------------------------------
    # Glutes
    # --------------------------------------------------------

    if any(
        word in text
        for word in [
            "glute",
            "glutes",
            "gluteus",
        ]
    ):
        add("glutes")

    # --------------------------------------------------------
    # Forearms
    # --------------------------------------------------------

    if any(
        word in text
        for word in [
            "forearm",
            "forearms",
        ]
    ):
        add("forearms")

    # --------------------------------------------------------
    # Core / Abs
    # --------------------------------------------------------

    if any(
        word in text
        for word in [
            "core",
            "abs",
            "ab",
            "abdominal",
            "abdominals",
        ]
    ):
        add("core")

    return groups


# ============================================================
# HUMAN-READABLE FOCUS GROUPS
# ============================================================

def _focus_requirements(focus):

    groups = _focus_groups(focus)

    if not groups:
        return "Full Body"

    if "full_body" in groups:
        return "Full Body"

    labels = {
        "chest": "Chest",
        "back": "Back",
        "lats": "Lats",
        "shoulders": "Shoulders",
        "biceps": "Biceps",
        "triceps": "Triceps",
        "legs": "Legs",
        "glutes": "Glutes",
        "forearms": "Forearms",
        "core": "Core",
        "push": "Push",
        "pull": "Pull",
    }

    return ", ".join(
        labels[group]
        for group in groups
        if group in labels
    )


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
                "name",
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

            if isinstance(existing_names, list):
                names.extend(existing_names)

            plan = workout.get("plan")

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

            seen.add(normalized)

            unique.append(
                str(name).strip()
            )

    return unique


# ============================================================
# EXERCISE DATABASE FOR PROMPT
# Combination-aware
# ============================================================

def _relevant_exercises(focus):

    groups = _focus_groups(focus)

    database = []

    # --------------------------------------------------------
    # Full body
    # --------------------------------------------------------

    if "full_body" in groups:

        for group, exercises in EXERCISES.items():

            if group not in {
                "push",
                "pull",
            }:

                database.extend(exercises)

        return list(
            dict.fromkeys(database)
        )

    # --------------------------------------------------------
    # Push
    # --------------------------------------------------------

    if "push" in groups:

        database.extend(
            EXERCISES["push"]
        )

    # --------------------------------------------------------
    # Pull
    # --------------------------------------------------------

    if "pull" in groups:

        database.extend(
            EXERCISES["pull"]
        )

    # --------------------------------------------------------
    # Specific muscle groups
    # --------------------------------------------------------

    for group in groups:

        if group in EXERCISES:

            database.extend(
                EXERCISES[group]
            )

    # --------------------------------------------------------
    # Back also gets lat exercises
    # --------------------------------------------------------

    if groups == ["back"]:

        database.extend(
            EXERCISES["lats"]
        )

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

    focus_requirements = (
        _focus_requirements(focus)
    )

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
        else (
            "Use appropriate standard gym exercises."
        )
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

Required Muscle Groups:

{focus_requirements}

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

Avoid repeating exercises from previous workouts
when practical.

Do NOT return the exact same exercise list.

If some exercise repetition is necessary because the
muscle group has limited exercise options, change the
order, sets, reps, rest, or training structure.

Keep the workout realistic and safe.

Do not recommend dangerous or extreme training.


============================================================
MULTI-MUSCLE FOCUS RULE
============================================================

The requested training focus is:

{focus_requirements}

You MUST train EVERY requested muscle group.

This rule is mandatory.

If the focus contains multiple muscle groups, divide the
main exercises across those muscle groups.

Examples:

If focus = "Back + Biceps":

- Include multiple Back/Lats exercises.
- Include at least 2 direct Biceps exercises.
- Do NOT return a workout containing only Back/Lats.

If focus = "Chest + Triceps":

- Include Chest exercises.
- Include at least 2 direct Triceps exercises.
- Do NOT return a workout containing only Chest.

If focus = "Shoulders + Triceps":

- Include Shoulder exercises.
- Include at least 2 direct Triceps exercises.

If focus = "Legs + Core":

- Include Leg exercises.
- Include at least 2 direct Core exercises.

If focus = "Back + Biceps + Forearms":

- Include Back exercises.
- Include Biceps exercises.
- Include Forearm exercises.

The exercise list must visibly represent ALL requested
muscle groups.

Do not interpret "Back + Biceps" as only a Back workout.

Do not interpret "Chest + Triceps" as only a Chest workout.

Do not ignore any muscle group supplied in the Training Focus.

For a two-muscle-group workout with 5-8 exercises,
normally allocate approximately:

- 3-5 exercises to the primary/larger muscle group
- 2-3 direct exercises to the secondary muscle group

The final exercise list must contain direct exercises for
each requested muscle group.


============================================================
EXERCISE DESCRIPTION RULE
============================================================

Every exercise must have an exercise-specific "notes"
description.

The description must explain what the specific exercise
primarily targets or develops.

Examples:

Barbell Curl:
"Targets the biceps for strength and muscle growth."

Incline Dumbbell Press:
"Emphasizes the upper chest while also engaging the shoulders and triceps."

Lat Pulldown:
"Targets the lats to develop back width and pulling strength."

Rope Triceps Pushdown:
"Isolates the triceps with a controlled downward pressing movement."

Do NOT use:

"Use controlled form and stop if you experience pain."

Do NOT use the exact same description for every exercise.

Keep each description short and useful.

The description should normally be one sentence.


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
            "notes": "Exercise-specific description explaining the primary muscles targeted or main training purpose."
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

    if not isinstance(plan, dict):

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

    if not isinstance(exercises, list):

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

        clean_name = str(name).strip()

        # ----------------------------------------------------
        # Get Gemini's description as fallback.
        # Our local description database takes priority.
        # ----------------------------------------------------

        generated_notes = (
            exercise.get("notes")
            or exercise.get("description")
        )

        notes = _exercise_description(
            clean_name,
            generated_notes
        )

        cleaned_exercises.append({

            "exercise": clean_name,

            "sets": _safe_int(
                exercise.get(
                    "sets",
                    3
                ),
                3
            ),

            "reps": str(
                exercise.get(
                    "reps",
                    "8-12"
                )
            ).strip(),

            "rest": str(
                exercise.get(
                    "rest",
                    "60-90 sec"
                )
            ).strip(),

            "notes": notes,
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
        str(name)
        .strip()
        .lower()
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
# Combination-aware emergency workout
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

    groups = _focus_groups(
        focus
    )

    previous = {
        name.lower()
        for name in _extract_previous_exercises(
            previous_workouts
        )
    }

    # --------------------------------------------------------
    # Build pool for every requested group
    # --------------------------------------------------------

    group_pools = {}

    if "full_body" in groups:

        for group, pool in EXERCISES.items():

            if group not in {
                "push",
                "pull",
            }:

                group_pools[group] = list(
                    pool
                )

    else:

        for group in groups:

            if group in EXERCISES:

                group_pools[group] = list(
                    EXERCISES[group]
                )

        # ----------------------------------------------------
        # Back also gets lats
        # ----------------------------------------------------

        if groups == ["back"]:

            group_pools["back"] = list(
                dict.fromkeys(
                    EXERCISES["back"]
                    + EXERCISES["lats"]
                )
            )

    selected = []

    # --------------------------------------------------------
    # Guarantee every requested group is represented
    # --------------------------------------------------------

    for group, pool in group_pools.items():

        fresh = [
            exercise
            for exercise in pool
            if exercise.lower() not in previous
        ]

        if not fresh:
            fresh = pool[:]

        if fresh:

            selected.append(
                random.choice(
                    fresh
                )
            )

    # --------------------------------------------------------
    # Target number of exercises
    # --------------------------------------------------------

    target_count = min(
        max(
            5,
            duration // 10
        ),
        8
    )

    # --------------------------------------------------------
    # Build combined pool
    # --------------------------------------------------------

    combined_pool = []

    for pool in group_pools.values():

        for exercise in pool:

            if exercise not in combined_pool:

                combined_pool.append(
                    exercise
                )

    fresh_combined = [

        exercise

        for exercise in combined_pool

        if (
            exercise.lower() not in previous
            and exercise not in selected
        )
    ]

    random.shuffle(
        fresh_combined
    )

    for exercise in fresh_combined:

        if len(selected) >= target_count:
            break

        selected.append(
            exercise
        )

    # --------------------------------------------------------
    # Reuse exercises only if necessary
    # --------------------------------------------------------

    if len(selected) < target_count:

        remaining = [

            exercise

            for exercise in combined_pool

            if exercise not in selected
        ]

        random.shuffle(
            remaining
        )

        for exercise in remaining:

            if len(selected) >= target_count:
                break

            selected.append(
                exercise
            )

    random.shuffle(
        selected
    )

    # --------------------------------------------------------
    # Create exercise objects
    # --------------------------------------------------------

    exercises = []

    for exercise in selected:

        sets = random.choice(
            [
                3,
                3,
                4
            ]
        )

        reps = random.choice(
            [
                "6-8",
                "8-10",
                "8-12",
                "10-12",
                "12-15",
            ]
        )

        rest = random.choice(
            [
                "45 sec",
                "60 sec",
                "75 sec",
                "90 sec",
            ]
        )

        exercises.append({

            "exercise": exercise,

            "sets": sets,

            "reps": reps,

            "rest": rest,

            "notes": _exercise_description(
                exercise
            ),
        })

    return {

        "title": f"{focus} Workout",

        "description": (
            "A fresh FitLyfe workout variation."
        ),

        "focus": focus,

        "generation_number": _safe_int(
            preferences.get(
                "generation_number",
                1
            ),
            1
        ),

        "duration_minutes": duration,

        "intensity": "Moderate",

        "estimated_calories": random.randint(
            250,
            550
        ),

        "warmup": [
            {
                "exercise": "Light Cardio",
                "duration": "5 minutes",
            }
        ],

        "exercises": exercises,

        "cooldown": [
            {
                "exercise": "Full Body Stretch",
                "duration": "5 minutes",
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

    fallback = _fallback_workout(
        profile,
        preferences,
        previous_workouts
    )

    fallback["_ai_error"] = (
        str(last_error)
        if last_error
        else ""
    )

    fallback["_fallback"] = True

    return fallback


# ============================================================
# LOCAL TEST
# ============================================================

if __name__ == "__main__":

    test_profile = {

        "name": "FitLyfe User",

        "age": 21,

        "height": 178,

        "weight": 75,

        "gender": "male",

        "activity_level": "moderate",

        "goal": "muscle_gain",
    }

    test_preferences = {

        "focus": "Back + Biceps",

        "workout_type": "gym",

        "equipment": "gym",

        "duration_minutes": 60,

        "fitness_level": "moderate",

        "generation_number": 1,
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