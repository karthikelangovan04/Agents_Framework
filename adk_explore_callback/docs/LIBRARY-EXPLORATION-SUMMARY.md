# Library Exploration Summary: ADK Callbacks

How I explored the google-adk package to understand callback signatures and behavior. Use this for reference in future chats.

---

## What I Did

### 1. Located the ADK Package Path

```bash
cd adk_explore_callback && uv run python -c "
import google.adk
p = google.adk.__path__[0]
print('ADK path:', p)
"
# Output: ADK path: .../adk_explore_callback/.venv/lib/python3.13/site-packages/google/adk
```

```bash
ls -la "$(uv run python -c 'import google.adk; print(google.adk.__path__[0])')/agents/"
```

Key files in `google/adk/agents/`:
- `base_agent.py` – Base agent, before/after agent callbacks
- `llm_agent.py` – LlmAgent, model and tool callbacks
- `callback_context.py` – `CallbackContext` definition
- `invocation_context.py` – InvocationContext
- `base_agent_config.py` – YAML config schema

### 2. Read the Type Aliases in `llm_agent.py`

`llm_agent.py` defines callback types (lines 66–124):

- **BeforeModelCallback:** `(CallbackContext, LlmRequest) -> Optional[LlmResponse]`
- **AfterModelCallback:** `(CallbackContext, LlmResponse) -> Optional[LlmResponse]`
- **BeforeToolCallback:** `(BaseTool, dict[str, Any], ToolContext) -> Optional[dict]`
- **AfterToolCallback:** `(BaseTool, dict[str, Any], ToolContext, dict) -> Optional[dict]`

### 3. Read `base_agent.py` for Agent Callbacks

- **BeforeAgentCallback / AfterAgentCallback:** `(CallbackContext) -> Optional[types.Content]`

### 4. Read `callback_context.py`

- `CallbackContext` extends `ReadonlyContext`
- Provides `state`, `session`, `load_artifact`, `save_artifact`, `add_session_to_memory`, etc.
- Access to invocation context via `_invocation_context`

### 5. Checked Actual Invocation (Runtime Error)

When the script ran, `after_tool_callback` failed because the framework passes `tool_response` as the fourth positional argument, but I had used `tool_result`. That confirmed the parameter name is `tool_response`.

---

## Summary of What I Learnt

### Callback Signatures (Python ADK)

| Callback | Parameters | Return Type |
|----------|------------|-------------|
| before_agent | `callback_context: CallbackContext` | `Optional[types.Content]` |
| after_agent | `callback_context: CallbackContext` | `Optional[types.Content]` |
| before_model | `callback_context: CallbackContext`, `llm_request: LlmRequest` | `Optional[LlmResponse]` |
| after_model | `callback_context: CallbackContext`, `llm_response: LlmResponse` | `Optional[LlmResponse]` |
| before_tool | `tool: BaseTool`, `args: dict`, `tool_context: ToolContext` | `Optional[dict]` |
| after_tool | `tool: BaseTool`, `args: dict`, `tool_context: ToolContext`, `tool_response: dict` | `Optional[dict]` |

### Notes

1. **Tool callbacks** use `ToolContext`, not `CallbackContext`. `ToolContext` gives access to tool-specific data (e.g. `tool_name`).
2. **Model callbacks** use `CallbackContext`. They receive either the request or the response.
3. **Agent callbacks** use `CallbackContext` only; the agent’s output is produced during the run, not passed in.
4. **Return values:**
   - `None` → proceed with default behavior
   - Specific value (e.g. `LlmResponse`, `Content`, `dict`) → override/skip that step

### File Layout (Reference)

```
google/adk/
├── agents/
│   ├── base_agent.py        # Agent callbacks
│   ├── llm_agent.py         # Model & tool callbacks
│   ├── callback_context.py  # CallbackContext
│   └── ...
├── models/
│   ├── llm_request.py
│   └── llm_response.py
├── tools/
│   ├── tool_context.py      # ToolContext
│   └── ...
```

---

## Useful Commands for Future Exploration

```bash
# Package path
uv run python -c "import google.adk; print(google.adk.__path__[0])"

# Inspect Agent callback params
uv run python -c "
from google.adk.agents import Agent
a = Agent(name='t', model='x', instruction='x', before_agent_callback=lambda x: None)
print(hasattr(a, 'before_agent_callback'))
"

# Search for callback types in llm_agent
rg "Callback.*TypeAlias|_Single.*Callback" .venv/lib/python*/site-packages/google/adk/agents/llm_agent.py
```

---

## Related Docs in This Project

- `docs/CALLBACK-SIGNATURES-REFERENCE.md` – Callback signatures for use in code
- `docs/callbacks/` – ADK callbacks docs (from adk-docs)
- `callback_exploration.py` – Runnable script that prints callback arguments
