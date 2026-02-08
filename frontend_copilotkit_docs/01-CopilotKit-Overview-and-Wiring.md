# CopilotKit Overview and Wiring with Backend AG-UI

**File path**: `frontend_copilotkit_docs/01-CopilotKit-Overview-and-Wiring.md`  
**Reference app (read-only)**: `Adk_Copilotkit_UI_App/frontend`

---

## Overview

The frontend uses **CopilotKit** to provide chat and co-agent UIs that talk to the **backend AG-UI** endpoints. The flow is:

1. **Frontend** (Next.js App Router) exposes an API route that runs the CopilotKit runtime.
2. The **runtime** is configured with **agents** that are **HttpAgent** instances pointing at backend `/ag-ui/*` URLs.
3. Each request from the UI goes to the frontend API route; the runtime forwards to the backend with **headers** (`X-User-Id`, `X-Session-Id`) derived from **cookies**.
4. The **backend** (see `ag_ui/` docs) uses those headers to set state (`_ag_ui_user_id`, `_ag_ui_session_id`, etc.) and run the ADK agent.

No changes were made to the reference frontend; examples below are taken from it.

---

## High-level architecture

```
User browser
    → CopilotKit UI (CopilotSidebar, etc.)
    → Frontend API route (POST /api/copilotkit)
    → CopilotRuntime with agents: { deal_builder: HttpAgent(...), knowledge_qa: HttpAgent(...) }
    → Backend POST /ag-ui/deal_builder or /ag-ui/knowledge_qa
    → Backend ADKAgent + SessionService
```

---

## Key wiring elements

### 1. Runtime URL

The React app points CopilotKit at the frontend API route:

- **URL**: `/api/copilotkit` (same origin as the Next.js app).
- **Usage**: Passed as `runtimeUrl="/api/copilotkit"` to `<CopilotKit>`.

Example from reference `app/chat/page.tsx`:

```tsx
<CopilotKit
  runtimeUrl="/api/copilotkit"
  showDevConsole={false}
  agent="knowledge_qa"
>
  {/* ... */}
</CopilotKit>
```

### 2. Agent names

Agent names must match between:

- **Frontend**: `agent="deal_builder"` or `agent="knowledge_qa"` on `<CopilotKit>`, and the keys in the runtime `agents` object.
- **Backend**: Paths `/ag-ui/deal_builder` and `/ag-ui/knowledge_qa` registered with `add_adk_fastapi_endpoint`.

Example from reference `app/deal/page.tsx`:

```tsx
<CopilotKit
  runtimeUrl="/api/copilotkit"
  showDevConsole={false}
  agent="deal_builder"
>
```

### 3. Cookies → headers (user and session)

The backend expects `X-User-Id` and `X-Session-Id` to scope sessions. The reference app:

- Sets cookies **client-side** in `CookieInit.tsx`: `copilot_adk_user_id`, `copilot_adk_session_id`.
- Reads them in the **API route** and passes them as headers to each `HttpAgent`.

Example from reference `app/api/copilotkit/route.ts`:

```ts
const userId = req.cookies.get("copilot_adk_user_id")?.value || "default";
const sessionId = req.cookies.get("copilot_adk_session_id")?.value || "default";

// ...
deal_builder: new HttpAgent({
  url: `${backendUrl}/ag-ui/deal_builder`,
  headers: {
    "X-User-Id": userId,
    "X-Session-Id": sessionId,
  },
}),
```

Example from reference `app/CookieInit.tsx` (cookie names only):

```ts
setCookie("copilot_adk_user_id", "default");
setCookie("copilot_adk_session_id", randomId());
```

### 4. Backend URL

The API route builds the backend base URL from env (e.g. `NEXT_PUBLIC_API_URL`), defaulting to `http://localhost:8001`:

```ts
const backendUrl = (process.env.NEXT_PUBLIC_API_URL || "http://localhost:8001").replace(/\/$/, "");
```

---

## File-by-file reference usage (read-only)

| File | Purpose |
|------|--------|
| `app/api/copilotkit/route.ts` | POST handler; creates CopilotRuntime with HttpAgent(s); calls copilotRuntimeNextJSAppRouterEndpoint; reads cookies, sets headers. |
| `app/chat/page.tsx` | Knowledge Q&A page; CopilotKit + CopilotSidebar; agent `knowledge_qa`. |
| `app/deal/page.tsx` | Deal Builder; CopilotKit + useCoAgent (shared state) + useCopilotChat + CopilotSidebar; agent `deal_builder`; uses TextMessage, MessageRole from runtime-client-gql. |
| `app/CookieInit.tsx` | Sets copilot_adk_user_id and copilot_adk_session_id if missing. |
| `app/layout.tsx` | Renders CookieInit and children. |
| `app/page.tsx` | Home with links to /deal and /chat. |

---

## Related docs

- [02-CopilotKit-Runtime.md](02-CopilotKit-Runtime.md) — Runtime and API route in detail.
- [05-AG-UI-Client.md](05-AG-UI-Client.md) — HttpAgent and backend URL/headers.
- Backend: [ag_ui/01-AG-UI-Protocol-and-Core.md](../ag_ui/01-AG-UI-Protocol-and-Core.md), [ag_ui/02-AG-UI-ADK-Toolset.md](../ag_ui/02-AG-UI-ADK-Toolset.md).
