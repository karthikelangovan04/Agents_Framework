---
title: ADK Plugin & Agent Callbacks Flow
markmap:
  colorFreezeLevel: 2
---

# ADK: Runner → Agent → Model → Tool

## High-Level Flow

### 1. Runner
- **Entry point** for agent execution
- Receives `user_message`, manages session
- Registers **Plugins** (global scope)
- Orchestrates: Runner callbacks → Agent → Model → Tool
- Emits **Events** to client

### 2. Agent
- **Single agent** (e.g., LlmAgent) with instructions and tools
- Has **Agent callbacks** (local scope)
- Decides: call LLM, call tool, or respond
- Runs `_run_async_impl` (main logic)

### 3. Model
- **LLM** (e.g., Gemini) invoked for generation
- Receives `LlmRequest` (contents, system instruction, tools)
- Returns `LlmResponse` (text, function_call, etc.)
- **Model callbacks** wrap before/after the API call

### 4. Tool
- **Function** or **AgentTool** (e.g., `get_current_time`)
- Executed when LLM returns `function_call`
- Result passed back to LLM as `function_response`
- **Tool callbacks** wrap before/after execution

---

## Plugin vs Agent Callbacks

### Plugin Callbacks (Global, Run First)
- Registered on **Runner**: `Runner(plugins=[...])`
- Apply to **all** agents, tools, LLMs
- **Execution order**: Plugin runs **before** Agent callback
- **Short-circuit**: If Plugin returns value → Agent callback **skipped**

| Hook | When | Purpose |
|------|------|---------|
| `on_user_message` | User sends message | Inspect/modify user input |
| `before_run` | Runner starts | Global setup |
| `after_run` | Runner ends | Cleanup, final logs |
| `before_agent` | Before agent logic | Skip agent if needed |
| `after_agent` | After agent finishes | Post-process |
| `before_model` | Before LLM call | Cache, guardrails |
| `after_model` | After LLM returns | Store cache, sanitize |
| `on_model_error` | Model fails | Fallback response |
| `before_tool` | Before tool runs | Validate args |
| `after_tool` | After tool returns | Log, modify result |
| `on_tool_error` | Tool fails | Fallback dict |
| `on_event` | Each Event yielded | Modify event |

### Agent Callbacks (Local, Run After Plugin)
- Configured on **Agent**: `Agent(before_model_callback=...)`
- Apply to **this agent only**
- **Execution order**: Agent runs **after** Plugin (unless short-circuited)

| Hook | Same as Plugin | Agent-specific logic |
|------|----------------|----------------------|
| `before_agent` | ✓ | Setup state for agent |
| `after_agent` | ✓ | Modify agent output |
| `before_model` | ✓ | Inject instructions |
| `after_model` | ✓ | Format response |
| `before_tool` | ✓ | Validate tool args |
| `after_tool` | ✓ | Save to state |

---

## Execution Order (Single User Message)

```
Runner.run_async(new_message)
  │
  ├─ [Plugin] on_user_message_callback
  ├─ [Plugin] before_run_callback
  │
  ├─ [Plugin] before_agent_callback  ──► if returns Content: SKIP agent
  ├─ [Agent]  before_agent_callback
  │     │
  │     └─ Agent main logic
  │         ├─ [Plugin] before_model_callback  ──► if returns LlmResponse: SKIP LLM
  │         ├─ [Agent]  before_model_callback
  │         │     └─ LLM call (or cached)
  │         ├─ [Plugin] after_model_callback
  │         ├─ [Agent]  after_model_callback
  │         │
  │         ├─ [if function_call]
  │         │   ├─ [Plugin] before_tool_callback  ──► if returns dict: SKIP tool
  │         │   ├─ [Agent]  before_tool_callback
  │         │   │     └─ Tool execution
  │         │   ├─ [Plugin] after_tool_callback
  │         │   └─ [Agent]  after_tool_callback
  │         │
  │         ├─ [Plugin] on_event_callback (per Event)
  │         └─ [repeat model/tool as needed]
  │
  ├─ [Plugin] after_agent_callback
  ├─ [Agent]  after_agent_callback
  │
  └─ [Plugin] after_run_callback
```

---

## Scenario 1: Normal Question ("What time is it?")

1. **on_user_message** → No sensitive data, proceed
2. **before_run** → Log
3. **before_agent** → Proceed
4. **before_agent (Agent)** → Proceed
5. **before_model** → Cache miss
6. **LLM** returns `function_call: get_current_time`
7. **after_model** → (no text, skip cache store)
8. **before_tool** → Log
9. **Tool** runs → `{current_time: "07:34:46", ...}`
10. **after_tool** → Log
11. **before_model** (2nd) → Cache miss
12. **LLM** returns text: "The current time is 07:34:46..."
13. **after_model** → **Cache stored** in SQLite
14. **after_agent** → Done
15. **Response** streamed to user

---

## Scenario 2: Same Question (Cache Hit)

1. **on_user_message** → Proceed
2. **before_run** → Log
3. **before_agent** → Proceed
4. **before_model** → **CACHE HIT** → Return cached `LlmResponse`
5. **Agent model callback** → **SKIPPED** (Plugin returned value)
6. **LLM** → **NOT CALLED**
7. **Response** from cache: "The current time is 07:34:46..."

---

## Scenario 3: Sensitive Data (NPI + PCI) — Complete Flow

### User Message
- "My NPI is 1234567890 and my card is 4111 1111 1111 1111. Help me."

### Step-by-Step

1. **on_user_message_callback (Plugin)**
   - Detects NPI pattern `\b\d{10}\b`
   - Detects PCI pattern (credit card)
   - Sets `session.state["sensitive_data_detected"] = True`
   - Returns `None` → proceed

2. **before_run_callback (Plugin)**
   - Logs "Runner starting"
   - Returns `None`

3. **before_agent_callback (Plugin)**
   - Checks `callback_context.state.get("sensitive_data_detected")`
   - **True** → Returns `Content(role="model", parts=[Part(text="Your message contains sensitive data (NPI or credit card detected). Please rephrase without sharing such information.")])`
   - **Short-circuit**: Agent callbacks and agent logic **SKIPPED**

4. **Agent callbacks** → **NOT RUN**

5. **Model** → **NOT CALLED**

6. **Tool** → **NOT CALLED**

7. **on_event_callback (Plugin)**
   - Event from agent (the returned Content)

8. **after_run_callback (Plugin)**
   - Logs "Runner finished"

### Result
- User receives: *"Your message contains sensitive data (NPI or credit card detected). Please rephrase without sharing such information."*
- No LLM call, no tool call, no agent execution
- **Plugin** intercepts at `before_agent` and returns early

---

## Differentiation Summary

| Scenario | Plugin Intervenes? | Agent Runs? | LLM Called? | Tool Called? |
|----------|--------------------|-------------|-------------|--------------|
| Normal   | No                 | Yes         | Yes         | Yes          |
| Cache Hit| Yes (before_model) | Yes         | No          | No*          |
| Sensitive| Yes (before_agent) | No          | No          | No           |

\* Cache hit returns full response; tool may have been called in earlier turn
