# CopilotKit Runtime

**File path**: `frontend_copilotkit_docs/02-CopilotKit-Runtime.md`  
**Package**: `@copilotkit/runtime` (version 1.51.3 at assessment)

---

## Overview

`@copilotkit/runtime` runs on the **server** (e.g. in a Next.js API route). It creates a **CopilotRuntime** instance configured with **agents** (e.g. HttpAgent for backend AG-UI) and a **service adapter**, and exposes an HTTP endpoint via **copilotRuntimeNextJSAppRouterEndpoint** for the App Router.

All examples below are from the reference app `Adk_Copilotkit_UI_App/frontend` (read-only).

---

## Main exports used in the reference app

| Export | Purpose |
|--------|---------|
| **CopilotRuntime** | Class to create the runtime; accepts `agents` and optional adapter. |
| **ExperimentalEmptyAdapter** | No-op service adapter when using only remote agents (e.g. AG-UI backend). |
| **copilotRuntimeNextJSAppRouterEndpoint** | Returns a handler for Next.js App Router POST requests. |

---

## CopilotRuntime

**Constructor**: `new CopilotRuntime(options)`

- **agents**: Record of agent name → agent instance. For AG-UI backends, each value is an `HttpAgent` from `@ag-ui/client` (see [05-AG-UI-Client.md](05-AG-UI-Client.md)).
- **Service adapter**: Optional. When using only remote agents (no CopilotKit-hosted LLM), the reference app uses `ExperimentalEmptyAdapter` so the runtime does not require an LLM adapter.

Example from reference `app/api/copilotkit/route.ts`:

```ts
import {
  CopilotRuntime,
  ExperimentalEmptyAdapter,
  copilotRuntimeNextJSAppRouterEndpoint,
} from "@copilotkit/runtime";
import { HttpAgent } from "@ag-ui/client";

const backendUrl = (process.env.NEXT_PUBLIC_API_URL || "http://localhost:8001").replace(/\/$/, "");
const userId = req.cookies.get("copilot_adk_user_id")?.value || "default";
const sessionId = req.cookies.get("copilot_adk_session_id")?.value || "default";

const serviceAdapter = new ExperimentalEmptyAdapter();
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

## ExperimentalEmptyAdapter

- Use when the runtime **only** forwards to remote agents (e.g. AG-UI backend) and does not need an LLM (OpenAI, Anthropic, etc.).
- Implements the runtime’s expected service adapter interface but returns without doing LLM work.
- Copilot Suggestions may not work when using this adapter.

Example (from reference):

```ts
import { ExperimentalEmptyAdapter } from "@copilotkit/runtime";

const serviceAdapter = new ExperimentalEmptyAdapter();
```

---

## copilotRuntimeNextJSAppRouterEndpoint

**Signature (conceptually)**: `copilotRuntimeNextJSAppRouterEndpoint(options) => { handleRequest }`

- **options**: Object with `runtime`, `serviceAdapter`, and `endpoint` (path string for the route).
- **handleRequest**: Async function that accepts the Next.js `Request` and returns a `Response`. Use it in the route’s POST handler.

Example from reference `app/api/copilotkit/route.ts`:

```ts
const { handleRequest } = copilotRuntimeNextJSAppRouterEndpoint({
  runtime,
  serviceAdapter,
  endpoint: "/api/copilotkit",
});
return handleRequest(req);
```

Full route example (reference):

```ts
// app/api/copilotkit/route.ts
import {
  CopilotRuntime,
  ExperimentalEmptyAdapter,
  copilotRuntimeNextJSAppRouterEndpoint,
} from "@copilotkit/runtime";
import { HttpAgent } from "@ag-ui/client";
import { NextRequest } from "next/server";

const backendUrl = (process.env.NEXT_PUBLIC_API_URL || "http://localhost:8001").replace(/\/$/, "");

export async function POST(req: NextRequest) {
  const userId = req.cookies.get("copilot_adk_user_id")?.value || "default";
  const sessionId = req.cookies.get("copilot_adk_session_id")?.value || "default";

  const serviceAdapter = new ExperimentalEmptyAdapter();
  const runtime = new CopilotRuntime({
    agents: {
      deal_builder: new HttpAgent({
        url: `${backendUrl}/ag-ui/deal_builder`,
        headers: { "X-User-Id": userId, "X-Session-Id": sessionId },
      }),
      knowledge_qa: new HttpAgent({
        url: `${backendUrl}/ag-ui/knowledge_qa`,
        headers: { "X-User-Id": userId, "X-Session-Id": sessionId },
      }),
    },
  });

  const { handleRequest } = copilotRuntimeNextJSAppRouterEndpoint({
    runtime,
    serviceAdapter,
    endpoint: "/api/copilotkit",
  });
  return handleRequest(req);
}
```

---

## Other runtime exports (for reference)

The package also exports:

- **Service adapters**: OpenAIAdapter, AnthropicAdapter, LangChainAdapter, GoogleGenerativeAIAdapter, OpenAIAssistantAdapter, GroqAdapter, EmptyAdapter, etc.
- **Message/event types**: MessageRole, message input/output types, runtime event types.
- **Integrations**: copilotRuntimeNextJSPagesRouterEndpoint, copilotRuntimeNodeHttpEndpoint, etc.

For the reference app, only CopilotRuntime, ExperimentalEmptyAdapter, and copilotRuntimeNextJSAppRouterEndpoint are used.

---

## Related

- [01-CopilotKit-Overview-and-Wiring.md](01-CopilotKit-Overview-and-Wiring.md) — Overall flow and wiring.
- [05-AG-UI-Client.md](05-AG-UI-Client.md) — HttpAgent config (url, headers).
