# AG-UI Package Listing

**File path**: `ag_ui/03-Package-Listing-AG-UI.md`

**Document generated using**: Backend venv  
`/Users/karthike/Desktop/Vibe Coding/Google-ADK-A2A-Explore/Adk_Copilotkit_UI_App/backend/.venv`  
**ag_ui_adk version**: 0.1.0

---

## Summary (from explore_packages_agui)

| Package    | Version | Submodules |
|-----------|---------|------------|
| **ag_ui** | —       | `ag_ui.core`, `ag_ui.encoder` |
| **ag_ui_adk** | 0.1.0 | `adk_agent`, `client_proxy_tool`, `client_proxy_toolset`, `config`, `endpoint`, `event_translator`, `execution_state`, `session_manager`, `utils` |

---

## ag_ui (top-level)

- **Submodules**: `ag_ui.core`, `ag_ui.encoder`
- **Direct classes/functions**: None (namespace package). Use `ag_ui.core` and `ag_ui.encoder` for types and encoding.

---

## ag_ui.core

**Purpose**: Core types and events for the Agent User Interaction Protocol.

**Notable classes (partial list):**

- **RunAgentInput** — input for running an agent (threadId, runId, state, messages, tools, context, etc.)
- **Tool** — tool definition (name, description, parameters)
- **BaseEvent**, **EventType** — base event and event type enum
- **Message types**: UserMessage, AssistantMessage, SystemMessage, DeveloperMessage, ToolMessage, ActivityMessage
- **Event types**: RunStartedEvent, RunFinishedEvent, RunErrorEvent, ToolCallEndEvent, ToolCallResultEvent, SystemMessage, MessagesSnapshotEvent, ActivityDeltaEvent, ActivitySnapshotEvent, etc.

**Usage**: Import for request/response and state handling, e.g. `from ag_ui.core import RunAgentInput`.

---

## ag_ui_adk (top-level)

**Version**: 0.1.0  
**Doc**: “ADK Middleware for AG-UI Protocol — enables Google ADK agents to be used with the AG-UI protocol.”

### Classes

| Class | Description |
|-------|-------------|
| **ADKAgent** | Middleware bridging AG-UI protocol and Google ADK agents; manages sessions, state, and client-side tools. |
| **EventTranslator** | Translates ADK events to AG-UI protocol events. |
| **SessionManager** | Session lifecycle and state (get_or_create_session, update_session_state, cleanup, etc.). |
| **PredictStateMapping** | Config for predictive state updates (tool args → state keys). |

### Functions

| Function | Description |
|----------|-------------|
| **add_adk_fastapi_endpoint** | Registers AG-UI endpoint (and experimental /agents/state) on a FastAPI app or router. |
| **create_adk_app** | Creates a FastAPI app with one ADK endpoint. |
| **adk_events_to_messages** | Converts ADK session events to a list of AG-UI Message objects. |
| **normalize_predict_state** | Normalizes predict_state config to a list of PredictStateMapping. |

### Submodules (for implementation details)

| Submodule | Purpose |
|-----------|---------|
| **ag_ui_adk.adk_agent** | ADKAgent implementation. |
| **ag_ui_adk.endpoint** | add_adk_fastapi_endpoint, create_adk_app, request/response handling. |
| **ag_ui_adk.event_translator** | EventTranslator, adk_events_to_messages. |
| **ag_ui_adk.session_manager** | SessionManager, CONTEXT_STATE_KEY. |
| **ag_ui_adk.client_proxy_tool** | Single client-side proxy tool. |
| **ag_ui_adk.client_proxy_toolset** | ClientProxyToolset — dynamic toolset from RunAgentInput.tools. |
| **ag_ui_adk.config** | PredictStateMapping, normalize_predict_state. |
| **ag_ui_adk.execution_state** | ExecutionState for long-running tool tracking. |
| **ag_ui_adk.utils** | Internal helpers. |

---

## How to regenerate this listing

From repo root with backend venv:

```bash
Adk_Copilotkit_UI_App/backend/.venv/bin/python adk/explore_packages_agui.py
Adk_Copilotkit_UI_App/backend/.venv/bin/python adk/get_package_details_agui.py ag_ui_adk
Adk_Copilotkit_UI_App/backend/.venv/bin/python adk/get_package_details_agui.py ag_ui.core
```

See [How-to-Run-get_package_details_agui.md](How-to-Run-get_package_details_agui.md) for full usage.
