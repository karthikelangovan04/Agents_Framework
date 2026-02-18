# Understanding `update_deal` Function and AGUI Tools: Backend to Frontend Update Flow

## Table of Contents

1. [What is `update_deal` Function?](#what-is-update_deal-function)
2. [How `update_deal` Works Internally](#how-update_deal-works-internally)
3. [What are AGUI Tools?](#what-are-agui-tools)
4. [How Backend Updates Reach Frontend](#how-backend-updates-reach-frontend)
5. [Complete Flow Diagram](#complete-flow-diagram)
6. [Code Examples](#code-examples)

---

## What is `update_deal` Function?

`update_deal` is a **backend tool** (FunctionTool) that allows the AI agent to modify the deal state stored in the session. It's one of the core tools available to the `deal_builder` agent.

### Purpose

- **Update deal information**: Customer name, segment, products, estimated value, stage, next steps
- **Modify session state**: Changes are persisted in `session.state["deal"]`
- **Trigger frontend updates**: State changes automatically propagate to frontend via AG-UI protocol

### Function Signature

```python
def update_deal(
    tool_context: ToolContext,
    customer_name: str = "",
    segment: str = "",
    products: List[str] = None,
    estimated_value: str = "",
    stage: str = "",
    next_steps: List[str] = None,
    changes: str = "",
) -> Dict[str, str]:
```

### Parameters

- `tool_context`: Provides access to `tool_context.state` (session state)
- `customer_name`: Customer or account name
- `segment`: Industry segment (e.g., "Analytics and Artificial Intelligence")
- `products`: List of product names (e.g., ["Vertex AI", "Gemini Enterprise"])
- `estimated_value`: Deal value (e.g., "$3M")
- `stage`: Deal stage (e.g., "Discovery", "Proposal", "Negotiation")
- `next_steps`: List of recommended next steps
- `changes`: Brief description of what was changed

### Return Value

```python
{
    "status": "success",
    "message": "Deal updated successfully"
}
```

---

## How `update_deal` Works Internally

### Step-by-Step Execution

```python
def update_deal(tool_context: ToolContext, ...):
    # 1. Handle None values
    if products is None:
        products = []
    if next_steps is None:
        next_steps = []
    
    # 2. Build update object with provided values
    deal = {
        "customer_name": customer_name or "",
        "segment": segment or "",
        "products": products,
        "estimated_value": estimated_value or "",
        "stage": stage or "",
        "next_steps": next_steps,
        "changes": changes or "",
    }
    
    # 3. Get current deal from session state
    current = dict(tool_context.state.get("deal") or {})
    
    # 4. Merge updates into current deal (preserve existing values)
    for k, v in deal.items():
        if k in ("products", "next_steps"):
            if v:  # Only update if new value provided
                current[k] = list(v)
        elif v is not None and v != "":  # Only update non-empty values
            current[k] = v
    
    # 5. CRITICAL: Update session state
    tool_context.state["deal"] = current
    
    # 6. Return success response
    return {"status": "success", "message": "Deal updated successfully"}
```

### Key Points

1. **State Access**: Uses `tool_context.state` to access session state
2. **Merge Strategy**: Preserves existing values, only updates provided fields
3. **State Modification**: Direct assignment `tool_context.state["deal"] = current`
4. **Automatic Tracking**: ADK automatically captures state changes in `Event.actions.state_delta`

### Example Execution

**Before:**
```python
tool_context.state["deal"] = {
    "customer_name": "Cognizant",
    "segment": "",
    "products": ["Vertex AI "],
    "estimated_value": "",
    "stage": "Discovery",
    "next_steps": ["expand products"],
    "changes": ""
}
```

**Call:**
```python
update_deal(
    tool_context=tool_context,
    segment="Analytics and Artificial Intelligence",
    estimated_value="$3M",
    next_steps=["Research and recommend next steps for deal progression."]
)
```

**After:**
```python
tool_context.state["deal"] = {
    "customer_name": "Cognizant",  # Preserved
    "segment": "Analytics and Artificial Intelligence",  # Updated
    "products": ["Vertex AI "],  # Preserved
    "estimated_value": "$3M",  # Updated
    "stage": "Discovery",  # Preserved
    "next_steps": ["Research and recommend next steps for deal progression."],  # Updated
    "changes": ""  # Preserved
}
```

---

## What are AGUI Tools?

### AGUIToolset Overview

**AGUIToolset** is a special toolset that enables **client-side tools** - tools that execute on the frontend rather than the backend.

### Two Types of Tools

#### 1. **Backend Tools** (Server-Side)
- Execute on the backend server
- Examples: `update_deal`, `generate_proposal`, `SearchAgent`
- Have direct access to `tool_context.state`
- State changes happen immediately in backend

#### 2. **AGUI Tools** (Client-Side)
- Execute on the frontend (browser)
- Registered via `useCopilotAction` hook in React
- Examples: Custom UI actions, form submissions, frontend-only operations
- Results sent back to backend via SSE stream

### How AGUIToolset Works

```python
# Backend: deal_builder.py
from ag_ui_adk import AGUIToolset

# Add AGUIToolset to tools list
_tools = [update_deal, generate_proposal, search_agent_tool]
if AGUIToolset is not None:
    _tools.insert(0, AGUIToolset())  # Add client-side tools
```

**What AGUIToolset Does:**

1. **Receives Frontend Tools**: When frontend sends `RunAgentInput.tools`, AGUIToolset creates proxy tools
2. **Creates ClientProxyTool**: For each frontend tool, creates a `ClientProxyTool` wrapper
3. **Tool Call Flow**: When agent calls a client tool:
   - Backend emits `TOOL_CALL_START` event
   - Frontend receives event via SSE
   - Frontend executes `useCopilotAction` handler
   - Frontend sends result back via SSE
   - Backend receives result and continues agent execution

### Frontend Tool Registration

```typescript
// Frontend: page.tsx
import { useCopilotAction } from "@copilotkit/react-core";

function DealForm() {
  // Register a client-side tool
  useCopilotAction({
    name: "update_deal_ui",  // Tool name agent can call
    description: "Update deal in UI",
    parameters: [
      {
        name: "customer_name",
        type: "string",
        description: "Customer name"
      }
    ],
    handler: async ({ customer_name }) => {
      // Execute on frontend
      updateDeal({ customer_name });
      return { status: "success" };
    }
  });
}
```

### Detecting AGUI Tools in Callbacks

```python
def before_tool_callback(tool: Any, args: Dict[str, Any], tool_context: ToolContext):
    tool_type = type(tool).__name__
    
    # Detect client-side tools
    if "ClientProxy" in tool_type or "AGUI" in tool_type:
        print("⚠️  CLIENT-SIDE TOOL DETECTED (AGUIToolset)")
        print("     This tool will execute on the frontend")
        print("     Events will be sent via SSE to CopilotKit")
```

---

## How Backend Updates Reach Frontend

### Complete Flow: `update_deal` → Frontend Update

```
┌─────────────────────────────────────────────────────────────────┐
│ STEP 1: LLM Decides to Call update_deal                        │
└───────────────────────┬─────────────────────────────────────────┘
                        ▼
┌─────────────────────────────────────────────────────────────────┐
│ STEP 2: Tool Execution                                          │
│                                                                   │
│   update_deal(tool_context, segment="Analytics...", ...)        │
│   ├─ Reads: tool_context.state.get("deal")                      │
│   ├─ Merges: Updates deal dictionary                            │
│   └─ Writes: tool_context.state["deal"] = updated_deal           │
└───────────────────────┬─────────────────────────────────────────┘
                        ▼
┌─────────────────────────────────────────────────────────────────┐
│ STEP 3: ADK Captures State Change                               │
│                                                                   │
│   Event.actions.state_delta = {                                  │
│       "deal": {                                                  │
│           "segment": "Analytics and Artificial Intelligence",    │
│           "estimated_value": "$3M",                              │
│           ...                                                    │
│       }                                                          │
│   }                                                              │
└───────────────────────┬─────────────────────────────────────────┘
                        ▼
┌─────────────────────────────────────────────────────────────────┐
│ STEP 4: SessionService Processes Event                          │
│                                                                   │
│   session.state.update(event.actions.state_delta)               │
│   ├─ Merges delta into session.state                            │
│   └─ Persists to database (if DatabaseSessionService)           │
└───────────────────────┬─────────────────────────────────────────┘
                        ▼
┌─────────────────────────────────────────────────────────────────┐
│ STEP 5: EventTranslator Converts to AG-UI Event                 │
│                                                                   │
│   EventTranslator.translate(adk_event, session)                 │
│   ├─ Detects: event.actions.state_delta exists                  │
│   ├─ Creates: StateDeltaEvent                                   │
│   └─ Formats: JSON with op="add", path="/deal", value={...}    │
└───────────────────────┬─────────────────────────────────────────┘
                        ▼
┌─────────────────────────────────────────────────────────────────┐
│ STEP 6: SSE Stream Sends Event                                  │
│                                                                   │
│   data: {                                                        │
│       "type": "STATE_DELTA",                                    │
│       "delta": [{                                                │
│           "op": "add",                                           │
│           "path": "/deal",                                       │
│           "value": {                                             │
│               "segment": "Analytics...",                        │
│               "estimated_value": "$3M",                         │
│               ...                                                │
│           }                                                      │
│       }]                                                         │
│   }                                                              │
└───────────────────────┬─────────────────────────────────────────┘
                        ▼
┌─────────────────────────────────────────────────────────────────┐
│ STEP 7: CopilotKit Runtime Receives Event                       │
│                                                                   │
│   runtime.onEvent((event) => {                                  │
│       if (event.type === 'STATE_DELTA') {                        │
│           dispatchStateDelta(event.delta);                       │
│       }                                                          │
│   });                                                            │
└───────────────────────┬─────────────────────────────────────────┘
                        ▼
┌─────────────────────────────────────────────────────────────────┐
│ STEP 8: useCoAgent Hook Updates State                           │
│                                                                   │
│   useEffect(() => {                                              │
│       const unsubscribe = runtime.subscribe(                     │
│           "deal_builder",                                        │
│           (event) => {                                            │
│               if (event.type === 'STATE_DELTA') {                │
│                   setAgentState(prev =>                          │
│                       mergeState(prev, event.delta)              │
│                   );                                             │
│               }                                                  │
│           }                                                      │
│       );                                                         │
│       return unsubscribe;                                        │
│   }, []);                                                        │
└───────────────────────┬─────────────────────────────────────────┘
                        ▼
┌─────────────────────────────────────────────────────────────────┐
│ STEP 9: React useEffect Syncs to Local State                    │
│                                                                   │
│   useEffect(() => {                                              │
│       if (agentState?.deal) {                                    │
│           setDeal({                                              │
│               customer_name: agentState.deal.customer_name,     │
│               segment: agentState.deal.segment,  ← Updated      │
│               estimated_value: agentState.deal.estimated_value, ← Updated
│               ...                                                │
│           });                                                    │
│       }                                                          │
│   }, [agentState?.deal]);                                       │
└───────────────────────┬─────────────────────────────────────────┘
                        ▼
┌─────────────────────────────────────────────────────────────────┐
│ STEP 10: UI Re-renders with Updated State                       │
│                                                                   │
│   <input value={deal.segment} />  ← Shows "Analytics..."       │
│   <input value={deal.estimated_value} />  ← Shows "$3M"         │
└─────────────────────────────────────────────────────────────────┘
```

---

## Complete Flow Diagram

### Detailed Component Interaction

```
┌──────────────────────────────────────────────────────────────────────┐
│                         BACKEND (Python)                             │
├──────────────────────────────────────────────────────────────────────┤
│                                                                       │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │ LlmAgent (deal_builder)                                      │   │
│  │                                                               │   │
│  │  ┌──────────────────────────────────────────────────────┐    │   │
│  │  │ after_model_callback                                 │    │   │
│  │  │ - Detects function_call: update_deal                 │    │   │
│  │  └───────────────────────┬──────────────────────────────┘    │   │
│  │                          ▼                                    │   │
│  │  ┌──────────────────────────────────────────────────────┐    │   │
│  │  │ before_tool_callback                                 │    │   │
│  │  │ - Logs tool call                                     │    │   │
│  │  └───────────────────────┬────────────────────────────────┘    │   │
│  │                          ▼                                    │   │
│  │  ┌──────────────────────────────────────────────────────┐    │   │
│  │  │ update_deal(tool_context, ...)                       │    │   │
│  │  │                                                       │    │   │
│  │  │ 1. current = tool_context.state.get("deal")         │    │   │
│  │  │ 2. Merge updates into current                       │    │   │
│  │  │ 3. tool_context.state["deal"] = current  ← KEY     │    │   │
│  │  └───────────────────────┬──────────────────────────────┘    │   │
│  │                          ▼                                    │   │
│  │  ┌──────────────────────────────────────────────────────┐    │   │
│  │  │ after_tool_callback                                 │    │   │
│  │  │ - Detects state change                              │    │   │
│  │  └───────────────────────┬──────────────────────────────┘    │   │
│  └──────────────────────────┼────────────────────────────────────┘   │
│                             ▼                                        │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │ ADK Runner                                                    │   │
│  │                                                               │   │
│  │  Creates Event with:                                         │   │
│  │  ┌──────────────────────────────────────────────────────┐   │   │
│  │  │ Event.actions.state_delta = {                        │   │   │
│  │  │     "deal": {                                        │   │   │
│  │  │         "segment": "Analytics...",                   │   │   │
│  │  │         "estimated_value": "$3M",                    │   │   │
│  │  │         ...                                          │   │   │
│  │  │     }                                                │   │   │
│  │  │ }                                                    │   │   │
│  │  └───────────────────────┬──────────────────────────────┘   │   │
│  └──────────────────────────┼────────────────────────────────────┘   │
│                             ▼                                        │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │ SessionService                                                │   │
│  │                                                               │   │
│  │  session.state.update(event.actions.state_delta)            │   │
│  │  ├─ Merges delta into session.state                         │   │
│  │  └─ Persists to database                                     │   │
│  └───────────────────────┬───────────────────────────────────────┘   │
│                          ▼                                           │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │ EventTranslator (ag_ui_adk)                                  │   │
│  │                                                               │   │
│  │  translate(adk_event, session)                              │   │
│  │  ├─ Detects: event.actions.state_delta                      │   │
│  │  ├─ Creates: StateDeltaEvent                                │   │
│  │  └─ Formats: JSON with op, path, value                      │   │
│  └───────────────────────┬───────────────────────────────────────┘   │
│                          ▼                                           │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │ ADKAgent.run()                                               │   │
│  │                                                               │   │
│  │  async for event in runner.run_async(...):                  │   │
│  │      ag_ui_events = event_translator.translate(event)       │   │
│  │      for ag_ui_event in ag_ui_events:                       │   │
│  │          yield ag_ui_event  ← SSE Stream                    │   │
│  └───────────────────────┬───────────────────────────────────────┘   │
└──────────────────────────┼───────────────────────────────────────────┘
                           │
                           │ SSE Stream (Server-Sent Events)
                           │
                           ▼
┌──────────────────────────────────────────────────────────────────────┐
│                    MIDDLEWARE (Next.js API Route)                    │
├──────────────────────────────────────────────────────────────────────┤
│                                                                       │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │ CopilotRuntime                                                │   │
│  │                                                               │   │
│  │  - Receives SSE events                                       │   │
│  │  - Dispatches to subscribers                                │   │
│  └───────────────────────┬───────────────────────────────────────┘   │
└──────────────────────────┼───────────────────────────────────────────┘
                           │
                           │ Event Dispatch
                           │
                           ▼
┌──────────────────────────────────────────────────────────────────────┐
│                      FRONTEND (React)                                 │
├──────────────────────────────────────────────────────────────────────┤
│                                                                       │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │ useCoAgent Hook                                                │   │
│  │                                                               │   │
│  │  useEffect(() => {                                            │   │
│  │      runtime.subscribe("deal_builder", (event) => {          │   │
│  │          if (event.type === 'STATE_DELTA') {                 │   │
│  │              setAgentState(prev =>                            │   │
│  │                  mergeState(prev, event.delta)                │   │
│  │              );                                               │   │
│  │          }                                                    │   │
│  │      });                                                      │   │
│  │  }, []);                                                      │   │
│  └───────────────────────┬───────────────────────────────────────┘   │
│                          ▼                                           │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │ React Component (DealForm)                                    │   │
│  │                                                               │   │
│  │  useEffect(() => {                                            │   │
│  │      if (agentState?.deal) {                                  │   │
│  │          setDeal({                                            │   │
│  │              segment: agentState.deal.segment,  ← Updated    │   │
│  │              estimated_value: agentState.deal.estimated_value,│   │
│  │              ...                                              │   │
│  │          });                                                  │   │
│  │      }                                                        │   │
│  │  }, [agentState?.deal]);                                     │   │
│  └───────────────────────┬───────────────────────────────────────┘   │
│                          ▼                                           │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │ UI Re-renders                                                 │   │
│  │                                                               │   │
│  │  <input value={deal.segment} />                              │   │
│  │  <input value={deal.estimated_value} />                      │   │
│  └──────────────────────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────────────────────────┘
```

---

## Code Examples

### Backend: `update_deal` Function

```python
def update_deal(
    tool_context: ToolContext,
    customer_name: str = "",
    segment: str = "",
    products: List[str] = None,
    estimated_value: str = "",
    stage: str = "",
    next_steps: List[str] = None,
    changes: str = "",
) -> Dict[str, str]:
    """Update the current deal."""
    if products is None:
        products = []
    if next_steps is None:
        next_steps = []
    
    # Build update object
    deal = {
        "customer_name": customer_name or "",
        "segment": segment or "",
        "products": products,
        "estimated_value": estimated_value or "",
        "stage": stage or "",
        "next_steps": next_steps,
        "changes": changes or "",
    }
    
    # Get current deal and merge
    current = dict(tool_context.state.get("deal") or {})
    for k, v in deal.items():
        if k in ("products", "next_steps"):
            if v:
                current[k] = list(v)
        elif v is not None and v != "":
            current[k] = v
    
    # CRITICAL: Update state (triggers state_delta event)
    tool_context.state["deal"] = current
    
    return {"status": "success", "message": "Deal updated successfully"}
```

### Backend: Tool Registration

```python
from ag_ui_adk import AGUIToolset
from google.adk.tools import FunctionTool

# Create FunctionTool wrapper
update_deal_tool = FunctionTool(update_deal)

# Build tools list
_tools = [
    update_deal_tool,
    generate_proposal_tool,
    search_agent_tool
]

# Add AGUIToolset for client-side tools
if AGUIToolset is not None:
    _tools.insert(0, AGUIToolset())

# Create agent with tools
deal_builder_agent = LlmAgent(
    name="deal_builder",
    tools=_tools,
    ...
)
```

### Frontend: State Synchronization

```typescript
// Frontend: app/deal/page.tsx
import { useCoAgent } from "@copilotkit/react-core";

function DealForm() {
  // 1. Agent state (synced with backend)
  const { state: agentState, setState: setAgentState } = useCoAgent<AgentState>({
    name: "deal_builder",
    initialState: {
      deal: INITIAL_DEAL,
      proposal: INITIAL_PROPOSAL,
    },
  });
  
  // 2. Local React state (for UI)
  const [deal, setDeal] = useState<DealState>(INITIAL_DEAL);
  
  // 3. Sync from agent state to local state
  useEffect(() => {
    if (agentState?.deal) {
      const d = agentState.deal;
      setDeal({
        customer_name: d.customer_name ?? "",
        segment: d.segment ?? "",  // ← Updated from backend
        products: Array.isArray(d.products) ? d.products : [],
        estimated_value: d.estimated_value ?? "",  // ← Updated from backend
        stage: d.stage ?? "Discovery",
        next_steps: Array.isArray(d.next_steps) ? d.next_steps : [],
        changes: d.changes ?? "",
      });
    }
  }, [agentState?.deal]);
  
  // 4. Render UI
  return (
    <div>
      <input
        value={deal.segment}  // ← Shows updated value
        onChange={(e) => updateDeal({ segment: e.target.value })}
      />
      <input
        value={deal.estimated_value}  // ← Shows updated value
        onChange={(e) => updateDeal({ estimated_value: e.target.value })}
      />
    </div>
  );
}
```

### Frontend: Client-Side Tool Registration (AGUI)

```typescript
// Frontend: Register a client-side tool
import { useCopilotAction } from "@copilotkit/react-core";

function DealForm() {
  // Register tool that executes on frontend
  useCopilotAction({
    name: "highlight_deal_field",
    description: "Highlight a specific deal field in the UI",
    parameters: [
      {
        name: "field_name",
        type: "string",
        description: "Name of the field to highlight"
      }
    ],
    handler: async ({ field_name }) => {
      // Execute on frontend
      highlightField(field_name);
      return { status: "success" };
    }
  });
}
```

---

## Key Takeaways

1. **`update_deal` is a backend tool** that modifies `tool_context.state["deal"]`
2. **State changes are automatic**: ADK captures changes in `Event.actions.state_delta`
3. **EventTranslator converts** ADK events to AG-UI protocol events
4. **SSE stream sends** events to frontend in real-time
5. **useCoAgent hook** receives events and updates `agentState`
6. **React syncs** `agentState` to local component state
7. **UI re-renders** with updated values

### AGUI Tools vs Backend Tools

| Feature | Backend Tools | AGUI Tools (Client-Side) |
|---------|--------------|-------------------------|
| Execution Location | Backend server | Frontend browser |
| State Access | `tool_context.state` | Frontend state/UI |
| Registration | `FunctionTool(function)` | `useCopilotAction()` |
| Toolset | Direct function | `AGUIToolset()` |
| Use Case | Data processing, state updates | UI interactions, frontend-only ops |

### State Update Latency

- **Backend tool execution**: ~100-200ms
- **Event processing**: ~10-50ms
- **SSE transmission**: ~50-100ms
- **Frontend processing**: ~10-20ms
- **Total**: ~170-370ms from tool execution to UI update

---

## Summary

The `update_deal` function is a simple but powerful tool that:
1. Takes parameters from the LLM
2. Merges them into the current deal state
3. Updates `tool_context.state["deal"]`
4. Automatically triggers a state synchronization flow that updates the frontend UI in real-time

The entire process is **automatic** - you just modify `tool_context.state`, and ADK + AG-UI protocol + CopilotKit handle the rest!
