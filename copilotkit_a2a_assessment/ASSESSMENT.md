# CopilotKit + A2A + ADK + MCP Integration Assessment

**Date**: February 8, 2026  
**Scope**: Can CopilotKit connect via A2A (with AG-UI) to ADK agents with shared state, human-in-loop, and MCP support?

---

## Executive Summary

**YES** — CopilotKit can connect to ADK agents via A2A protocol, but it requires a **bridge architecture**. The AG-UI protocol remains the interface between CopilotKit and the backend; A2A is used for **backend-to-backend** agent-to-agent communication. Shared state, human-in-loop, plan interaction, and MCP tools are all achievable through different combination patterns documented below.

---

## Architecture Layers

```
┌─────────────────────────────────────────────────────────────────────┐
│                     FRONTEND (Browser)                              │
│                                                                     │
│  CopilotKit React (useCoAgent, useCopilotChat, useCopilotAction)   │
│  + CopilotKit MCP Apps (MCPAppsMiddleware, BuiltInAgent)           │
│  + CopilotSidebar / CopilotChat UI                                 │
└───────────────────────────┬─────────────────────────────────────────┘
                            │ HTTP POST (AG-UI Protocol / SSE)
                            ▼
┌─────────────────────────────────────────────────────────────────────┐
│                 MIDDLEWARE (Next.js API Route)                       │
│                                                                     │
│  CopilotRuntime + ExperimentalEmptyAdapter                         │
│  HttpAgent(s) pointing to backend AG-UI endpoints                  │
│  MCPAppsMiddleware (for MCP App rendering in chat)                 │
└───────────────────────────┬─────────────────────────────────────────┘
                            │ HTTP POST (AG-UI Protocol / SSE)
                            ▼
┌─────────────────────────────────────────────────────────────────────┐
│              BACKEND GATEWAY (FastAPI + ag_ui_adk)                  │
│                                                                     │
│  ag_ui_adk.ADKAgent wraps the orchestrator LlmAgent               │
│  add_adk_fastapi_endpoint() serves the AG-UI endpoint              │
│  SessionManager handles shared state ←→ AG-UI state sync          │
│  ClientProxyToolset exposes frontend tools to backend agents       │
│  EventTranslator converts ADK events → AG-UI events (SSE stream)  │
└───────────────────────────┬─────────────────────────────────────────┘
                            │
              ┌─────────────┼──────────────┐
              │             │              │
              ▼             ▼              ▼
┌─────────────────┐ ┌──────────────┐ ┌──────────────────┐
│  ADK LlmAgent   │ │ RemoteA2a    │ │  McpToolset      │
│  (local agent)  │ │ Agent(s)     │ │  (MCP servers)   │
│                 │ │ (A2A proto)  │ │                  │
│  - tools        │ │              │ │  - filesystem    │
│  - callbacks    │ │              │ │  - weather       │
│  - sub_agents   │ │              │ │  - custom        │
└─────────────────┘ └──────┬───────┘ └──────────────────┘
                           │ A2A Protocol (HTTP/JSON-RPC/gRPC)
                           ▼
              ┌─────────────────────────────┐
              │   REMOTE A2A AGENT SERVERS  │
              │                             │
              │  ADK App() or A2A Server    │
              │  - Own session/state        │
              │  - Own MCP tools            │
              │  - Specialized capabilities │
              └─────────────────────────────┘
```

---

## Protocol Boundary Clarification

| Protocol | Layer | Purpose |
|----------|-------|---------|
| **AG-UI** | Frontend ↔ Backend Gateway | CopilotKit to backend communication. Handles shared state sync, message streaming, client-side tool calls, UI events. |
| **A2A** | Backend Gateway ↔ Remote Agents | Agent-to-agent communication. Handles agent discovery (AgentCard), message passing, task management, context filtering. |
| **MCP** | Backend Agent ↔ External Tools | Tool protocol. Agents call MCP servers for external capabilities (filesystem, APIs, databases). |
| **MCP Apps** | Frontend ↔ MCP Server | CopilotKit MCP Apps middleware renders MCP tool UIs directly in the chat. |

**Key insight**: AG-UI and A2A operate at **different layers**. CopilotKit always talks AG-UI to the backend; the backend gateway then uses A2A internally to reach remote agents. They don't compete — they compose.

---

## Shared State Flow with A2A

### Current (AG-UI only — Combo 1)
```
Frontend useCoAgent state ←→ AG-UI RunAgentInput.state ←→ ADKAgent session.state ←→ tool_context.state
```
Bidirectional. Frontend changes flow to backend via state in the POST body. Backend changes flow to frontend via state prediction events in the SSE stream.

### With A2A (Combo 2)
```
Frontend useCoAgent state
    ←→ AG-UI RunAgentInput.state
    ←→ Orchestrator ADKAgent session.state
    → (filtered context) → A2A → Remote Agent
    ← (response) ← A2A ← Remote Agent
    → Orchestrator updates session.state
    ←→ AG-UI state prediction events → Frontend
```
The orchestrator maintains the **primary shared state** with the frontend. Remote A2A agents receive **filtered context** (not the full state). Remote agent responses are integrated back into the orchestrator's session state, which then syncs to the frontend.

---

## Human-in-Loop with A2A

CopilotKit provides three mechanisms for human-in-loop that work with the A2A bridge:

### 1. useCopilotAction (Frontend Actions)
Backend agent calls a client-side tool → AG-UI emits ToolCallStartEvent → CopilotKit executes the action in the browser → result sent back → agent continues.

```
Orchestrator Agent → "approve_plan" tool call → AG-UI → CopilotKit
    → useCopilotAction renders approval UI → user clicks Approve
    → result sent back → AG-UI → Orchestrator continues
    → may call A2A remote agent with approved plan
```

### 2. useCoAgent (Shared State)
Backend agent updates state → state syncs to frontend → UI renders the plan/data → user modifies → changes sync back.

```
Remote A2A Agent → returns plan → Orchestrator updates session.state["plan"]
    → AG-UI predict_state event → Frontend useCoAgent sees plan update
    → UI renders plan with edit controls → user modifies
    → useCoAgent.setState → next AG-UI request includes modified state
    → Orchestrator reads state → sends to next A2A agent if needed
```

### 3. useCopilotChat (Message-based)
User sends approval/feedback messages in chat → orchestrator processes them.

---

## Five Integration Combinations

| # | Combination | Shared State | Human-in-Loop | MCP | Multi-Agent |
|---|------------|--------------|---------------|-----|-------------|
| 1 | CopilotKit → AG-UI → ADK | Yes (direct) | Yes (all 3 methods) | Backend only | Local sub_agents only |
| 2 | CopilotKit → AG-UI → A2A → ADK | Yes (via orchestrator) | Yes (all 3 methods) | No | A2A remote agents |
| 3 | CopilotKit → AG-UI → A2A → ADK + MCP | Yes (via orchestrator) | Yes (all 3 methods) | Backend MCP on both orchestrator and remote agents | A2A remote agents + MCP tools |
| 4 | CopilotKit MCP Apps + AG-UI → A2A → ADK | Yes (via orchestrator) | Yes (all 3 + MCP App UI) | Frontend MCP Apps + Backend MCP | A2A remote agents + MCP App UI |
| 5 | Full Integration (all of the above) | Yes (all layers) | Yes (all methods + MCP App UI) | Both frontend and backend MCP | A2A + local + MCP App agents |

---

## Detailed Combination Documentation

- **[Combo 1](combo1_copilotkit_agui_adk/)** — Baseline: CopilotKit → AG-UI → ADK (current working demo)
- **[Combo 2](combo2_copilotkit_agui_a2a_adk/)** — Main assessment: CopilotKit → AG-UI → A2A → ADK
- **[Combo 3](combo3_a2a_adk_mcp_backend/)** — Backend MCP: A2A + ADK + MCP tools on agents
- **[Combo 4](combo4_copilotkit_mcp_apps_a2a/)** — Frontend MCP: CopilotKit MCP Apps + A2A + ADK
- **[Combo 5](combo5_full_integration/)** — Full integration: everything combined

---

## Key Findings

### What Works
1. **AG-UI + A2A compose naturally** — AG-UI handles frontend↔backend, A2A handles backend↔remote agents
2. **Shared state works through the orchestrator** — the orchestrator ADK agent is the state bridge
3. **Human-in-loop is fully supported** — ClientProxyToolset/AGUIToolset enables frontend tool calls even in A2A scenarios
4. **MCP tools integrate at both layers** — backend agents use McpToolset, frontend uses MCPAppsMiddleware
5. **Multiple A2A agents can contribute to shared state** — orchestrator merges results into session state

### Gaps / Considerations
1. **No direct A2A from CopilotKit** — CopilotKit speaks AG-UI only; A2A is always behind the gateway
2. **State sync latency** — state travels: Frontend → AG-UI → Orchestrator → A2A → Remote → back. Plan for async patterns.
3. **Token cost in multi-agent** — orchestrator should filter context before forwarding to A2A agents (see ADK doc on token optimization)
4. **Remote agent state isolation** — remote A2A agents have their own sessions; they don't directly see frontend state unless the orchestrator passes it
5. **MCP App UI rendering** — requires CopilotKit v2 with `BuiltInAgent` and `MCPAppsMiddleware`; only works with CopilotKit-hosted LLMs (not with `ExperimentalEmptyAdapter` alone for the MCP Apps agent)

### Recommended Architecture
For maximum capability (shared state + human-in-loop + multi-agent + MCP):

```
CopilotKit Frontend
  ├── useCoAgent (shared state with orchestrator)
  ├── useCopilotAction (human-in-loop approvals)
  └── CopilotChat / CopilotSidebar
         │
    Next.js API Route
  ├── CopilotRuntime (agents: { orchestrator: HttpAgent })
  └── MCPAppsMiddleware (optional, for MCP App UI rendering)
         │
    FastAPI Backend (ag_ui_adk)
  ├── ADKAgent wrapping OrchestratorAgent
  │   ├── AGUIToolset (client-side tools for human-in-loop)
  │   ├── McpToolset (backend MCP servers)
  │   ├── Local tools (generate_recipe, etc.)
  │   └── sub_agents:
  │       ├── RemoteA2aAgent("math_agent", agent_card_url=...)
  │       ├── RemoteA2aAgent("data_agent", agent_card_url=...)
  │       └── Local LlmAgent("helper_agent")
  └── SessionService (InMemory or Database)
         │
    Remote A2A Agent Servers
  ├── ADK App (math_agent) on port 8000
  ├── ADK App (data_agent) on port 8001 with McpToolset
  └── A2A SDK Server (custom_agent) on port 8002
```

---

## Version Matrix

| Component | Version | Notes |
|-----------|---------|-------|
| @copilotkit/react-core | 1.51.3 | useCoAgent, useCopilotChat, useCopilotAction |
| @copilotkit/runtime | 1.51.3 | CopilotRuntime, ExperimentalEmptyAdapter |
| @ag-ui/client | 0.0.44 | HttpAgent |
| ag_ui_adk (Python) | 0.1.0 | ADKAgent, add_adk_fastapi_endpoint, AGUIToolset |
| google-adk | 1.22.1+ | LlmAgent, RemoteA2aAgent, McpToolset |
| a2a-sdk | 0.3.22 | Client, Server, A2AFastAPI |
| @modelcontextprotocol/ext-apps | latest | MCP Apps middleware for CopilotKit |
