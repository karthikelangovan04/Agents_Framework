#!/usr/bin/env python3
"""
Fetch invocation/trace details programmatically from ADK Web or from session events.

Usage:
  # 1. From ADK Web server (run while 'adk web' is running)
  python get_trace_details.py --base-url http://localhost:8000 --session-id <session_id>
  python get_trace_details.py --base-url http://localhost:8000 --event-id <event_id>

  # 2. With app_name/user_id if your server uses them in the path
  python get_trace_details.py --base-url http://localhost:8000 --app-name my_app --user-id user1 --session-id <session_id>

  # 3. Session-based summary (from code that has a Session object)
  # Use get_trace_summary_from_session(session) in your plugin or after runner.run_async.
"""

import argparse
import json
import sys
from typing import Any, Optional


def fetch_trace_for_session(
    base_url: str,
    session_id: str,
    app_name: Optional[str] = None,
    user_id: Optional[str] = None,
) -> dict[str, Any]:
    """
    GET /debug/trace/session/{session_id} from ADK Web.
    Returns the response JSON (spans for that session).
    """
    try:
        import requests
    except ImportError:
        print("Install requests: pip install requests", file=sys.stderr)
        sys.exit(1)

    base_url = base_url.rstrip("/")
    if app_name and user_id:
        path = f"/apps/{app_name}/users/{user_id}/debug/trace/session/{session_id}"
    else:
        path = f"/debug/trace/session/{session_id}"
    url = f"{base_url}{path}"
    r = requests.get(url, timeout=10)
    r.raise_for_status()
    return r.json() if r.headers.get("content-type", "").startswith("application/json") else {"raw": r.text}


def fetch_trace_for_event(base_url: str, event_id: str) -> dict[str, Any]:
    """
    GET /debug/trace/{event_id} from ADK Web.
    Returns the response JSON (trace for that event).
    """
    try:
        import requests
    except ImportError:
        print("Install requests: pip install requests", file=sys.stderr)
        sys.exit(1)

    base_url = base_url.rstrip("/")
    url = f"{base_url}/debug/trace/{event_id}"
    r = requests.get(url, timeout=10)
    r.raise_for_status()
    return r.json() if r.headers.get("content-type", "").startswith("application/json") else {"raw": r.text}


def get_trace_summary_from_session(session: Any) -> list[dict[str, Any]]:
    """
    Build a trace-like summary from session.events (no HTTP, no OTel).
    Use this when you have a Session object (e.g. in a plugin after_run, or after
    loading session from session_service.get_session).

    Args:
        session: google.adk Session (or any object with .events where each event
                 has invocation_id, author, timestamp, content).

    Returns:
        List of dicts: one per invocation, with events and simple timing info.
    """
    events = getattr(session, "events", []) or []
    by_inv: dict[str, list[Any]] = {}
    for event in events:
        inv = getattr(event, "invocation_id", None) or "unknown"
        by_inv.setdefault(inv, []).append(event)

    result = []
    for inv_id, inv_events in by_inv.items():
        entries = []
        for e in inv_events:
            ts = getattr(e, "timestamp", None)
            author = getattr(e, "author", "?")
            has_content = bool(getattr(e, "content", None))
            entries.append({
                "author": author,
                "timestamp": str(ts) if ts is not None else None,
                "has_content": has_content,
            })
        result.append({"invocation_id": inv_id, "events": entries})
    return result


def main() -> None:
    ap = argparse.ArgumentParser(description="Fetch ADK trace details from Web debug API or summarize from session")
    ap.add_argument("--base-url", default="http://localhost:8000", help="ADK Web base URL")
    ap.add_argument("--session-id", help="Session ID for GET /debug/trace/session/{session_id}")
    ap.add_argument("--event-id", help="Event ID for GET /debug/trace/{event_id}")
    ap.add_argument("--app-name", help="App name (optional; use if trace is under /apps/.../debug/...)")
    ap.add_argument("--user-id", help="User ID (optional; use with --app-name)")
    ap.add_argument("--pretty", action="store_true", default=True, help="Pretty-print JSON (default: True)")
    args = ap.parse_args()

    if args.event_id:
        data = fetch_trace_for_event(args.base_url, args.event_id)
        print(json.dumps(data, indent=2 if args.pretty else None))
        return

    if args.session_id:
        data = fetch_trace_for_session(
            args.base_url,
            args.session_id,
            app_name=args.app_name,
            user_id=args.user_id,
        )
        print(json.dumps(data, indent=2 if args.pretty else None))
        return

    print("Provide either --session-id or --event-id. See --help.", file=sys.stderr)
    sys.exit(1)


if __name__ == "__main__":
    main()
