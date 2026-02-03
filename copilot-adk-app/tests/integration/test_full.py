#!/usr/bin/env python3
"""
Integration test: register -> login -> list sessions -> create session -> (optional) AG-UI.
Backend must be running. Run from project root: uv run python tests/integration/test_full.py
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


def test_full():
    try:
        import requests
    except ImportError:
        print("SKIP: requests not installed")
        return False

    print("Integration test (full flow)")
    print("  BACKEND_URL:", BASE_URL)
    ok = True

    # Health
    try:
        r = requests.get(f"{BASE_URL}/health", timeout=5)
        r.raise_for_status()
    except Exception as e:
        print("  FAIL: backend not reachable:", e)
        return False

    username = f"intuser_{os.getpid()}"
    password = "intpass123"

    # Register
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
            raise ValueError("Missing token or user_id")
        print("  OK: register -> user_id=%s" % user_id)
    except Exception as e:
        print("  FAIL: register", e)
        return False

    headers = {"Authorization": f"Bearer {token}"}

    # Login
    try:
        r = requests.post(
            f"{BASE_URL}/auth/login",
            json={"username": username, "password": password},
            timeout=10,
        )
        r.raise_for_status()
        print("  OK: login")
    except Exception as e:
        print("  FAIL: login", e)
        ok = False

    # List sessions
    try:
        r = requests.get(f"{BASE_URL}/api/sessions", headers=headers, timeout=10)
        r.raise_for_status()
        sessions = r.json().get("sessions", [])
        print("  OK: list_sessions (count=%s)" % len(sessions))
    except Exception as e:
        print("  FAIL: list_sessions", e)
        ok = False

    # Create session
    try:
        r = requests.post(f"{BASE_URL}/api/sessions", headers=headers, timeout=10)
        r.raise_for_status()
        sid = r.json().get("id", "")
        print("  OK: create_session (id=%s...)" % sid[:8])
    except Exception as e:
        print("  FAIL: create_session", e)
        ok = False

    if ok:
        print("  PASS: Integration test")
    return ok


def main():
    ok = test_full()
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
