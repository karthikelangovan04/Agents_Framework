#!/usr/bin/env python3
"""Quick tests for backend running on port 8001. Run: python test_backend.py"""
import urllib.request
import urllib.error
import json

BASE = "http://localhost:8001"


def test_health():
    req = urllib.request.Request(f"{BASE}/health")
    with urllib.request.urlopen(req, timeout=5) as r:
        data = json.loads(r.read().decode())
        assert data.get("status") == "ok", data
    print("GET /health -> 200 OK")


def test_ag_ui_endpoints_exist():
    # AG-UI endpoints expect a specific POST body; empty body may return 405 or 400.
    # We only check that the routes respond (not 404).
    for path in ["/ag-ui/deal_builder", "/ag-ui/knowledge_qa"]:
        req = urllib.request.Request(
            f"{BASE}{path}",
            data=b"{}",
            headers={"Content-Type": "application/json", "X-User-Id": "test", "X-Session-Id": "test"},
            method="POST",
        )
        try:
            urllib.request.urlopen(req, timeout=10)
        except urllib.error.HTTPError as e:
            if e.code == 404:
                raise SystemExit(f"FAIL: {path} returned 404 (route not found)")
            if e.code == 501:
                raise SystemExit(f"FAIL: {path} returned 501 (ag_ui_adk not loaded - start server with backend venv)")
            # 400/422 = body validation (route works); 405 = method not allowed
            print(f"POST {path} -> {e.code} (route OK; 422 = validation, CopilotKit sends full body)")
        else:
            print(f"POST {path} -> 200 OK")


if __name__ == "__main__":
    print("Testing backend at", BASE, "\n")
    test_health()
    test_ag_ui_endpoints_exist()
    print("\nBackend tests OK.")
