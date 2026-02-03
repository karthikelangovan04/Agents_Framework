#!/usr/bin/env python3
"""
Test Backend API: health, register, login, list sessions, create session.
Backend must be running. Run from project root: uv run python tests/backend/test_backend.py
"""
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
BACKEND_ENV = ROOT / "backend" / ".env"
if BACKEND_ENV.exists():
    from dotenv import load_dotenv
    load_dotenv(BACKEND_ENV)

BASE_URL = os.getenv("BACKEND_URL", "http://localhost:8000").rstrip("/")


def test_backend():
    try:
        import requests
    except ImportError:
        print("SKIP: requests not installed (pip install requests)")
        return False

    print("Backend test")
    print("  BASE_URL:", BASE_URL)
    ok = True

    # 1. Health
    try:
        r = requests.get(f"{BASE_URL}/health", timeout=5)
        r.raise_for_status()
        print("  OK: GET /health")
    except Exception as e:
        print("  FAIL: GET /health", e)
        return False

    # 2. Register
    username = f"testuser_{os.getpid()}"
    password = "testpass123"
    try:
        r = requests.post(
            f"{BASE_URL}/auth/register",
            json={"username": username, "password": password},
            timeout=10,
        )
        r.raise_for_status()
        data = r.json()
        token = data.get("access_token")
        user_id = data.get("user_id")
        if not token or not user_id:
            raise ValueError("Missing access_token or user_id")
        print("  OK: POST /auth/register")
    except Exception as e:
        print("  FAIL: POST /auth/register", e)
        return False

    headers = {"Authorization": f"Bearer {token}"}

    # 3. Login
    try:
        r = requests.post(
            f"{BASE_URL}/auth/login",
            json={"username": username, "password": password},
            timeout=10,
        )
        r.raise_for_status()
        data = r.json()
        if not data.get("access_token"):
            raise ValueError("Missing access_token")
        print("  OK: POST /auth/login")
    except Exception as e:
        print("  FAIL: POST /auth/login", e)
        ok = False

    # 4. List sessions
    try:
        r = requests.get(f"{BASE_URL}/api/sessions", headers=headers, timeout=10)
        r.raise_for_status()
        data = r.json()
        sessions = data.get("sessions", [])
        print("  OK: GET /api/sessions (count=%s)" % len(sessions))
    except Exception as e:
        print("  FAIL: GET /api/sessions", e)
        ok = False

    # 5. Create session
    try:
        r = requests.post(f"{BASE_URL}/api/sessions", headers=headers, timeout=10)
        r.raise_for_status()
        data = r.json()
        sid = data.get("id")
        if not sid:
            raise ValueError("Missing session id")
        print("  OK: POST /api/sessions (id=%s...)" % sid[:8])
    except Exception as e:
        print("  FAIL: POST /api/sessions", e)
        ok = False

    if ok:
        print("  PASS: Backend test")
    return ok


def main():
    ok = test_backend()
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
