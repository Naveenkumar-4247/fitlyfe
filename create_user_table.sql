-- FITLYFE PostgreSQL / Supabase schema
-- The Flask app also runs db.create_all(), so this script is optional.

CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    name VARCHAR(120) NOT NULL,
    email VARCHAR(120) NOT NULL UNIQUE,
    password VARCHAR(200) NOT NULL,
    age INTEGER,
    height DOUBLE PRECISION,
    weight DOUBLE PRECISION,
    gender VARCHAR(20),
    activity_level VARCHAR(50),
    goal VARCHAR(50)
);

CREATE TABLE IF NOT EXISTS weekly_goals (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    week_start DATE NOT NULL,
    workouts_target INTEGER DEFAULT 5,
    calories_target INTEGER DEFAULT 2000,
    water_target_l DOUBLE PRECISION DEFAULT 2.5,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_weekly_goal_user_week UNIQUE(user_id, week_start)
);

CREATE TABLE IF NOT EXISTS daily_logs (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    log_date DATE NOT NULL,
    workout_done BOOLEAN DEFAULT FALSE,
    calories_intake INTEGER,
    water_intake_l DOUBLE PRECISION,
    sleep_hours DOUBLE PRECISION,
    mood INTEGER,
    notes TEXT DEFAULT '',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_daily_log_user_date UNIQUE(user_id, log_date)
);

CREATE TABLE IF NOT EXISTS daily_goals (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    goal_date DATE NOT NULL,
    title VARCHAR(255) NOT NULL,
    completed BOOLEAN DEFAULT FALSE,
    description VARCHAR(255) DEFAULT '',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS diet_plans (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    plan_json TEXT NOT NULL,
    inputs_json TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
