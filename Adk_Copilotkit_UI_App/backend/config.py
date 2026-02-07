"""
Environment-based configuration. Ports and DB configurable via env.
"""
import os
from pathlib import Path

_env_file = Path(__file__).resolve().parent / ".env"
if _env_file.exists():
    from dotenv import load_dotenv
    load_dotenv(_env_file)

APP_NAME = os.getenv("APP_NAME", "adk_copilotkit_app")

# LLM (Gemini via ADK)
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")
if not GOOGLE_API_KEY:
    import warnings
    warnings.warn("GOOGLE_API_KEY not set; agent runs may fail.")

# Postgres for DatabaseSessionService (sessions/events). Use adk_db_new as per approval.
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://adk_user:adk_password@localhost:5433/adk_db_new",
)

# Server: use different ports than reference (copilot-adk-app uses 8000 + 3000)
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "8001"))

# CORS: frontend URL (this app defaults to 3001 to avoid conflict with reference on 3000)
CORS_ORIGINS_STR = os.getenv("CORS_ORIGINS", "http://localhost:3001,http://127.0.0.1:3001")
CORS_ORIGINS = [o.strip() for o in CORS_ORIGINS_STR.split(",") if o.strip()]

SESSION_TIMEOUT_SECONDS = int(os.getenv("SESSION_TIMEOUT_SECONDS", "604800"))
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")
