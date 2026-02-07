# Adk_Copilotkit_UI_App

Agentic app with **Deal Builder** (shared state) and **Knowledge Q&A** (persistent chat) using CopilotKit, AG-UI, and ADK Python backend with Postgres sessions.

**Wiring** is aligned with the reference project `copilot-adk-app`: same AG-UI header → state flow (`X-User-Id`, `X-Session-Id` → `_ag_ui_user_id`, `_ag_ui_session_id`, `_ag_ui_thread_id`, `_ag_ui_app_name`), `user_id_extractor`, `DatabaseSessionService`. User auth is skipped; cookies `copilot_adk_user_id` and `copilot_adk_session_id` are set by the frontend (defaults or generated session id) so the backend can scope sessions.

## Architecture

- **Backend:** FastAPI + ADK (`deal_builder`, `knowledge_qa` agents) + `DatabaseSessionService` (Postgres, DB name `adk_db_new`). Two AG-UI endpoints: `/ag-ui/deal_builder`, `/ag-ui/knowledge_qa`. Shutdown closes session service.
- **Frontend:** Next.js + CopilotKit. Same cookie names as reference; `CookieInit` sets user/session cookies when missing. Pages: `/` (home), `/deal` (Deal Builder + sidebar chat), `/chat` (Knowledge Q&A chat).
- **Ports:** This app uses **8001** (backend) and **3001** (frontend) by default so it can run alongside the reference `copilot-adk-app` (3000 + 8000). Backend checks if the port is in use before starting and exits with a clear message if it is.

## Backend setup (uv venv)

```bash
cd backend
uv venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
uv pip install -e .
```

Copy `backend/env.example` to `backend/.env` and set:

- `GOOGLE_API_KEY` (required)
- `DATABASE_URL` (Postgres with DB `adk_db_new`, e.g. `postgresql+asyncpg://adk_user:adk_password@localhost:5433/adk_db_new`)
- `PORT` (optional, default **8001**; reference uses 8000)
- `CORS_ORIGINS` (frontend origin, default `http://localhost:3001,http://127.0.0.1:3001`)

Run (use **port 8001** so reference can keep 8000; uvicorn ignores .env unless you pass `--port`):

```bash
cd backend
source .venv/bin/activate   # or: .venv\Scripts\activate on Windows
python main.py
# Or explicitly: uvicorn main:app --host 0.0.0.0 --port 8001
```
`python main.py` reads `PORT` from `.env` (default **8001**) and checks the port is free before starting.

## Frontend setup

```bash
cd frontend
npm install
```

Copy `frontend/env.example` to `frontend/.env.local`; `NEXT_PUBLIC_API_URL` defaults to `http://localhost:8001`.

Run (frontend uses port **3001** by default so it doesn’t clash with reference on 3000):

```bash
cd frontend
npm run dev
# override: PORT=3002 npm run dev
```

Open http://localhost:3001. Use **Deal Builder** for shared-state deal form + AI, **Knowledge Q&A** for persistent chat.

## Reference

- Use cases and architecture: [USE_CASES_AND_APPROVAL.md](./USE_CASES_AND_APPROVAL.md)
- ADK docs: `../adk/docs` (sessions, runners, agents, state)
