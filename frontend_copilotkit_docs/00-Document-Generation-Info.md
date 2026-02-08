# Frontend CopilotKit Documentation — Generation and Assessment

**Directory**: `frontend_copilotkit_docs/`  
**Reference app (read-only)**: `Adk_Copilotkit_UI_App/frontend`

---

## How we assessed and what steps were followed

This section describes **exactly how** the frontend CopilotKit and related packages were assessed and how this documentation was produced. No changes were made to the reference frontend.

### Step 1: Identify scope from the reference app

- **Read** `Adk_Copilotkit_UI_App/frontend/package.json` to list direct dependencies.
- **Identified packages to document**:
  - `@copilotkit/react-core`, `@copilotkit/react-ui`, `@copilotkit/runtime` (direct)
  - `@ag-ui/client` (direct — AG-UI HTTP client for backend)
  - `@copilotkit/runtime-client-gql` (transitive; used in deal page for `TextMessage`, `MessageRole`)

### Step 2: Record installed versions (read-only)

- **Read** each package’s `package.json` under `Adk_Copilotkit_UI_App/frontend/node_modules/`:
  - `@copilotkit/runtime/package.json` → version 1.51.3
  - `@copilotkit/react-core/package.json` → version 1.51.3
  - `@copilotkit/react-ui/package.json` → version 1.51.3
  - `@copilotkit/runtime-client-gql/package.json` → version 1.51.3
  - `@ag-ui/client/package.json` → version 0.0.44

No `npm install` or any other command was run inside the frontend directory.

### Step 3: Discover public API (exports and types)

- **Read** TypeScript declaration files (`.d.ts`) for each package’s main entry:
  - `node_modules/@copilotkit/runtime/dist/index.d.ts` — CopilotRuntime, ExperimentalEmptyAdapter, copilotRuntimeNextJSAppRouterEndpoint, service adapters, message types.
  - `node_modules/@copilotkit/react-core/dist/index.d.ts` — CopilotKit, useCoAgent, useCopilotChat, useCopilotAction, context types, etc.
  - `node_modules/@copilotkit/react-ui/dist/index.d.ts` — CopilotSidebar, CopilotChat, CopilotPopup, message components, styles export.
  - `node_modules/@copilotkit/runtime-client-gql/dist/index.d.ts` — TextMessage, MessageRole, Message types, conversion helpers.
  - `node_modules/@ag-ui/client/dist/index.d.ts` — HttpAgent, HttpAgentConfig, AbstractAgent, RunAgentParameters, event types.

- **Read** selected source files where needed for clarity (e.g. `runtime/src/service-adapters/empty/empty-adapter.ts`, `runtime/src/lib/index.ts`).

### Step 4: Map usage in the reference app (read-only)

- **Read** the following files under `Adk_Copilotkit_UI_App/frontend/app/` **without modifying them**:
  - `api/copilotkit/route.ts` — CopilotRuntime, ExperimentalEmptyAdapter, copilotRuntimeNextJSAppRouterEndpoint, HttpAgent, cookies → headers.
  - `chat/page.tsx` — CopilotKit, CopilotSidebar, runtimeUrl, agent name.
  - `deal/page.tsx` — CopilotKit, useCoAgent, useCopilotChat, CopilotSidebar, TextMessage, MessageRole, shared state pattern.
  - `CookieInit.tsx` — Cookie names for AG-UI (copilot_adk_user_id, copilot_adk_session_id).
  - `layout.tsx`, `page.tsx` — Layout and home links.

- **Extracted** examples and wiring patterns (runtime URL, agent names, state keys, cookie → header flow) from these files for use in the docs.

### Step 5: Create exploration script (outside frontend)

- **Added** `frontend_copilotkit_docs/explore_copilotkit_packages.js` at repo root level.
- Script **reads** `Adk_Copilotkit_UI_App/frontend/package.json` and `node_modules/@copilotkit/*`, `node_modules/@ag-ui/*` and outputs a JSON summary (package names, versions, entry points).
- Script is **run from repo root**: `node frontend_copilotkit_docs/explore_copilotkit_packages.js`.
- **No files** under `Adk_Copilotkit_UI_App/frontend` were created or modified.

### Step 6: Write documentation

- **Created** all markdown files in `frontend_copilotkit_docs/`:
  - Overview and wiring (01), Runtime (02), React Core (03), React UI (04), AG-UI Client (05), Package listing (06).
  - Index (INDEX.md), How-to-run for the exploration script, and this file (00).
- **Examples** in the docs are taken verbatim or in simplified form from the reference app files listed in Step 4.
- **Version and environment** information (see below) was recorded in this file and in individual docs where relevant.

---

## Document origin and environment

| Field | Value |
|-------|--------|
| **Repository root** | `Google-ADK-A2A-Explore` |
| **Reference frontend** | `Adk_Copilotkit_UI_App/frontend` (read-only) |
| **Assessment approach** | Read package.json, node_modules package.json, .d.ts files, and app source; run exploration script from repo root |
| **Exploration script** | `frontend_copilotkit_docs/explore_copilotkit_packages.js` |

## Package versions (at assessment time)

| Package | Version (installed) | In app package.json |
|---------|--------------------|----------------------|
| @copilotkit/runtime | 1.51.3 | ^1.51.0 |
| @copilotkit/react-core | 1.51.3 | ^1.51.0 |
| @copilotkit/react-ui | 1.51.3 | ^1.51.0 |
| @copilotkit/runtime-client-gql | 1.51.3 | (transitive) |
| @ag-ui/client | 0.0.44 | ^0.0.44 |

Reference app: Next.js 14.2.0, React ^18.2.0.

## Generated artifacts

- **explore_copilotkit_packages.js** — Run with `node frontend_copilotkit_docs/explore_copilotkit_packages.js` from repo root; outputs JSON summary of packages and versions.
- All `.md` files in this directory — Written from the assessment steps above; examples from reference app only.

## Related

- [How-to-Run-Exploration-Scripts.md](How-to-Run-Exploration-Scripts.md) — How to run the exploration script.
- [ag_ui/](../ag_ui/) — Backend AG-UI documentation (Python, venv-based assessment).
