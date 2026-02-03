# Test Scripts

Run each layer separately, then the full flow.

## Order

1. **Postgres** – DB connectivity and `users` table
2. **Backend** – API health, auth, sessions (backend server must be running)
3. **Frontend** – Build and optional dev-server check
4. **Integration** – Full flow: register → login → sessions → agent (backend + optional frontend)

## Prerequisites

- From project root: `uv venv` and `uv pip install -r backend/requirements.txt` (backend deps include `requests` for API tests).
- For Postgres test: Postgres running, `backend/.env` with valid `DATABASE_URL`.
- For Backend test: Backend running (`uv run uvicorn main:app --app-dir backend --host 0.0.0.0 --port 8000`).
- For Frontend test: Node 20+; for dev-server check, frontend running (`npm run dev` in `frontend/`).
- For Integration: Backend running; frontend optional.

## Run from project root (`copilot-adk-app/`)

```bash
# 1. Postgres only (no backend needed)
uv run python tests/postgres/test_postgres.py

# 2. Backend only (start backend first in another terminal)
uv run python tests/backend/test_backend.py

# 3. Frontend only (build check; optional: start frontend for URL check)
uv run python tests/frontend/test_frontend.py

# 4. Integration (backend must be running)
uv run python tests/integration/test_full.py
```

## Run all in sequence

```bash
./tests/run_all_tests.sh
# or
bash tests/run_all_tests.sh
```

**Note:** Backend and integration tests require the backend server to be running. Postgres test requires a running Postgres with `DATABASE_URL`. Frontend build test requires `npm install` in `frontend/` first.

## Env (optional)

- `DATABASE_URL` – used by Postgres test (default: from `backend/.env`).
- `BACKEND_URL` – used by Backend and Integration tests (default: `http://localhost:8000`).
- `FRONTEND_URL` – used by Frontend dev-server check (default: `http://localhost:3000`).
