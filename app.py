import re
import json
from datetime import date, timedelta, datetime
from zoneinfo import ZoneInfo

from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    session,
    jsonify,
)

from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from werkzeug.security import generate_password_hash, check_password_hash

import config

from ml_utils import (
    predict_next_day,
    predict_next_week,
    predict_weekly_trend,
    calculate_consistency_score,
)

from diet_ai import generate_diet_plan


# ============================================================
# APP CONFIGURATION
# ============================================================

app = Flask(__name__)
app.config.from_object(config)

db = SQLAlchemy(
    app,
    engine_options=config.SQLALCHEMY_ENGINE_OPTIONS
)


# ============================================================
# DATABASE MODELS
# ============================================================

class User(db.Model):
    __tablename__ = "users"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    name = db.Column(
        db.String(120),
        nullable=False
    )

    email = db.Column(
        db.String(120),
        unique=True,
        nullable=False
    )

    password = db.Column(
        db.String(200),
        nullable=False
    )

    age = db.Column(
        db.Integer
    )

    height = db.Column(
        db.Float
    )

    weight = db.Column(
        db.Float
    )

    gender = db.Column(
        db.String(20)
    )

    activity_level = db.Column(
        db.String(50)
    )

    goal = db.Column(
        db.String(50)
    )


class WeeklyGoal(db.Model):
    __tablename__ = "weekly_goals"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False
    )

    week_start = db.Column(
        db.Date,
        nullable=False
    )

    workouts_target = db.Column(
        db.Integer,
        default=5
    )

    calories_target = db.Column(
        db.Integer,
        default=2000
    )

    water_target_l = db.Column(
        db.Float,
        default=2.5
    )

    created_at = db.Column(
        db.DateTime,
        server_default=db.func.now()
    )

    __table_args__ = (
        db.UniqueConstraint(
            "user_id",
            "week_start",
            name="uq_weekly_goal_user_week"
        ),
    )


class DailyLog(db.Model):
    __tablename__ = "daily_logs"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False
    )

    log_date = db.Column(
        db.Date,
        nullable=False
    )

    workout_done = db.Column(
        db.Boolean,
        default=False
    )

    calories_intake = db.Column(
        db.Integer
    )

    water_intake_l = db.Column(
        db.Float
    )

    sleep_hours = db.Column(
        db.Float
    )

    mood = db.Column(
        db.Integer
    )

    notes = db.Column(
        db.Text,
        default=""
    )

    created_at = db.Column(
        db.DateTime,
        server_default=db.func.now()
    )

    __table_args__ = (
        db.UniqueConstraint(
            "user_id",
            "log_date",
            name="uq_daily_log_user_date"
        ),
    )


class DailyGoal(db.Model):
    __tablename__ = "daily_goals"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False
    )

    goal_date = db.Column(
        db.Date,
        nullable=False
    )

    title = db.Column(
        db.String(255),
        nullable=False
    )

    completed = db.Column(
        db.Boolean,
        default=False
    )

    description = db.Column(
        db.String(255),
        default=""
    )

    created_at = db.Column(
        db.DateTime,
        server_default=db.func.now()
    )


class DietPlan(db.Model):
    __tablename__ = "diet_plans"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False
    )

    plan_json = db.Column(
        db.Text,
        nullable=False
    )

    inputs_json = db.Column(
        db.Text,
        nullable=False
    )

    created_at = db.Column(
        db.DateTime,
        server_default=db.func.now()
    )


# ============================================================
# DATABASE INITIALIZATION + SAFE GENDER MIGRATION
# ============================================================

with app.app_context():

    db.create_all()

    # Lightweight migrations keep existing local/PostgreSQL
    # databases compatible when FitLyfe gains new fields.
    def _add_column_if_missing(
        table_name,
        column_name,
        column_sql
    ):
        try:

            inspector = db.inspect(
                db.engine
            )

            existing = {
                col["name"]
                for col in inspector.get_columns(
                    table_name
                )
            }

            if column_name not in existing:

                db.session.execute(
                    db.text(
                        f"ALTER TABLE {table_name} "
                        f"ADD COLUMN {column_name} {column_sql}"
                    )
                )

                db.session.commit()

        except Exception as exc:

            db.session.rollback()

            print(
                f"MIGRATION WARNING "
                f"[{table_name}.{column_name}]:",
                exc
            )

    _add_column_if_missing(
        "users",
        "gender",
        "VARCHAR(20)"
    )

    _add_column_if_missing(
        "daily_goals",
        "description",
        "VARCHAR(255)"
    )

    _add_column_if_missing(
        "daily_logs",
        "notes",
        "TEXT"
    )


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def india_today():
    """
    Return today's date according to India Standard Time (IST).

    Render servers normally use UTC, so date.today() can return
    yesterday during the early morning hours in India.
    """
    return datetime.now(
        ZoneInfo("Asia/Kolkata")
    ).date()


# ------------------------------------------------------------

def get_current_user():

    user_id = session.get(
        "user_id"
    )

    if not user_id:
        return None

    return db.session.get(
        User,
        user_id
    )


# ------------------------------------------------------------

def week_start_for(d):

    return d - timedelta(
        days=d.weekday()
    )


# ------------------------------------------------------------

def parse_date(value):

    if not value:
        return None

    try:

        return date.fromisoformat(
            value
        )

    except (
        ValueError,
        TypeError
    ):

        return None


# ------------------------------------------------------------
# SAFE NEXT PAGE
# ------------------------------------------------------------

def get_safe_next_page(value):

    """
    Only allow internal application paths.

    Valid:
        /detail
        /bmi-calculator
        /dashboard

    Invalid:
        https://example.com
        //example.com
    """

    if not value:
        return None

    value = str(
        value
    ).strip()

    if (
        value.startswith("/")
        and not value.startswith("//")
    ):

        return value

    return None


# ------------------------------------------------------------

def login_required_json():

    user = get_current_user()

    if not user:

        return None, (
            jsonify({
                "success": False,
                "error": "Authentication required."
            }),
            401,
        )

    return user, None


# ------------------------------------------------------------

def profile_is_complete(user):

    if not user:
        return False

    return all([
        user.age is not None,
        user.height is not None,
        user.weight is not None,
        user.activity_level,
        user.goal,
    ])


# ------------------------------------------------------------

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
    "weight_maintenance": "maintenance",

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


ALLOWED_GOALS = {
    "weight_loss",
    "weight_gain",
    "muscle_gain",
    "maintenance",
    "general_fitness",
    "endurance",
}


ACTIVITY_ALIASES = {

    "sedentary": "sedentary",
    "low": "sedentary",

    "light": "light",
    "lightly active": "light",

    "moderate": "moderate",
    "moderately active": "moderate",

    "active": "active",

    "very active": "very_active",
    "very_active": "very_active",
}


def normalize_goal(value):

    """Return one canonical fitness-goal key for any common spelling."""

    if value is None:
        return None

    raw = str(
        value
    ).strip().lower()

    raw = re.sub(
        r"[^a-z0-9]+",
        "_",
        raw
    ).strip("_")

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

    # Also support human-readable aliases and legacy database values.
    spaced = raw.replace(
        "_",
        " "
    )

    alias = (
        GOAL_ALIASES.get(spaced)
        or GOAL_ALIASES.get(raw)
    )

    if alias:
        return alias

    # Last-resort semantic repair for old/custom labels.
    if any(
        token in raw
        for token in (
            "lose",
            "loss",
            "fat"
        )
    ):
        return "weight_loss"

    if any(
        token in raw
        for token in (
            "muscle",
            "build"
        )
    ):
        return "muscle_gain"

    if any(
        token in raw
        for token in (
            "endurance",
            "cardio",
            "stamina"
        )
    ):
        return "endurance"

    if any(
        token in raw
        for token in (
            "gain",
            "bulk"
        )
    ):
        return "weight_gain"

    if any(
        token in raw
        for token in (
            "maintain",
            "maintenance"
        )
    ):
        return "maintenance"

    if "fitness" in raw:
        return "general_fitness"

    return None


def normalize_activity(value):

    if value is None:
        return None

    raw = re.sub(
        r"\s+",
        " ",
        str(value).strip().lower()
    )

    return ACTIVITY_ALIASES.get(
        raw
    )


# ------------------------------------------------------------

def get_profile_redirect():

    user = get_current_user()

    if not user:

        return redirect(
            url_for("login")
        )

    if not profile_is_complete(user):

        flash(
            "⚠️ Please complete your profile first.",
            "warning"
        )

        return redirect(
            url_for(
                "profile",
                next=request.path
            )
        )

    return None


# ============================================================
# STREAK CALCULATION
# ============================================================

def calculate_current_streak(user_id):

    logs = (
        DailyLog.query
        .filter_by(
            user_id=user_id
        )
        .order_by(
            DailyLog.log_date.desc()
        )
        .all()
    )

    if not logs:
        return 0

    completed_dates = {
        log.log_date
        for log in logs
        if log.workout_done
    }

    if not completed_dates:
        return 0

    today = india_today()

    if today in completed_dates:

        current_day = today

    elif (
        today - timedelta(days=1)
    ) in completed_dates:

        current_day = (
            today
            - timedelta(days=1)
        )

    else:

        return 0

    streak = 0

    while current_day in completed_dates:

        streak += 1

        current_day -= timedelta(
            days=1
        )

    return streak


# ============================================================
# HISTORICAL WEEKLY PROGRESS
# ============================================================

def get_historical_weekly_progress(
    user_id,
    number_of_weeks=4
):

    today = india_today()

    current_week = week_start_for(
        today
    )

    weekly_progress = []

    for i in range(
        number_of_weeks - 1,
        -1,
        -1
    ):

        week_start = (
            current_week
            - timedelta(
                weeks=i
            )
        )

        week_end = (
            week_start
            + timedelta(
                days=6
            )
        )

        goal = (
            WeeklyGoal.query
            .filter_by(
                user_id=user_id,
                week_start=week_start
            )
            .first()
        )

        workouts_target = (
            goal.workouts_target
            if goal
            else 5
        )

        completed = (
            DailyLog.query
            .filter(
                DailyLog.user_id == user_id,
                DailyLog.log_date >= week_start,
                DailyLog.log_date <= week_end,
                DailyLog.workout_done.is_(True),
            )
            .count()
        )

        if workouts_target:

            percentage = round(
                min(
                    completed
                    / workouts_target
                    * 100,
                    100,
                ),
                1
            )

        else:

            percentage = 0

        weekly_progress.append({
            "week_start": week_start.isoformat(),
            "completed": completed,
            "target": workouts_target,
            "percentage": percentage,
        })

    return weekly_progress


# ============================================================
# HOME
# ============================================================

@app.route("/")
def home():

    return render_template(
        "index.html"
    )


# ============================================================
# LOGIN
# ============================================================

@app.route(
    "/login",
    methods=["GET", "POST"]
)
def login():

    if request.method == "POST":

        email = (
            request.form
            .get("email", "")
            .strip()
            .lower()
        )

        password = request.form.get(
            "password",
            ""
        )

        user = (
            User.query
            .filter_by(
                email=email
            )
            .first()
        )

        if (
            not user
            or not check_password_hash(
                user.password,
                password
            )
        ):

            flash(
                "❌ Invalid email or password.",
                "danger"
            )

            return redirect(
                url_for("login")
            )

        session.clear()

        session["user_id"] = user.id

        # First successful login -> profile setup.
        # Later logins -> detail.
        if not profile_is_complete(user):

            flash(
                "Welcome to FitLyfe! Complete your profile to continue.",
                "success"
            )

            return redirect(
                url_for("profile")
            )

        flash(
            f"Welcome back, {user.name}!",
            "success"
        )

        return redirect(
            url_for("detail")
        )

    return render_template(
        "login.html"
    )


# ============================================================
# REGISTER
# ============================================================

@app.route(
    "/register",
    methods=["GET", "POST"]
)
def register():

    if request.method == "POST":

        name = (
            request.form
            .get("name", "")
            .strip()
        )

        email = (
            request.form
            .get("email", "")
            .strip()
            .lower()
        )

        password = request.form.get(
            "password",
            ""
        )

        confirm_password = request.form.get(
            "confirm_password",
            ""
        )

        # ----------------------------------------------------
        # BASIC VALIDATION
        # ----------------------------------------------------

        if not name or not email or not password:

            flash(
                "⚠️ Please fill in all required fields.",
                "warning"
            )

            return render_template(
                "register.html",
                name=name,
                email=email
            )

        if not re.match(
            r"^[^@\s]+@[^@\s]+\.[^@\s]+$",
            email
        ):

            flash(
                "⚠️ Please enter a valid email address.",
                "warning"
            )

            return render_template(
                "register.html",
                name=name,
                email=email
            )

        if len(password) < 6:

            flash(
                "⚠️ Password must contain at least 6 characters.",
                "warning"
            )

            return render_template(
                "register.html",
                name=name,
                email=email
            )

        if password != confirm_password:

            flash(
                "❌ Passwords do not match.",
                "danger"
            )

            return render_template(
                "register.html",
                name=name,
                email=email
            )

        # ----------------------------------------------------
        # CASE-INSENSITIVE DUPLICATE EMAIL CHECK
        # ----------------------------------------------------

        existing = (
            User.query
            .filter(
                func.lower(
                    func.trim(
                        User.email
                    )
                ) == email
            )
            .first()
        )

        if existing:

            flash(
                "⚠️ This email is already registered. Please login instead.",
                "warning"
            )

            return render_template(
                "register.html",
                name=name,
                email=email,
                email_exists=True
            )

        # ----------------------------------------------------
        # CREATE USER
        # ----------------------------------------------------

        user = User(
            name=name,
            email=email,
            password=generate_password_hash(
                password
            )
        )

        db.session.add(user)

        # ====================================================
        # DATABASE DIAGNOSTIC
        # ====================================================

        print(
            "DATABASE:",
            db.engine.url.render_as_string(
                hide_password=True
            )
        )

        # ----------------------------------------------------
        # SAVE USER
        # ----------------------------------------------------

        try:

            db.session.commit()

            print(
                "REGISTER SAVED:",
                user.id,
                user.name,
                user.email
            )

        except IntegrityError:

            db.session.rollback()

            print(
                "REGISTER ERROR: IntegrityError"
            )

            flash(
                "⚠️ This email is already registered. Please login instead.",
                "warning"
            )

            return render_template(
                "register.html",
                name=name,
                email=email,
                email_exists=True
            )

        # ----------------------------------------------------
        # SUCCESS
        # ----------------------------------------------------

        flash(
            "🎉 Account created! Please login to start your FitLyfe journey.",
            "success"
        )

        return redirect(
            url_for("login")
        )

    return render_template(
        "register.html"
    )


# ============================================================
# CHECK EMAIL
# ============================================================

@app.route(
    "/api/check-email"
)
def check_email():

    email = (
        request.args
        .get("email", "")
        .strip()
        .lower()
    )

    valid = bool(
        re.match(
            r"^[^@\s]+@[^@\s]+\.[^@\s]+$",
            email
        )
    )

    if not valid:

        return jsonify({
            "success": True,
            "available": False,
            "exists": False,
            "valid": False
        })

    exists = (
        User.query
        .filter(
            func.lower(
                func.trim(
                    User.email
                )
            ) == email
        )
        .first()
        is not None
    )

    return jsonify({
        "success": True,
        "available": not exists,
        "exists": exists,
        "valid": True,
    })


# ============================================================
# PROFILE
# ============================================================

@app.route(
    "/profile",
    methods=["GET", "POST"]
)
def profile():

    user = get_current_user()

    if not user:

        return redirect(
            url_for("login")
        )

    # ========================================================
    # GET PROFILE PAGE
    # ========================================================

    if request.method == "GET":

        next_page = get_safe_next_page(
            request.args.get(
                "next",
                ""
            )
        )

        if next_page:

            session["profile_next"] = next_page

        if not next_page:

            next_page = get_safe_next_page(
                session.get(
                    "profile_next",
                    ""
                )
            )

        return render_template(
            "profile.html",
            user=user,
            next_page=next_page or ""
        )

    # ========================================================
    # POST - SAVE PROFILE
    # ========================================================

    next_page = (
        request.form.get("next")
        or request.args.get("next")
        or session.get("profile_next")
        or ""
    )

    next_page = get_safe_next_page(
        next_page
    )

    was_profile_complete = profile_is_complete(
        user
    )

    # ========================================================
    # NAME
    # ========================================================

    user.name = (
        request.form
        .get("name", "")
        .strip()
    )

    # ========================================================
    # EMAIL
    # ========================================================

    new_email = (
        request.form
        .get("email", "")
        .strip()
        .lower()
    )

    if (
        new_email
        and new_email != user.email
    ):

        existing_email_user = (
            User.query
            .filter(
                User.email == new_email,
                User.id != user.id
            )
            .first()
        )

        if existing_email_user:

            flash(
                "❌ This email address is already in use.",
                "danger"
            )

            return redirect(
                url_for(
                    "profile",
                    next=next_page
                )
                if next_page
                else url_for("profile")
            )

    user.email = new_email

    # ========================================================
    # AGE
    # ========================================================

    age_value = (
        request.form
        .get("age", "")
        .strip()
    )

    if age_value:

        try:

            user.age = int(
                age_value
            )

        except ValueError:

            user.age = None

    else:

        user.age = None

    # ========================================================
    # HEIGHT
    # ========================================================

    height_value = (
        request.form
        .get("height", "")
        .strip()
    )

    if height_value:

        try:

            user.height = float(
                height_value
            )

        except ValueError:

            user.height = None

    else:

        user.height = None

    # ========================================================
    # WEIGHT
    # ========================================================

    weight_value = (
        request.form
        .get("weight", "")
        .strip()
    )

    if weight_value:

        try:

            user.weight = float(
                weight_value
            )

        except ValueError:

            user.weight = None

    else:

        user.weight = None

    # ========================================================
    # GENDER
    # ========================================================

    gender_value = (
        request.form
        .get("gender", "")
        .strip()
        .lower()
    )

    allowed_genders = {
        "male",
        "female",
    }

    if gender_value in allowed_genders:

        user.gender = gender_value

    else:

        user.gender = None

    # ========================================================
    # ACTIVITY LEVEL
    # ========================================================

    user.activity_level = normalize_activity(
        request.form.get(
            "activity_level",
            ""
        )
    ) or ""

    # ========================================================
    # GOAL
    # ========================================================

    user.goal = normalize_goal(
        request.form.get(
            "goal",
            ""
        )
    ) or ""

    # ========================================================
    # SAVE DATABASE
    # ========================================================

    try:

        db.session.commit()

    except Exception as e:

        db.session.rollback()

        print(
            "PROFILE UPDATE ERROR:",
            e
        )

        flash(
            "❌ Unable to update your profile. Please try again.",
            "danger"
        )

        if next_page:

            return redirect(
                url_for(
                    "profile",
                    next=next_page
                )
            )

        return redirect(
            url_for("profile")
        )

    flash(
        "✅ Profile updated successfully!",
        "success"
    )

    # ========================================================
    # REDIRECT AFTER SUCCESSFUL SAVE
    # ========================================================

    if next_page:

        session.pop(
            "profile_next",
            None
        )

        return redirect(
            next_page
        )

    if (
        not was_profile_complete
        and profile_is_complete(user)
    ):

        session.pop(
            "profile_next",
            None
        )

        return redirect(
            url_for("detail")
        )

    return redirect(
        url_for("detail")
    )


# ============================================================
# LOGOUT
# ============================================================

@app.route("/logout")
def logout():

    session.clear()

    flash(
        "👋 You have been logged out.",
        "success"
    )

    return redirect(
        url_for("login")
    )


# ============================================================
# FEATURES
# ============================================================

@app.route("/features")
def features():

    return render_template(
        "features.html"
    )


# ============================================================
# DETAIL
# ============================================================

@app.route("/detail")
def detail():

    redirect_response = get_profile_redirect()

    if redirect_response:
        return redirect_response

    user = get_current_user()

    return render_template(
        "detail.html",
        user=user
    )


# ============================================================
# ABOUT
# ============================================================

@app.route("/about")
def about():

    return render_template(
        "about.html"
    )


# ============================================================
# GOAL TRACKER PAGE
# ============================================================

@app.route("/goal-tracker")
def goal_tracker():

    redirect_response = get_profile_redirect()

    if redirect_response:
        return redirect_response

    user = get_current_user()

    return render_template(
        "goal_tracker.html",
        user=user
    )


# ============================================================
# BMI CALCULATOR
# ============================================================

@app.route("/bmi-calculator")
def bmi_calculator():

    redirect_response = get_profile_redirect()

    if redirect_response:
        return redirect_response

    user = get_current_user()

    bmi = None
    category = None
    category_description = None

    # --------------------------------------------------------
    # BMI CALCULATION
    # --------------------------------------------------------

    if (
        user.height
        and user.weight
        and user.height > 0
        and user.weight > 0
    ):

        height_m = (
            float(user.height)
            / 100
        )

        weight_kg = float(
            user.weight
        )

        bmi = round(
            weight_kg
            / (height_m * height_m),
            1
        )

        # ----------------------------------------------------
        # STANDARD ADULT BMI CATEGORIES
        # ----------------------------------------------------

        if bmi < 18.5:

            category = "Underweight"

            category_description = (
                "Your BMI is below the standard healthy range. "
                "A balanced nutrition plan may help you reach "
                "a healthier weight."
            )

        elif bmi < 25:

            category = "Healthy Weight"

            category_description = (
                "Your BMI is within the standard healthy range. "
                "Keep maintaining balanced nutrition, exercise, "
                "sleep, and hydration."
            )

        elif bmi < 30:

            category = "Overweight"

            category_description = (
                "Your BMI is above the standard healthy range. "
                "A consistent exercise routine and balanced "
                "nutrition can support healthy progress."
            )

        else:

            category = "Obesity"

            category_description = (
                "Your BMI is in the obesity range. "
                "Consider focusing on sustainable nutrition, "
                "regular activity, and professional guidance "
                "where appropriate."
            )

    return render_template(
        "bmi_calculator.html",
        user=user,
        bmi=bmi,
        category=category,
        category_description=category_description,
    )


# ============================================================
# AI DIET CHART PAGE
# ============================================================

@app.route("/ai-diet-chart")
def ai_diet_chart():

    redirect_response = get_profile_redirect()

    if redirect_response:
        return redirect_response

    user = get_current_user()

    latest_plan = (
        DietPlan.query
        .filter_by(
            user_id=user.id
        )
        .order_by(
            DietPlan.created_at.desc()
        )
        .first()
    )

    plan_data = None

    if latest_plan:

        try:

            plan_data = json.loads(
                latest_plan.plan_json
            )

        except Exception:

            plan_data = None

    return render_template(
        "ai_diet_chart.html",
        user=user,
        latest_plan=plan_data
    )


# ============================================================
# AI DIET PLAN GENERATION API
# ============================================================

@app.route(
    "/api/diet-plan/generate",
    methods=["POST"]
)
def generate_diet_plan_api():

    user, error_response = login_required_json()

    if error_response:
        return error_response

    data = request.get_json(
        silent=True
    ) or {}

    # --------------------------------------------------------
    # VALIDATE PROFILE
    # --------------------------------------------------------

    if (
        user.age is None
        or user.height is None
        or user.weight is None
        or not user.activity_level
        or not user.goal
    ):

        return jsonify({
            "success": False,
            "error": (
                "Please complete your profile before "
                "generating a diet plan."
            )
        }), 400

    # --------------------------------------------------------
    # AGE
    # --------------------------------------------------------

    try:

        age = int(
            user.age
        )

    except (
        ValueError,
        TypeError
    ):

        return jsonify({
            "success": False,
            "error": "Invalid age in profile."
        }), 400

    # --------------------------------------------------------
    # HEIGHT
    # --------------------------------------------------------

    try:

        height = float(
            user.height
        )

    except (
        ValueError,
        TypeError
    ):

        return jsonify({
            "success": False,
            "error": "Invalid height in profile."
        }), 400

    # --------------------------------------------------------
    # WEIGHT
    # --------------------------------------------------------

    try:

        weight = float(
            user.weight
        )

    except (
        ValueError,
        TypeError
    ):

        return jsonify({
            "success": False,
            "error": "Invalid weight in profile."
        }), 400

    # --------------------------------------------------------
    # ACTIVITY LEVEL
    # --------------------------------------------------------

    activity_level = (
        str(user.activity_level)
        .strip()
        .lower()
    )

    activity_aliases = {

        "sedentary": "sedentary",
        "low": "sedentary",

        "light": "light",
        "lightly active": "light",

        "moderate": "moderate",
        "moderately active": "moderate",

        "active": "active",

        "very active": "very_active",
        "very_active": "very_active",
    }

    activity_level = activity_aliases.get(
        activity_level,
        activity_level
    )

    allowed_activity = {
        "sedentary",
        "light",
        "moderate",
        "active",
        "very_active",
    }

    if activity_level not in allowed_activity:

        return jsonify({
            "success": False,
            "error": "Invalid activity level in profile."
        }), 400

    # --------------------------------------------------------
    # GOAL
    # --------------------------------------------------------

    goal = normalize_goal(
        user.goal
    )

    # Repair legacy goal values automatically.
    if (
        goal in ALLOWED_GOALS
        and user.goal != goal
    ):

        user.goal = goal

        try:

            db.session.commit()

        except Exception:

            db.session.rollback()

    if goal not in ALLOWED_GOALS:

        return jsonify({
            "success": False,
            "error": (
                "Your saved fitness goal is not recognized. "
                "Open Profile, select your goal again, and save it."
            ),
            "profile_goal": str(
                user.goal or ""
            ),
        }), 400

    # --------------------------------------------------------
    # GENDER / SEX
    # --------------------------------------------------------

    sex_value = str(
        data.get("sex")
        or user.gender
        or "prefer_not_to_say"
    ).strip().lower()

    allowed_sex = {
        "male",
        "female",
        "prefer_not_to_say",
    }

    if sex_value not in allowed_sex:

        sex_value = "prefer_not_to_say"

    # --------------------------------------------------------
    # PROFILE DATA
    # --------------------------------------------------------

    profile = {

        "name": user.name,

        "age": age,

        "height": height,

        "weight": weight,

        "gender": user.gender,

        "activity_level": activity_level,

        "goal": goal,
    }

    # --------------------------------------------------------
    # OPTIONAL DIET PREFERENCES
    # --------------------------------------------------------

    diet_type = str(
        data.get(
            "diet_type",
            "balanced"
        )
    ).strip().lower()

    meals_per_day = data.get(
        "meals_per_day",
        3
    )

    try:

        meals_per_day = int(
            meals_per_day
        )

    except (
        ValueError,
        TypeError
    ):

        meals_per_day = 3

    if meals_per_day < 2:
        meals_per_day = 2

    if meals_per_day > 6:
        meals_per_day = 6

    allergies = str(
        data.get(
            "allergies",
            ""
        )
    ).strip()

    dislikes = str(
        data.get(
            "dislikes",
            ""
        )
    ).strip()

    cuisine = str(
        data.get(
            "cuisine",
            "Indian"
        )
    ).strip()

    budget = str(
        data.get(
            "budget",
            "moderate"
        )
    ).strip().lower()

    preferences = {

        "diet_type": diet_type,

        "meals_per_day": meals_per_day,

        "sex": sex_value,

        "allergies": allergies,

        "dislikes": dislikes,

        "cuisine": cuisine,

        "budget": budget,
    }

    # --------------------------------------------------------
    # GENERATE AI PLAN
    # --------------------------------------------------------

    try:

        generated_plan = generate_diet_plan(
            profile,
            preferences
        )

    except Exception as e:

        print(
            "DIET PLAN GENERATION ERROR:",
            e
        )

        return jsonify({
            "success": False,
            "error": (
                "Unable to generate the diet plan "
                "right now. Please try again."
            )
        }), 500

    # --------------------------------------------------------
    # CONVERT PLAN TO JSON
    # --------------------------------------------------------

    try:

        if isinstance(
            generated_plan,
            str
        ):

            try:

                plan_json_data = json.loads(
                    generated_plan
                )

            except json.JSONDecodeError:

                plan_json_data = {
                    "plan": generated_plan
                }

        else:

            plan_json_data = generated_plan

        plan_json = json.dumps(
            plan_json_data,
            ensure_ascii=False
        )

    except Exception as e:

        print(
            "DIET PLAN JSON ERROR:",
            e
        )

        return jsonify({
            "success": False,
            "error": "Invalid diet plan response."
        }), 500

    # --------------------------------------------------------
    # SAVE PLAN
    # --------------------------------------------------------

    try:

        saved_plan = DietPlan(

            user_id=user.id,

            plan_json=plan_json,

            inputs_json=json.dumps(
                {
                    "profile": profile,
                    "preferences": preferences,
                },
                ensure_ascii=False
            ),
        )

        db.session.add(
            saved_plan
        )

        db.session.commit()

    except Exception as e:

        db.session.rollback()

        print(
            "DIET PLAN DATABASE ERROR:",
            e
        )

        return jsonify({
            "success": False,
            "error": (
                "Diet plan was generated but could "
                "not be saved."
            )
        }), 500

    return jsonify({

        "success": True,

        "plan": plan_json_data,

        "message": (
            "AI diet plan generated successfully."
        )
    })


# ============================================================
# DASHBOARD
# ============================================================

@app.route("/dashboard")
def dashboard():

    redirect_response = get_profile_redirect()

    if redirect_response:
        return redirect_response

    user = get_current_user()

    return render_template(
        "dashboard.html",
        user=user
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

    goal = (
        WeeklyGoal.query
        .filter_by(
            user_id=user.id,
            week_start=week_start
        )
        .first()
    )

    if not goal:

        goal = WeeklyGoal(
            user_id=user.id,
            week_start=week_start,
        )

        db.session.add(
            goal
        )

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

    return jsonify({

        "success": True,

        "message": "Weekly goal saved successfully.",

        "goal": {

            "week_start": (
                week_start.isoformat()
            ),

            "workouts_target": (
                goal.workouts_target
            ),

            "calories_target": (
                goal.calories_target
            ),

            "water_target_l": (
                goal.water_target_l
            ),
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

    log = (
        DailyLog.query
        .filter_by(
            user_id=user.id,
            log_date=log_date
        )
        .first()
    )

    if not log:

        return jsonify({
            "success": True,
            "log": None
        })

    return jsonify({

        "success": True,

        "log": {

            "date": log.log_date.isoformat(),

            "workout_done": bool(
                log.workout_done
            ),

            "calories_intake": (
                log.calories_intake
            ),

            "water_intake_l": (
                log.water_intake_l
            ),

            "sleep_hours": (
                log.sleep_hours
            ),

            "mood": log.mood,

            "notes": log.notes or "",
        }
    })


# ============================================================
# API - DAILY LOG
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

    log_date = parse_date(
        data.get("log_date")
    )

    if not log_date:

        log_date = india_today()

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

    if mood is not None:

        mood = max(
            1,
            min(
                mood,
                5
            )
        )

    notes = str(
        data.get(
            "notes",
            ""
        )
    ).strip()[:2000]

    log = (
        DailyLog.query
        .filter_by(
            user_id=user.id,
            log_date=log_date
        )
        .first()
    )

    if not log:

        log = DailyLog(
            user_id=user.id,
            log_date=log_date,
        )

        db.session.add(
            log
        )

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

    return jsonify({

        "success": True,

        "message": "Daily log saved successfully.",

        "log": {

            "date": log.log_date.isoformat(),

            "workout_done": bool(
                log.workout_done
            ),

            "calories_intake": (
                log.calories_intake
            ),

            "water_intake_l": (
                log.water_intake_l
            ),

            "sleep_hours": (
                log.sleep_hours
            ),

            "mood": log.mood,

            "notes": log.notes or "",
        }
    })


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

    return jsonify({

        "success": True,

        "goals": [

            {

                "id": goal.id,

                "title": goal.title,

                "completed": goal.completed,

                "description": (
                    goal.description or ""
                ),

                "goal_date": (
                    goal.goal_date.isoformat()
                ),
            }

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

    title = (
        str(
            data.get(
                "title",
                ""
            )
        )
        .strip()
    )

    if not title:

        return jsonify({

            "success": False,

            "error": "Goal title is required."
        }), 400

    goal_date = parse_date(
        data.get("goal_date")
    )

    if not goal_date:

        goal_date = india_today()

    description = str(
        data.get(
            "description",
            ""
        )
    ).strip()[:255]

    goal = DailyGoal(

        user_id=user.id,

        goal_date=goal_date,

        title=title,

        completed=False,

        description=description,
    )

    db.session.add(
        goal
    )

    db.session.commit()

    return jsonify({

        "success": True,

        "goal": {

            "id": goal.id,

            "title": goal.title,

            "completed": goal.completed,

            "description": (
                goal.description or ""
            ),

            "goal_date": (
                goal.goal_date.isoformat()
            ),
        }
    })


# ============================================================
# API - DAILY GOAL TOGGLE
# ============================================================

@app.route(
    "/api/daily-goals/<int:goal_id>/toggle",
    methods=["POST"]
)
def toggle_daily_goal(goal_id):

    user, error_response = login_required_json()

    if error_response:
        return error_response

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

            "error": "Goal not found."
        }), 404

    goal.completed = not goal.completed

    db.session.commit()

    return jsonify({

        "success": True,

        "completed": goal.completed
    })


# ============================================================
# API - DAILY GOAL DELETE
# ============================================================

@app.route(
    "/api/daily-goals/<int:goal_id>",
    methods=["DELETE"]
)
def delete_daily_goal(goal_id):

    user, error_response = login_required_json()

    if error_response:
        return error_response

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

            "error": "Goal not found."
        }), 404

    db.session.delete(
        goal
    )

    db.session.commit()

    return jsonify({

        "success": True,

        "message": "Goal deleted successfully."
    })


# ============================================================
# BACKWARD-COMPATIBILITY GOAL ENDPOINTS
# ============================================================

# Older cached dashboard.js versions used /api/goals.
# Keep these aliases so an old browser tab cannot break
# goal creation/toggling/deletion.

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
def legacy_toggle_goal(goal_id):

    return toggle_daily_goal(
        goal_id
    )


@app.route(
    "/api/goals/<int:goal_id>",
    methods=["DELETE"]
)
def legacy_delete_goal(goal_id):

    return delete_daily_goal(
        goal_id
    )


# ============================================================
# API - CALENDAR DATA
# ============================================================

@app.route(
    "/api/calendar-data"
)
def calendar_data():

    user, error_response = login_required_json()

    if error_response:
        return error_response

    try:

        year = int(
            request.args.get(
                "year",
                india_today().year
            )
        )

        month = int(
            request.args.get(
                "month",
                india_today().month
            )
        )

        if not 1 <= month <= 12:
            raise ValueError

    except (
        ValueError,
        TypeError
    ):

        year = india_today().year
        month = india_today().month

    import calendar as _calendar

    days_in_month = _calendar.monthrange(
        year,
        month
    )[1]

    start_date = date(
        year,
        month,
        1
    )

    end_date = date(
        year,
        month,
        days_in_month
    )

    logs = (
        DailyLog.query
        .filter(
            DailyLog.user_id == user.id,
            DailyLog.log_date >= start_date,
            DailyLog.log_date <= end_date,
        )
        .all()
    )

    goals = (
        DailyGoal.query
        .filter(
            DailyGoal.user_id == user.id,
            DailyGoal.goal_date >= start_date,
            DailyGoal.goal_date <= end_date,
        )
        .all()
    )

    logs_by_date = {
        item.log_date: item
        for item in logs
    }

    goals_by_date = {}

    for goal in goals:

        goals_by_date.setdefault(
            goal.goal_date,
            []
        ).append(
            goal
        )

    today = india_today()

    days = []

    for day_number in range(
        1,
        days_in_month + 1
    ):

        current = date(
            year,
            month,
            day_number
        )

        log = logs_by_date.get(
            current
        )

        day_goals = goals_by_date.get(
            current,
            []
        )

        if day_goals:

            percentage = round(
                sum(
                    1
                    for goal in day_goals
                    if goal.completed
                )
                / len(day_goals)
                * 100
            )

        elif log:

            percentage = (
                100
                if log.workout_done
                else 0
            )

        else:

            percentage = 0

        if current > today:

            state = "future"

        elif (
            percentage >= 100
            and (day_goals or log)
        ):

            state = "completed"

        elif (
            percentage > 0
            or log
        ):

            state = "partial"

        else:

            state = "missed"

        days.append({

            "day": day_number,

            "date": current.isoformat(),

            "state": state,

            "percentage": percentage,

            "has_log": bool(log),

            "has_goals": bool(day_goals),

            "goal_count": len(day_goals),

            "completed_goals": sum(
                1
                for goal in day_goals
                if goal.completed
            ),

            "is_today": (
                current == today
            ),
        })

    return jsonify({

        "success": True,

        "year": year,

        "month": month,

        "days": days,
    })


# ============================================================
# API - DASHBOARD DATA
# ============================================================

@app.route(
    "/api/dashboard-data"
)
def dashboard_data():

    user, error_response = login_required_json()

    if error_response:
        return error_response

    selected_date = (
        parse_date(
            request.args.get("date")
        )
        or india_today()
    )

    today = india_today()

    selected_goals = (
        DailyGoal.query
        .filter_by(
            user_id=user.id,
            goal_date=selected_date,
        )
        .order_by(
            DailyGoal.id.asc()
        )
        .all()
    )

    selected_log = (
        DailyLog.query
        .filter_by(
            user_id=user.id,
            log_date=selected_date,
        )
        .first()
    )

    goal_total = len(
        selected_goals
    )

    goal_completed = sum(
        1
        for goal in selected_goals
        if goal.completed
    )

    if goal_total:

        selected_percentage = round(
            goal_completed
            / goal_total
            * 100
        )

    elif selected_log:

        selected_percentage = (
            100
            if selected_log.workout_done
            else 0
        )

    else:

        selected_percentage = 0

    # ========================================================
    # CURRENT WEEK
    # ========================================================

    week_start = week_start_for(
        today
    )

    week_end = (
        week_start
        + timedelta(days=6)
    )

    week_logs = (
        DailyLog.query
        .filter(
            DailyLog.user_id == user.id,
            DailyLog.log_date >= week_start,
            DailyLog.log_date <= week_end,
        )
        .all()
    )

    week_goals = (
        DailyGoal.query
        .filter(
            DailyGoal.user_id == user.id,
            DailyGoal.goal_date >= week_start,
            DailyGoal.goal_date <= week_end,
        )
        .all()
    )

    logs_by_date = {
        log.log_date: log
        for log in week_logs
    }

    goals_by_date = {}

    for goal in week_goals:

        goals_by_date.setdefault(
            goal.goal_date,
            []
        ).append(
            goal
        )

    weekly_labels = []
    weekly_series = []

    for offset in range(7):

        current = (
            week_start
            + timedelta(days=offset)
        )

        day_goals = goals_by_date.get(
            current,
            []
        )

        log = logs_by_date.get(
            current
        )

        if day_goals:

            rate = round(
                sum(
                    1
                    for goal in day_goals
                    if goal.completed
                )
                / len(day_goals)
                * 100
            )

        elif log:

            rate = (
                100
                if log.workout_done
                else 0
            )

        else:

            rate = 0

        weekly_labels.append(
            current.strftime("%a")
        )

        weekly_series.append(
            rate
        )

    weekly_average = round(
        sum(weekly_series)
        / len(weekly_series)
    )

    active_days = sum(
        1
        for value in weekly_series
        if value > 0
    )

    # ========================================================
    # ALL HISTORICAL ACTIVITY
    # ========================================================

    all_logs = (
        DailyLog.query
        .filter_by(
            user_id=user.id
        )
        .order_by(
            DailyLog.log_date.asc()
        )
        .all()
    )

    all_goals = (
        DailyGoal.query
        .filter_by(
            user_id=user.id
        )
        .order_by(
            DailyGoal.goal_date.asc()
        )
        .all()
    )

    history_by_date = {}

    for goal in all_goals:

        bucket = history_by_date.setdefault(
            goal.goal_date,
            {
                "completed": 0,
                "total": 0,
                "workout": False
            },
        )

        bucket["total"] += 1

        if goal.completed:

            bucket["completed"] += 1

    for log in all_logs:

        bucket = history_by_date.setdefault(
            log.log_date,
            {
                "completed": 0,
                "total": 0,
                "workout": False
            },
        )

        bucket["workout"] = bool(
            log.workout_done
        )

    historical_daily_percentages = []

    for day_key in sorted(
        history_by_date
    ):

        bucket = history_by_date[
            day_key
        ]

        if bucket["total"]:

            value = (
                bucket["completed"]
                / bucket["total"]
                * 100
            )

        else:

            value = (
                100
                if bucket["workout"]
                else 0
            )

        historical_daily_percentages.append(
            value
        )

    # ========================================================
    # WEEKLY HISTORY
    # ========================================================

    weekly_history = []

    for weeks_ago in range(
        3,
        -1,
        -1
    ):

        ws = (
            week_start
            - timedelta(
                days=7 * weeks_ago
            )
        )

        we = (
            ws
            + timedelta(days=6)
        )

        values = []

        for (
            day_key,
            bucket
        ) in history_by_date.items():

            if ws <= day_key <= we:

                if bucket["total"]:

                    value = (
                        bucket["completed"]
                        / bucket["total"]
                        * 100
                    )

                else:

                    value = (
                        100
                        if bucket["workout"]
                        else 0
                    )

                values.append(
                    value
                )

        weekly_history.append(

            round(
                sum(values)
                / len(values),
                1
            )

            if values
            else 0
        )

    # ========================================================
    # STREAKS
    # ========================================================

    completion_dates = set()

    for (
        day_key,
        bucket
    ) in history_by_date.items():

        complete = (

            bucket["completed"]
            == bucket["total"]

            if bucket["total"]

            else bucket["workout"]
        )

        if complete:

            completion_dates.add(
                day_key
            )

    current_streak = 0

    cursor = today

    while cursor in completion_dates:

        current_streak += 1

        cursor -= timedelta(
            days=1
        )

    best_streak = 0

    running = 0

    previous = None

    for item in sorted(
        completion_dates
    ):

        if (
            previous
            and item
            == previous
            + timedelta(days=1)
        ):

            running += 1

        else:

            running = 1

        best_streak = max(
            best_streak,
            running
        )

        previous = item

    total_completed_goals = sum(
        1
        for goal in all_goals
        if goal.completed
    )

    # ========================================================
    # DAILY STATISTICS
    # ========================================================

    calorie_values = [

        log.calories_intake

        for log in all_logs

        if log.calories_intake
        is not None
    ]

    water_values = [

        log.water_intake_l

        for log in all_logs

        if log.water_intake_l
        is not None
    ]

    sleep_values = [

        log.sleep_hours

        for log in all_logs

        if log.sleep_hours
        is not None
    ]

    mood_values = [

        log.mood

        for log in all_logs

        if log.mood
        is not None
    ]

    # ========================================================
    # NEXT DAY PREDICTION
    # ========================================================

    try:

        tomorrow = predict_next_day(

            goal_completed,

            goal_total,

            historical_daily_percentages[
                -7:
            ],

            current_streak,
        )

    except Exception as exc:

        print(
            "NEXT DAY PREDICTION ERROR:",
            exc
        )

        tomorrow = {

            "percentage":
                selected_percentage,

            "message":
                "Add more daily data to improve the prediction.",
        }

    # ========================================================
    # NEXT WEEK PREDICTION
    # ========================================================

    try:

        completed_week_goals = sum(
            1
            for goal in week_goals
            if goal.completed
        )

        target_week_goals = max(
            len(week_goals),
            1
        )

        next_week = predict_next_week(

            completed_week_goals,

            target_week_goals,

            [
                value / 100
                for value in weekly_history
            ],

            current_streak,
        )

    except Exception as exc:

        print(
            "NEXT WEEK PREDICTION ERROR:",
            exc
        )

        next_week = {

            "percentage":
                weekly_average
        }

    # ========================================================
    # TREND PREDICTION
    # ========================================================

    try:

        trend = predict_weekly_trend(

            [
                value / 100
                for value in weekly_history
            ]
        )

    except Exception as exc:

        print(
            "TREND PREDICTION ERROR:",
            exc
        )

        trend = {

            "history":
                weekly_history,

            "next_week":
                weekly_average,

            "trend":
                "Building",
        }

    # ========================================================
    # CONSISTENCY SCORE
    # ========================================================

    try:

        consistency = calculate_consistency_score(

            selected_percentage,

            weekly_average,

            current_streak,

            [
                value / 100
                for value in weekly_history
            ],
        )

    except Exception as exc:

        print(
            "CONSISTENCY ERROR:",
            exc
        )

        consistency = round(

            selected_percentage
            * 0.5

            +

            weekly_average
            * 0.5
        )

    # ========================================================
    # CONFIDENCE
    # ========================================================

    confidence = min(

        95,

        45
        + len(
            historical_daily_percentages
        )
        * 5
    )

    # ========================================================
    # RETURN DASHBOARD DATA
    # ========================================================

    return jsonify({

        "success": True,

        "selected_date":
            selected_date.isoformat(),

        # ----------------------------------------------------
        # SELECTED DAY GOALS
        # ----------------------------------------------------

        "goals": [

            {

                "id": goal.id,

                "title": goal.title,

                "description":
                    goal.description or "",

                "completed":
                    bool(goal.completed),

                "goal_date":
                    goal.goal_date.isoformat(),
            }

            for goal in selected_goals
        ],

        # ----------------------------------------------------
        # SELECTED DAY LOG
        # ----------------------------------------------------

        "log": (

            {

                "date":
                    selected_log.log_date.isoformat(),

                "workout_done":
                    bool(
                        selected_log.workout_done
                    ),

                "calories_intake":
                    selected_log.calories_intake,

                "water_intake_l":
                    selected_log.water_intake_l,

                "sleep_hours":
                    selected_log.sleep_hours,

                "mood":
                    selected_log.mood,

                "notes":
                    selected_log.notes or "",
            }

            if selected_log

            else None
        ),

        # ----------------------------------------------------
        # TODAY
        # ----------------------------------------------------

        "today": {

            "completed":
                goal_completed,

            "total":
                goal_total,

            "percentage":
                selected_percentage,
        },

        # ----------------------------------------------------
        # WEEKLY
        # ----------------------------------------------------

        "weekly": {

            "labels":
                weekly_labels,

            "series":
                weekly_series,

            "average":
                weekly_average,
        },

        # ----------------------------------------------------
        # STREAKS
        # ----------------------------------------------------

        "streak":
            current_streak,

        "best_streak":
            best_streak,

        "active_days":
            active_days,

        "total_completed":
            total_completed_goals,

        # ----------------------------------------------------
        # OVERALL
        # ----------------------------------------------------

        "overall": {

            "total_workouts": sum(

                1

                for log in all_logs

                if log.workout_done
            ),

            "total_days":
                len(history_by_date),

            "average_calories": (

                round(
                    sum(calorie_values)
                    / len(calorie_values)
                )

                if calorie_values

                else 0
            ),

            "average_water": (

                round(
                    sum(water_values)
                    / len(water_values),
                    2
                )

                if water_values

                else 0
            ),

            "average_sleep": (

                round(
                    sum(sleep_values)
                    / len(sleep_values),
                    1
                )

                if sleep_values

                else 0
            ),

            "average_mood": (

                round(
                    sum(mood_values)
                    / len(mood_values),
                    1
                )

                if mood_values

                else 0
            ),

            "consistency_score":
                consistency,
        },

        # ----------------------------------------------------
        # PREDICTION
        # ----------------------------------------------------

        "prediction": {

            "tomorrow_percentage":
                tomorrow.get(
                    "percentage",
                    selected_percentage
                ),

            "next_week_percentage":
                next_week.get(
                    "percentage",
                    next_week.get(
                        "predicted_percentage",
                        weekly_average
                    )
                ),

            "confidence_percentage":
                confidence,

            "trend":
                trend.get(
                    "trend",
                    "Building"
                ),

            "trend_history":
                trend.get(
                    "history",
                    weekly_history
                ),

            "message":
                tomorrow.get(
                    "message",
                    ""
                ),
        },

        # ----------------------------------------------------
        # CURRENT WEEK
        # ----------------------------------------------------

        "current_week": {

            "week_start":
                week_start.isoformat(),

            "week_end":
                week_end.isoformat(),
        },
    })


# ============================================================
# APPLICATION START
# ============================================================

if __name__ == "__main__":

    app.run(
        debug=True
    )