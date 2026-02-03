#!/usr/bin/env bash
# Run tests in order: Postgres -> Backend -> Frontend -> Integration.
# From project root: ./tests/run_all_tests.sh
# Backend must be running for backend and integration tests.

set -e
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

echo "=== 1. Postgres ==="
uv run python tests/postgres/test_postgres.py
echo ""

echo "=== 2. Backend (ensure backend is running: uv run uvicorn main:app --app-dir backend --port 8000) ==="
uv run python tests/backend/test_backend.py
echo ""

echo "=== 3. Frontend (build) ==="
uv run python tests/frontend/test_frontend.py
echo ""

echo "=== 4. Integration ==="
uv run python tests/integration/test_full.py
echo ""

echo "=== All tests completed ==="
