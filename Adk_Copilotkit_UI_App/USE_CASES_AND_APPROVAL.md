# Adk_Copilotkit_UI_App – Use Cases, Architecture & Approval

**Context:** Agentic/Gen AI app with CopilotKit + AG-UI + ADK Python backend, Postgres sessions (`DatabaseSessionService`), configurable ports, and uv venv. References: `adk/docs` in this repo, postgres-agent sample, and existing copilot-adk-app.

---

## 1. Proposed use cases (no banking; generic product/assistant flows)

These map to the reference patterns and fit a single app with multiple agents/pages.

| # | Use case | Pattern from reference | Description |
|---|----------|-------------------------|-------------|
| **1** | **Deal / Opportunity Builder** | Shared state (Recipe-like) | User builds a “deal” (customer name, segment, products, estimated value, stage, next steps). AI suggests products, next steps, or improves the deal via a tool that updates shared state; UI stays in sync. |
| **2** | **Knowledge Q&A Chat** | Postgres session + LlmAgent | Persistent chat (session in Postgres) for product/pricing/playbook Q&A. Uses `DatabaseSessionService` + single LlmAgent; history and context per user/session. |
| **3** | **Search / research agent** | Postgres + optional search tool | Same Postgres session storage and Runner; agent can use a search tool (e.g. web search or internal KB) for “latest news” or “competitive intel.” Optional for v1. |
| **4** | **Human-in-the-loop (approval)** | Frontend action / approval step | Agent proposes an action (e.g. “Apply 15% discount”); user approves in UI. Can be added to Deal Builder or as a separate flow. |

---

## 2. Recommended scope for first delivery

- **In scope**
  - **Agent 1 – Deal Builder (shared state):** One ADK `LlmAgent` with an “update deal” tool, `AGUIToolset`, callbacks to inject/read state; one CopilotKit page with `useCoAgent` and a form (customer, products, value, stage) + chat/sidebar. Backend: `DatabaseSessionService` + Postgres.
  - **Agent 2 – Knowledge Q&A:** One `LlmAgent` (no shared-state tool); same Postgres session service; one chat-only page (sidebar or full chat). Sessions persisted in Postgres (`adk_db_new`).
  - **App shell:** Next.js frontend + FastAPI backend; configurable frontend and backend ports via env; uv venv in this directory with all ADK, AG-UI, and backend deps.
  - **Backend:** Single FastAPI app; `add_adk_fastapi_endpoint` with multiple agents (by agent name / integration id); `DatabaseSessionService(db_url=...)` with `adk_db_new`; `user_id` / `session_id` from headers.
- **Optional for v1**
  - Search/research agent (extra agent + optional search tool).
  - Human-in-the-loop approval flow (frontend tool + agent instruction).

---

## 3. Agents and pages (concrete)

| Agent name (backend) | Frontend page / integration | Purpose |
|----------------------|-----------------------------|---------|
| `deal_builder` | e.g. `/deal` or integrationId `deal_builder` | Shared-state deal form + “Improve with AI” style chat. |
| `sales_qa` or `knowledge_qa` | e.g. `/chat` or integrationId `knowledge_qa` | Persistent Knowledge Q&A chat (Postgres sessions). |

**Ports:** Backend configurable via `PORT` (e.g. `8000`). Frontend configurable via `PORT` or `npm run dev -- -p 3000` / env.

---

## 4. Tech alignment with references

- **Postgres / sessions:** Same as postgres-agent test: `DatabaseSessionService(db_url=...)`, `Runner(agent=..., session_service=session_service, ...)`. DB name `adk_db_new`. See `adk/docs/07-Sessions-Package.md`, `adk/docs/21-DatabaseSessionService-Schema.md`.
- **AG-UI / CopilotKit:** Same as existing copilot-adk-app: `ADKAgent`, `add_adk_fastapi_endpoint`, `extract_state_from_request` / `user_id_extractor` for `X-User-Id` and `X-Session-Id`.
- **Shared state:** Backend tool writes to `tool_context.state`; frontend `useCoAgent` with same agent name; optional `before_model_callback` to inject current state into system instruction.
- **UI pattern:** CopilotKit `runtimeUrl`, `agent="..."`, CopilotSidebar / mobile pull-up, labels applied to Deal Builder and Knowledge Q&A pages.

---

## 5. Libraries for uv venv (ADK and AG-UI)

Create venv in this directory (or in a `backend` subfolder) with:

```bash
uv venv
source .venv/bin/activate   # or .venv\Scripts\activate on Windows
uv pip install -e .         # if using pyproject.toml, or:
```

**Backend (Python) – suggested stack:**

| Library | Purpose | Reference doc |
|---------|---------|----------------|
| `google-adk` | Agents, tools, runners, callbacks | `adk/docs/01-Agents-Package.md`, `10-Runners-Package.md` |
| `ag-ui-adk` | ADKAgent, add_adk_fastapi_endpoint for CopilotKit | Existing copilot-adk-app |
| `fastapi` | HTTP API | `adk/docs/05-Apps-Package.md` |
| `uvicorn[standard]` | ASGI server | — |
| `asyncpg` | Async Postgres for DatabaseSessionService | `adk/docs/07-Sessions-Package.md`, `21-DatabaseSessionService-Schema.md` |
| `sqlalchemy[asyncio]>=2.0` | Required by DatabaseSessionService | `adk/docs/07-Sessions-Package.md` |
| `python-dotenv` | Env and config | — |
| `google-genai` | Pulled in by google-adk (Gemini) | `adk/docs/00-Setup-and-Installation.md` |

Optional for auth (if reusing copilot-adk-app pattern): `python-jose[cryptography]`, `passlib[bcrypt]`, `python-multipart`.

**Frontend:** Next.js, `@copilotkit/react-core`, `@copilotkit/react-ui`, `@ag-ui/client` (versions aligned with existing copilot-adk-app).

---

## 6. Gen AI / Agentic AI architecture – summary for the team

This section gives a **high-level architecture** for building, testing, and deploying agentic/Gen AI apps with the ADK stack, so the team can align on perspectives and human-in-the-loop before implementation.

### 6.1 ADK framework “services” and building blocks (from `adk/docs`)

Relevant ADK packages and how they fit:

| Layer | Package / component | Role |
|-------|----------------------|------|
| **Agents** | `google.adk.agents` (Agent/LlmAgent, SequentialAgent, etc.) | Define behavior, model, instructions, tools. See `adk/docs/01-Agents-Package.md`. |
| **Tools** | `google.adk.tools` (FunctionTool, AgentTool, MCP, OpenAPI, retrieval, etc.) | Extend agent capabilities. See `adk/docs/02-Tools-Package.md`. |
| **Sessions** | `google.adk.sessions` (InMemorySessionService, DatabaseSessionService, VertexAiSessionService) | Conversation context, state, persistence. See `adk/docs/07-Sessions-Package.md`, `21-DatabaseSessionService-Schema.md`. |
| **Memory** | `google.adk.memory` (InMemoryMemoryService, VertexAiMemoryBankService, VertexAiRagMemoryService) | Long-term memory. See `adk/docs/08-Memory-Package.md`, `18-Memory-Services-Comparison.md`. |
| **Runners** | `google.adk.runners` (Runner, InMemoryRunner) | Execute agents; manage sessions, events, services. See `adk/docs/10-Runners-Package.md`. |
| **Apps** | `google.adk.apps` (App) | Web/API exposure of agents. See `adk/docs/05-Apps-Package.md`. |
| **Evaluation** | `google.adk.evaluation` (AgentEvaluator) | Evaluate agent performance. See `adk/docs/09-Other-Packages.md`. |
| **A2A** | `google.adk.a2a` | Agent-to-agent communication. See `adk/docs/04-A2A-Package.md`. |

For this app: **Agents + Tools + Sessions (DatabaseSessionService) + Runners** are in scope; Memory and A2A are optional.

### 6.2 Research required for building agents

- **Agent design:** Instructions, tools, callbacks (`before_agent`, `before_model`, `after_model`). Reuse shared-state pattern (tool writes to `tool_context.state`; callbacks inject state into prompts). Refs: `01-Agents-Package.md`, `23a-State-Prefixes-and-Database-Storage-Mapping.md`.
- **Session and state:** When to use app vs user vs session state; how `DatabaseSessionService` stores and merges state. Refs: `07-Sessions-Package.md`, `21-DatabaseSessionService-Schema.md`, `23a-State-Prefixes-and-Database-Storage-Mapping.md`.
- **Runner vs Agent:** Agent = configuration; Runner = execution (sessions, events, services). Refs: `01-Agents-Package.md`, `10-Runners-Package.md`.
- **Frontend integration:** AG-UI protocol (X-User-Id, X-Session-Id), CopilotKit runtimeUrl and agent selection. Refs: existing copilot-adk-app, CopilotKit ADK docs.

### 6.3 Testing

- **State and session:** Programmatic session creation, event replay, state inspection. Refs: `adk/docs/23b-Testing-and-Setting-State-in-ADK-Web.md`, `22-Getting-Trace-and-Invocation-Details-Programmatically.md`.
- **Runner:** Use `Runner` with `DatabaseSessionService` (or `InMemorySessionService` for unit tests); prefer `run_async()` for tests and production. Use `InMemoryRunner` only for local/dev. Refs: `10-Runners-Package.md`, `12-Runnable-vs-API-Execution-Models.md`.
- **Evaluation:** `google.adk.evaluation.AgentEvaluator` for structured evaluation. Ref: `09-Other-Packages.md`.

### 6.4 Deploying

- **API / web:** FastAPI + `add_adk_fastapi_endpoint` (AG-UI); or ADK `App` + uvicorn. Refs: `05-Apps-Package.md`, existing copilot-adk-app.
- **Sessions:** Production = `DatabaseSessionService` (Postgres or other SQLAlchemy-compatible DB). Dev = `InMemorySessionService` or same DB. Refs: `07-Sessions-Package.md`, `10-Runners-Package.md` (production deployments).
- **Config:** Ports, `DATABASE_URL`, API keys via env (e.g. `.env`); no company names in docs.

### 6.5 Human-in-the-loop (assessment and approval)

- **In flow:** Agent proposes an action; user approves or rejects in the UI (e.g. “Apply discount”, “Submit deal”). Implement via CopilotKit frontend actions or backend tool that requires a confirmation step.
- **In process:** Team uses this document to assess scope, risks, and rollout; a designated person approves the plan before implementation.

---

## 7. Plan and approval request

**Proposed plan:**

1. **Setup:** uv venv in `Adk_Copilotkit_UI_App` (or `backend`), install ADK + AG-UI + FastAPI + asyncpg + sqlalchemy + dotenv (and optional auth libs).
2. **Backend:** FastAPI app with `DatabaseSessionService(db_url=..., adk_db_new)`; two agents (`deal_builder`, `knowledge_qa`); `add_adk_fastapi_endpoint` with header-based user/session extraction; configurable `PORT`.
3. **Frontend:** Next.js + CopilotKit + two pages (Deal Builder with shared state, Knowledge Q&A chat); configurable frontend port.
4. **Testing:** Session/state tests aligned with `23b-Testing-and-Setting-State-in-ADK-Web.md` and Runner usage in `10-Runners-Package.md`.
5. **Docs:** Keep this file and `adk/docs` as the single reference; no company names; optional one-pager for “architecture + build/test/deploy” for the team.

**Approval checklist – please confirm:**

1. **Use cases:** Deal Builder (shared state) + Knowledge Q&A (Postgres chat) as the first two agents. Any rename (e.g. “Opportunity Assistant”, “Product Q&A”)?
2. **DB:** Postgres DB name `adk_db_new` and `DATABASE_URL` pattern `postgresql+asyncpg://...`.
3. **Ports:** Backend via `PORT` env; frontend configurable when running (env or CLI). Sufficient?
4. **Optional v1:** Include search/research agent and/or human-in-the-loop approval in v1, or defer?
5. **Architecture summary:** Is the Gen AI / Agentic AI architecture section (services, research, testing, deployment, human-in-the-loop) sufficient for team perspectives and your approval?

Once you approve (or adjust) the above, implementation will proceed: uv venv, backend (FastAPI + ADK + DatabaseSessionService + two agents), frontend (Next.js + CopilotKit + two pages), and configurable ports.
