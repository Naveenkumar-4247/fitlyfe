import os
from dotenv import load_dotenv

load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY", "fitlyfe-dev-secret-change-me")

DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_NAME = os.getenv("DB_NAME")

# If Supabase/PostgreSQL credentials are present, use them.
# Otherwise FitLyfe starts with a local SQLite database so the UI can be tested immediately.
if all([DB_HOST, DB_USER, DB_PASSWORD, DB_NAME]):
    SQLALCHEMY_DATABASE_URI = (
        f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}"
        f"@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    )
    SQLALCHEMY_ENGINE_OPTIONS = {
        "connect_args": {
            "sslmode": "require",
            "connect_timeout": 10,
        },
        "pool_pre_ping": True,
        "pool_recycle": 1800,
    }
else:
    SQLALCHEMY_DATABASE_URI = "sqlite:///fitlyfe_local.db"
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_pre_ping": True,
    }

SQLALCHEMY_TRACK_MODIFICATIONS = False
SESSION_COOKIE_SECURE = False
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "Lax"
