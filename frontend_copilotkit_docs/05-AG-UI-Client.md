# AG-UI Client (frontend)

**File path**: `frontend_copilotkit_docs/05-AG-UI-Client.md`  
**Package**: `@ag-ui/client` (version 0.0.44 at assessment)

---

## Overview

`@ag-ui/client` is the **frontend** client for the **AG-UI protocol**. It provides **HttpAgent**, which sends requests to a backend AG-UI endpoint (e.g. the Python `ag_ui_adk` FastAPI routes) and consumes the event stream. The reference app uses HttpAgent only; all examples are from `Adk_Copilotkit_UI_App/frontend` (read-only).

---

## HttpAgent

**Purpose**: Agent implementation that talks to a backend over HTTP (AG-UI protocol). Used by CopilotRuntime as one of its `agents`.

**Config (HttpAgentConfig)**:

- **url**: string — Full URL of the backend AG-UI endpoint (e.g. `http://localhost:8001/ag-ui/deal_builder`).
- **headers**: Record<string, string> — Optional. Sent with every request; typically `X-User-Id` and `X-Session-Id` for backend session scoping.

Other optional fields (from types): agentId, description, threadId, initialMessages, initialState, debug.

---

## Example: API route (reference `app/api/copilotkit/route.ts`)

```ts
import { HttpAgent } from "@ag-ui/client";

const backendUrl = (process.env.NEXT_PUBLIC_API_URL || "http://localhost:8001").replace(/\/$/, "");
const userId = req.cookies.get("copilot_adk_user_id")?.value || "default";
const sessionId = req.cookies.get("copilot_adk_session_id")?.value || "default";

const runtime = new CopilotRuntime({
  agents: {
    deal_builder: new HttpAgent({
      url: `${backendUrl}/ag-ui/deal_builder`,
      headers: {
        "X-User-Id": userId,
        "X-Session-Id": sessionId,
      },
    }),
    knowledge_qa: new HttpAgent({
      url: `${backendUrl}/ag-ui/knowledge_qa`,
      headers: {
        "X-User-Id": userId,
        "X-Session-Id": sessionId,
      },
    }),
  },
});
```

---

## How it fits with the backend

1. **Frontend** (this package): HttpAgent sends POST requests to `url` with `headers`. The CopilotKit runtime serializes messages and agent state according to the protocol.
2. **Backend** (see `ag_ui/` docs): FastAPI receives the request; `extract_state_from_request` merges headers into state (`_ag_ui_user_id`, `_ag_ui_session_id`, etc.); ADKAgent runs the Google ADK agent and streams AG-UI events back.
3. **Cookies**: The reference app does not use HttpAgent directly in the browser; the **API route** reads cookies and passes their values as headers when constructing HttpAgent. So user/session are fixed per request on the server.

---

## Other exports (for reference)

From the package’s type definitions:

- **AbstractAgent** — Base class; HttpAgent extends it.
- **RunAgentParameters**, **RunAgentResult**, **AgentSubscriber** — For running the agent and subscribing to events.
- **Middleware**, **FilterToolCallsMiddleware**, **FunctionMiddleware** — For customizing behavior.
- **compactEvents**, **parseSSEStream**, **runHttpRequest**, etc. — Lower-level utilities.
- Re-exports from `@ag-ui/core`: Message, State, RunAgentInput, event types, etc.

The reference app only uses the HttpAgent constructor with `url` and `headers`.

---

## Related

- Backend AG-UI: [ag_ui/01-AG-UI-Protocol-and-Core.md](../ag_ui/01-AG-UI-Protocol-and-Core.md), [ag_ui/02-AG-UI-ADK-Toolset.md](../ag_ui/02-AG-UI-ADK-Toolset.md).
- [01-CopilotKit-Overview-and-Wiring.md](01-CopilotKit-Overview-and-Wiring.md) — Cookies and headers flow.
- [02-CopilotKit-Runtime.md](02-CopilotKit-Runtime.md) — Where HttpAgent is used in the runtime.
