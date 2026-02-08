# How to Run `get_package_details_agui.py` and `explore_packages_agui.py`

**File path**: `adk/get_package_details_agui.py`, `adk/explore_packages_agui.py`

## Overview

These scripts introspect the **AG-UI**-related Python packages (`ag_ui`, `ag_ui_adk`) and their submodules. They use Python’s `inspect` (and, for exploration, `pkgutil`) to list classes, methods, functions, signatures, and docstrings. Use the **backend venv** so `ag_ui` and `ag_ui_adk` are available.

## Venv and location

- **Venv**: `/Users/karthike/Desktop/Vibe Coding/Google-ADK-A2A-Explore/Adk_Copilotkit_UI_App/backend/.venv`
- **Repo root**: `/Users/karthike/Desktop/Vibe Coding/Google-ADK-A2A-Explore`
- Run from **repo root** so paths to `adk/` scripts are correct.

## Prerequisites

1. Backend venv created and dependencies installed, e.g.:
   ```bash
   cd Adk_Copilotkit_UI_App/backend
   python3 -m venv .venv
   .venv/bin/pip install -r requirements.txt   # includes ag-ui-adk, google-adk, etc.
   ```
2. From repo root, use the venv’s Python:
   ```bash
   Adk_Copilotkit_UI_App/backend/.venv/bin/python adk/explore_packages_agui.py
   Adk_Copilotkit_UI_App/backend/.venv/bin/python adk/get_package_details_agui.py <module_name>
   ```

## 1. Explore packages (`explore_packages_agui.py`)

Lists top-level modules and their submodules, classes, and functions.

```bash
Adk_Copilotkit_UI_App/backend/.venv/bin/python adk/explore_packages_agui.py
```

**Example output (summary):**

- `ag_ui`: submodules `ag_ui.core`, `ag_ui.encoder`
- `ag_ui_adk`: version, file path, submodules (e.g. `adk_agent`, `endpoint`, `client_proxy_toolset`), classes (e.g. `ADKAgent`, `EventTranslator`, `SessionManager`), functions (e.g. `add_adk_fastapi_endpoint`, `create_adk_app`)

## 2. Get package/module details (`get_package_details_agui.py`)

Outputs JSON for a single module: classes (with methods and signatures), functions, and constants.

### Usage

```bash
Adk_Copilotkit_UI_App/backend/.venv/bin/python adk/get_package_details_agui.py <module_name>
```

### Examples

```bash
# Top-level ag_ui (namespace; may have few direct members)
Adk_Copilotkit_UI_App/backend/.venv/bin/python adk/get_package_details_agui.py ag_ui

# Core types and events (RunAgentInput, Tool, BaseEvent, EventType, messages, etc.)
Adk_Copilotkit_UI_App/backend/.venv/bin/python adk/get_package_details_agui.py ag_ui.core

# AG-UI ADK middleware (ADKAgent, add_adk_fastapi_endpoint, SessionManager, etc.)
Adk_Copilotkit_UI_App/backend/.venv/bin/python adk/get_package_details_agui.py ag_ui_adk
```

### Saving output

```bash
Adk_Copilotkit_UI_App/backend/.venv/bin/python adk/get_package_details_agui.py ag_ui_adk > ag_ui_adk_details.json 2>&1
Adk_Copilotkit_UI_App/backend/.venv/bin/python adk/get_package_details_agui.py ag_ui.core | python3 -m json.tool > ag_ui_core_details.json
```

## Output shape (get_package_details_agui)

Rough structure:

- `name`: module name
- `module_doc`: module docstring
- `file`: `__file__` of the module (if any)
- `version`: `__version__` (if any)
- `classes`: list of `{ name, doc, signature, methods: [ { name, signature, doc } ] }`
- `functions`: list of `{ name, signature, doc }`
- `constants`: list (if collected)
- `error`: present if import or introspection failed

## Relation to ADK scripts

- **adk/get_package_details.py** — for `google.adk.<package>` (e.g. `agents`, `tools`, `sessions`). See [adk/docs/How-to-Run-get_package_details.md](../adk/docs/How-to-Run-get_package_details.md).
- **adk/get_package_details_agui.py** — for `ag_ui`, `ag_ui.core`, `ag_ui_adk`, etc.; same idea, different module prefix.
- **adk/explore_packages_agui.py** — discovers `ag_ui` and `ag_ui_adk` and their submodules; analogous to `explore_packages.py` for Google ADK.

## Document generation

The markdown docs in the `ag_ui/` directory (including this file and [00-Document-Generation-Info.md](00-Document-Generation-Info.md)) were created using the above venv and scripts, and note the venv path and package versions at generation time.
