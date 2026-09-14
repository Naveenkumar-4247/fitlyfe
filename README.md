# FitLyfe 2.1 — Premium Animated Fitness Goal Tracking & Analytics

FitLyfe is a Flask + SQLAlchemy fitness analytics project with per-user accounts, profile setup, BMI, AI diet planning, daily logs, daily goals, calendar history and a personal dashboard.

## Authentication flow

1. Landing page → **Start Your Journey** → Register.
2. Registration creates the account and redirects to **Login** (the new user is NOT automatically logged in).
3. First successful login with an incomplete profile → **Profile Setup**.
4. After profile setup → **Detail**.
5. Future logins using the same email/password → **Detail** directly.
6. Profile edits can preserve their source page:
   - Detail → Edit Profile → save → Detail
   - BMI → Change Details → save → BMI
7. All logs, goals, diet plans and analytics are filtered by the authenticated `user_id`, so users never share dashboard data.

## Run locally

```powershell
cd FITLYFE
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python app.py
```

If `.env` is not configured, FitLyfe automatically uses a local SQLite database (`fitlyfe_local.db`) for testing.

## Supabase / PostgreSQL

Copy `.env.example` to `.env` and fill in the Supabase PostgreSQL connection values. The application uses SSL and a 10-second connection timeout. You can run `create_user_table.sql` in the Supabase SQL Editor, or let Flask create missing tables.

Never commit your real `.env` or API keys.

## AI Diet

Set `GEMINI_API_KEY` in `.env`. The AI plan uses the user's saved profile plus diet type, meals/day, allergies, dislikes, cuisine and budget. Generated plans are stored under the authenticated user's ID.

## Main modules

- Animated landing / authentication pages
- Profile setup and editing
- Personal fitness detail page
- BMI calculator
- AI diet plan generator
- Daily goal tracker
- Progress calendar
- Weekly goal tracking
- Analytics dashboard with streaks, trends, consistency and predictions
- Per-user database isolation


## What was fixed in 2.1

- Login always sends an authenticated user to **Detail** after login.
- Incomplete profiles are sent to **Profile Setup** first.
- Profile edits preserve the source page using a safe internal `next` path.
- Goal values are normalized (`lose_weight`, `maintain`, `build_muscle`, `improve_endurance`, etc.) so AI nutrition never rejects valid profile choices.
- Dashboard goal requests use the same `/api/daily-goals` endpoints as Flask.
- Dashboard analytics JSON and dashboard JavaScript now use one stable data contract.
- ML utilities are called with their actual function signatures.
- Daily goals support a title, description, date, completion and delete actions.
- The calendar is user-specific and date-specific.
- Daily check-ins support workout, calories, water, sleep, mood and a private note.
- AI Diet uses Gemini when available and a local personalized fallback when Gemini is unavailable.
- `google-genai` is included in `requirements.txt`.
- New premium motion effects are loaded globally with `premium.css` and `premium.js`.
- Existing database files receive lightweight migrations for the new fields.

## Important local-development note

If an older FitLyfe server is already running on port 5000, stop it with `CTRL+C` before starting this copy. Otherwise your browser may still be connected to the old code and appear to ignore redirect or endpoint fixes.

For a clean test, stop all old FitLyfe terminals, then run:

```powershell
.\.venv\Scriptsctivate
python app.py
```

Then hard-refresh the browser with `CTRL+F5`.

