# How to Run the Frontend CopilotKit Exploration Script

**Script**: `frontend_copilotkit_docs/explore_copilotkit_packages.js`

---

## Purpose

The script **reads** the reference frontend’s `package.json` and installed `@copilotkit` / `@ag-ui` packages under `node_modules` and prints a JSON summary (package names, versions, entry points). It does **not** modify anything in `Adk_Copilotkit_UI_App/frontend`.

---

## Prerequisites

- Reference frontend at `Adk_Copilotkit_UI_App/frontend`.
- Dependencies installed (e.g. `npm install` or `pnpm install` in that directory) so `node_modules` exists.

---

## Command

From the **repository root** (`Google-ADK-A2A-Explore`):

```bash
node frontend_copilotkit_docs/explore_copilotkit_packages.js
```

---

## Output

JSON with:

- **source**: Paths to the frontend `package.json` and frontend directory.
- **app**: App name, version, dependencies, devDependencies from that package.json.
- **packages**: For each package under `node_modules/@copilotkit` and `node_modules/@ag-ui`:
  - version, main, module, types, exports (keys), and whether it’s a direct or transitive dependency.

Example (excerpt):

```json
{
  "source": {
    "packageJson": ".../Adk_Copilotkit_UI_App/frontend/package.json",
    "frontendDir": ".../Adk_Copilotkit_UI_App/frontend"
  },
  "app": {
    "name": "adk-copilotkit-frontend",
    "version": "0.1.0",
    "dependencies": { ... }
  },
  "packages": {
    "@copilotkit/runtime": {
      "version": "1.51.3",
      "main": "./dist/index.js",
      "exports": [".", "./v2", "./langgraph"],
      "inAppDependencies": "^1.51.0"
    },
    ...
  }
}
```

---

## Saving output

```bash
node frontend_copilotkit_docs/explore_copilotkit_packages.js > frontend_copilotkit_docs/packages_summary.json
```

---

## Relation to documentation

- The docs in `frontend_copilotkit_docs/` were produced using this script plus manual reading of `.d.ts` and reference app source. See [00-Document-Generation-Info.md](00-Document-Generation-Info.md) for the full assessment steps.
