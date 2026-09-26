# ============================================================
# FITLYFE - GOAL MODULE
# ============================================================
#
# This file contains:
#   - Weekly Goal API
#   - Daily Log APIs
#   - Persistent User Goals
#   - Daily Goal APIs
#   - Legacy Goal APIs
#
# The existing app.py remains responsible for:
#   - Flask app creation
#   - SQLAlchemy database
#   - Database models
#   - Shared helpers
#   - Dashboard
#   - Calendar
#   - Workout
#   - Diet
#
# ============================================================


# ============================================================
# IMPORTS FROM MAIN APP
# ============================================================

from app import (
    app,
    db,
    request,
    jsonify,
    func,
    IntegrityError,

    # Shared helpers
    login_required_json,
    parse_date,
    india_today,
    week_start_for,

    # Goal-related database models
    WeeklyGoal,
    DailyLog,
    DailyGoal,
    UserGoal,
)


# ============================================================
# API - WEEKLY GOAL
# ============================================================

@app.route(
    "/api/goal",
    methods=["POST"]
)
def save_goal():

    user, error_response = login_required_json()

    if error_response:
        return error_response

    data = request.get_json(
        silent=True
    ) or {}

    week_start = parse_date(
        data.get("week_start")
    )

    if not week_start:
        week_start = week_start_for(
            india_today()
        )

    # --------------------------------------------------------
    # WORKOUT TARGET
    # --------------------------------------------------------

    try:
        workouts_target = int(
            data.get(
                "workouts_target",
                5
            )
        )
    except (
        ValueError,
        TypeError
    ):
        workouts_target = 5

    # --------------------------------------------------------
    # CALORIE TARGET
    # --------------------------------------------------------

    try:
        calories_target = int(
            data.get(
                "calories_target",
                2000
            )
        )
    except (
        ValueError,
        TypeError
    ):
        calories_target = 2000

    # --------------------------------------------------------
    # WATER TARGET
    # --------------------------------------------------------

    try:
        water_target_l = float(
            data.get(
                "water_target_l",
                2.5
            )
        )
    except (
        ValueError,
        TypeError
    ):
        water_target_l = 2.5

    # --------------------------------------------------------
    # FIND EXISTING WEEKLY GOAL
    # --------------------------------------------------------

    goal = (
        WeeklyGoal.query
        .filter_by(
            user_id=user.id,
            week_start=week_start
        )
        .first()
    )

    # --------------------------------------------------------
    # CREATE IF NOT FOUND
    # --------------------------------------------------------

    if not goal:

        goal = WeeklyGoal(
            user_id=user.id,
            week_start=week_start,
        )

        db.session.add(
            goal
        )

    # --------------------------------------------------------
    # UPDATE VALUES
    # --------------------------------------------------------

    goal.workouts_target = (
        workouts_target
    )

    goal.calories_target = (
        calories_target
    )

    goal.water_target_l = (
        water_target_l
    )

    db.session.commit()

    # --------------------------------------------------------
    # RESPONSE
    # --------------------------------------------------------

    return jsonify({

        "success": True,

        "message":
            "Weekly goal saved successfully.",

        "goal": {

            "week_start":
                week_start.isoformat(),

            "workouts_target":
                goal.workouts_target,

            "calories_target":
                goal.calories_target,

            "water_target_l":
                goal.water_target_l,

        }

    })


# ============================================================
# API - DAILY LOG GET
# ============================================================

@app.route(
    "/api/daily-log",
    methods=["GET"]
)
def get_daily_log():

    user, error_response = login_required_json()

    if error_response:
        return error_response

    log_date = (
        parse_date(
            request.args.get("date")
        )
        or india_today()
    )

    # --------------------------------------------------------
    # FIND LOG
    # --------------------------------------------------------

    log = (
        DailyLog.query
        .filter_by(
            user_id=user.id,
            log_date=log_date
        )
        .first()
    )

    # --------------------------------------------------------
    # NO LOG
    # --------------------------------------------------------

    if not log:

        return jsonify({

            "success": True,

            "log": None

        })

    # --------------------------------------------------------
    # RETURN LOG
    # --------------------------------------------------------

    return jsonify({

        "success": True,

        "log": {

            "date":
                log.log_date.isoformat(),

            "workout_done":
                bool(log.workout_done),

            "calories_intake":
                log.calories_intake,

            "water_intake_l":
                log.water_intake_l,

            "sleep_hours":
                log.sleep_hours,

            "mood":
                log.mood,

            "notes":
                log.notes or "",

        }

    })


# ============================================================
# API - DAILY LOG SAVE
# ============================================================

@app.route(
    "/api/daily-log",
    methods=["POST"]
)
def save_daily_log():

    user, error_response = login_required_json()

    if error_response:
        return error_response

    data = request.get_json(
        silent=True
    ) or {}

    # --------------------------------------------------------
    # DATE
    # --------------------------------------------------------

    log_date = parse_date(
        data.get("log_date")
    )

    if not log_date:
        log_date = india_today()

    # --------------------------------------------------------
    # WORKOUT DONE
    # --------------------------------------------------------

    workout_value = data.get(
        "workout_done",
        False
    )

    if isinstance(
        workout_value,
        str
    ):

        workout_done = (
            workout_value
            .strip()
            .lower()
            in {
                "1",
                "true",
                "yes",
                "on"
            }
        )

    else:

        workout_done = bool(
            workout_value
        )

    # --------------------------------------------------------
    # CALORIES
    # --------------------------------------------------------

    calories_value = data.get(
        "calories_intake"
    )

    try:

        calories_intake = (
            int(calories_value)
            if calories_value not in (
                None,
                "",
            )
            else None
        )

    except (
        ValueError,
        TypeError
    ):

        calories_intake = None

    # --------------------------------------------------------
    # WATER
    # --------------------------------------------------------

    water_value = data.get(
        "water_intake_l"
    )

    try:

        water_intake_l = (
            float(water_value)
            if water_value not in (
                None,
                "",
            )
            else None
        )

    except (
        ValueError,
        TypeError
    ):

        water_intake_l = None

    # --------------------------------------------------------
    # SLEEP
    # --------------------------------------------------------

    sleep_value = data.get(
        "sleep_hours"
    )

    try:

        sleep_hours = (
            float(sleep_value)
            if sleep_value not in (
                None,
                "",
            )
            else None
        )

    except (
        ValueError,
        TypeError
    ):

        sleep_hours = None

    # --------------------------------------------------------
    # MOOD
    # --------------------------------------------------------

    mood_value = data.get(
        "mood"
    )

    try:

        mood = (
            int(mood_value)
            if mood_value not in (
                None,
                "",
            )
            else None
        )

    except (
        ValueError,
        TypeError
    ):

        mood = None

    # Keep mood between 1 and 5.
    if mood is not None:

        mood = max(
            1,
            min(
                mood,
                5
            )
        )

    # --------------------------------------------------------
    # NOTES
    # --------------------------------------------------------

    notes = str(
        data.get(
            "notes",
            ""
        )
    ).strip()[:2000]

    # --------------------------------------------------------
    # FIND EXISTING LOG
    # --------------------------------------------------------

    log = (
        DailyLog.query
        .filter_by(
            user_id=user.id,
            log_date=log_date
        )
        .first()
    )

    # --------------------------------------------------------
    # CREATE LOG IF NEEDED
    # --------------------------------------------------------

    if not log:

        log = DailyLog(
            user_id=user.id,
            log_date=log_date,
        )

        db.session.add(
            log
        )

    # --------------------------------------------------------
    # UPDATE LOG
    # --------------------------------------------------------

    log.workout_done = (
        workout_done
    )

    log.calories_intake = (
        calories_intake
    )

    log.water_intake_l = (
        water_intake_l
    )

    log.sleep_hours = (
        sleep_hours
    )

    log.mood = mood

    log.notes = notes

    db.session.commit()

    # --------------------------------------------------------
    # RESPONSE
    # --------------------------------------------------------

    return jsonify({

        "success": True,

        "message":
            "Daily log saved successfully.",

        "log": {

            "date":
                log.log_date.isoformat(),

            "workout_done":
                bool(log.workout_done),

            "calories_intake":
                log.calories_intake,

            "water_intake_l":
                log.water_intake_l,

            "sleep_hours":
                log.sleep_hours,

            "mood":
                log.mood,

            "notes":
                log.notes or "",

        }

    })


# ============================================================
# PERSISTENT USER GOALS
# ============================================================

DEFAULT_USER_GOALS = [

    {
        "title": "Workout",
        "description":
            "Complete today's workout or physical activity."
    },

    {
        "title": "Water Intake",
        "description":
            "Drink enough water throughout the day."
    },

    {
        "title": "Study",
        "description":
            "Spend at least 2 hours learning or studying."
    },

    {
        "title": "Sleep",
        "description":
            "Aim for 7–8 hours of quality sleep."
    },

    {
        "title": "Steps",
        "description":
            "Aim for around 8,000 steps today."
    },

    {
        "title": "Meditation",
        "description":
            "Spend at least 10 minutes on mindfulness or meditation."
    },

]


# ============================================================
# ENSURE USER GOALS
# ============================================================

def ensure_user_goals(user_id):

    existing_goals = (
        UserGoal
        .query
        .filter_by(
            user_id=user_id
        )
        .count()
    )

    if existing_goals > 0:
        return

    for item in DEFAULT_USER_GOALS:

        user_goal = UserGoal(

            user_id=user_id,

            title=item["title"],

            description=item["description"],

            active=True

        )

        db.session.add(
            user_goal
        )

    db.session.commit()


# ============================================================
# MATERIALIZE DAILY GOALS
# ============================================================

def materialize_daily_goals(
    user_id,
    goal_date
):

    # Make sure persistent goals exist.
    ensure_user_goals(
        user_id
    )

    # --------------------------------------------------------
    # ACTIVE PERSISTENT GOALS
    # --------------------------------------------------------

    active_goals = (

        UserGoal.query

        .filter_by(
            user_id=user_id,
            active=True
        )

        .order_by(
            UserGoal.id.asc()
        )

        .all()

    )

    if not active_goals:
        return []

    # --------------------------------------------------------
    # EXISTING DAILY GOALS
    # --------------------------------------------------------

    existing_daily_goals = (

        DailyGoal.query

        .filter_by(
            user_id=user_id,
            goal_date=goal_date
        )

        .all()

    )

    existing_titles = {

        goal.title.strip().lower()

        for goal in existing_daily_goals

    }

    created = False

    # --------------------------------------------------------
    # CREATE MISSING DAILY INSTANCES
    # --------------------------------------------------------

    for user_goal in active_goals:

        normalized_title = (
            user_goal.title
            .strip()
            .lower()
        )

        if normalized_title in existing_titles:
            continue

        daily_goal = DailyGoal(

            user_id=user_id,

            goal_date=goal_date,

            title=user_goal.title,

            completed=False,

            description=
                user_goal.description or ""

        )

        db.session.add(
            daily_goal
        )

        existing_titles.add(
            normalized_title
        )

        created = True

    # --------------------------------------------------------
    # SAVE NEW GOALS
    # --------------------------------------------------------

    if created:
        db.session.commit()

    # --------------------------------------------------------
    # RETURN DAILY GOALS
    # --------------------------------------------------------

    return (

        DailyGoal.query

        .filter_by(
            user_id=user_id,
            goal_date=goal_date
        )

        .order_by(
            DailyGoal.id.asc()
        )

        .all()

    )


# ============================================================
# DAILY GOAL RESPONSE HELPER
# ============================================================

def daily_goal_to_dict(goal):

    return {

        "id":
            goal.id,

        "title":
            goal.title,

        "completed":
            bool(goal.completed),

        "description":
            goal.description or "",

        "goal_date":
            goal.goal_date.isoformat()

    }


# ============================================================
# API - DAILY GOALS GET
# ============================================================

@app.route(
    "/api/daily-goals",
    methods=["GET"]
)
def get_daily_goals():

    user, error_response = login_required_json()

    if error_response:
        return error_response

    selected_date = parse_date(
        request.args.get("date")
    )

    if not selected_date:
        selected_date = india_today()

    today = india_today()

    # --------------------------------------------------------
    # CURRENT / FUTURE DATE
    # --------------------------------------------------------

    if selected_date >= today:

        goals = materialize_daily_goals(

            user.id,

            selected_date

        )

    # --------------------------------------------------------
    # HISTORICAL DATE
    # --------------------------------------------------------

    else:

        goals = (

            DailyGoal.query

            .filter_by(

                user_id=user.id,

                goal_date=selected_date

            )

            .order_by(
                DailyGoal.id.asc()
            )

            .all()

        )

    # --------------------------------------------------------
    # RESPONSE
    # --------------------------------------------------------

    return jsonify({

        "success": True,

        "goals": [

            daily_goal_to_dict(
                goal
            )

            for goal in goals

        ]

    })


# ============================================================
# API - DAILY GOAL CREATE
# ============================================================

@app.route(
    "/api/daily-goals",
    methods=["POST"]
)
def create_daily_goal():

    user, error_response = login_required_json()

    if error_response:
        return error_response

    data = request.get_json(
        silent=True
    ) or {}

    # --------------------------------------------------------
    # TITLE
    # --------------------------------------------------------

    title = str(
        data.get(
            "title",
            ""
        )
    ).strip()

    if not title:

        return jsonify({

            "success": False,

            "error":
                "Goal title is required."

        }), 400

    if len(title) > 255:

        return jsonify({

            "success": False,

            "error":
                "Goal title is too long."

        }), 400

    # --------------------------------------------------------
    # DATE
    # --------------------------------------------------------

    goal_date = parse_date(
        data.get("goal_date")
    )

    if not goal_date:
        goal_date = india_today()

    today = india_today()

    # Historical goals cannot be added.
    if goal_date < today:

        return jsonify({

            "success": False,

            "error":
                "Goals cannot be added to historical dates."

        }), 400

    # --------------------------------------------------------
    # DESCRIPTION
    # --------------------------------------------------------

    description = str(

        data.get(
            "description",
            ""
        )

    ).strip()[:255]

    # --------------------------------------------------------
    # INITIALIZE DEFAULT USER GOALS
    # --------------------------------------------------------

    ensure_user_goals(
        user.id
    )

    normalized_title = (
        title.lower()
    )

    # ========================================================
    # CHECK ACTIVE PERSISTENT GOALS
    # ========================================================

    existing_user_goals = (

        UserGoal.query

        .filter_by(

            user_id=user.id,

            active=True

        )

        .all()

    )

    for existing in existing_user_goals:

        if (

            existing.title

            and existing.title
            .strip()
            .lower()

            == normalized_title

        ):

            return jsonify({

                "success": False,

                "error":
                    "This goal already exists."

            }), 409

    # ========================================================
    # CHECK DAILY GOALS FOR SELECTED DATE
    # ========================================================

    existing_daily_goals = (

        DailyGoal.query

        .filter_by(

            user_id=user.id,

            goal_date=goal_date

        )

        .all()

    )

    for existing in existing_daily_goals:

        if (

            existing.title

            and existing.title
            .strip()
            .lower()

            == normalized_title

        ):

            return jsonify({

                "success": False,

                "error":
                    "This goal already exists for this date."

            }), 409

    # ========================================================
    # CREATE PERSISTENT GOAL
    # ========================================================

    user_goal = UserGoal(

        user_id=user.id,

        title=title,

        description=description,

        active=True

    )

    db.session.add(
        user_goal
    )

    # ========================================================
    # CREATE DAILY INSTANCE
    # ========================================================

    daily_goal = DailyGoal(

        user_id=user.id,

        goal_date=goal_date,

        title=title,

        completed=False,

        description=description

    )

    db.session.add(
        daily_goal
    )

    # ========================================================
    # COMMIT
    # ========================================================

    try:

        db.session.commit()

    except IntegrityError:

        db.session.rollback()

        return jsonify({

            "success": False,

            "error":
                "Unable to create this goal."

        }), 500

    except Exception as exc:

        db.session.rollback()

        print(
            "CREATE GOAL ERROR:",
            exc
        )

        return jsonify({

            "success": False,

            "error":
                "Unable to create this goal."

        }), 500

    # ========================================================
    # RESPONSE
    # ========================================================

    return jsonify({

        "success": True,

        "goal":
            daily_goal_to_dict(
                daily_goal
            )

    })


# ============================================================
# API - DAILY GOAL TOGGLE
# ============================================================

@app.route(
    "/api/daily-goals/<int:goal_id>/toggle",
    methods=["POST"]
)
def toggle_daily_goal(
    goal_id
):

    user, error_response = login_required_json()

    if error_response:
        return error_response

    # --------------------------------------------------------
    # FIND GOAL
    # --------------------------------------------------------

    goal = (

        DailyGoal.query

        .filter_by(

            id=goal_id,

            user_id=user.id

        )

        .first()

    )

    if not goal:

        return jsonify({

            "success": False,

            "error":
                "Goal not found."

        }), 404

    today = india_today()

    # --------------------------------------------------------
    # PROTECT HISTORY
    # --------------------------------------------------------

    if goal.goal_date < today:

        return jsonify({

            "success": False,

            "error":
                "Historical goals cannot be changed."

        }), 400

    # --------------------------------------------------------
    # TOGGLE
    # --------------------------------------------------------

    goal.completed = not bool(
        goal.completed
    )

    # --------------------------------------------------------
    # SAVE
    # --------------------------------------------------------

    try:

        db.session.commit()

    except Exception as exc:

        db.session.rollback()

        print(
            "TOGGLE GOAL ERROR:",
            exc
        )

        return jsonify({

            "success": False,

            "error":
                "Unable to update goal."

        }), 500

    # --------------------------------------------------------
    # RESPONSE
    # --------------------------------------------------------

    return jsonify({

        "success": True,

        "completed":
            bool(goal.completed)

    })


# ============================================================
# API - DAILY GOAL DELETE
# ============================================================

@app.route(
    "/api/daily-goals/<int:goal_id>",
    methods=["DELETE"]
)
def delete_daily_goal(
    goal_id
):

    user, error_response = login_required_json()

    if error_response:
        return error_response

    # --------------------------------------------------------
    # FIND GOAL
    # --------------------------------------------------------

    goal = (

        DailyGoal.query

        .filter_by(

            id=goal_id,

            user_id=user.id

        )

        .first()

    )

    if not goal:

        return jsonify({

            "success": False,

            "error":
                "Goal not found."

        }), 404

    today = india_today()

    # --------------------------------------------------------
    # PROTECT HISTORY
    # --------------------------------------------------------

    if goal.goal_date < today:

        return jsonify({

            "success": False,

            "error":
                "Historical goals cannot be deleted."

        }), 400

    normalized_title = (

        goal.title or ""

    ).strip().lower()

    # ========================================================
    # DISABLE ACTIVE PERSISTENT GOAL
    # ========================================================

    active_user_goals = (

        UserGoal.query

        .filter_by(

            user_id=user.id,

            active=True

        )

        .order_by(
            UserGoal.id.desc()
        )

        .all()

    )

    matching_user_goal = next(

        (

            item

            for item in active_user_goals

            if (

                item.title

                and item.title
                .strip()
                .lower()

                == normalized_title

            )

        ),

        None

    )

    if matching_user_goal:

        matching_user_goal.active = False

    # ========================================================
    # DELETE FUTURE DAILY INSTANCES
    #
    # Historical records remain untouched.
    # ========================================================

    future_goals = (

        DailyGoal.query

        .filter(

            DailyGoal.user_id == user.id,

            DailyGoal.goal_date >= goal.goal_date,

            func.lower(

                func.trim(
                    DailyGoal.title
                )

            ) == normalized_title

        )

        .all()

    )

    for future_goal in future_goals:

        db.session.delete(
            future_goal
        )

    # ========================================================
    # COMMIT
    # ========================================================

    try:

        db.session.commit()

    except Exception as exc:

        db.session.rollback()

        print(
            "DELETE GOAL ERROR:",
            exc
        )

        return jsonify({

            "success": False,

            "error":
                "Unable to delete goal."

        }), 500

    # ========================================================
    # RESPONSE
    # ========================================================

    return jsonify({

        "success": True,

        "message":
            "Goal deleted successfully."

    })


# ============================================================
# BACKWARD-COMPATIBILITY GOAL ENDPOINTS
# ============================================================
#
# These keep the old frontend/API URLs working.
#
# Existing:
#   /api/goals
#   /api/goals/<id>/toggle
#   /api/goals/<id>
#
# continue to use the new Goal functions.
#
# ============================================================


@app.route(
    "/api/goals",
    methods=["GET", "POST"]
)
def legacy_goals():

    if request.method == "GET":

        return get_daily_goals()

    return create_daily_goal()


@app.route(
    "/api/goals/<int:goal_id>/toggle",
    methods=["POST"]
)
def legacy_toggle_goal(
    goal_id
):

    return toggle_daily_goal(
        goal_id
    )


@app.route(
    "/api/goals/<int:goal_id>",
    methods=["DELETE"]
)
def legacy_delete_goal(
    goal_id
):

    return delete_daily_goal(
        goal_id
    )


# ============================================================
# END OF GOAL MODULE
# ============================================================