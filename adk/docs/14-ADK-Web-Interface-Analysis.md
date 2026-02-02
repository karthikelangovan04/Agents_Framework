# ADK Web Interface — Detailed Analysis

**File Path**: `docs/14-ADK-Web-Interface-Analysis.md`  
**Reference**: [Official ADK Web Interface Docs](https://google.github.io/adk-docs/runtime/web-interface/)

This document analyzes how the **Google ADK web interface** works, based on the official documentation and inspection of the `google-adk` library in the project’s virtual environment (`.venv`).

---

## 1. Overview

The **ADK web interface** (“ADK Web” / “Dev UI”) is a browser-based UI for developing and debugging agents. It lets you:

- **Chat** with agents and see responses in real time  
- **Manage sessions** (create, switch, delete)  
- **Inspect and edit session state** during development  
- **View event history** for each run  

**Important**: ADK Web is **for development and debugging only**. It is **not** intended for production deployments.

---

## 2. How to Start the Web Interface

### 2.1 Basic Command (Python)

```bash
adk web [AGENTS_DIR]
```

- **`AGENTS_DIR`**: Directory where each **subdirectory** is one agent (see [Agent discovery](#4-agent-discovery-and-structure) below).  
- Default: current working directory (or per-CLI default).

**Example:**

```bash
adk web --port 3000 --session_service_uri "sqlite:///sessions.db" path/to/agents
```

The server starts at **`http://localhost:8000`** by default (or the port you set).

### 2.2 Common Options (from `adk web --help`)

| Option | Description | Default |
|--------|-------------|---------|
| `--host` | Binding host | `127.0.0.1` |
| `--port` | Server port | `8000` |
| `--allow_origins` | CORS origins (literal or `regex:...`) | — |
| `--session_service_uri` | Session storage URI | In-memory or local (see below) |
| `--artifact_service_uri` | Artifact storage URI | Local `.adk/artifacts` or in-memory |
| `--memory_service_uri` | Memory service URI | — |
| `--use_local_storage` / `--no_use_local_storage` | Use local `.adk` when URIs unset | `use_local_storage` |
| `--reload` / `--no-reload` | Auto-reload on code changes | — |
| `--reload_agents` | Live reload when agent code changes | — |
| `--a2a` | Enable A2A endpoints | — |
| `--url_prefix` | Path prefix when behind proxy (e.g. `/api/v1`) | — |
| `--logo-text` | Logo text in Dev UI | — |
| `--logo-image-url` | Logo image URL | — |
| `--extra_plugins` | Comma-separated plugin classes/instances | — |
| `--eval_storage_uri` | Evals storage (e.g. `gs://bucket`) | — |
| `--trace_to_cloud` | Cloud Trace telemetry | — |
| `--otel_to_cloud` | OTel → GCP (Trace, Logging) | — |
| `-v` / `--log_level` | Logging level | — |

**Session / artifact URIs:**

- `memory://` — in-memory  
- `sqlite:///path/to/file.db` — SQLite  
- `gs://bucket` — GCS (artifacts)  
- `agentengine://<id>` — Agent Engine  
- `file:///path` — local directory (artifacts)  
- Others per SQLAlchemy / ADK docs  

---

## 3. Architecture

### 3.1 High-Level Flow

```
adk web [AGENTS_DIR]
    │
    ├─► Click CLI (cli_tools_click.py)
    │       └─► get_fast_api_app(..., web=True)
    │
    ├─► fast_api.py
    │       ├─► Create session, artifact, memory, credential, eval services
    │       ├─► AgentLoader(agents_dir)
    │       ├─► AdkWebServer(...)
    │       └─► adk_web_server.get_fast_api_app(web_assets_dir=cli/browser)
    │
    └─► FastAPI app
            ├─► REST + SSE + WebSocket API (adk_web_server)
            ├─► /dev-ui/ → Angular SPA (static files)
            └─► Optional: A2A routes, builder routes
```

### 3.2 Key Library Paths (`.venv`)

| Component | Path |
|-----------|------|
| CLI entrypoint | `adk` → `google.adk.cli:main` |
| CLI commands | `google/adk/cli/cli_tools_click.py` |
| Web command | `@main.command("web")` → `get_fast_api_app(..., web=True)` |
| FastAPI factory | `google/adk/cli/fast_api.py` |
| Web server logic | `google/adk/cli/adk_web_server.py` |
| Agent loader | `google/adk/cli/utils/agent_loader.py` |
| Dev UI assets | `google/adk/cli/browser/` |
| Runtime config | `google/adk/cli/browser/assets/config/runtime-config.json` |

### 3.3 `adk web` vs `adk api_server`

- **`adk web`**: Same FastAPI app **plus** Dev UI. Uses `web=True` → `web_assets_dir` set to `cli/browser`, serves `/dev-ui/`, `/` → redirect to `/dev-ui/`.  
- **`adk api_server`**: Same API, **no** Dev UI (`web=False`). No static UI, no redirect.

The **backend API is identical**; only the presence of the Dev UI differs.

---

## 4. Agent Discovery and Structure

Agents are loaded by **`AgentLoader`** from `AGENTS_DIR`. Each **subdirectory** (or single module) is treated as one agent.

Supported layouts:

| Structure | Description |
|-----------|-------------|
| `{agents_dir}/{name}/agent.py` | Module `{name}.agent` with `root_agent` (or `app`) |
| `{agents_dir}/{name}/__init__.py` | Package `{name}` with `root_agent` or `app` |
| `{agents_dir}/{name}.py` | Module `{name}` with `root_agent` or `app` |
| `{agents_dir}/{name}/root_agent.yaml` | YAML-defined root agent |

Loader checks, in order:

1. `app` (as `App` instance)  
2. `root_agent` (as `BaseAgent`)  

`.env` under each agent dir can be loaded for that agent.  
`sys.path` is temporarily augmented with `agents_dir` so imports resolve.

---

## 5. API Endpoints

The FastAPI app is built in **`AdkWebServer.get_fast_api_app()`**. Below are the main endpoints.

### 5.1 Apps and Sessions

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/list-apps` | List agent app names. `?detailed=true` → full `ListAppsResponse` |
| `GET` | `/apps/{app_name}/users/{user_id}/sessions/{session_id}` | Get session |
| `GET` | `/apps/{app_name}/users/{user_id}/sessions` | List sessions (excludes eval sessions) |
| `POST` | `/apps/{app_name}/users/{user_id}/sessions` | Create session (optional body: `CreateSessionRequest`) |
| `POST` | `/apps/{app_name}/users/{user_id}/sessions/{session_id}` | **(Deprecated)** Create session with specific ID |
| `PATCH` | `/apps/{app_name}/users/{user_id}/sessions/{session_id}` | Update session state only (`UpdateSessionRequest`) |
| `DELETE` | `/apps/{app_name}/users/{user_id}/sessions/{session_id}` | Delete session |

### 5.2 Running the Agent

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/run` | Run agent, **non‑streaming**. Returns `list[Event]`. |
| `POST` | `/run_sse` | Run agent with **SSE streaming**. `RunAgentRequest.streaming` enables streaming. |
| `WebSocket` | `/run_live` | **Live** bidi streaming (text/audio). Query: `app_name`, `user_id`, `session_id`, `modalities` (e.g. `TEXT`, `AUDIO`). |

**Request body** (`RunAgentRequest`):

```python
app_name: str
user_id: str
session_id: str
new_message: types.Content    # User message (google.genai.types)
streaming: bool = False
state_delta: Optional[dict[str, Any]] = None
invocation_id: Optional[str] = None   # For resume of long-running tools
```

- **`/run`**: Session must exist. Runner is resolved per `app_name`, then `runner.run_async(...)` is called. All events are collected and returned as a list.  
- **`/run_sse`**: Same, but events are streamed as SSE: `data: <event JSON>\n\n`. If an event has both `content` and `artifact_delta`, the server may send **two** events (one content-only, one artifact-only) so the Dev UI can render them correctly.  
- **`/run_live`**: WebSocket. Client sends serialized `LiveRequest`; server streams back event JSON. Uses `Runner.run_live` with `LiveRequestQueue` and `RunConfig(response_modalities=...)`.

### 5.3 Artifacts

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `.../sessions/{session_id}/artifacts` | List artifact names |
| `GET` | `.../artifacts/{artifact_name}` | Load artifact (`?version` optional) |
| `GET` | `.../artifacts/{artifact_name}/versions` | List versions |
| `GET` | `.../artifacts/{artifact_name}/versions/{version_id}` | Load specific version |
| `POST` | `.../sessions/{session_id}/artifacts` | Save artifact (`SaveArtifactRequest`) |
| `DELETE` | `.../artifacts/{artifact_name}` | Delete artifact |

All under `/apps/{app_name}/users/{user_id}/sessions/...`.

### 5.4 Evaluation

Eval endpoints are under `/apps/{app_name}/` and (where applicable) `eval-sets` or legacy `eval_sets`:

- Create/list eval sets, add session to eval set, list evals in set  
- Get/update/delete eval cases  
- **Run eval**: `POST /apps/{app_name}/eval-sets/{eval_set_id}/run` with `RunEvalRequest`  
- List/get eval results, **metrics-info**  

Details and request/response shapes are in `adk_web_server.py` (eval tags).

### 5.5 Debug and Tracing

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/debug/trace/{event_id}` | Trace info for an event (if exported) |
| `GET` | `/debug/trace/session/{session_id}` | Spans for a session (OTel) |
| `GET` | `.../sessions/{session_id}/events/{event_id}/graph` | **Event graph** (Graphviz DOT) for function calls/responses |

### 5.6 Dev UI and Config (when `web=True`)

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/` | Redirect → `/dev-ui/` (or `{url_prefix}/dev-ui/`) |
| `GET` | `/dev-ui` | Redirect → `/dev-ui/` |
| `GET` | `/dev-ui/*` | Static Dev UI (Angular SPA) |
| `GET` | `/dev-ui/config` | `{ "logo_text": ..., "logo_image_url": ... }` |

### 5.7 Builder (when using Dev UI builder)

- `POST /builder/save` — Upload and save builder files (optional `tmp` mode).  
- `GET /builder/app/{app_name}` — Get agent file (e.g. YAML); `?file_path=...`, `?tmp=...`.  
- `POST /builder/app/{app_name}/cancel` — Cancel / cleanup tmp builder state.

### 5.8 A2A (optional, `--a2a`)

When `--a2a` is used, for each A2A app (dir with `agent.json`):

- RPC: `POST /a2a/{app_name}`  
- Agent card: `GET /a2a/{app_name}/.well-known/agent.json` (or equivalent well-known path).  

Implemented via `A2AStarletteApplication` and `A2aAgentExecutor` wiring in `fast_api.py`.

---

## 6. Request / Response Models (Summary)

- **`CreateSessionRequest`**: optional `session_id`, `state`, `events`.  
- **`UpdateSessionRequest`**: `state_delta`.  
- **`RunAgentRequest`**: see [Running the Agent](#52-running-the-agent).  
- **`SaveArtifactRequest`**: `filename`, `artifact` (`types.Part`), optional `custom_metadata`.  
- Events use `google.adk.events` (and GenAI `types`) and are serialized with `model_dump_json(by_alias=True, exclude_none=True)` for SSE/WebSocket.

---

## 7. Frontend (Dev UI)

### 7.1 Stack and Location

- **Location**: `google/adk/cli/browser/` in the installed package.  
- **App**: Angular SPA (`<app-root>`, `index.html`).  
- **Assets**: `index.html`, `main-*.js`, `chunk-*.js`, `polyfills-*.js`, `styles-*.css`, `adk_favicon.svg`, `assets/` (incl. `runtime-config.json`, images, `audio-processor.js`).

### 7.2 Serving

- **Mount**: `StaticFiles(directory=web_assets_dir, html=True)` at `/dev-ui/`.  
- **Base href**: `./` in `index.html`.  
- **Root**: `/` and `/dev-ui` redirect to `{url_prefix}/dev-ui/` when `web=True`.

### 7.3 Runtime Config

- **File**: `browser/assets/config/runtime-config.json`.  
- **Contents**: `backendUrl` (same as `--url_prefix` or `""`), and optionally `logo: { text, imageUrl }` when both `--logo-text` and `--logo-image-url` are set.  
- The server overwrites this at startup when `web_assets_dir` is provided (`_setup_runtime_config`).

### 7.4 Features (Match Official Docs)

- **Chat**: Send messages, view responses (via `/run` or `/run_sse`).  
- **Session management**: Create/switch/delete sessions (session API above).  
- **State inspection**: View/edit session state (PATCH session, state UI in Dev UI).  
- **Event history**: Inspect events (from run and debug endpoints).

---

## 8. Execution Path: Runner and Services

### 8.1 Runner Resolution

- **`AdkWebServer.get_runner_async(app_name)`**:  
  - Uses `AgentLoader.load_agent(app_name)` → `BaseAgent` or `App`.  
  - If `BaseAgent`, wraps in `App(name=app_name, root_agent=agent, plugins=...)`.  
  - Builds `Runner(app=app, artifact_service=..., session_service=..., memory_service=..., credential_service=...)` and caches it per `app_name`.  
- **Cleanup**: `reload_agents` + file watcher can mark runners for cleanup; next `get_runner_async` closes and recreates them.

### 8.2 Services Injected into the Runner

| Service | Role |
|---------|------|
| `session_service` | Create, get, list, delete, update sessions; append events |
| `artifact_service` | Store/load/delete artifacts (file, GCS, or in-memory) |
| `memory_service` | Memory/RAG (optional) |
| `credential_service` | Credentials (Dev UI uses in-memory) |

Eval managers (`EvalSetsManager`, `EvalSetResultsManager`) are used by eval endpoints only, not by the Runner.

### 8.3 Telemetry

- **OTel**: TracerProvider, span processors.  
- **Custom exporters**: `ApiServerSpanExporter` (trace by event id), `InMemoryExporter` (spans per session for debug).  
- **Optional**: `--trace_to_cloud`, `--otel_to_cloud` → GCP Trace / Logging.  
- **Instrumentation**: `opentelemetry.instrumentation.google_genai.GoogleGenAiSdkInstrumentor` if available (else warning).

---

## 9. CORS, URL Prefix, and Lifespan

- **CORS**: If `allow_origins` is passed, `CORSMiddleware` is added (literal origins + optional `regex:` patterns).  
- **URL prefix**: `--url_prefix` (e.g. `/api/v1`) is applied to redirects and `backendUrl` in runtime config; API routes themselves are typically mounted at root.  
- **Lifespan**: Custom lifespan can be passed; internal lifespan handles observer teardown (file watcher) and **closing all cached runners** on shutdown.

---

## 10. Relationship to `App` and `examples/web_app.py`

- **`google.adk.apps.App`**: A **config model** (Pydantic) holding `name`, `root_agent`, `plugins`, `resumability_config`, etc. It is **not** an ASGI app.  
- **`examples/web_app.py`** uses `App(agent=...)` and `uvicorn.run(app, ...)`. The **current** `apps.App` in the library expects `name` and `root_agent` (no `agent=`), and **does not** implement ASGI.  
- The **production-ready** web/API stack that **does** serve the Dev UI and all endpoints above is the **`adk web`** / **`adk api_server`** flow via `get_fast_api_app` and `AdkWebServer`.  
- For a **custom** FastAPI app, you would call `get_fast_api_app(...)` (or otherwise instantiate `AdkWebServer` and use `get_fast_api_app`) and mount or merge routes, rather than passing `App` directly to uvicorn.

---

## 11. Quick Reference

| Topic | Location |
|-------|----------|
| Start UI | `adk web [AGENTS_DIR]` |
| Default URL | `http://localhost:8000` → redirect to `http://localhost:8000/dev-ui/` |
| List agents | `GET /list-apps` |
| Create session | `POST /apps/{app}/users/{user}/sessions` |
| Run (streaming) | `POST /run_sse` with `RunAgentRequest` |
| Live (bidi) | `WebSocket /run_live` |
| Dev UI assets | `google/adk/cli/browser/` |
| Server logic | `google/adk/cli/adk_web_server.py` |
| Official docs | https://google.github.io/adk-docs/runtime/web-interface/ |

---

## 12. Related Documentation

- [Apps Package](05-Apps-Package.md) — App model and resumability  
- [Sessions Package](07-Sessions-Package.md) — Sessions and state  
- [Runners Package](10-Runners-Package.md) — How agents run  
- [Runnable vs API Execution](12-Runnable-vs-API-Execution-Models.md) — Runner vs HTTP API  
- [A2A Package](04-A2A-Package.md) — A2A and agent cards  
- [Setup and Installation](00-Setup-and-Installation.md) — Environment and `adk` CLI  

---

**Last Updated:** 2025-01-25  
**Library inspected:** `google-adk` in project `.venv`  
**Official reference:** [ADK Web Interface](https://google.github.io/adk-docs/runtime/web-interface/)
