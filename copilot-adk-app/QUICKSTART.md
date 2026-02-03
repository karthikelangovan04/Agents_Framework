# Quick Start Guide

Get the CopilotKit + ADK multi-user chat app running in **5 steps**.

## Prerequisites

Ensure you have:
- ✅ **Google Gemini API key** ([Get one here](https://aistudio.google.com/app/apikey))
- ✅ **PostgreSQL** running locally or accessible remotely
- ✅ **Python 3.9+** and [uv](https://docs.astral.sh/uv/) installed
- ✅ **Node.js 20+** and npm installed

## Step 1: Clone and Setup Python Environment

```bash
cd /path/to/copilot-adk-app

# Create virtual environment
uv venv

# Install backend dependencies
uv pip install -r backend/requirements.txt
```

**Expected output:** Successfully installed packages like `fastapi`, `google-genai`, `passlib`, etc.

## Step 2: Configure Environment Variables

### Backend Configuration

Create `backend/.env`:

```bash
# Google Gemini API Key
GOOGLE_API_KEY=your_google_api_key_here

# Database URL (adjust for your Postgres setup)
DATABASE_URL=postgresql+asyncpg://adk_user:adk_password@localhost:5433/copilot_adk_db

# Gemini Model (use simple names for ADK)
# Best options based on your rate limits:
#   gemini-2.5-flash (1,000 RPM) - Newest, RECOMMENDED
#   gemini-2.0-flash (2,000 RPM) - Very fast
GEMINI_MODEL=gemini-2.5-flash

# JWT Secret (generate a random string)
JWT_SECRET=your-super-secret-jwt-key-change-me-in-production

# CORS origins (comma-separated)
CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
```

**Database URL Format:**
```
postgresql+asyncpg://USERNAME:PASSWORD@HOST:PORT/DATABASE_NAME
```

### Frontend Configuration

Create `frontend/.env.local`:

```bash
# Backend API URL
NEXT_PUBLIC_API_URL=http://localhost:8000
```

## Step 3: Start PostgreSQL

Make sure PostgreSQL is running and create the database:

```sql
-- Example SQL commands
CREATE DATABASE copilot_adk_db;
CREATE USER adk_user WITH PASSWORD 'adk_password';
GRANT ALL PRIVILEGES ON DATABASE copilot_adk_db TO adk_user;
```

**Verify connection:**

```bash
.venv/bin/python3 tests/postgres/test_postgres.py
```

**Expected output:**
```
✓ Connected to Postgres
✓ Users table created
PASS: Postgres test
```

## Step 4: Start the Backend Server

From the project root:

```bash
.venv/bin/python3 -m uvicorn main:app --app-dir backend --host 0.0.0.0 --port 8000
```

**Expected output:**
```
INFO:     Started server process
INFO:     Uvicorn running on http://0.0.0.0:8000
```

**Verify backend is running:**

Open a new terminal and run:

```bash
curl http://localhost:8000/health
```

**Expected output:** `{"status":"ok"}`

**Or run the backend test:**

```bash
.venv/bin/python3 tests/backend/test_backend.py
```

## Step 5: Setup and Start the Frontend

### Option A: Automated Setup (Recommended)

```bash
cd frontend
./setup.sh
```

This script will:
1. Clean old dependencies
2. Install all npm packages (takes 2-3 minutes)
3. Verify installation

**Then start the dev server:**

```bash
npm run dev
```

### Option B: Manual Setup

```bash
cd frontend
rm -rf node_modules package-lock.json
npm install
npm run dev
```

**Expected output:**
```
> copilot-adk-frontend@0.1.0 dev
> next dev

  ▲ Next.js 14.2.0
  - Local:        http://localhost:3000
```

## Step 6: Use the App! 🎉

1. **Open your browser:** http://localhost:3000
2. **Register a new user:** Enter username and password
3. **Start chatting:** Use the AI agent powered by Google Gemini
4. **Create new chats:** Click "New Chat" to start a new session
5. **Switch between chats:** Your conversation history is saved

### Features to Try

- 📝 **Multi-user support:** Each user has their own chat sessions
- 💬 **Session history:** Switch between old chats and see full context
- 🔒 **Secure authentication:** JWT-based auth with password hashing
- 🤖 **Google Gemini AI:** Powered by ADK with tool support
- 💾 **Persistent storage:** All messages stored in PostgreSQL

## Troubleshooting

### Backend won't start

**Error:** `asyncpg.exceptions.InvalidPasswordError`
- ✅ Check `DATABASE_URL` in `backend/.env`
- ✅ Verify Postgres credentials and port (5432 or 5433?)
- ✅ Ensure database exists

**Error:** `ModuleNotFoundError: No module named 'fastapi'`
- ✅ Activate venv: `source .venv/bin/activate`
- ✅ Reinstall: `uv pip install -r backend/requirements.txt`

### Frontend won't build

**Error:** `No matching version found for @ag-ui/client@^0.3.0`
- ✅ Use the `frontend/setup.sh` script (fixes version conflicts)
- ✅ Or manually update `package.json` to use `@ag-ui/client@^0.0.44`

**Error:** Type conflicts with `@ag-ui/client`
- ✅ Delete `node_modules` and `package-lock.json`
- ✅ Run `npm install` (the `overrides` in package.json will fix it)

### Cannot connect frontend to backend

**Error:** CORS or 404 errors
- ✅ Check `NEXT_PUBLIC_API_URL` in `frontend/.env.local`
- ✅ Verify backend is running: `curl http://localhost:8000/health`
- ✅ Check `CORS_ORIGINS` in `backend/.env` includes `http://localhost:3000`

### Database tables not created

**Error:** `relation "users" does not exist`
- ✅ Backend creates tables automatically on first startup
- ✅ Restart the backend server
- ✅ Check database permissions

## Running Tests

See **[TESTING.md](TESTING.md)** for comprehensive testing instructions.

**Quick test all components:**

```bash
# 1. Test Postgres
.venv/bin/python3 tests/postgres/test_postgres.py

# 2. Test Backend (start backend first)
.venv/bin/python3 tests/backend/test_backend.py

# 3. Test Frontend (after npm install)
.venv/bin/python3 tests/frontend/test_frontend.py

# 4. Test Integration (backend must be running)
.venv/bin/python3 tests/integration/test_full.py
```

## Next Steps

- 🚀 **Deploy to Cloud Run:** See deployment section in main README
- 🎨 **Customize UI:** Edit frontend components in `frontend/app/`
- 🛠️ **Add tools to agent:** Modify `backend/agent.py`
- 📊 **Add observability:** See [ADK docs](https://docs.copilotkit.ai/adk)

---

**Need help?** Check the full [README.md](README.md) or [TESTING.md](TESTING.md) for more details.
