---
title: callback_plugin_agent_full_demo.py - Code Walkthrough
markmap:
  colorFreezeLevel: 2
---

# callback_plugin_agent_full_demo.py

## Overview
- **Purpose**: Demonstrates ALL Plugin + Agent callbacks with SQLite cache and sensitive data detection
- **Key features**: Plugin runs first, Agent runs after, Cache short-circuits LLM, Sensitive data skips agent
- **Run**: `GEMINI_MODEL=gemini-2.5-flash uv run python callback_plugin_agent_full_demo.py`

---

## 1. Configuration & Constants

### Globals
- `APP_NAME` = "callback_plugin_agent_full_demo"
- `GEMINI_MODEL` from env (default: gemini-2.5-flash)
- `DB_PATH` = `llm_cache.db` (SQLite)
- `_cache_key_by_session` = dict (pass cache key between before_model and after_model)

### Regex Patterns
- `NPI_PATTERN` = `\b(\d{10})\b` (10-digit National Provider Identifier)
- `PCI_PATTERN` = credit card (4 groups of 4 digits, optional spaces/dashes)

---

## 2. Helper Functions

### Sensitive Data
- `_has_sensitive_data(text)` → bool
  - Returns True if NPI or valid PCI (13–19 digits) found
  - Used in `on_user_message_callback`

### Content Extraction
- `_get_text_from_content(c)` → str
  - Extracts text from `Content.parts`
- `_extract_text_from_response(llm_response)` → str
  - Gets text from `LlmResponse.content`
- `_make_cache_key(llm_request)` → str
  - SHA256 hash of `role:text` for each content in request
  - First 32 chars used as cache key

### Cache
- `_build_cached_response(text)` → LlmResponse
  - Constructs `LlmResponse(content=Content(role="model", parts=[Part(text=text)]))`
  - Used when returning cached or fallback response

### SQLite
- `init_cache_db()` → Creates `llm_cache` table
  - Columns: `cache_key` (PK), `response_text`, `created_at`

---

## 3. FullDemoPlugin (extends BasePlugin)

### Purpose
- Logs every callback point
- Detects sensitive data (on_user_message)
- Skips agent when sensitive data (before_agent)
- Error fallbacks (on_model_error, on_tool_error)

### Callbacks Implemented

#### on_user_message_callback
- **Input**: `invocation_context`, `user_message`
- **Logic**: Extract text → if `_has_sensitive_data()` → set `session.state["sensitive_data_detected"] = True`
- **Return**: None (proceed)
- **Log**: "User message received", "*** SENSITIVE DATA DETECTED ***" if found

#### before_run_callback
- **Input**: `invocation_context`
- **Logic**: Log
- **Return**: None
- **Log**: "Runner starting"

#### after_run_callback
- **Input**: `invocation_context`
- **Logic**: Log
- **Return**: None
- **Log**: "Runner finished"

#### before_agent_callback
- **Input**: `agent`, `callback_context`
- **Logic**: If `state.get("sensitive_data_detected")` → return `Content` with warning message (SHORT-CIRCUIT)
- **Return**: Content (skip) or None (proceed)
- **Log**: "Agent 'X' about to run", "Skipping agent - sensitive data" if skip

#### after_agent_callback
- **Input**: `agent`, `callback_context`
- **Logic**: Log
- **Return**: None
- **Log**: "Agent 'X' finished"

#### before_model_callback
- **Input**: `callback_context`, `llm_request`
- **Logic**: Log only (CachePlugin handles cache)
- **Return**: None
- **Log**: "Before LLM call"

#### after_model_callback
- **Input**: `callback_context`, `llm_response`
- **Logic**: Log only
- **Return**: None
- **Log**: "After LLM call"

#### on_model_error_callback
- **Input**: `callback_context`, `llm_request`, `error`
- **Logic**: Return fallback `LlmResponse` to suppress exception
- **Return**: `_build_cached_response("[Fallback] Model error: ...")`
- **Log**: "Model error: {error}"

#### before_tool_callback
- **Input**: `tool`, `tool_args`, `tool_context`
- **Logic**: Log
- **Return**: None
- **Log**: "Tool 'X' about to run, args={...}"

#### after_tool_callback
- **Input**: `tool`, `tool_args`, `tool_context`, `result`
- **Logic**: Log
- **Return**: None
- **Log**: "Tool 'X' finished, result={...}"

#### on_tool_error_callback
- **Input**: `tool`, `tool_args`, `tool_context`, `error`
- **Logic**: Return fallback dict to suppress exception
- **Return**: `{"error": str(error), "fallback": True}`
- **Log**: "Tool 'X' error: {error}"

#### on_event_callback
- **Input**: `invocation_context`, `event`
- **Logic**: Log
- **Return**: None
- **Log**: "Event from {author}"

---

## 4. CachePlugin (extends BasePlugin)

### Purpose
- Cache LLM responses in SQLite
- Key = hash of `llm_request.contents`
- before_model: check cache, return cached LlmResponse if hit
- after_model: store response in cache on miss (only final text, not function_call)

### before_model_callback
- **Input**: `callback_context`, `llm_request`
- **Logic**:
  1. `cache_key = _make_cache_key(llm_request)`
  2. Store key in `_cache_key_by_session[session_id]`
  3. Query SQLite: `SELECT response_text WHERE cache_key = ?`
  4. If row found → return `_build_cached_response(row[0])` (SKIP LLM)
- **Return**: LlmResponse (cache hit) or None (cache miss)

### after_model_callback
- **Input**: `callback_context`, `llm_response`
- **Logic**:
  1. `cache_key = _cache_key_by_session.pop(session_id)`
  2. Extract text from response
  3. Skip if response has `function_call` (intermediate, not final)
  4. If text and no function_call → `INSERT OR REPLACE INTO llm_cache`
- **Return**: None

---

## 5. Tool: get_current_time

### Definition
- **Function**: `get_current_time(tool_context: ToolContext) -> Dict[str, str]`
- **Docstring**: "Returns current date and time. Call when user asks about time or date."
- **Returns**: `{current_time, current_date, timezone}`
- **Wrapper**: `FunctionTool(get_current_time)` → `get_current_time_tool`

---

## 6. Agent Callbacks (standalone functions)

### Registered on Agent
- `agent_before_agent(callback_context)` → None, log
- `agent_after_agent(callback_context)` → None, log
- `agent_before_model(callback_context, llm_request)` → None, log
- `agent_after_model(callback_context, llm_response)` → None, log
- `agent_before_tool(tool, args, tool_context)` → None, log
- `agent_after_tool(tool, args, tool_context, tool_response)` → None, log

### Execution Order
- Plugin callback runs **first**
- Agent callback runs **second** (unless Plugin returned value and short-circuited)

---

## 7. root_agent

### Configuration
- **name**: full_demo_agent
- **model**: GEMINI_MODEL (gemini-2.5-flash)
- **description**: "Helpful assistant - tells time."
- **instruction**: "You are helpful. Use get_current_time when asked about time. Be concise."
- **tools**: [get_current_time_tool]
- **callbacks**: All 6 agent callbacks attached

---

## 8. Main Flow (main())

### Setup
1. `init_cache_db()` → create llm_cache table
2. Open output file `callback_plugin_agent_full_demo_output_{timestamp}.txt`
3. Tee stdout/stderr to file
4. Create `FullDemoPlugin()` and `CachePlugin()`
5. Create `Runner(agent=root_agent, plugins=[full_plugin, cache_plugin], ...)`
6. Create session `full_demo_{timestamp}`

### Test 1: Normal Question
- **Message**: "What time is it right now?"
- **Flow**:
  - on_user_message → no sensitive data
  - before_run, before_agent → proceed
  - before_model → cache miss (FullDemoPlugin logs, CachePlugin checks)
  - LLM returns function_call → get_current_time
  - before_tool, tool runs, after_tool
  - before_model (2nd) → cache miss
  - LLM returns text
  - after_model → CachePlugin stores in SQLite
  - after_agent, after_run
- **Output**: "The current time is 07:34:46 on 2026-02-12."

### Test 2: Same Question (Cache Hit)
- **Session**: New session `full_demo_cache_{timestamp}`
- **Message**: Same "What time is it right now?"
- **Flow**:
  - Same prompt → same cache_key
  - before_model (2nd call, after tool) → CachePlugin CACHE HIT
  - Returns cached LlmResponse → LLM NOT called
  - Agent model callbacks SKIPPED (Plugin returned value)
- **Output**: Cached time from Test 1

### Test 3: Sensitive Data
- **Message**: "My NPI is 1234567890 and my card is 4111 1111 1111 1111. Help me."
- **Flow**:
  - on_user_message → `_has_sensitive_data()` True → `state["sensitive_data_detected"] = True`
  - before_run → proceed
  - before_agent (Plugin) → checks state → returns Content (SHORT-CIRCUIT)
  - Agent callbacks SKIPPED, Agent logic SKIPPED, Model SKIPPED, Tool SKIPPED
  - on_event (Plugin) → Event with returned Content
  - after_run → done
- **Output**: "Your message contains sensitive data (NPI or credit card detected). Please rephrase without sharing such information."

---

## 9. TeeOutput Class

- **Purpose**: Write to both console and file
- **Methods**: `write(msg)`, `flush()`
- **Usage**: `sys.stdout = TeeOutput(file_handle, sys.stdout)`

---

## 10. Data Flow Diagram (Conceptual)

```
User Message
    ↓
on_user_message (Plugin) ──► [sensitive?] → state
    ↓
before_run (Plugin)
    ↓
before_agent (Plugin) ──► [sensitive?] → return Content → DONE
    ↓
before_agent (Agent)
    ↓
before_model (Plugin)
before_model (CachePlugin) ──► [cache hit?] → return LlmResponse → skip LLM
    ↓
before_model (Agent)
    ↓
LLM call (or cached)
    ↓
after_model (Plugin)
after_model (CachePlugin) ──► [no function_call?] → INSERT cache
    ↓
after_model (Agent)
    ↓
[if function_call] before_tool → tool → after_tool
    ↓
on_event (Plugin) [per event]
    ↓
after_agent (Plugin)
after_agent (Agent)
    ↓
after_run (Plugin)
    ↓
Events to client
```

---

## 11. File Outputs

- **Log**: `callback_plugin_agent_full_demo_output_{timestamp}.txt`
- **Cache DB**: `llm_cache.db` (table: llm_cache)
