# AG-UI ADK Toolset and Middleware

**File path**: `ag_ui/02-AG-UI-ADK-Toolset.md`  
**Package**: `ag_ui_adk`

**Document generated using**: Backend venv  
`/Users/karthike/Desktop/Vibe Coding/Google-ADK-A2A-Explore/Adk_Copilotkit_UI_App/backend/.venv`  
**ag_ui_adk version at assessment**: **0.1.0**

---

## Overview

**ag_ui_adk** is the ADK middleware for the AG-UI protocol. It:

- Exposes Google ADK agents over HTTP (FastAPI) using AG-UI request/response shapes.
- Translates ADK events to AG-UI protocol events (streaming, e.g. SSE).
- Manages sessions and state (with optional ADK `SessionService` / `MemoryService`).
- Supports client-side tools via a dynamic toolset that creates proxy tools from `RunAgentInput.tools`.

## Package structure

```
ag_ui_adk
├── __init__.py          # ADKAgent, add_adk_fastapi_endpoint, create_adk_app, EventTranslator, SessionManager, etc.
├── adk_agent.py         # ADKAgent implementation
├── endpoint.py          # add_adk_fastapi_endpoint, create_adk_app
├── event_translator.py  # EventTranslator, adk_events_to_messages
├── session_manager.py   # SessionManager, CONTEXT_STATE_KEY
├── client_proxy_tool.py # ClientProxyTool (per client tool)
├── client_proxy_toolset.py # ClientProxyToolset (dynamic tools from RunAgentInput.tools)
├── config.py            # PredictStateMapping, normalize_predict_state
├── execution_state.py   # ExecutionState (long-running tool tracking)
└── utils/
```

## Key classes and functions

### ADKAgent

Middleware that bridges the AG-UI protocol and Google ADK agents.

**Constructor (summary):**

```python
ADKAgent(
    adk_agent: BaseAgent,                    # Your Google ADK agent (e.g. LlmAgent)
    app_name: Optional[str] = None,
    session_timeout_seconds: Optional[int] = 1200,
    app_name_extractor: Optional[Callable[[RunAgentInput], str]] = None,
    user_id: Optional[str] = None,
    user_id_extractor: Optional[Callable[[RunAgentInput], str]] = None,
    session_service: Optional[BaseSessionService] = None,
    artifact_service: Optional[BaseArtifactService] = None,
    memory_service: Optional[BaseMemoryService] = None,
    credential_service: Optional[BaseCredentialService] = None,
    run_config_factory: Optional[Callable[[RunAgentInput], ADKRunConfig]] = None,
    use_in_memory_services: bool = True,
    execution_timeout_seconds: int = 600,
    tool_timeout_seconds: int = 300,
    max_concurrent_executions: int = 10,
    cleanup_interval_seconds: int = 300,
    max_sessions_per_user: Optional[int] = None,
    delete_session_on_cleanup: bool = True,
    save_session_to_memory_on_cleanup: bool = True,
    predict_state: Optional[Iterable[PredictStateMapping]] = None,
    emit_messages_snapshot: bool = False,
)
```

**Main methods:**

- **`run(self, input: RunAgentInput) -> AsyncGenerator[BaseEvent, None]`**  
  Runs the ADK agent with the given AG-UI input; yields AG-UI protocol events (including client-side tool handling).

- **`close(self)`**  
  Cleans up resources and active executions.

**Class method:**

- **`from_app(cls, app: App, ...)`**  
  Builds an `ADKAgent` from an ADK `App` instance.

### add_adk_fastapi_endpoint

Registers the AG-UI endpoint and (in current versions) an experimental `POST /agents/state` endpoint.

```python
add_adk_fastapi_endpoint(
    app: FastAPI | APIRouter,
    agent: ADKAgent,
    path: str = "/",
    extract_headers: Optional[List[str]] = None,   # Deprecated: use extract_state_from_request
    extract_state_from_request: Optional[
        Callable[[Request, RunAgentInput], Coroutine[dict[str, Any], Any, Any]]
    ] = None,
)
```

- **extract_state_from_request**: async `(request, input_data) -> dict`; merged into `input_data.state` before running the agent. Use this to inject `_ag_ui_user_id`, `_ag_ui_session_id`, etc. from headers.

### create_adk_app

Creates a FastAPI app with a single ADK endpoint (convenience wrapper).

```python
create_adk_app(
    agent: ADKAgent,
    path: str = "/",
    extract_headers: Optional[List[str]] = None,
    extract_state_from_request: Optional[Callable[...]] = None,
) -> FastAPI
```

### EventTranslator

Translates Google ADK events to AG-UI protocol events (streaming, tool calls, etc.). Used internally by `ADKAgent`. Supports optional `predict_state` for real-time state updates.

### SessionManager

Singleton that wraps ADK `SessionService` (and optional `MemoryService`), handles get-or-create session by `(thread_id, app_name, user_id)`, state updates, and cleanup. Uses `CONTEXT_STATE_KEY` for storing context in session state.

### ClientProxyToolset and client-side tools

- **ClientProxyToolset**  
  A Google ADK `BaseToolset` that builds one **ClientProxyTool** per tool in `RunAgentInput.tools`. Those tools are “long-running”: the agent emits tool-call events to the client; the client runs the tool and submits results back; the same run continues.

- **AGUIToolset**  
  In some codebases (e.g. demo snippets) you may see `AGUIToolset`. In **ag_ui_adk 0.1.0** the public API exposes **ClientProxyToolset** (used internally by ADKAgent for client tools). If your code imports `AGUIToolset`, it may be an alias or from another version; you can use the same pattern with the agent’s built-in client tool handling.

### Other exports

- **adk_events_to_messages(events)** — converts ADK session events to a list of AG-UI message objects.
- **PredictStateMapping**, **normalize_predict_state** — for predictive state updates in the UI.
- **CONTEXT_STATE_KEY** — key used in session state for context.

## Example: Minimal FastAPI backend with ADK and session state

```python
from fastapi import FastAPI, Request
from ag_ui.core import RunAgentInput
from ag_ui_adk import ADKAgent, add_adk_fastapi_endpoint
from google.adk import Agent
from google.adk.sessions import BaseSessionService  # or DatabaseSessionService

# Your ADK agent
deal_builder_agent = Agent(
    name="deal_builder",
    model="gemini-2.0-flash",
    instruction="You help with deals.",
    tools=[],  # or server-side tools; client tools are added by ag_ui_adk from RunAgentInput.tools
)

async def extract_user_and_session(request: Request, input_data: RunAgentInput) -> dict:
    state = {}
    if request.headers.get("X-User-Id"):
        state["_ag_ui_user_id"] = request.headers.get("X-User-Id")
    if request.headers.get("X-Session-Id"):
        sid = request.headers.get("X-Session-Id")
        state["_ag_ui_session_id"] = sid
        state["_ag_ui_thread_id"] = sid
    state["_ag_ui_app_name"] = "my_app"
    return state

def user_id_extractor(input: RunAgentInput) -> str:
    return (input.state or {}).get("_ag_ui_user_id") or f"thread_user_{getattr(input, 'thread_id', 'default')}"

session_service: BaseSessionService = ...  # e.g. DatabaseSessionService

adk_agent = ADKAgent(
    adk_agent=deal_builder_agent,
    app_name="my_app",
    user_id_extractor=user_id_extractor,
    session_service=session_service,
    use_in_memory_services=False,
)

app = FastAPI()
add_adk_fastapi_endpoint(
    app,
    adk_agent,
    path="/ag-ui/deal_builder",
    extract_state_from_request=extract_user_and_session,
)
```

## Example: Getting full API details (classes/methods)

```bash
# From repo root
Adk_Copilotkit_UI_App/backend/.venv/bin/python adk/get_package_details_agui.py ag_ui_adk
```

Output is JSON with all classes (ADKAgent, EventTranslator, SessionManager, PredictStateMapping), their methods and signatures, and top-level functions.

## Related

- [01-AG-UI-Protocol-and-Core.md](01-AG-UI-Protocol-and-Core.md) — RunAgentInput, state keys, protocol
- [00-Document-Generation-Info.md](00-Document-Generation-Info.md) — venv and version used for this doc
