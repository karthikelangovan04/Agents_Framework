# Plan: Frontend CopilotKit & Related Packages Documentation

**Status**: DRAFT — awaiting your approval before any implementation.  
**Reference app (read-only)**: `Adk_Copilotkit_UI_App/frontend` — **no changes** will be made to that directory.

---

## 1. Objective

Create documentation for the **frontend** CopilotKit and related packages, in the same spirit as the **backend AG-UI** docs in `ag_ui/`:

- Separate directory for all frontend/CopilotKit docs
- Document package structure, main exports, and usage
- Include version and environment info (where docs were generated from)
- Use the existing frontend app only as **reference** (read-only) for examples and wiring

---

## 2. Scope and constraints

| Item | Detail |
|------|--------|
| **Reference frontend** | `Adk_Copilotkit_UI_App/frontend` (Next.js 14, React 18) |
| **Constraint** | Do **not** modify any file under `Adk_Copilotkit_UI_App/frontend` |
| **Documentation only** | All new content lives under `frontend_copilotkit_docs/` (and any scripts under `adk/` or this directory) |
| **Package versions** | Document against the versions in the reference app’s `package.json` (and lockfile if we reference it) |

---

## 3. Packages to document (from reference app)

From `Adk_Copilotkit_UI_App/frontend/package.json` and actual imports in the app:

| Package | Version (ref) | Role in app |
|---------|----------------|-------------|
| **@copilotkit/react-core** | ^1.51.0 | `CopilotKit`, `useCoAgent`, `useCopilotChat` |
| **@copilotkit/react-ui** | ^1.51.0 | `CopilotSidebar`, `@copilotkit/react-ui/styles.css` |
| **@copilotkit/runtime** | ^1.51.0 | `CopilotRuntime`, `ExperimentalEmptyAdapter`, `copilotRuntimeNextJSAppRouterEndpoint` |
| **@copilotkit/runtime-client-gql** | (transitive) | `TextMessage`, `MessageRole` (used in deal page) |
| **@ag-ui/client** | ^0.0.44 | `HttpAgent` (AG-UI backend client) |

---

## 4. Approach (how we’ll document)

- **Backend (ag_ui)** used Python `inspect` and scripts on the venv.  
- **Frontend** is TypeScript/JavaScript and npm packages, so we will:

1. **Environment**
   - Record **where** docs were generated (e.g. repo root, node version, that we used the reference app’s `node_modules` only for reading).

2. **Package discovery**
   - Use the reference app’s installed packages (read `package.json`, `node_modules/@copilotkit/*/package.json`, `node_modules/@ag-ui/*/package.json`).
   - Optionally add a small script (in `adk/` or `frontend_copilotkit_docs/`) that lists package names, versions, and main entry points (no edits to frontend).

3. **API / surface area**
   - Derive from:
     - Published READMEs and CHANGELOGs in `node_modules`
     - TypeScript types / `.d.ts` or source (e.g. `index.ts`, `index.tsx`) to list exports and key types
   - Summarize **classes**, **hooks**, **components**, and **key types** in markdown (similar to `ag_ui/01-AG-UI-Protocol-and-Core.md`, `02-AG-UI-ADK-Toolset.md`).

4. **Examples and wiring**
   - Take examples **only from** the reference app (read-only):
     - `app/api/copilotkit/route.ts` — runtime, HttpAgent, cookies → headers
     - `app/chat/page.tsx` — CopilotKit + CopilotSidebar
     - `app/deal/page.tsx` — CopilotKit, useCoAgent, useCopilotChat, shared state
     - `app/CookieInit.tsx` — AG-UI cookie names and session id
   - Document patterns (e.g. “runtime URL”, “agent names”, “X-User-Id / X-Session-Id”, “useCoAgent state”) without changing any of that code.

5. **Optional script**
   - If useful, add something like `explore_copilotkit_packages.js` (or `.ts`) that:
     - Runs from repo root
     - Reads `Adk_Copilotkit_UI_App/frontend/package.json` and `node_modules` for @copilotkit and @ag-ui
     - Outputs a simple JSON/markdown summary (names, versions, entry points).  
   - Script lives under `frontend_copilotkit_docs/` or `adk/`; **never** under `Adk_Copilotkit_UI_App/frontend`.

---

## 5. Proposed directory and document list

**Directory**: `frontend_copilotkit_docs/` (at repo root, alongside `ag_ui/`, `adk/`).

| Document | Purpose |
|----------|--------|
| **00-Document-Generation-Info.md** | Where and how docs were generated; node/npm context; reference app path; package versions. |
| **01-CopilotKit-Overview-and-Wiring.md** | High-level: CopilotKit ↔ backend AG-UI; runtime URL; cookies → headers; agent names. |
| **02-CopilotKit-Runtime.md** | `@copilotkit/runtime`: CopilotRuntime, ExperimentalEmptyAdapter, Next.js App Router endpoint; usage from reference `route.ts`. |
| **03-CopilotKit-React-Core.md** | `@copilotkit/react-core`: CopilotKit provider, useCoAgent, useCopilotChat; examples from chat and deal pages. |
| **04-CopilotKit-React-UI.md** | `@copilotkit/react-ui`: CopilotSidebar (and other UI components if relevant); styles. |
| **05-AG-UI-Client.md** | `@ag-ui/client`: HttpAgent; how it fits with backend `/ag-ui/*` and headers. |
| **06-Package-Listing-CopilotKit.md** | Summary table of packages, versions, main exports (like `ag_ui/03-Package-Listing-AG-UI.md`). |
| **How-to-Run-Exploration-Scripts.md** | (If we add scripts) How to run them and from where; no changes to frontend. |
| **INDEX.md** | Index of all docs in this directory. |

Optional (if we add a discovery script):

- **explore_copilotkit_packages.js** (or .ts) in `frontend_copilotkit_docs/` or `adk/`
- **07-Reference-App-Usage-Summary.md** — short summary of which file uses which export (for maintainability).

---

## 6. What we will not do

- Change, add, or delete any file under `Adk_Copilotkit_UI_App/frontend`.
- Install or update dependencies in the reference app.
- Run dev/build/lint in the frontend (unless you ask); we only read files and, if you approve, run a small exploration script from repo root that reads the frontend’s package.json and node_modules.

---

## 7. Approval request

If you approve this plan, we will:

1. Create the documents listed in **Section 5** under `frontend_copilotkit_docs/`.
2. Populate them using only **read-only** use of `Adk_Copilotkit_UI_App/frontend` and its `node_modules`.
3. Optionally add one small exploration script (location as above) and document it in **How-to-Run-Exploration-Scripts.md**.

Please confirm or adjust (e.g. add/remove docs, change naming, or skip the script) and we’ll proceed accordingly.
