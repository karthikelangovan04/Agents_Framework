# Plugins vs Agent Callbacks: Comparison and Execution Order

This document compares **Plugin-level callbacks**, **Agent-level callbacks**, and **Runner/User-level hooks** in ADK. It explains how they differ, how they are executed, and when to use each.

**Sources:** [Plugins docs](https://google.github.io/adk-docs/plugins/#plugin-callback-hooks), [Callbacks docs](https://google.github.io/adk-docs/callbacks/), `docs/plugins/index.md`, `docs/callbacks/`.

---

## 1. Overview: Three Levels of Callbacks

| Level | Where Configured | Scope | Callback Hooks |
|-------|------------------|-------|----------------|
| **Plugin** | `Runner(plugins=[...])` | Global (all agents/tools/LLMs) | User, Runner, Agent, Model, Tool, Event |
| **Agent** | `Agent(before_agent_callback=...)` | Local (single agent) | Agent, Model, Tool only |
| **Runner/User** | Plugins only | Runner boundary | `on_user_message`, `before_run`, `after_run` |

---

## 2. Plugin vs Agent Callbacks

### Plugins

- **Scope:** Global. Registered once on the `Runner`; apply to **every** Agent, Model, and Tool managed by that runner.
- **Configuration:** `Runner(agent=..., plugins=[CountPlugin(), LoggingPlugin()])`
- **Use case:** Cross-cutting concerns (logging, security, caching, metrics, policy enforcement).
- **Execution:** Plugin callbacks run **first** (before Agent callbacks).

### Agent Callbacks (Normal Callbacks)

- **Scope:** Local. Configured on a **specific** `BaseAgent` instance; apply only to that agent (and its tools/LLM).
- **Configuration:** `Agent(before_model_callback=my_fn, after_tool_callback=...)` (see `callback_exploration.py`).
- **Use case:** Agent-specific logic (modify prompts, handle tool results, agent-specific guardrails).
- **Execution:** Agent callbacks run **after** Plugin callbacks.

### Comparison Table (from ADK docs)

| | **Plugins** | **Agent Callbacks** |
|--|-------------|---------------------|
| **Scope** | **Global**: All agents/tools/LLMs in the Runner | **Local**: Only the specific agent |
| **Primary Use Case** | Logging, policy, monitoring, caching | Agent-specific behavior and state |
| **Configuration** | Once on `Runner` | Per `BaseAgent` instance |
| **Execution Order** | Run **before** Agent Callbacks | Run **after** Plugin callbacks |

---

## 3. Execution Order and Precedence

### Rule 1: Plugins Run First

For any given event (e.g., before model call), the flow is:

```
1. Plugin before_model_callback  ← runs first
2. Agent before_model_callback   ← runs second (if Plugin returns None)
```

### Rule 2: Returning a Value Short-Circuits

- If a **Plugin** callback returns a non-`None` value (e.g., `LlmResponse`), the **Agent** callback is **skipped**.
- The Runner treats the Plugin’s return value as the result and does not run the underlying action (e.g., no actual LLM call).

Example:

```
Plugin before_model_callback returns cached LlmResponse
  → Agent before_model_callback is SKIPPED
  → LLM is NOT called
```

### Rule 3: Full Execution Order (Single User Message)

For one user message, the typical order is:

```
Runner receives user message
  │
  ├─ on_user_message_callback (Plugin only)
  ├─ before_run_callback (Plugin only)
  │
  ├─ before_agent_callback (Plugin) → before_agent_callback (Agent)
  │     └─ Agent main logic starts
  │         │
  │         ├─ before_model_callback (Plugin) → before_model_callback (Agent)
  │         │     └─ LLM call (or skipped if callback returned LlmResponse)
  │         ├─ after_model_callback (Plugin)  → after_model_callback (Agent)
  │         │
  │         ├─ [if tool called]
  │         │   ├─ before_tool_callback (Plugin) → before_tool_callback (Agent)
  │         │   │     └─ Tool execution
  │         │   └─ after_tool_callback (Plugin)  → after_tool_callback (Agent)
  │         │
  │         ├─ [on_event_callback (Plugin) – for each Event]
  │         │
  │         └─ [repeat model/tool as needed]
  │
  ├─ after_agent_callback (Plugin) → after_agent_callback (Agent)
  │
  └─ after_run_callback (Plugin only)
```

---

## 4. Plugin Hook Categories

### 4.1 Runner/User-Level Hooks (Plugin Only)

These exist **only** in Plugins, not in Agent callbacks.

| Hook | When | Purpose |
|------|------|---------|
| `on_user_message_callback` | Right after `runner.run()`, before other processing | Inspect or replace user input |
| `before_run_callback` | Before any agent logic | Global setup before run |
| `after_run_callback` | After Runner finishes | Cleanup, final metrics, logs |

### 4.2 Agent-Level Hooks

Available in **Plugins** and **Agent callbacks**:

| Hook | Plugin | Agent | When |
|------|--------|-------|------|
| `before_agent_callback` | ✓ | ✓ | Before agent’s main work |
| `after_agent_callback` | ✓ | ✓ | After agent finishes |

### 4.3 Model-Level Hooks

| Hook | Plugin | Agent | When |
|------|--------|-------|------|
| `before_model_callback` | ✓ | ✓ | Before LLM call |
| `after_model_callback` | ✓ | ✓ | After LLM returns |
| `on_model_error_callback` | ✓ | ✗ | On model exception (Plugin only) |

### 4.4 Tool-Level Hooks

| Hook | Plugin | Agent | When |
|------|--------|-------|------|
| `before_tool_callback` | ✓ | ✓ | Before tool runs |
| `after_tool_callback` | ✓ | ✓ | After tool returns |
| `on_tool_error_callback` | ✓ | ✗ | On tool exception (Plugin only) |

### 4.5 Event Hook (Plugin Only)

| Hook | When |
|------|------|
| `on_event_callback` | After agent yields an Event, before it’s streamed to the client |

---

## 5. Code Reference: Agent Callbacks

In `callback_exploration.py`, Agent callbacks are configured as:

```python
root_agent = Agent(
    name="callback_exploration_agent",
    model=GEMINI_MODEL,
    instruction="...",
    tools=[get_current_time_tool],
    before_agent_callback=before_agent_callback,
    after_agent_callback=after_agent_callback,
    before_model_callback=before_model_callback,
    after_model_callback=after_model_callback,
    before_tool_callback=before_tool_callback,
    after_tool_callback=after_tool_callback,
)
```

These are **Agent-level** callbacks: they run only for this agent, and only **after** any Plugin callbacks for the same hook.

---

## 6. When to Use What

| Scenario | Use |
|----------|-----|
| Logging, metrics, tracing across all agents | **Plugin** |
| Security/policy (guardrails, auth) for the whole app | **Plugin** |
| Caching at request/response level | **Plugin** |
| Error handling for model/tool failures | **Plugin** (`on_model_error`, `on_tool_error`) |
| Inspect/modify user message before any agent | **Plugin** (`on_user_message`) |
| Agent-specific prompt changes | **Agent callback** |
| Agent-specific tool result handling | **Agent callback** |
| Per-agent guardrails or logic | **Agent callback** |

---

## 7. Return Value Behavior

### Observe (return `None`)

- Workflow continues normally.
- Use for logging, metrics, non-invasive checks.

### Intervene (return specific object)

- Short-circuits the step.
- Plugin return value skips Agent callback and the underlying action.

| Callback | Return to skip/replace |
|----------|------------------------|
| `before_agent` | `types.Content` |
| `before_model` | `LlmResponse` |
| `before_tool` | `dict` |
| `after_agent` | `types.Content` |
| `after_model` | `LlmResponse` |
| `after_tool` | `dict` |

### Amend (mutate context)

- Modify context (e.g., `llm_request`) in place.
- Do **not** return a value to skip; workflow continues with updated context.

---

## 8. References

- [Plugins - Plugin callback hooks](https://google.github.io/adk-docs/plugins/#plugin-callback-hooks)
- [Callbacks](https://google.github.io/adk-docs/callbacks/)
- `adk_explore_callback/docs/plugins/index.md`
- `adk_explore_callback/docs/callbacks/index.md`
- `adk_explore_callback/docs/callbacks/types-of-callbacks.md`
- `adk_explore_callback/callback_exploration.py`
