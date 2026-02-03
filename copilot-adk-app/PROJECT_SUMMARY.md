# Project Summary

## What Was Built

A complete **multi-user AI chat application** with:
- **Backend:** Python FastAPI + Google ADK agent + Postgres session storage
- **Frontend:** Next.js + CopilotKit (ChatGPT-like UI)
- **Auth:** Username/password with JWT
- **Sessions:** Per-user, per-chat; messages stored in Postgres
- **Tests:** Separate test scripts for each layer + integration
- **Deployment-ready:** Parameterized for dev and Google Cloud Run

## Project Structure

```
copilot-adk-app/
├── README.md              # Main documentation
├── QUICKSTART.md          # 5-minute setup guide
├── TESTING.md             # Detailed testing guide
├── PROJECT_SUMMARY.md     # This file
├── .gitignore             # Ignore venv, .env, node_modules, etc.
├── .venv/                 # Python venv (created with: uv venv)
│
├── backend/               # FastAPI + ADK Python agent
│   ├── .env               # Env vars (GOOGLE_API_KEY, DATABASE_URL, JWT_SECRET)
│   ├── env.example        # Template for .env
│   ├── config.py          # Load env and export config
│   ├── db.py              # Postgres pool + users table
│   ├── auth.py            # JWT + bcrypt password hashing
│   ├── agent.py           # ADK LlmAgent + DatabaseSessionService
│   ├── main.py            # FastAPI app (health, auth, sessions, AG-UI)
│   ├── requirements.txt   # Python deps (fastapi, google-adk, ag-ui-adk, asyncpg, etc.)
│   ├── pyproject.toml     # uv/pip project metadata
│   └── Dockerfile         # For Cloud Run deployment
│
├── frontend/              # Next.js + CopilotKit
│   ├── .env.local         # NEXT_PUBLIC_API_URL
│   ├── env.example        # Template
│   ├── package.json       # Node deps (@copilotkit/*, next, react, etc.)
│   ├── tsconfig.json
│   ├── next.config.js
│   ├── next-env.d.ts
│   ├── app/               # Next.js App Router
│   │   ├── layout.tsx     # Root layout with AuthProvider
│   │   ├── page.tsx       # Redirect to /login or /chat
│   │   ├── globals.css    # Dark theme
│   │   ├── login/page.tsx
│   │   ├── register/page.tsx
│   │   ├── chat/page.tsx  # Main chat UI (sidebar + CopilotKit)
│   │   └── api/
│   │       ├── copilotkit/route.ts  # Proxy to backend /ag-ui with user/session headers
│   │       └── session/route.ts     # Set session cookie
│   ├── contexts/
│   │   └── AuthContext.tsx          # React context for auth
│   └── lib/
│       ├── auth.ts        # Token storage, logout
│       └── api.ts         # API helpers (listSessions, createSession)
│
└── tests/                 # Test scripts (run one-by-one or all)
    ├── README.md          # Test docs
    ├── run_all_tests.sh   # Run all tests in order
    ├── __init__.py
    ├── postgres/
    │   ├── __init__.py
    │   └── test_postgres.py   # DB connectivity, users table
    ├── backend/
    │   ├── __init__.py
    │   └── test_backend.py    # /health, register, login, sessions
    ├── frontend/
    │   ├── __init__.py
    │   └── test_frontend.py   # npm run build
    └── integration/
        ├── __init__.py
        └── test_full.py       # Full auth → session flow
```

## Key Features

### Backend

1. **FastAPI app** (`backend/main.py`):
   - `GET /health` – Health check
   - `POST /auth/register` – Register username/password
   - `POST /auth/login` – Login (returns JWT)
   - `GET /api/sessions` – List user's chat sessions
   - `POST /api/sessions` – Create new chat session
   - `/ag-ui` – AG-UI endpoint for CopilotKit (uses ADK agent)

2. **ADK agent** (`backend/agent.py`):
   - `LlmAgent` with `gemini-2.0-flash` (configurable)
   - `DatabaseSessionService` (Postgres) for session/message storage
   - Shared across all users; user_id and session_id are per-request

3. **Postgres** (`backend/db.py`):
   - Same DB for:
     - App `users` table (username, password_hash)
     - ADK tables (`sessions`, `events`, etc.) via `DatabaseSessionService`

4. **Auth** (`backend/auth.py`):
   - JWT tokens (Bearer auth)
   - Bcrypt password hashing

5. **Config** (`backend/config.py`):
   - Parameterized: `GOOGLE_API_KEY`, `DATABASE_URL`, `JWT_SECRET`, `CORS_ORIGINS`, etc.
   - Dev and Cloud Run ready

### Frontend

1. **Next.js App Router** with TypeScript
2. **Auth pages**: login, register (store JWT in localStorage)
3. **Chat page** (`app/chat/page.tsx`):
   - Left sidebar: list of sessions, "New chat" button, logout
   - Right sidebar: CopilotKit chat (talks to backend AG-UI)
   - Session switching: click a session → set cookie → agent uses that session
4. **CopilotKit integration**:
   - `/api/copilotkit` proxy reads user_id and session_id from cookies
   - Forwards to backend `/ag-ui` with `X-User-Id` and `X-Session-Id` headers
5. **Dark theme** (ChatGPT-like)

### Tests

- **Postgres test:** Connect, ensure `users` table exists, list tables
- **Backend test:** Register, login, list sessions, create session
- **Frontend test:** `npm run build` (optional: dev server check)
- **Integration test:** Full flow (register → login → sessions)
- **run_all_tests.sh:** Run all four in order

## How It Works (Flow)

1. **User registers** → Backend stores username + hashed password in Postgres `users` table
2. **User logs in** → Backend returns JWT; frontend stores it and sets `copilot_adk_user_id` cookie
3. **Frontend loads chat page** → Calls `GET /api/sessions` with JWT → Backend returns list of sessions for that user
4. **User selects or creates session** → Frontend sets `copilot_adk_session_id` cookie
5. **User sends message** → CopilotKit calls `/api/copilotkit` → Next.js proxy reads cookies → Calls backend `/ag-ui` with `X-User-Id` and `X-Session-Id` → Backend ADK agent uses `DatabaseSessionService` to:
   - Load previous messages from Postgres for that (user_id, session_id)
   - Send message + context to Gemini
   - Store new messages in Postgres
6. **Agent responds** → Streamed back to frontend → Displayed in CopilotKit chat
7. **User switches session** → Frontend sets new `copilot_adk_session_id` cookie → Next agent call loads that session's history

## Environment Variables

### Backend (`backend/.env`)

```bash
GOOGLE_API_KEY=your_google_api_key
DATABASE_URL=postgresql+asyncpg://adk_user:adk_password@localhost:5432/copilot_adk_db
JWT_SECRET=dev-secret-change-in-production
CORS_ORIGINS=http://localhost:3000
APP_NAME=copilot_adk_app
GEMINI_MODEL=gemini-2.0-flash
SESSION_TIMEOUT_SECONDS=3600
PORT=8000
```

### Frontend (`frontend/.env.local`)

```bash
NEXT_PUBLIC_API_URL=http://localhost:8000
```

## Deployment (Google Cloud Run)

### Backend

1. Build Docker image from `backend/Dockerfile`
2. Set env vars in Cloud Run:
   - `GOOGLE_API_KEY`
   - `DATABASE_URL` (Cloud SQL or any Postgres)
   - `JWT_SECRET` (use Secret Manager)
   - `CORS_ORIGINS` (your frontend URL)
   - `PORT` (Cloud Run sets this)
3. Deploy

### Frontend

1. Set `NEXT_PUBLIC_API_URL` to your backend URL
2. Build: `npm run build`
3. Deploy to Cloud Run, Vercel, or static hosting

### Postgres

- Use Cloud SQL (Postgres) or any managed Postgres
- Same DB for ADK sessions and app users
- Connection string format: `postgresql+asyncpg://user:password@host:port/database`

## What's Parameterized

All URLs, secrets, and config are environment-based:
- ✅ Backend API URL (`NEXT_PUBLIC_API_URL`)
- ✅ Database URL (`DATABASE_URL`)
- ✅ Google API key (`GOOGLE_API_KEY`)
- ✅ JWT secret (`JWT_SECRET`)
- ✅ CORS origins (`CORS_ORIGINS`)
- ✅ Port (`PORT`)
- ✅ Model (`GEMINI_MODEL`)

Dev and Cloud Run use the same code; only env vars change.

## Files Created

- **Backend:** 11 files (main.py, agent.py, db.py, auth.py, config.py, requirements.txt, pyproject.toml, Dockerfile, env.example, .env)
- **Frontend:** 17 files (pages, components, API routes, contexts, lib, config, .env.local, env.example)
- **Tests:** 8 test files + README + run script
- **Docs:** README.md, QUICKSTART.md, TESTING.md, PROJECT_SUMMARY.md, .gitignore

**Total:** ~40 files, all structured and ready for dev and production.

## Next Steps

1. **Test locally:**
   - See [QUICKSTART.md](QUICKSTART.md) or [TESTING.md](TESTING.md)
2. **Customize agent:**
   - Edit `backend/agent.py` (instruction, tools, model)
3. **Add features:**
   - CopilotKit docs in `Copliot Kit/` folder
   - ADK docs in `adk/docs/`
4. **Deploy:**
   - See main README.md → "Deployment (Google Cloud Run)"
5. **Productionize:**
   - Use strong `JWT_SECRET` (Secret Manager)
   - Use Cloud SQL for Postgres
   - Add monitoring, logging (OpenTelemetry, Cloud Logging)
   - Add user email verification, password reset, etc.

---

**Built with:**
- Python 3.11, uv, FastAPI, Google ADK, ag-ui-adk, asyncpg, python-jose, passlib
- Node.js 20, Next.js 14, React 18, CopilotKit, TypeScript
- PostgreSQL 15
- Docker (optional for local Postgres)

All code is in `/Users/karthike/Desktop/Vibe Coding/Google-ADK-A2A-Explore/copilot-adk-app/` and ready to run!
