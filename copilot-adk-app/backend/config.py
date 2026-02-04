"""
Environment-based configuration for dev and Cloud Run.
Parameterize DATABASE_URL, API URL, CORS, etc.
"""
import os
from pathlib import Path

# Load .env from backend directory if present
_env_file = Path(__file__).resolve().parent / ".env"
if _env_file.exists():
    from dotenv import load_dotenv
    load_dotenv(_env_file)

# App
APP_NAME = os.getenv("APP_NAME", "copilot_adk_app")

# Google Gemini
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")
assert GOOGLE_API_KEY, "GOOGLE_API_KEY must be set"

# Database: same Postgres for ADK sessions + app users
# Dev: local Postgres; Cloud Run: use Cloud SQL or any Postgres URL
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://adk_user:adk_password@localhost:5432/copilot_adk_db",
)
# Sync URL for SQLAlchemy create_all (optional, for users table)
DATABASE_URL_SYNC = DATABASE_URL.replace("+asyncpg", "").replace("postgresql+asyncpg", "postgresql")

# JWT for auth (use a long random secret in production)
JWT_SECRET = os.getenv("JWT_SECRET", "dev-secret-change-in-production")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
JWT_EXPIRE_MINUTES = int(os.getenv("JWT_EXPIRE_MINUTES", "60"))

# Server (for Cloud Run, host/port are set by the platform)
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "8000"))

# CORS: comma-separated origins; Cloud Run: your frontend URL
CORS_ORIGINS_STR = os.getenv("CORS_ORIGINS", "http://localhost:3000")
CORS_ORIGINS = [o.strip() for o in CORS_ORIGINS_STR.split(",") if o.strip()]

# AG-UI / Session
# Default: 7 days (604800 seconds) - sessions persist for a week
# Set to 0 or very large number to effectively disable cleanup
SESSION_TIMEOUT_SECONDS = int(os.getenv("SESSION_TIMEOUT_SECONDS", "604800"))

# Gemini model (use simple names for ADK)
# Best options: gemini-2.5-flash (1K RPM), gemini-2.0-flash (2K RPM)
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
