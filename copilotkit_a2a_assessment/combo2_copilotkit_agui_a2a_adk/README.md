# Combo 2: CopilotKit → AG-UI → A2A → ADK

**Status**: FEASIBLE (architecture validated, code samples provided)  
**Shared State**: Yes, via orchestrator as state bridge  
**Human-in-Loop**: Yes, all three CopilotKit methods work  
**Multi-Agent**: Yes, A2A remote agents  
**MCP**: Not in this combo (see Combo 3)

---

## Architecture

```
┌────────────────────────────────┐
│   CopilotKit Frontend          │
│   - useCoAgent("orchestrator") │
│   - useCopilotAction           │
│   - useCopilotChat             │
│   - Plan display component     │
│   agent="orchestrator"         │
└──────────┬─────────────────────┘
           │ POST /api/copilotkit (AG-UI)
           ▼
┌────────────────────────────────┐
│   Next.js API Route            │
│   CopilotRuntime               │
│   HttpAgent → backend:8001/    │
└──────────┬─────────────────────┘
           │ POST / (AG-UI, SSE)
           ▼
┌────────────────────────────────────────────────────┐
│   FastAPI Backend (ag_ui_adk)                       │
│                                                     │
│   ADKAgent wrapping OrchestratorAgent              │
│   ├── AGUIToolset (approve_plan, show_results)     │
│   ├── generate_plan tool                           │
│   └── sub_agents:                                  │
│       ├── RemoteA2aAgent("recipe_agent")           │
│       │   → http://localhost:8010/agent_card.json  │
│       ├── RemoteA2aAgent("nutrition_agent")        │
│       │   → http://localhost:8011/agent_card.json  │
│       └── LocalAgent("formatter")                  │
│                                                     │
│   SessionService → shared state bridge             │
└──────────────────────┬─────────────────────────────┘
                       │ A2A Protocol (HTTP)
          ┌────────────┼───────────────┐
          ▼            ▼               ▼
┌─────────────┐ ┌──────────────┐ ┌──────────────┐
│ Recipe Agent │ │ Nutrition    │ │ (Other A2A   │
│ ADK App     │ │ Agent        │ │  agents)     │
│ port 8010   │ │ ADK App      │ │              │
│             │ │ port 8011    │ │              │
└─────────────┘ └──────────────┘ └──────────────┘
```

## Shared State Flow with A2A

### Step-by-step
1. User types "Create a healthy pasta recipe" in CopilotKit chat
2. `useCoAgent` state includes current recipe form data
3. AG-UI sends state + message to backend
4. OrchestratorAgent reads `callback_context.state["recipe"]`
5. OrchestratorAgent decides to delegate to `recipe_agent` via A2A
6. `RemoteA2aAgent` sends filtered context to remote recipe agent
7. Remote recipe agent returns a recipe
8. OrchestratorAgent receives response, calls `generate_recipe` tool
9. Tool updates `tool_context.state["recipe"]` with the new recipe
10. State change flows back via AG-UI SSE → `useCoAgent` → UI updates
11. OrchestratorAgent then delegates to `nutrition_agent` for analysis
12. Nutrition info merged into state → UI shows nutrition panel

### State ownership
- **Frontend** owns the UI representation (form fields, editing state)
- **Orchestrator** owns the canonical state (session.state)
- **Remote agents** receive filtered context and return results (stateless recommended)

## Human-in-Loop Patterns

### Pattern 1: Plan Approval via useCopilotAction

The orchestrator generates a plan and asks for frontend approval before executing.

```python
# Backend: Orchestrator uses AGUIToolset which includes client-defined tools
# The frontend defines an "approve_plan" action that renders UI

# Frontend:
# useCopilotAction({
#   name: "approve_plan",
#   description: "Show a plan to the user for approval",
#   parameters: [{ name: "plan", type: "object" }],
#   handler: async ({ plan }) => {
#     // Render plan UI, wait for user to approve/modify
#     const approved = await showPlanModal(plan);
#     return { approved, modifications: approved.changes };
#   }
# })
```

### Pattern 2: Plan Display via useCoAgent

The orchestrator puts the plan in shared state, UI renders it with edit controls.

```python
# Backend: orchestrator updates state
tool_context.state["plan"] = {
    "steps": ["Step 1: ...", "Step 2: ..."],
    "agents_to_use": ["recipe_agent", "nutrition_agent"],
    "estimated_time": "30 seconds",
    "status": "pending_approval"
}

# Frontend: useCoAgent sees state["plan"] update
# UI renders plan with Approve/Reject/Modify buttons
# User clicks Approve → setAgentState({ plan: { ...plan, status: "approved" } })
# Next message carries approved plan → orchestrator proceeds
```

### Pattern 3: Interactive Feedback via Chat

User provides feedback in natural language, orchestrator adjusts.

```
User: "Make it vegetarian and add more protein"
Orchestrator: reads current state, understands context
→ Delegates to recipe_agent via A2A with modified requirements
→ Updates state with new recipe
→ Frontend renders updated recipe
```

## Why A2A Adds Value

1. **Specialized agents** — each agent can have its own model, tools, and expertise
2. **Scalability** — agents run as separate services, scale independently
3. **Agent discovery** — agents publish AgentCards; orchestrator discovers capabilities
4. **Language agnostic** — remote agents can be in any language (Python ADK, Node.js, etc.)
5. **Deployment flexibility** — agents can run on different machines/clouds
6. **Team ownership** — different teams own different agents

## Limitations

- **Additional latency** — A2A adds network hops
- **State is not directly shared** — remote agents don't see frontend state unless orchestrator passes it
- **Token cost** — orchestrator must be smart about context filtering
- **Complexity** — more moving parts to deploy and monitor
- **No MCP in this combo** — see Combo 3 and 5 for MCP integration
