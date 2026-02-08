# AG-UI Documentation Index

**Directory**: `ag_ui/`  
**Purpose**: Documentation for the AG-UI protocol and AG-UI ADK toolset, generated using the backend venv and assessment scripts.

**Venv used**: `/Users/karthike/Desktop/Vibe Coding/Google-ADK-A2A-Explore/Adk_Copilotkit_UI_App/backend/.venv`  
**ag_ui_adk version at assessment**: 0.1.0

---

## Documents

| Document | Description |
|----------|-------------|
| [00-Document-Generation-Info.md](00-Document-Generation-Info.md) | Venv path, package versions, and how this documentation was produced. |
| [01-AG-UI-Protocol-and-Core.md](01-AG-UI-Protocol-and-Core.md) | AG-UI protocol and `ag_ui.core` types (RunAgentInput, Tool, BaseEvent, messages, state keys). |
| [02-AG-UI-ADK-Toolset.md](02-AG-UI-ADK-Toolset.md) | `ag_ui_adk` package: ADKAgent, add_adk_fastapi_endpoint, ClientProxyToolset, SessionManager, examples. |
| [03-Package-Listing-AG-UI.md](03-Package-Listing-AG-UI.md) | Listing of modules, classes, and functions for ag_ui and ag_ui_adk. |
| [How-to-Run-get_package_details_agui.md](How-to-Run-get_package_details_agui.md) | How to run `get_package_details_agui.py` and `explore_packages_agui.py` with the backend venv. |

---

## Assessment scripts (in `adk/`)

- **adk/get_package_details_agui.py** — JSON details for a module: `ag_ui`, `ag_ui.core`, `ag_ui_adk`, etc.
- **adk/explore_packages_agui.py** — Lists ag_ui and ag_ui_adk submodules, classes, and functions.

Run from repository root using the backend venv (see [How-to-Run-get_package_details_agui.md](How-to-Run-get_package_details_agui.md)).

---

## Related documentation

- **Google ADK**: [adk/docs/](../adk/docs/) — agents, tools, sessions, runners, etc.
- **ADK package assessment**: [adk/docs/How-to-Run-get_package_details.md](../adk/docs/How-to-Run-get_package_details.md)
