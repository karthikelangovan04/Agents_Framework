# CopilotKit + ADK Multi-User Chat App

Full-stack demo: **ADK Python agent** with **Postgres** sessions, **multi-user auth**, and **CopilotKit** frontend with ChatGPT-like chat history.

📖 **Quick Start:** [QUICKSTART.md](QUICKSTART.md)  
🧪 **Testing:** [TESTING.md](TESTING.md)  
📊 **Status:** [STATUS.md](STATUS.md) - All tests passing ✅  
🤖 **Model Guide:** [MODEL-OPTIMIZATION.md](MODEL-OPTIMIZATION.md) - Optimized for your rate limits  
🔒 **Security:** [SECURITY-REPORT.md](SECURITY-REPORT.md) - Safe to commit to GitHub ✅

## Features

- **Backend**: FastAPI + Google ADK + AG-UI, `DatabaseSessionService` (Postgres) for chat sessions
- **Auth**: Username/password in same Postgres DB; JWT for API
- **Frontend**: Next.js + CopilotKit; login/register; chat list and session switching (like ChatGPT)
- **Sessions**: Per-user, per-chat; messages stored in Postgres and used as context when resuming a chat

## Prerequisites

- Google Gemini API key
- Node.js 20+
- Python 3.9+
- [uv](https://docs.astral.sh/uv/) (recommended) or pip for backend
- PostgreSQL (local or Cloud SQL)

## Quick Start

**🚀 Super Quick:** Use the automated startup script:

```bash
./start-dev.sh
```

This will start both backend (port 8000) and frontend (port 3000). Press Ctrl+C to stop both.

---

### Manual Setup:

### 1. Backend: uv venv and install

From the project root (`copilot-adk-app/`):

```bash
cd copilot-adk-app
uv venv
uv pip install -r backend/requirements.txt
```

Or with classic pip after activating the venv:

```bash
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r backend/requirements.txt
```

### 2. Environment

Copy example files and fill in your values:

```bash
# Backend - Copy and edit
cp backend/env.example backend/.env
# Fill in: GOOGLE_API_KEY, DATABASE_URL, JWT_SECRET

# Frontend - Copy and edit
cp frontend/env.example frontend/.env.local
# Fill in: NEXT_PUBLIC_API_URL (backend URL)
```

**Security Note:** The `.env` files are gitignored and will NOT be committed. See [SECURITY-REPORT.md](SECURITY-REPORT.md) for details.

### 3. Database

Create a Postgres database. Backend will create:

- ADK tables: `sessions`, `events`, etc. (via `DatabaseSessionService`)
- App table: `users` (for login)

Default dev URL:

`postgresql+asyncpg://adk_user:adk_password@localhost:5432/copilot_adk_db`

### 4. Run Backend

From project root (so `.venv` is used):

```bash
cd copilot-adk-app
uv run uvicorn main:app --app-dir backend --host 0.0.0.0 --port 8000
```

Or from `backend/` with the root venv:

```bash
cd backend
../.venv/bin/python -m uvicorn main:app --host 0.0.0.0 --port 8000
```

### 5. Run Frontend

**Option A: Use the automated setup script (recommended):**

```bash
cd frontend
./setup.sh
```

This will:
- Clean old dependencies
- Install all npm packages with correct versions
- Verify the installation

**Option B: Manual setup:**

```bash
cd frontend
npm install
npm run dev
```

After setup, start the dev server:

```bash
npm run dev
```

Open http://localhost:3000 → Register/Login → use the chat.

## Project Layout

See `.gitignore` for ignored paths (`.venv/`, `.env`, `frontend/.next`, `node_modules`, etc.).

## Testing

Test each part separately, then run the full suite. See **[tests/README.md](tests/README.md)** for details.

```bash
# From project root
uv run python tests/postgres/test_postgres.py   # 1. Postgres (DB must be up)
uv run python tests/backend/test_backend.py     # 2. Backend (server must be up)
uv run python tests/frontend/test_frontend.py   # 3. Frontend (build; run npm install first)
uv run python tests/integration/test_full.py   # 4. Integration (backend must be up)

# Or run all (backend must be running for steps 2 and 4)
./tests/run_all_tests.sh
```

```
copilot-adk-app/
├── .venv/                # uv venv (create with: uv venv)
├── .gitignore
├── README.md             # Main documentation
├── QUICKSTART.md         # Quick start guide ⭐
├── TESTING.md            # Testing guide
├── STATUS.md             # Current status & test results ⭐
├── start-dev.sh          # Start both servers ⭐ NEW
│
├── backend/              # ADK agent + FastAPI
│   ├── .env              # Environment variables
│   ├── main.py           # FastAPI app, AG-UI endpoint, auth
│   ├── agent.py          # LlmAgent + DatabaseSessionService
│   ├── auth.py           # JWT, password hashing (argon2)
│   ├── db.py             # Postgres connection, users table
│   ├── config.py         # Env-based config (dev / Cloud Run)
│   ├── requirements.txt  # Python dependencies
│   └── pyproject.toml
│
├── tests/                # Test scripts (all passing ✅)
│   ├── README.md         # How to run tests
│   ├── run_all_tests.sh  # Run all tests
│   ├── postgres/         # test_postgres.py
│   ├── backend/          # test_backend.py
│   ├── frontend/         # test_frontend.py
│   └── integration/      # test_full.py
│
└── frontend/             # Next.js + CopilotKit
    ├── .env.local        # Frontend environment variables
    ├── setup.sh          # Automated frontend setup ⭐ NEW
    ├── app/              # App Router pages, API routes
    ├── components/       # Auth, chat sidebar, etc.
    └── package.json
```

## Deployment (Google Cloud Run)

All URLs and secrets are parameterized via environment variables.

### Backend (Cloud Run)

- **Env vars**: `GOOGLE_API_KEY`, `DATABASE_URL` (Cloud SQL or any Postgres), `JWT_SECRET`, `CORS_ORIGINS` (comma-separated frontend origins, e.g. `https://your-app.web.app`).
- **Optional**: `APP_NAME`, `GEMINI_MODEL`, `SESSION_TIMEOUT_SECONDS`, `PORT` (Cloud Run sets `PORT`).
- Build a container from `backend/` (e.g. `Dockerfile` with `pip install -r requirements.txt` and `uvicorn main:app --host 0.0.0.0 --port $PORT`).

### Frontend (Vercel / Cloud Run / static)

- **Env**: `NEXT_PUBLIC_API_URL` = your backend URL (e.g. `https://your-backend-xxxx.run.app`).
- Build: `npm run build`; start: `npm run start` or deploy to Vercel.

### Postgres (Cloud SQL or other)

- Use the **same** Postgres database for:
  - ADK tables (`sessions`, `events`, etc.) created by `DatabaseSessionService`
  - App `users` table created by `backend/db.py`
- Connection string format: `postgresql+asyncpg://user:password@host:port/database`

### Multi-user / session isolation

- The frontend sends the logged-in user id and current chat session id to the backend via cookies (`copilot_adk_user_id`, `copilot_adk_session_id`). The Next.js API route `/api/copilotkit` forwards these as `X-User-Id` and `X-Session-Id` when calling the backend `/ag-ui` endpoint. If your `ag-ui-adk` version supports per-request user/session, the backend will use them; otherwise all traffic may use a single default session until the library supports header-based context.
- Session list and create APIs use the authenticated user id from the JWT.

See `backend/config.py`, `backend/env.example`, and `frontend/env.example` for all parameters.
