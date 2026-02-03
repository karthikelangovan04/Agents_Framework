#!/usr/bin/env python3
"""
Test Frontend: build check and optional dev-server check.
Run from project root: uv run python tests/frontend/test_frontend.py
For dev-server check, set FRONTEND_URL or start frontend (npm run dev) and use --url-check.
"""
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
FRONTEND_DIR = ROOT / "frontend"
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000").rstrip("/")


def test_build():
    """Run npm run build in frontend/; success if exit code 0."""
    print("Frontend test (build)")
    print("  frontend dir:", FRONTEND_DIR)
    if not FRONTEND_DIR.is_dir():
        print("  FAIL: frontend/ not found")
        return False
    try:
        # Use shell so npm picks up node_modules/.bin (e.g. next)
        out = subprocess.run(
            "npm run build",
            cwd=str(FRONTEND_DIR),
            capture_output=True,
            text=True,
            timeout=120,
            shell=True,
        )
        if out.returncode != 0:
            print("  FAIL: npm run build exited", out.returncode)
            if out.stderr:
                print(out.stderr[-2000:])
            return False
        print("  OK: npm run build")
        return True
    except FileNotFoundError:
        print("  SKIP: npm not found")
        return True
    except subprocess.TimeoutExpired:
        print("  FAIL: build timed out")
        return False
    except Exception as e:
        print("  FAIL:", e)
        return False


def test_url():
    """Check if FRONTEND_URL returns 200 (dev server running)."""
    try:
        import requests
    except ImportError:
        print("  SKIP: requests not installed for URL check")
        return True
    print("Frontend test (URL check)")
    print("  FRONTEND_URL:", FRONTEND_URL)
    try:
        r = requests.get(FRONTEND_URL, timeout=5)
        if r.status_code != 200:
            print("  FAIL: GET %s -> %s" % (FRONTEND_URL, r.status_code))
            return False
        print("  OK: GET %s -> 200" % FRONTEND_URL)
        return True
    except Exception as e:
        print("  FAIL:", e)
        return False


def main():
    do_build = "--no-build" not in sys.argv
    do_url = "--url-check" in sys.argv

    ok = True
    if do_build:
        ok = test_build() and ok
    if do_url:
        ok = test_url() and ok
    if not do_build and not do_url:
        ok = test_build()

    if ok:
        print("  PASS: Frontend test")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
