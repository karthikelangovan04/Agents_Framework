# AG-UI Protocol and Core Types

**File path**: `ag_ui/01-AG-UI-Protocol-and-Core.md`  
**Package**: `ag_ui` (namespace), `ag_ui.core` (core types and events)

**Document generated using**: Backend venv  
`/Users/karthike/Desktop/Vibe Coding/Google-ADK-A2A-Explore/Adk_Copilotkit_UI_App/backend/.venv`  
**ag_ui_adk version at assessment**: 0.1.0

---

## Overview

The **AG-UI (Agent User Interaction)** stack defines a protocol between frontends (e.g. CopilotKit, `@ag-ui/client`) and backends. The Python side provides:

- **`ag_ui`** — namespace package with submodules:
  - **`ag_ui.core`** — core types and events for the Agent User Interaction Protocol (Pydantic models, event types).
  - **`ag_ui.encoder`** — event encoding (e.g. SSE) for HTTP responses.

Backend code typically uses `ag_ui.core` for input/output types and `ag_ui_adk` for wiring Google ADK to this protocol.

## Package structure

```
ag_ui
├── core      # Types and events (RunAgentInput, Tool, BaseEvent, messages, etc.)
└── encoder   # EventEncoder for HTTP (e.g. SSE)
```

## Key types in `ag_ui.core`

### RunAgentInput

Input for running an agent. This is the body of the POST request to an AG-UI endpoint.

```python
from ag_ui.core import RunAgentInput

# Signature (conceptually):
# RunAgentInput(
#     *,
#     threadId: str,
#     runId: str,
#     parentRunId: Optional[str] = None,
#     state: Any,
#     messages: List[Message],   # DeveloperMessage | SystemMessage | AssistantMessage | UserMessage | ToolMessage | ActivityMessage
#     tools: List[Tool],
#     context: List[Context],
#     forwardedProps: Any,
#     **extra_data: Any
# )
```

**Typical backend usage**: `add_adk_fastapi_endpoint` receives `RunAgentInput` and optional `extract_state_from_request(request, input_data)`. The backend often puts `X-User-Id` and `X-Session-Id` into `input_data.state` (e.g. `_ag_ui_user_id`, `_ag_ui_session_id`, `_ag_ui_thread_id`, `_ag_ui_app_name`) so ADK and session services can scope by user and session.

### Tool

A tool definition from the client (name, description, parameters).

```python
# Tool(*, name: str, description: str, parameters: Any, **extra_data: Any)
```

Used by `ag_ui_adk` to build proxy tools (e.g. `ClientProxyToolset`) so the ADK agent can invoke client-provided tools.

### BaseEvent and EventType

- **BaseEvent**: base for all protocol events (`type`, `timestamp`, `rawEvent`, etc.).
- **EventType**: enum-like event type (e.g. run lifecycle, message, tool call).

The backend (via `ag_ui_adk`) translates Google ADK events into AG-UI protocol events and streams them (e.g. via `ag_ui.encoder.EventEncoder`).

### Message types

`ag_ui.core` defines message roles used in `RunAgentInput.messages` and in history:

- **UserMessage**, **AssistantMessage**, **SystemMessage**, **DeveloperMessage**
- **ToolMessage** — tool call results
- **ActivityMessage** — activity/progress between chat messages

Events can be deltas (e.g. `ActivityDeltaEvent`) or snapshots (e.g. `ActivitySnapshotEvent`, `MessagesSnapshotEvent`).

## Example: Using RunAgentInput in the backend

```python
from fastapi import Request
from ag_ui.core import RunAgentInput

async def extract_user_and_session(request: Request, input_data: RunAgentInput) -> dict:
    """Put X-User-Id and X-Session-Id into state for ADK/session service."""
    state = {}
    user_id = request.headers.get("X-User-Id")
    session_id = request.headers.get("X-Session-Id")
    if user_id:
        state["_ag_ui_user_id"] = user_id
    if session_id:
        state["_ag_ui_session_id"] = session_id
        state["_ag_ui_thread_id"] = session_id
    state["_ag_ui_app_name"] = "my_app"
    return state

def user_id_extractor(input: RunAgentInput) -> str:
    """Used by ADKAgent to resolve user for session/memory."""
    if isinstance(getattr(input, "state", None), dict):
        uid = input.state.get("_ag_ui_user_id")
        if uid:
            return str(uid)
    return f"thread_user_{getattr(input, 'thread_id', 'default')}"
```

Then pass these to `add_adk_fastapi_endpoint(..., extract_state_from_request=extract_user_and_session)` and `ADKAgent(..., user_id_extractor=user_id_extractor)`.

## Example: Inspecting ag_ui.core

```bash
# From repo root, with backend venv
Adk_Copilotkit_UI_App/backend/.venv/bin/python adk/get_package_details_agui.py ag_ui.core
```

This outputs all classes (events, messages, RunAgentInput, Tool, etc.) and their methods/signatures in JSON.

## Related

- [02-AG-UI-ADK-Toolset.md](02-AG-UI-ADK-Toolset.md) — ADKAgent, endpoints, ClientProxyToolset
- [00-Document-Generation-Info.md](00-Document-Generation-Info.md) — venv path and versions
