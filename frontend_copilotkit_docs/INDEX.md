# Frontend CopilotKit Documentation Index

**Directory**: `frontend_copilotkit_docs/`  
**Reference app (read-only)**: `Adk_Copilotkit_UI_App/frontend`

---

## Assessment and generation

| Document | Description |
|----------|-------------|
| [00-Document-Generation-Info.md](00-Document-Generation-Info.md) | **How we assessed** (steps 1–6), document origin, package versions, and generated artifacts. |
| [How-to-Run-Exploration-Scripts.md](How-to-Run-Exploration-Scripts.md) | How to run `explore_copilotkit_packages.js` from repo root. |

---

## Conceptual and wiring

| Document | Description |
|----------|-------------|
| [01-CopilotKit-Overview-and-Wiring.md](01-CopilotKit-Overview-and-Wiring.md) | Overview, frontend → backend flow, runtime URL, agent names, cookies → headers, file-by-file reference usage. |

---

## Packages (with examples from reference app)

| Document | Package | Description |
|----------|---------|-------------|
| [02-CopilotKit-Runtime.md](02-CopilotKit-Runtime.md) | @copilotkit/runtime | CopilotRuntime, ExperimentalEmptyAdapter, copilotRuntimeNextJSAppRouterEndpoint; full API route example. |
| [03-CopilotKit-React-Core.md](03-CopilotKit-React-Core.md) | @copilotkit/react-core | CopilotKit, useCoAgent, useCopilotChat; chat and deal page examples. |
| [04-CopilotKit-React-UI.md](04-CopilotKit-React-UI.md) | @copilotkit/react-ui | CopilotSidebar, styles; examples from chat and deal pages. |
| [05-AG-UI-Client.md](05-AG-UI-Client.md) | @ag-ui/client | HttpAgent (url, headers); API route example and backend fit. |

---

## Reference

| Document | Description |
|----------|-------------|
| [06-Package-Listing-CopilotKit.md](06-Package-Listing-CopilotKit.md) | Summary table of packages, versions, and what the reference app uses. |

---

## Script

| File | Description |
|------|-------------|
| **explore_copilotkit_packages.js** | Node script (run from repo root) that lists @copilotkit and @ag-ui packages and versions; read-only on frontend. |

---

## Backend docs

- **ag_ui/** — Backend AG-UI protocol and ag_ui_adk toolset (Python, venv-based assessment).
