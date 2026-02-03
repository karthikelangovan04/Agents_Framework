"""
Postgres connection and app users table.
ADK sessions/events use DatabaseSessionService (separate tables).
"""
import asyncpg
from typing import Optional

# Will be set by main on startup
_pool: Optional[asyncpg.Pool] = None


def get_db_url_for_asyncpg() -> str:
    """Convert SQLAlchemy-style URL to asyncpg connection params."""
    from urllib.parse import urlparse
    from config import DATABASE_URL
    url = DATABASE_URL
    if url.startswith("postgresql+asyncpg://"):
        url = url.replace("postgresql+asyncpg://", "postgresql://")
    parsed = urlparse(url)
    return (
        f"postgresql://{parsed.username}:{parsed.password}@{parsed.hostname or 'localhost'}:{parsed.port or 5432}{parsed.path or '/postgres'}"
    )


async def init_db():
    """Create connection pool and ensure users table exists."""
    global _pool
    from config import DATABASE_URL
    # asyncpg uses postgresql:// (no +asyncpg)
    url = DATABASE_URL
    if "+asyncpg" in url:
        url = url.replace("postgresql+asyncpg://", "postgresql://")
    _pool = await asyncpg.create_pool(url, min_size=1, max_size=10, command_timeout=60)
    await _ensure_users_table()
    return _pool


async def _ensure_users_table():
    """Create app users table if not exists (same DB as ADK)."""
    async with _pool.acquire() as conn:
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                username VARCHAR(255) UNIQUE NOT NULL,
                password_hash VARCHAR(255) NOT NULL,
                created_at TIMESTAMP DEFAULT NOW()
            )
        """)


async def close_db():
    global _pool
    if _pool:
        await _pool.close()
        _pool = None


def get_pool() -> asyncpg.Pool:
    if _pool is None:
        raise RuntimeError("DB not initialized; call init_db() first")
    return _pool


async def get_user_by_username(username: str) -> Optional[dict]:
    """Return user row with id, username, password_hash or None."""
    pool = get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT id, username, password_hash FROM users WHERE username = $1",
            username.strip().lower(),
        )
    if row is None:
        return None
    return dict(row)


async def create_user(username: str, password_hash: str) -> dict:
    """Insert user and return id, username."""
    pool = get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            """
            INSERT INTO users (username, password_hash)
            VALUES ($1, $2)
            RETURNING id, username
            """,
            username.strip().lower(),
            password_hash,
        )
    return dict(row)
