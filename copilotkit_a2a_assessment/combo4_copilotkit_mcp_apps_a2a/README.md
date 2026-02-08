# Combo 4: CopilotKit MCP Apps + AG-UI → A2A → ADK

**Status**: FEASIBLE (requires CopilotKit v2 with MCP Apps support)  
**Shared State**: Yes, via orchestrator + MCP App state  
**Human-in-Loop**: Yes, all three methods + MCP App interactive UI in chat  
**Multi-Agent**: Yes, A2A remote agents + MCP App agents  
**MCP**: Yes, Frontend MCP Apps (UI rendering in chat) + Backend MCP tools

---

## Key Innovation: MCP Apps for Frontend UI Rendering

CopilotKit MCP Apps (via `MCPAppsMiddleware` and `BuiltInAgent`) allow MCP servers
to render **interactive UI components directly in the chat**. This is different from
backend MCP tools — these are frontend-rendered widgets.

Example from the weather server: the `get-forecast` tool returns weather data AND
the MCP server provides an HTML/JS UI component that renders a weather card in the chat.

---

## Architecture

```
┌──────────────────────────────────────────────────────────┐
│   CopilotKit Frontend                                     │
│                                                           │
│   ┌─────────────────────────────────────────────────┐    │
│   │ CopilotChat (v2)                                 │    │
│   │  - Regular text messages                         │    │
│   │  - MCP App UI widgets rendered inline            │    │
│   │    (weather cards, maps, charts, etc.)           │    │
│   │  - Interactive tool result displays              │    │
│   └─────────────────────────────────────────────────┘    │
│                                                           │
│   useCoAgent("orchestrator") ← shared state              │
│   useCopilotAction ← human-in-loop                       │
│   agent="default" (BuiltInAgent with MCPAppsMiddleware)  │
└──────────┬───────────────────────────────────────────────┘
           │ POST /api/copilotkit (AG-UI)
           ▼
┌──────────────────────────────────────────────────────────┐
│   Next.js API Route                                       │
│                                                           │
│   CopilotRuntime with TWO agent strategies:              │
│                                                           │
│   Strategy A: BuiltInAgent + MCPAppsMiddleware            │
│   - Uses OpenAI/Gemini hosted by CopilotKit              │
│   - MCPAppsMiddleware connects to MCP App servers         │
│   - Handles MCP App UI rendering                         │
│   - For: weather, maps, charts, PDF viewer               │
│                                                           │
│   Strategy B: HttpAgent → backend                        │
│   - Points to backend AG-UI endpoint                     │
│   - For: recipe orchestration with A2A                    │
│   - Shared state, human-in-loop                          │
│                                                           │
│   Both can coexist as different agents in the runtime     │
└──────────┬────────────────┬──────────────────────────────┘
           │                │
           ▼                ▼
┌─────────────────┐  ┌─────────────────────────────────┐
│  MCP App Servers │  │ FastAPI Backend (ag_ui_adk)      │
│  (for UI tools)  │  │                                  │
│                  │  │ ADKAgent → OrchestratorAgent     │
│  - weather:3006  │  │   ├── AGUIToolset                │
│  - map:3102      │  │   ├── McpToolset (backend)       │
│  - pdf:3003      │  │   └── sub_agents:                │
│  - charts:3105   │  │       ├── RemoteA2aAgent(recipe) │
└─────────────────┘  │       └── RemoteA2aAgent(data)   │
                      └──────────────────┬───────────────┘
                                         │ A2A Protocol
                                ┌────────┼────────┐
                                ▼        ▼        ▼
                          ┌──────┐ ┌────────┐ ┌────────┐
                          │Recipe│ │ Data   │ │ Other  │
                          │Agent │ │ Agent  │ │ A2A    │
                          └──────┘ └────────┘ └────────┘
```

## Two-Agent Strategy in the API Route

The key to this combo is running **two types of agents** in the CopilotRuntime:

```typescript
// app/api/copilotkit/route.ts
import { CopilotRuntime, ExperimentalEmptyAdapter, copilotRuntimeNextJSAppRouterEndpoint } from "@copilotkit/runtime";
import { BuiltInAgent } from "@copilotkit/runtime/v2";
import { MCPAppsMiddleware } from "@ag-ui/mcp-apps-middleware";
import { HttpAgent } from "@ag-ui/client";

// MCP App servers for frontend UI rendering
const mcpMiddleware = new MCPAppsMiddleware({
  mcpServers: [
    { type: "http", url: "http://localhost:3006/mcp", serverId: "weather-server" },
    { type: "http", url: "http://localhost:3102/mcp", serverId: "map-server" },
  ],
});

// Agent 1: MCP Apps agent (handles weather, maps, etc. with UI rendering)
const mcpAppsAgent = new BuiltInAgent({
  model: "openai/gpt-4o",
  prompt: "You can show weather forecasts and maps. Use the appropriate tools.",
}).use(mcpMiddleware);

// Agent 2: ADK orchestrator via AG-UI (handles recipe, A2A, shared state)
const adkOrchestratorAgent = new HttpAgent({
  url: "http://localhost:8001/",
  headers: { "X-User-Id": userId, "X-Session-Id": sessionId },
});

const runtime = new CopilotRuntime({
  agents: {
    mcp_apps: mcpAppsAgent,         // For MCP App UI tools
    orchestrator: adkOrchestratorAgent, // For ADK + A2A with shared state
  },
});
```

### Frontend Switching Between Agents

```tsx
// Page with MCP Apps
<CopilotKit runtimeUrl="/api/copilotkit" agent="mcp_apps">
  <CopilotChat />  {/* MCP App UIs render inline */}
</CopilotKit>

// Page with ADK Orchestrator (shared state, A2A)
<CopilotKit runtimeUrl="/api/copilotkit" agent="orchestrator">
  <RecipeForm />
  <CopilotSidebar />
</CopilotKit>

// OR: Single page that uses both (user or LLM decides routing)
<CopilotKit runtimeUrl="/api/copilotkit" agent="mcp_apps">
  <RecipeForm />
  <CopilotChat />
  {/* Chat can show weather cards AND recipe state updates */}
</CopilotKit>
```

## MCP App UI Rendering Flow

When the user asks "What's the weather in San Francisco?":

1. CopilotKit sends message to the `mcp_apps` agent
2. BuiltInAgent (GPT-4o) calls the `get-forecast` MCP tool
3. Weather MCP server:
   - Calls NWS API for forecast data
   - Returns JSON data as tool result
   - Provides HTML/JS UI component via resource URI
4. MCPAppsMiddleware:
   - Receives tool result + UI resource
   - Injects the HTML/JS widget into the chat stream
5. CopilotKit renders the weather card widget directly in the chat

The user sees an **interactive weather card** in the chat, not just text.

## Combining MCP App UI with Shared State

While MCP Apps handle UI rendering in chat, the ADK orchestrator handles
shared state. They can work together:

```
User: "Create a recipe for a BBQ in San Francisco this weekend"

1. Orchestrator receives request
2. Orchestrator calls weather MCP tool → gets San Francisco weather
3. Weather info affects recipe choices (outdoor-friendly, season-appropriate)
4. Orchestrator delegates to recipe_specialist (A2A) with weather context
5. Recipe agent returns recipe
6. Orchestrator updates state["recipe"] → UI form updates
7. Orchestrator also renders weather card in chat (if using MCP Apps agent)
```

## Limitations

- **BuiltInAgent requires LLM API key** — needs OpenAI/Gemini key for MCP Apps agent (cannot use ExperimentalEmptyAdapter)
- **Two agents, two LLMs** — MCP Apps agent uses one LLM, ADK orchestrator uses another
- **Agent switching** — frontend must specify which agent to use, or implement routing
- **MCP App server management** — need to run MCP App servers (weather, map, etc.)
- **CopilotKit v2 required** — MCP Apps support needs newer CopilotKit version

## When to Use

- Need **rich interactive UI components** in the chat (charts, maps, weather)
- Want **visual tool results** beyond text
- Building a **dashboard-like chat experience**
- Combining **data visualization** with **agent orchestration**
