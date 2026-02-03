# Testing Guide

Step-by-step guide to test the full stack: Postgres → Backend → Frontend → Integration.

## Setup (one-time)

From project root:

```bash
cd "/Users/karthike/Desktop/Vibe Coding/Google-ADK-A2A-Explore/copilot-adk-app"

# 1. Backend venv and dependencies
uv venv
uv pip install -r backend/requirements.txt

# 2. Frontend dependencies
cd frontend
npm install
cd ..

# 3. Postgres (Docker example)
docker run -d --name copilot-pg \
  -p 5432:5432 \
  -e POSTGRES_USER=adk_user \
  -e POSTGRES_PASSWORD=adk_password \
  -e POSTGRES_DB=copilot_adk_db \
  postgres:15
```

## Environment Files

Ensure these exist (already created if you followed setup):

- **`backend/.env`**: `GOOGLE_API_KEY`, `DATABASE_URL`, `JWT_SECRET`, etc.
- **`frontend/.env.local`**: `NEXT_PUBLIC_API_URL=http://localhost:8000`

## Test 1: Postgres

Test DB connectivity and users table creation.

**No servers needed.**

```bash
.venv/bin/python tests/postgres/test_postgres.py
```

**Expected output:**

```
Postgres test
  DATABASE_URL: localhost:5432/copilot_adk_db
  OK: Connected
  OK: users table exists
  Tables: users
  users row count: 0
  PASS: Postgres test
```

**If it fails:**
- Check Postgres is running: `docker ps` or `psql -h localhost -U adk_user -d copilot_adk_db`
- Verify `backend/.env` has correct `DATABASE_URL`

---

## Test 2: Backend

Start the backend server, then test API endpoints.

**Terminal 1 (backend server):**

```bash
cd "/Users/karthike/Desktop/Vibe Coding/Google-ADK-A2A-Explore/copilot-adk-app"
.venv/bin/python -m uvicorn main:app --app-dir backend --host 0.0.0.0 --port 8000
```

Wait for: `Application startup complete.`

**Terminal 2 (test):**

```bash
cd "/Users/karthike/Desktop/Vibe Coding/Google-ADK-A2A-Explore/copilot-adk-app"
.venv/bin/python tests/backend/test_backend.py
```

**Expected output:**

```
Backend test
  BASE_URL: http://localhost:8000
  OK: GET /health
  OK: POST /auth/register
  OK: POST /auth/login
  OK: GET /api/sessions (count=1)
  OK: POST /api/sessions (id=abc123...)
  PASS: Backend test
```

**If it fails:**
- Ensure backend is running on port 8000
- Check `backend/.env` for `GOOGLE_API_KEY`
- Check logs in Terminal 1

---

## Test 3: Frontend

Test build (no server needed) or dev server (optional).

**Build test (no server):**

```bash
.venv/bin/python tests/frontend/test_frontend.py
```

**Expected output:**

```
Frontend test (build)
  frontend dir: .../frontend
  OK: npm run build
  PASS: Frontend test
```

**Optional: Dev server check**

**Terminal 1:**

```bash
cd frontend
npm run dev
```

Wait for: `Local: http://localhost:3000`

**Terminal 2:**

```bash
.venv/bin/python tests/frontend/test_frontend.py --url-check
```

**If build fails:**
- Run `npm install` in `frontend/` first
- Check for Node.js 20+

---

## Test 4: Integration

Full flow: register → login → sessions → (optional) agent.

**Backend must be running** (same as Test 2, Terminal 1).

**Terminal 2 (test):**

```bash
.venv/bin/python tests/integration/test_full.py
```

**Expected output:**

```
Integration test (full flow)
  BACKEND_URL: http://localhost:8000
  OK: register -> user_id=123
  OK: login
  OK: list_sessions (count=1)
  OK: create_session (id=xyz789...)
  PASS: Integration test
```

---

## Run All Tests

**Prerequisites:**
- Postgres running
- Backend running (Terminal 1)
- `npm install` done in `frontend/`

**Run:**

```bash
./tests/run_all_tests.sh
```

This runs all four tests in order.

---

## Manual Testing (Full App)

### Backend (Terminal 1)

```bash
cd "/Users/karthike/Desktop/Vibe Coding/Google-ADK-A2A-Explore/copilot-adk-app"
.venv/bin/python -m uvicorn main:app --app-dir backend --host 0.0.0.0 --port 8000
```

### Frontend (Terminal 2)

```bash
cd "/Users/karthike/Desktop/Vibe Coding/Google-ADK-A2A-Explore/copilot-adk-app/frontend"
npm run dev
```

### Browser

1. Open http://localhost:3000
2. Click "Register" → create username/password
3. Login
4. Use the chat sidebar to talk to the agent
5. Click "New chat" to create a new session
6. Switch between sessions in the left sidebar
7. Messages are stored in Postgres per user/session

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Postgres test fails | Check Postgres running, verify `DATABASE_URL` in `backend/.env` |
| Backend test fails (connection refused) | Start backend: `uv run uvicorn main:app --app-dir backend --port 8000` |
| Backend test fails (500 error) | Check `GOOGLE_API_KEY` in `backend/.env` |
| Frontend build fails | Run `npm install` in `frontend/` |
| Integration test fails | Ensure backend is running on port 8000 |
| Chat doesn't work | Check backend logs; verify `NEXT_PUBLIC_API_URL` in `frontend/.env.local` |
| Session not switching | Check browser cookies; ensure backend session API is working |

---

## Test Results Reference

All tests passing means:
- ✅ Postgres: DB connected, `users` table exists
- ✅ Backend: API health, auth (register/login), session CRUD work
- ✅ Frontend: Next.js builds successfully
- ✅ Integration: Full auth → session flow works end-to-end

Now the app is ready for use!
