# Combo 1: CopilotKit → AG-UI → ADK (Baseline)

**Status**: WORKING (current demo)  
**Shared State**: Yes, direct via `useCoAgent` ↔ `ag_ui_adk` ↔ `tool_context.state`  
**Human-in-Loop**: Yes, via `useCopilotAction`, `useCoAgent`, `useCopilotChat`  
**Multi-Agent**: Local sub_agents only (no A2A)  
**MCP**: Backend only (ADK `McpToolset`)

---

## Architecture

```
┌──────────────────────────┐
│  CopilotKit Frontend     │
│  - useCoAgent            │
│  - useCopilotChat        │
│  - CopilotSidebar        │
│  agent="shared_state"    │
└──────────┬───────────────┘
           │ POST /api/copilotkit (AG-UI protocol)
           ▼
┌──────────────────────────┐
│  Next.js API Route       │
│  CopilotRuntime          │
│  HttpAgent → backend     │
│  headers: X-User-Id,     │
│           X-Session-Id   │
└──────────┬───────────────┘
           │ POST / (AG-UI protocol, SSE stream)
           ▼
┌──────────────────────────┐
│  FastAPI Backend          │
│  ag_ui_adk.ADKAgent      │
│  - LlmAgent (Gemini)    │
│  - AGUIToolset           │
│  - generate_recipe tool  │
│  - Callbacks (state)     │
│  - InMemorySession       │
└──────────────────────────┘
```

## How Shared State Works

1. **Frontend → Backend**: `useCoAgent` sets state → included in `RunAgentInput.state` in the AG-UI POST body → `ag_ui_adk.SessionManager` stores it in ADK session → available in `tool_context.state` and `callback_context.state`

2. **Backend → Frontend**: Agent tool modifies `tool_context.state["recipe"]` → `EventTranslator` detects state change → emits AG-UI state prediction event in SSE stream → CopilotKit receives → updates `useCoAgent` state → React re-renders UI

3. **Bidirectional sync**: User edits the recipe form → `setAgentState()` called → next chat message carries updated state → backend receives it → agent sees current state in `before_model_callback`

## Key Files (from working demo)

### Frontend (page.tsx)
```tsx
// useCoAgent provides bidirectional state sync
const { state: agentState, setState: setAgentState } = useCoAgent<RecipeAgentState>({
  name: "shared_state",
  initialState: INITIAL_STATE,
});

// useCopilotChat for programmatic message sending
const { appendMessage, isLoading } = useCopilotChat();
```

### Backend (Python)
```python
# ag_ui_adk middleware bridges AG-UI protocol to ADK
adk_shared_state_agent = ADKAgent(
    adk_agent=shared_state_agent,
    app_name="demo_app",
    user_id="demo_user",
    session_timeout_seconds=3600,
    use_in_memory_services=True
)

# Agent uses AGUIToolset for client-side tool support + custom tools
shared_state_agent = LlmAgent(
    name="RecipeAgent",
    model="gemini-2.5-pro",
    tools=[AGUIToolset(), generate_recipe],
    before_agent_callback=on_before_agent,
    before_model_callback=before_model_modifier,
    after_model_callback=simple_after_model_modifier,
)
```

## Limitations

- **Single agent only** — no multi-agent orchestration
- **No remote agents** — everything runs in one process
- **State is in-memory** — lost on restart
- **No A2A** — cannot discover or delegate to remote agents
- **MCP tools possible** but not demonstrated in the demo

## When to Use

- Simple single-agent applications
- Prototyping shared state UI concepts
- When all logic fits in one agent
- No need for distributed agent systems
