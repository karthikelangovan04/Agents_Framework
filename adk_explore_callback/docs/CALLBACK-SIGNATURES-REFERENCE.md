# ADK Callback Signatures Reference

Quick reference for what is passed to each callback. Use `callback_exploration.py` to see RAW and FORMATTED output in practice.

## Callback Order in a Single Turn

When the agent runs (e.g., user asks "What time is it?"):

1. **before_agent_callback**
2. **before_model_callback** (LLM receives user message)
3. **after_model_callback** (LLM returns – possibly a function_call)
4. If tool was called:
   - **before_tool_callback**
   - (tool executes)
   - **after_tool_callback**
   - **before_model_callback** (LLM receives tool result, generates final text)
   - **after_model_callback** (LLM returns final text)
5. **after_agent_callback**

---

## Agent Callbacks

### before_agent_callback

```python
def before_agent_callback(callback_context: CallbackContext) -> Optional[types.Content]:
    ...
    return None  # Proceed with agent run
    # OR return Content(...) to skip agent and use as final output
```

**Received:**
- `callback_context`: CallbackContext with `session`, `state`, `agent_name`, etc.

**Return:** `None` to proceed, or `types.Content` to skip agent execution and use as response.

---

### after_agent_callback

```python
def after_agent_callback(callback_context: CallbackContext) -> Optional[types.Content]:
    ...
    return None  # Use agent's output as-is
    # OR return Content(...) to replace agent's output
```

**Received:**
- `callback_context`: CallbackContext (includes session, state)

**Return:** `None` to keep agent output, or `types.Content` to replace it.

---

## Model Callbacks (LlmAgent only)

### before_model_callback

```python
def before_model_callback(
    callback_context: CallbackContext, llm_request: LlmRequest
) -> Optional[LlmResponse]:
    ...
    return None  # Proceed with LLM call
    # OR return LlmResponse(...) to skip LLM call (guardrails, cache)
```

**Received:**
- `callback_context`: CallbackContext
- `llm_request`: LlmRequest with `contents` (list of Content), `config` (system_instruction, tools), `model`

**Return:** `None` to call LLM, or `LlmResponse` to skip the call.

---

### after_model_callback

```python
def after_model_callback(
    callback_context: CallbackContext, llm_response: LlmResponse
) -> Optional[LlmResponse]:
    ...
    return None  # Use LLM response as-is
    # OR return LlmResponse(...) to replace/modify it
```

**Received:**
- `callback_context`: CallbackContext
- `llm_response`: LlmResponse with `content` (role, parts), `usage_metadata`, etc.

**Return:** `None` to use LLM response, or `LlmResponse` to replace it.

---

## Tool Callbacks (LlmAgent with tools)

### before_tool_callback

```python
def before_tool_callback(
    tool: BaseTool, args: Dict[str, Any], tool_context: ToolContext
) -> Optional[Dict[str, Any]]:
    ...
    return None  # Proceed with tool execution
    # OR return dict to skip tool and use as result (validation, cache)
```

**Received:**
- `tool`: The tool instance (e.g., FunctionTool)
- `args`: Arguments passed to the tool (from LLM’s function_call)
- `tool_context`: ToolContext with `state`, `tool_name`, etc.

**Return:** `None` to run the tool, or `dict` to skip execution and use as tool result.

---

### after_tool_callback

```python
def after_tool_callback(
    tool: BaseTool, args: Dict[str, Any], tool_context: ToolContext, tool_response: Dict[str, Any]
) -> Optional[Dict[str, Any]]:
    ...
    return None  # Use tool result as-is
    # OR return dict to replace tool result
```

**Received:**
- `tool`: The tool instance
- `args`: Arguments passed to the tool
- `tool_context`: ToolContext
- `tool_response`: Result returned by the tool

**Return:** `None` to use tool result, or `dict` to replace it.

---

## Run the Exploration Script

```bash
GEMINI_MODEL=gemini-2.5-flash uv run python callback_exploration.py
```

Output is saved to `callback_exploration_output_<timestamp>.txt` with RAW and FORMATTED dumps of all callback arguments.
