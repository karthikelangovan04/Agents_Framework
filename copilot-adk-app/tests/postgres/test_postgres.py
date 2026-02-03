#!/usr/bin/env python3
"""
Test Postgres connectivity and app schema (users table).
Run from project root: uv run python tests/postgres/test_postgres.py
Uses DATABASE_URL from env or backend/.env.
"""
import asyncio
import os
import sys
from pathlib import Path

# Load backend/.env if present (project root = copilot-adk-app)
ROOT = Path(__file__).resolve().parent.parent.parent
BACKEND_ENV = ROOT / "backend" / ".env"
if BACKEND_ENV.exists():
    from dotenv import load_dotenv
    load_dotenv(BACKEND_ENV)

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://adk_user:adk_password@localhost:5432/copilot_adk_db",
)


async def test_postgres():
    """Connect, ensure users table exists, optionally list ADK tables."""
    try:
        import asyncpg
    except ImportError:
        print("SKIP: asyncpg not installed (pip install asyncpg)")
        return False

    # asyncpg wants postgresql:// (no +asyncpg)
    url = DATABASE_URL
    if "+asyncpg" in url:
        url = url.replace("postgresql+asyncpg://", "postgresql://")

    print("Postgres test")
    print("  DATABASE_URL:", url.split("@")[-1] if "@" in url else url[:50] + "...")
    conn = None
    try:
        conn = await asyncpg.connect(url)
        print("  OK: Connected")

        # Ensure users table exists (same as backend/db.py)
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                username VARCHAR(255) UNIQUE NOT NULL,
                password_hash VARCHAR(255) NOT NULL,
                created_at TIMESTAMP DEFAULT NOW()
            )
        """)
        print("  OK: users table exists")

        # List tables in public schema
        rows = await conn.fetch("""
            SELECT table_name FROM information_schema.tables
            WHERE table_schema = 'public' ORDER BY table_name
        """)
        tables = [r["table_name"] for r in rows]
        print("  Tables:", ", ".join(tables) if tables else "(none)")

        if "users" in tables:
            count = await conn.fetchval("SELECT COUNT(*) FROM users")
            print("  users row count:", count)
        print("  PASS: Postgres test")
        return True
    except Exception as e:
        print("  FAIL:", e)
        return False
    finally:
        if conn:
            await conn.close()
            conn = None


def main():
    ok = asyncio.run(test_postgres())
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
