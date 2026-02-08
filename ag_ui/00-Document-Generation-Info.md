# AG-UI Documentation — Generation Info

**Directory**: `ag_ui/` (AG UI documentation)  
**Repository**: `Google-ADK-A2A-Explore`

## Document origin and environment

| Field | Value |
|-------|--------|
| **Venv path** | `/Users/karthike/Desktop/Vibe Coding/Google-ADK-A2A-Explore/Adk_Copilotkit_UI_App/backend/.venv` |
| **Python** | `backend/.venv/bin/python` (used for assessment) |
| **Created from** | Repository root: `Google-ADK-A2A-Explore` |
| **Assessment scripts** | `adk/get_package_details_agui.py`, `adk/explore_packages_agui.py` |

## Package versions (at assessment time)

| Package | Version |
|---------|---------|
| **ag_ui** | (namespace; no `__version__`; provided by `ag-ui` npm / client stack) |
| **ag_ui_adk** | **0.1.0** |
| **ag_ui.core** | (submodule of `ag_ui`; types/events for Agent User Interaction Protocol) |

## How this documentation was produced

1. **Explore packages**  
   Run from repo root with backend venv:
   ```bash
   Adk_Copilotkit_UI_App/backend/.venv/bin/python adk/explore_packages_agui.py
   ```

2. **Get detailed package/module info**  
   Same venv, for each module:
   ```bash
   Adk_Copilotkit_UI_App/backend/.venv/bin/python adk/get_package_details_agui.py ag_ui
   Adk_Copilotkit_UI_App/backend/.venv/bin/python adk/get_package_details_agui.py ag_ui.core
   Adk_Copilotkit_UI_App/backend/.venv/bin/python adk/get_package_details_agui.py ag_ui_adk
   ```

3. **Output**  
   Scripts print JSON (classes, methods, functions, signatures, docstrings). The markdown docs in `ag_ui/` are written from that output and from code inspection, in the same style as `adk/docs`.

## Generated artifacts

- **ag_ui/ag_ui_adk_details.json** — Full JSON output of `get_package_details_agui.py ag_ui_adk` (classes, methods, functions, signatures). Regenerate with the commands in [How-to-Run-get_package_details_agui.md](How-to-Run-get_package_details_agui.md).

## Related docs

- [How to run get_package_details_agui](How-to-Run-get_package_details_agui.md)
- [ADK docs](../adk/docs/) — Google ADK packages (e.g. agents, tools, sessions)
- [adk/docs/How-to-Run-get_package_details.md](../adk/docs/How-to-Run-get_package_details.md) — ADK package assessment

---

*Generated for the AG-UI protocol and AG-UI ADK toolset; venv and versions as above.*
