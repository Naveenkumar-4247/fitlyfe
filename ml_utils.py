"""
============================================================
FITLYFE — MACHINE LEARNING UTILITIES
============================================================

Predictions:
    1. Next-day goal completion probability   (weighted blend)
    2. Next-week goal completion probability  (weighted blend)
    3. Weekly trend line + next-week forecast (linear regression
       via numpy.polyfit) -- this feeds the "up/down" weekly chart
    4. Consistency score
    5. Goal achievement probability (bootstrapped Logistic Regression)

All functions are framework-agnostic (no Flask/SQLAlchemy) so
they can be imported directly into app.py.
============================================================
"""

import numpy as np

from sklearn.linear_model import LogisticRegression


# ============================================================
# CONSTANTS
# ============================================================

DAYS_PER_WEEK = 7

MIN_PROBABILITY = 0.05
MAX_PROBABILITY = 0.98


# ============================================================
# BOOTSTRAP MODEL (used by predict_goal_achievement)
# ============================================================

def _build_model():
    rng = np.random.default_rng(42)

    X = []
    y = []

    for _ in range(2500):
        consistency = rng.uniform(0, 1)
        weekly_rate = rng.uniform(0, 1)
        streak = rng.integers(0, 15)
        goal_rate = rng.uniform(0.1, 1.3)

        streak_score = min(streak / DAYS_PER_WEEK, 1)
        goal_rate_score = min(goal_rate, 1)

        score = (
            consistency * 0.40
            + weekly_rate * 0.30
            + streak_score * 0.15
            + goal_rate_score * 0.15
        )

        label = 1 if score >= 0.58 else 0

        X.append([consistency, weekly_rate, streak_score, goal_rate_score])
        y.append(label)

    model = LogisticRegression(max_iter=1000, random_state=42)
    model.fit(np.array(X), np.array(y))
    return model


_MODEL = _build_model()


# ============================================================
# HELPERS
# ============================================================

def _clamp(value, minimum=0.0, maximum=1.0):
    try:
        value = float(value)
    except (TypeError, ValueError):
        return minimum
    return max(minimum, min(value, maximum))


def _safe_number(value, default=0.0):
    try:
        number = float(value)
        if np.isfinite(number):
            return number
    except (TypeError, ValueError):
        pass
    return default


def _normalise_streak(streak):
    streak = max(0, _safe_number(streak))
    return _clamp(streak / DAYS_PER_WEEK)


def _normalise_history(history):
    if not history:
        return []
    result = []
    for value in history:
        value = _safe_number(value)
        if value > 1:
            value = value / 100
        result.append(_clamp(value))
    return result


# ============================================================
# CONSISTENCY SCORE
# ============================================================

def calculate_consistency_score(
    daily_completion,
    weekly_completion,
    streak=0,
    historical_progress=None,
):
    daily = _safe_number(daily_completion)
    weekly = _safe_number(weekly_completion)

    if daily > 1:
        daily /= 100
    if weekly > 1:
        weekly /= 100

    daily = _clamp(daily)
    weekly = _clamp(weekly)

    streak_score = _normalise_streak(streak)
    history = _normalise_history(historical_progress)

    history_average = (sum(history) / len(history)) if history else weekly

    score = (
        daily * 0.25
        + weekly * 0.35
        + history_average * 0.25
        + streak_score * 0.15
    )

    return round(_clamp(score) * 100, 1)


# ============================================================
# NEXT-DAY PREDICTION
# ============================================================

def predict_next_day(
    today_completed,
    today_total,
    recent_daily_progress=None,
    current_streak=0,
):
    today_completed = max(0, _safe_number(today_completed))
    today_total = max(0, _safe_number(today_total))

    today_rate = _clamp(today_completed / today_total) if today_total > 0 else 0

    history = _normalise_history(recent_daily_progress)
    recent_average = (sum(history) / len(history)) if history else today_rate

    streak_score = _normalise_streak(current_streak)

    probability = (
        today_rate * 0.40
        + recent_average * 0.40
        + streak_score * 0.20
    )

    probability = MIN_PROBABILITY + probability * (MAX_PROBABILITY - MIN_PROBABILITY)
    probability = _clamp(probability, MIN_PROBABILITY, MAX_PROBABILITY)

    predicted_completion = round(probability * 100)

    if probability >= 0.75:
        message = (
            "Strong momentum. Your current consistency suggests a high "
            "chance of completing tomorrow's goals."
        )
    elif probability >= 0.50:
        message = (
            "You're maintaining reasonable consistency. Staying focused "
            "tomorrow can keep your progress on track."
        )
    else:
        message = (
            "Your consistency is still developing. Completing a few key "
            "goals tomorrow can help rebuild your momentum."
        )

    return {
        "probability": round(probability, 3),
        "percentage": predicted_completion,
        "message": message,
        "today_rate": round(today_rate, 3),
        "recent_average": round(recent_average, 3),
        "streak_score": round(streak_score, 3),
    }


# ============================================================
# NEXT-WEEK PREDICTION (probability-based)
# ============================================================

def predict_next_week(
    weekly_completed,
    current_target,
    historical_weekly_progress=None,
    current_streak=0,
):
    weekly_completed = max(0, _safe_number(weekly_completed))
    current_target = max(0, _safe_number(current_target))

    history = _normalise_history(historical_weekly_progress)
    historical_average = (sum(history) / len(history)) if history else 0

    current_progress = (
        _clamp(weekly_completed / current_target) if current_target > 0 else 0
    )

    streak_score = _normalise_streak(current_streak)
    consistency = historical_average if history else current_progress

    probability = (
        consistency * 0.40
        + current_progress * 0.40
        + streak_score * 0.20
    )
    probability = _clamp(probability, MIN_PROBABILITY, MAX_PROBABILITY)

    predicted_percentage = round(probability * 100)

    if current_target > 0:
        predicted_completed = round(current_target * (0.75 + probability * 0.30))
        predicted_completed = min(predicted_completed, current_target + 2)
    else:
        predicted_completed = 0
    predicted_completed = max(0, predicted_completed)

    if current_target > 0:
        recommended_target = round(current_target * (0.85 + probability * 0.20))
        recommended_target = max(3, min(recommended_target, current_target + 2))
    else:
        recommended_target = 3

    if probability >= 0.75:
        message = (
            "Excellent consistency. Your recent activity suggests you're "
            "ready for another strong week."
        )
    elif probability >= 0.50:
        message = (
            "You're building good consistency. Maintaining your current "
            "routine should keep you on track next week."
        )
    else:
        message = (
            "Your activity is still developing. Focus on completing "
            "smaller daily goals to improve next week's consistency."
        )

    return {
        "probability": round(probability, 3),
        "percentage": predicted_percentage,
        "predicted_completed": predicted_completed,
        "predicted_workouts": predicted_completed,
        "recommended_target": recommended_target,
        "consistency": round(_clamp(consistency), 3),
        "historical_average": round(historical_average, 3),
        "current_progress": round(current_progress, 3),
        "streak": max(0, int(current_streak)),
        "message": message,
    }


# ============================================================
# WEEKLY TREND + FORECAST (linear regression / numpy.polyfit)
# ============================================================

def predict_weekly_trend(weekly_history):
    """
    Fit a straight line through past weekly completion percentages
    and project the next week's value. This is what should drive
    the "up / down" weekly insights chart.

    Parameters
    ----------
    weekly_history : list
        Weekly average completion values, oldest -> newest.
        Accepts 0-1 or 0-100 scale.

    Returns
    -------
    dict with:
        history      -- the input, normalised to 0-100
        trend_line   -- the fitted straight line over the same points
        next_week    -- predicted % for the upcoming week
        trend        -- "Improving" / "Declining" / "Stable" / "Building"
        slope        -- raw slope (points of % per week)
    """

    history = [h * 100 for h in _normalise_history(weekly_history)]

    if len(history) < 2:
        current = history[0] if history else 0
        return {
            "history": [round(h, 1) for h in history],
            "trend_line": [round(h, 1) for h in history],
            "next_week": round(current),
            "trend": "Building",
            "slope": 0.0,
        }

    x = np.arange(len(history))
    slope, intercept = np.polyfit(x, history, 1)

    trend_line = [round(float(_clamp(slope * xi + intercept, 0, 100)), 1) for xi in x]
    next_week = round(float(_clamp(slope * len(history) + intercept, 0, 100)))

    if slope > 2:
        trend = "Improving"
    elif slope < -2:
        trend = "Declining"
    else:
        trend = "Stable"

    return {
        "history": [round(h, 1) for h in history],
        "trend_line": trend_line,
        "next_week": next_week,
        "trend": trend,
        "slope": round(float(slope), 2),
    }


# ============================================================
# GOAL-SPECIFIC PREDICTION
# ============================================================

def predict_goal(
    completed,
    target,
    recent_completion=None,
    streak=0,
    goal_type="goal",
):
    completed = max(0, _safe_number(completed))
    target = max(0, _safe_number(target))

    current_rate = _clamp(completed / target) if target > 0 else 0

    history = _normalise_history(recent_completion)
    recent_average = (sum(history) / len(history)) if history else current_rate

    streak_score = _normalise_streak(streak)

    probability = (
        current_rate * 0.45
        + recent_average * 0.35
        + streak_score * 0.20
    )
    probability = _clamp(probability, MIN_PROBABILITY, MAX_PROBABILITY)
    percentage = round(probability * 100)

    return {
        "goal": str(goal_type),
        "probability": round(probability, 3),
        "percentage": percentage,
        "current_rate": round(current_rate, 3),
        "recent_average": round(recent_average, 3),
        "message": f"{goal_type.capitalize()} completion prediction is {percentage}%.",
    }


# ============================================================
# DAILY GOAL ANALYSIS
# ============================================================

def analyze_daily_goals(goals):
    if not goals:
        return {
            "total": 0, "completed": 0, "remaining": 0,
            "percentage": 0, "status": "No goals",
        }

    total = len(goals)
    completed = sum(
        1 for goal in goals
        if (goal.get("completed", False) if isinstance(goal, dict) else bool(goal))
    )
    remaining = max(total - completed, 0)
    percentage = round((completed / total) * 100)

    if percentage == 100:
        status = "Completed"
    elif percentage >= 75:
        status = "Almost Done"
    elif percentage >= 50:
        status = "Good Progress"
    elif percentage > 0:
        status = "Getting Started"
    else:
        status = "Not Started"

    return {
        "total": total, "completed": completed, "remaining": remaining,
        "percentage": percentage, "status": status,
    }


# ============================================================
# WEEKLY DAILY ANALYSIS
# ============================================================

def analyze_weekly_progress(daily_completion):
    if not daily_completion:
        return {
            "average": 0, "best_day": 0, "worst_day": 0,
            "completed_days": 0, "current_streak": 0, "trend": "No Data",
        }

    values = []
    for value in daily_completion:
        value = _safe_number(value)
        if value <= 1:
            value *= 100
        values.append(max(0, min(value, 100)))

    average = sum(values) / len(values)
    best_day = max(values)
    worst_day = min(values)
    completed_days = sum(1 for value in values if value >= 100)

    current_streak = 0
    for value in reversed(values):
        if value >= 70:
            current_streak += 1
        else:
            break

    if len(values) >= 2:
        first_half = values[: len(values) // 2]
        second_half = values[len(values) // 2:]
        first_average = sum(first_half) / len(first_half)
        second_average = sum(second_half) / len(second_half)
        difference = second_average - first_average

        if difference >= 10:
            trend = "Improving"
        elif difference <= -10:
            trend = "Declining"
        else:
            trend = "Stable"
    else:
        trend = "Stable"

    return {
        "average": round(average, 1),
        "best_day": round(best_day, 1),
        "worst_day": round(worst_day, 1),
        "completed_days": completed_days,
        "current_streak": current_streak,
        "trend": trend,
    }


# ============================================================
# COMPLETE DASHBOARD PREDICTION (convenience wrapper)
# ============================================================

def generate_dashboard_prediction(
    today_completed,
    today_total,
    weekly_completed,
    weekly_target,
    daily_history=None,
    weekly_history=None,
    current_streak=0,
):
    daily_history = daily_history if daily_history else []
    weekly_history = weekly_history if weekly_history else []

    today_analysis = analyze_daily_goals([
        {"completed": today_completed}
        for _ in range(max(int(_safe_number(today_total)), 0))
    ])

    next_day = predict_next_day(
        today_completed=today_completed,
        today_total=today_total,
        recent_daily_progress=daily_history,
        current_streak=current_streak,
    )

    next_week = predict_next_week(
        weekly_completed=weekly_completed,
        current_target=weekly_target,
        historical_weekly_progress=weekly_history,
        current_streak=current_streak,
    )

    trend = predict_weekly_trend(weekly_history)

    weekly_rate = (weekly_completed / weekly_target) if weekly_target > 0 else 0

    consistency = calculate_consistency_score(
        daily_completion=(today_completed / today_total) if today_total > 0 else 0,
        weekly_completion=weekly_rate,
        streak=current_streak,
        historical_progress=weekly_history,
    )

    return {
        "today": today_analysis,
        "next_day": next_day,
        "next_week": next_week,
        "trend": trend,
        "consistency_score": consistency,
    }


# ============================================================
# BACKWARD COMPATIBILITY
# ============================================================

def predict_goal_achievement(
    completion_rate,
    days_elapsed,
    days_left,
    target,
    completed_so_far,
):
    if target <= 0:
        return 0.0

    completion_rate = _clamp(_safe_number(completion_rate))
    days_elapsed = max(0, _safe_number(days_elapsed))
    days_left = max(0, _safe_number(days_left))
    target = max(0, _safe_number(target))
    completed_so_far = max(0, _safe_number(completed_so_far))

    weekly_rate = _clamp(completed_so_far / target)

    projected_workouts = (
        completed_so_far / max(days_elapsed, 1) * DAYS_PER_WEEK
    )
    goal_rate = _clamp(projected_workouts / target if target > 0 else 0)
    streak_score = _clamp(days_elapsed / DAYS_PER_WEEK)

    features = np.array([[completion_rate, weekly_rate, streak_score, goal_rate]])
    probability = float(_MODEL.predict_proba(features)[0][1])

    if completed_so_far >= target:
        return 1.0

    if completed_so_far + days_left < target:
        probability *= 0.45

    return round(_clamp(probability), 3)


# ============================================================
# MODULE TEST
# ============================================================

if __name__ == "__main__":
    print("=" * 60)
    print("FITLYFE ML UTILITIES TEST")
    print("=" * 60)

    print("\nNext Day Prediction:")
    print(predict_next_day(4, 5, [80, 60, 100, 80, 90], 4))

    print("\nNext Week Prediction:")
    print(predict_next_week(4, 5, [80, 60, 75, 90], 4))

    print("\nWeekly Trend (up/down forecast):")
    print(predict_weekly_trend([55, 60, 58, 65, 70, 68, 74, 80]))

    print("\nConsistency Score:")
    print(f"{calculate_consistency_score(80, 75, 4, [70, 80, 65, 90])}%")

    print("\nGoal Prediction:")
    print(predict_goal(1, 1, [100, 80, 100], 4, "Workout"))

    print("\n" + "=" * 60)