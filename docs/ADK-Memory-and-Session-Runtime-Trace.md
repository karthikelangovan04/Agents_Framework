# Google ADK: Memory and Session Runtime Trace

Implementation trace from installed SDK source (`google.adk` v1.21.0). All paths refer to the package under `site-packages/google/adk/`.

---

## 1. Long-term memory (MemoryService / MemoryBank)

### Classes involved

| Class | File | Role |
|------|------|------|
| `BaseMemoryService` | `memory/base_memory_service.py` | ABC: `add_session_to_memory(session)`, `search_memory(app_name, user_id, query)` → `SearchMemoryResponse` |
| `InMemoryMemoryService` | `memory/in_memory_memory_service.py` | In-memory store: `_session_events[user_key][session_id]` = list of events with content |
| `VertexAiMemoryBankService` | `memory/vertex_ai_memory_bank_service.py` | Vertex AI Memory Bank (semantic/long-term) |
| `VertexAiRagMemoryService` | `memory/vertex_ai_rag_memory_service.py` | Vertex AI RAG (retrieval) |
| `SearchMemoryResponse` | `memory/base_memory_service.py` | `memories: list[MemoryEntry]` |
| `MemoryEntry` | `memory/memory_entry.py` | `content: types.Content`, `author`, `timestamp`, `custom_metadata` |
| `ToolContext` | `tools/tool_context.py` | Exposes `search_memory(query)` to tools via `invocation_context.memory_service` |

### When memory is retrieved (not automatic at run start)

Long-term memory is **not** loaded when a run starts. It is used only when:

1. **Tool calls** – A tool (e.g. `LoadMemoryTool`, `PreloadMemoryTool`) calls `tool_context.search_memory(query)`.

**Flow:**

```
tools/tool_context.py  ToolContext.search_memory(query)
  → if invocation_context.memory_service is None: return empty
  → return await invocation_context.memory_service.search_memory(
        app_name=..., user_id=..., query=query
     )
```

**Returned structure:** `SearchMemoryResponse(memories=[MemoryEntry(content=Content, author=..., timestamp=...), ...])`

### When memory is written

- **Explicit:** `CallbackContext.add_session_to_memory()` (e.g. in `after_agent`). Implemented in `agents/callback_context.py`:

```python
# agents/callback_context.py  CallbackContext.add_session_to_memory()
if self._invocation_context.memory_service is None:
    raise ValueError(...)
await self._invocation_context.memory_service.add_session_to_memory(
    self._invocation_context.session
)
```

- **Web UI:** `cli/adk_web_server.py` calls `await self.memory_service.add_session_to_memory(session)` after a turn (e.g. when saving to memory).

### InMemoryMemoryService behavior

```python
# memory/in_memory_memory_service.py

# Storage: _session_events["app_name/user_id"][session_id] = [events with content]
async def add_session_to_memory(self, session: Session):
    self._session_events[user_key][session.id] = [
        event for event in session.events if event.content and event.content.parts
    ]

# Retrieval: keyword overlap (no embedding)
async def search_memory(self, *, app_name, user_id, query) -> SearchMemoryResponse:
    words_in_query = _extract_words_lower(query)
    # For each stored event, if any query word in event text → append MemoryEntry(content=event.content, ...)
    return SearchMemoryResponse(memories=...)
```

**Summary:** Long-term memory is **tool/callback-driven**. Session load does not pull memory; tools pull it via `memory_service.search_memory()`. Object returned to caller: `SearchMemoryResponse` with `memories: list[MemoryEntry]`.

---

## 2. Persisted session load when a run starts

### Entry point: session fetch

**File:** `runners.py`  
**Method:** `Runner.run_async()`

```python
# runners.py  Runner.run_async()  (inside _run_with_trace)
session = await self.session_service.get_session(
    app_name=self.app_name, user_id=user_id, session_id=session_id
)
if not session:
    raise ValueError(message)
# ...
invocation_context = await self._setup_context_for_new_invocation(
    session=session, new_message=new_message, ...
)
# ctx.agent = self._find_agent_to_run(session, self.agent)
# then execute: async for event in self._exec_with_plugin(..., execute_fn=execute): yield event
```

So the **entry point** for loading persisted session data is `session_service.get_session(app_name, user_id, session_id)`.

### InMemorySessionService – session load

**File:** `sessions/in_memory_session_service.py`

```python
# InMemorySessionService.get_session → _get_session_impl
session = self.sessions[app_name][user_id].get(session_id)   # in-memory dict
copied_session = copy.deepcopy(session)
if config and config.num_recent_events:
    copied_session.events = copied_session.events[-config.num_recent_events:]
if config and config.after_timestamp:
    # trim events before after_timestamp
return self._merge_state(app_name, user_id, copied_session)
```

**Reconstruction:**

- **Conversation history:** `session.events` is already the full (or trimmed) list of `Event` objects; no separate “history” object.
- **State:** `_merge_state()` merges:
  - `app_state` → `copied_session.state["app:" + key]`
  - `user_state` → `copied_session.state["user:" + key]`
  - Session-level state is already on `session.state` (plain dict).

So **session = Session(id, app_name, user_id, state=merged dict, events=list[Event], last_update_time)**.

### DatabaseSessionService – session load

**File:** `sessions/database_session_service.py`

```python
# DatabaseSessionService.get_session()
async with self.database_session_factory() as sql_session:
    storage_session = await sql_session.get(StorageSession, (app_name, user_id, session_id))
    if storage_session is None:
        return None
    # Load events (optional filter: after_timestamp, num_recent_events)
    stmt = select(StorageEvent).filter(...).order_by(StorageEvent.timestamp.desc())
    result = await sql_session.execute(stmt)
    storage_events = result.scalars().all()
    # Load app/user state
    storage_app_state = await sql_session.get(StorageAppState, (app_name))
    storage_user_state = await sql_session.get(StorageUserState, (app_name, user_id))
    # Merge: app_state, user_state (with prefixes), session_state
    merged_state = _merge_state(app_state, user_state, session_state)
    events = [e.to_event() for e in reversed(storage_events)]
    session = storage_session.to_session(state=merged_state, events=events)
return session
```

**Reconstruction:**

- **Event history:** Each `StorageEvent` is converted with `to_event()` → `Event(id, invocation_id, author, content=decode_model(content, types.Content), actions, ...)`.
- **Session state:** Single flat dict: session-level state plus `State.APP_PREFIX + k` and `State.USER_PREFIX + k` from app/user tables.

So persisted session data becomes a **runtime `Session`**: `state` (dict) + `events` (list of `Event`).

---

## 3. Where persisted session becomes runtime state, working memory, and model input

| What | Where it becomes that |
|------|------------------------|
| **Runtime state** | As soon as `get_session()` returns. The returned `Session` is the in-memory object; `session.state` (dict) and `session.events` (list) are the runtime session state. Runner passes this `Session` into `InvocationContext(session=session, ...)`. |
| **Short-term working memory / context** | Same object. “Working memory” for the run is `invocation_context.session` (and thus `invocation_context.session.events` and `invocation_context.session.state`). No separate “working memory” structure; the session is the context. |
| **Model input (prompt)** | In the LLM flow’s **content request processor**. Session events are turned into a list of `types.Content` and assigned to `llm_request.contents`, which is then sent to the model. |

### Exact place: session → model prompt

**File:** `flows/llm_flows/contents.py`  
**Class:** `_ContentLlmRequestProcessor`  
**Method:** `run_async(invocation_context, llm_request)`

```python
if agent.include_contents == 'default':
    llm_request.contents = _get_contents(
        invocation_context.branch,
        invocation_context.session.events,   # <-- session event history
        agent.name,
    )
else:
    llm_request.contents = _get_current_turn_contents(
        invocation_context.branch,
        invocation_context.session.events,
        agent.name,
    )
```

So **persisted session data** (after load) lives in `invocation_context.session.events` and `invocation_context.session.state`. The **prompt** is built from `session.events` inside `_get_contents()` / `_get_current_turn_contents()` → list of `types.Content` → `llm_request.contents` → model.

---

## 4. Data structures

### Session state

- **Runtime:** `Session.state` is `dict[str, Any]` (see `sessions/session.py`). Keys can be:
  - `app:...` (app-level, from `State.APP_PREFIX`)
  - `user:...` (user-level, from `State.USER_PREFIX`)
  - Unprefixed: session-level.
- **Storage (DB):** `StorageSession.state` (JSON), `StorageAppState.state`, `StorageUserState.state`; merged on load via `_merge_state()`.
- **Delta handling:** `State` in `sessions/state.py` has `_value` (committed) and `_delta` (uncommitted). Session’s `state` in the API is a plain dict; delta application happens in `BaseSessionService.append_event()` → `_update_session_state(session, event)` which does `session.state.update(event.actions.state_delta)` (and in DB/InMemory, state_delta is split by prefix and written to app/user/session storage).

### Event history

- **Runtime:** `Session.events: list[Event]` (see `sessions/session.py`).
- **Event:** `events/event.py` – `Event` extends `LlmResponse`: `invocation_id`, `author`, `actions: EventActions`, `content` (genai `Content`), `branch`, `timestamp`, etc.
- **EventActions:** `events/event_actions.py` – `state_delta`, `artifact_delta`, `transfer_to_agent`, `compaction`, `end_of_agent`, `agent_state`, `rewind_before_invocation_id`, etc.
- **Storage (DB):** `StorageEvent` – same fields serialized (e.g. `content` as JSON, `actions` as pickle). Reconstructed with `to_event()`.

### Working memory / context assembly

- **Context for the run:** `InvocationContext` holds `session: Session`, so `session.events` and `session.state` are the “working memory.”
- **Context for the model:** Built in `flows/llm_flows/contents.py`:
  - `_get_contents(branch, events, agent_name)`:
    - Rewind filtering (drop events annulled by rewind).
    - `_should_include_event_in_context(branch, event)` (branch, non-empty content, not auth/confirmation).
    - Compaction handling (`_process_compaction_events`).
    - Transcription aggregation; other-agent events turned into user-style content.
    - `_rearrange_events_for_latest_function_response` and `_rearrange_events_for_async_function_responses_in_history`.
    - Then `contents = [copy.deepcopy(event.content) for event in result_events if event.content]`.
  - Result: `list[types.Content]` = the model’s conversation view (short-term “working memory” in the prompt).

---

## 5. Single run end-to-end

### Step-by-step execution timeline

| Step | File | Class | Method | Snippet / behavior |
|------|------|--------|--------|--------------------|
| 1. Entry | `runners.py` | `Runner` | `run()` | Sync wrapper: starts thread, runs `run_async()`, puts events in queue, yields. |
| 2. Async entry | `runners.py` | `Runner` | `run_async()` | `run_config or RunConfig()`. Sets `new_message.role = 'user'` if missing. Enters `_run_with_trace(new_message, invocation_id)`. |
| 3. Session load | `runners.py` | `Runner` | `run_async()` → `_run_with_trace` | `session = await self.session_service.get_session(app_name, user_id, session_id)`. Raises if not found. |
| 4. Session load (impl) | `sessions/in_memory_session_service.py` or `sessions/database_session_service.py` | InMemorySessionService / DatabaseSessionService | `get_session()` | InMemory: copy from dict, optionally trim events, merge app/user state into `session.state`. DB: load StorageSession, StorageEvents, StorageAppState, StorageUserState; merge state; `events = [e.to_event() for e in reversed(storage_events)]`; `session = storage_session.to_session(state=merged_state, events=events)`. |
| 5. Invocation context | `runners.py` | `Runner` | `_setup_context_for_new_invocation()` | `invocation_context = self._new_invocation_context(session, new_message=new_message, run_config=run_config)`; `await self._handle_new_message(...)` (append user message to session); `invocation_context.agent = self._find_agent_to_run(session, self.agent)`. |
| 6. New invocation ctx | `runners.py` | `Runner` | `_new_invocation_context()` | `InvocationContext(session=session, user_content=new_message, session_service, memory_service, ...)`. Session (with loaded state + events) is now in context. |
| 7. Append user message | `runners.py` | `Runner` | `_append_new_message_to_session()` | Build `Event(invocation_id, author='user', content=new_message[, state_delta])`; `await self.session_service.append_event(session, event)`. |
| 8. Append event (state update) | `sessions/base_session_service.py` | `BaseSessionService` | `append_event()` | `_trim_temp_delta_state(event)`; `_update_session_state(session, event)` → `session.state.update(event.actions.state_delta)`; `session.events.append(event)`. (DB/InMemory override to persist.) |
| 9. Execute with plugins | `runners.py` | `Runner` | `_exec_with_plugin()` | `before_run`; then `async for event in execute_fn(invocation_context):` where `execute_fn` = `lambda ctx: ctx.agent.run_async(ctx)`. |
| 10. Agent run | `agents/llm_agent.py` | `LlmAgent` | `run_async(ctx)` | Delegates to flow (e.g. `AutoFlow`): `async with Aclosing(self.flow.run_async(ctx)) as agen: async for event in agen: yield event`. |
| 11. Flow run | `flows/llm_flows/base_llm_flow.py` | `BaseLlmFlow` | `run_async()` | `_preprocess_async(ctx, llm_request)` (runs request processors, including contents); then loop: generate → `_generate_async()` → LLM call; process response; yield events; break when final or transfer. |
| 12. Contents (prompt) | `flows/llm_flows/contents.py` | `_ContentLlmRequestProcessor` | `run_async(ctx, llm_request)` | `llm_request.contents = _get_contents(ctx.branch, ctx.session.events, agent.name)` (or `_get_current_turn_contents`). So **session.events → model prompt**. |
| 13. Memory retrieval | (optional) | — | — | Only if a tool calls `tool_context.search_memory(query)` → `invocation_context.memory_service.search_memory(...)` → `SearchMemoryResponse(memories=[...])`. Not called by default at run start. |
| 14. Model call | `flows/llm_flows/base_llm_flow.py` / models | BaseLlmFlow / BaseLlm | `generate_async` / connection | `llm_request.contents` (and tools, etc.) sent to model; response parsed into `LlmResponse` / `Event`. |
| 15. State mutation | `sessions/base_session_service.py` | `BaseSessionService` | `append_event()` | Each yielded event is appended by Runner in `_exec_with_plugin`: `await self.session_service.append_event(session, event)` → state_delta applied to `session.state`, event appended to `session.events`. |
| 16. Session persistence | `sessions/in_memory_session_service.py` or `sessions/database_session_service.py` | InMemorySessionService / DatabaseSessionService | `append_event()` | InMemory: update in-memory session dict and apply state_delta to app_state/user_state/session.state. DB: persist StorageEvent, update StorageSession/StorageAppState/StorageUserState from state_delta, commit. |
| 17. Compaction | `runners.py` | `Runner` | `run_async()` | After generator finishes: if `self.app.events_compaction_config`: `await _run_compaction_for_sliding_window(self.app, session, self.session_service)`. |

### Simplified code path (key lines)

```text
runner.run(...)
  → runners.run_async()
      → session = await self.session_service.get_session(...)     # session load
      → invocation_context = await _setup_context_for_new_invocation(session, new_message, ...)
          → _new_invocation_context(session, ...)                  # session in context
          → _handle_new_message → _append_new_message_to_session  # user event appended
          → invocation_context.agent = _find_agent_to_run(session, self.agent)
      → async for event in _exec_with_plugin(..., execute_fn):
            execute_fn = lambda ctx: ctx.agent.run_async(ctx)
          → llm_agent.run_async(ctx)
              → flow.run_async(ctx)
                  → _preprocess_async(ctx, llm_request)
                      → contents.request_processor.run_async(ctx, llm_request)
                          → llm_request.contents = _get_contents(ctx.branch, ctx.session.events, agent.name)
                  → generate → model invoked with llm_request.contents
                  → yield events
            → for each event: await session_service.append_event(session, event)  # state + persistence
            → yield event
      → compaction if configured
```

---

## 6. Storage vs runtime, episodic vs semantic, immutable vs mutable

| Concept | Implementation |
|--------|-----------------|
| **Storage** | Session: DB tables (`StorageSession`, `StorageEvent`, `StorageAppState`, `StorageUserState`) or in-memory dicts (`InMemorySessionService.sessions`, `app_state`, `user_state`). Memory: `InMemoryMemoryService._session_events` or Vertex AI (Memory Bank / RAG). |
| **Runtime memory** | `Session` instance: `state` (dict), `events` (list). Held in `InvocationContext.session`. No separate “runtime store”; the session object is the runtime view. |
| **Episodic (conversation)** | `Session.events`: ordered list of `Event` (user/model/tool turns). Used to build `llm_request.contents` in `contents.py`. Episodic = event history. |
| **Semantic (long-term)** | Memory service: `add_session_to_memory(session)` ingests session; `search_memory(query)` returns relevant `MemoryEntry`s. InMemory uses keyword match; Vertex uses embeddings/Memory Bank/RAG. Only used when tools/callbacks call search/add. |
| **Immutable** | Loaded events are not mutated in place for history; new events are appended. Compaction adds new events (compacted_content) and can hide older events from context. |
| **Mutable** | `Session.state` is updated in place when `append_event()` applies `event.actions.state_delta`. The same `Session` reference is passed through the run; DB/InMemory persist state on append. |

---

## 7. ASCII diagram: memory flow

```text
                    run_async(user_id, session_id, new_message)
                                      │
                                      ▼
                    ┌─────────────────────────────────────────┐
                    │  session_service.get_session(...)        │
                    │  → Session(state, events)                │
                    └─────────────────────────────────────────┘
                      │ InMemory: dict copy + merge_state
                      │ DB: StorageSession/StorageEvent/App/User
                      │     → to_session(merged_state, events)
                      ▼
                    ┌─────────────────────────────────────────┐
                    │  InvocationContext(session=session,      │
                    │   memory_service=..., ...)              │
                    └─────────────────────────────────────────┘
                      │
                      ├── session.state (dict) ────────────────► runtime state
                      ├── session.events (list[Event]) ─────────► event history
                      │
                      ▼
                    append_event(session, user_message_event)
                      │
                      ▼
                    ┌─────────────────────────────────────────┐
                    │  flow.run_async(ctx)                     │
                    │    _preprocess_async → contents processor│
                    │      _get_contents(ctx.session.events)   │
                    │      → llm_request.contents              │
                    └─────────────────────────────────────────┘
                      │
                      ▼
                    ┌─────────────────────────────────────────┐
                    │  model.generate(llm_request)             │  ◄── prompt = contents
                    │  (optional: tool calls → search_memory)  │
                    └─────────────────────────────────────────┘
                      │
                      ▼
                    for each event: append_event(session, event)
                      │
                      ├── session.state.update(state_delta)   ► mutable state
                      ├── session.events.append(event)         ► persistence
                      └── DB/InMemory persist event + state
                                      │
                    (optional) callback_context.add_session_to_memory()
                      │
                      ▼
                    memory_service.add_session_to_memory(session)  ► long-term (semantic)
```

---

## 8. Summary table: concept → code

| Concept | File | Class / function | Notes |
|---------|------|-------------------|-------|
| Session load entry | `runners.py` | `Runner.run_async` | `get_session(app_name, user_id, session_id)` |
| Session (runtime) | `sessions/session.py` | `Session` | `id`, `app_name`, `user_id`, `state: dict`, `events: list[Event]` |
| Session load (memory) | `sessions/in_memory_session_service.py` | `InMemorySessionService._get_session_impl` | Copy from dict; merge app/user state into `session.state` |
| Session load (DB) | `sessions/database_session_service.py` | `DatabaseSessionService.get_session` | Load Storage*; merge state; `to_session(merged_state, events)` |
| State merge | `sessions/_session_util.py` | `extract_state_delta` | Splits keys by `app:`, `user:`, else session. |
| State update on event | `sessions/base_session_service.py` | `BaseSessionService.append_event` → `_update_session_state` | `session.state.update(event.actions.state_delta)` |
| Event history | `sessions/session.py` | `Session.events` | `list[Event]` |
| Event → prompt | `flows/llm_flows/contents.py` | `_get_contents`, `_ContentLlmRequestProcessor.run_async` | Filter/compact/reorder events → `list[types.Content]` → `llm_request.contents` |
| Long-term memory read | `memory/base_memory_service.py` | `BaseMemoryService.search_memory` | Returns `SearchMemoryResponse(memories=[MemoryEntry])`. Invoked by tools via `ToolContext.search_memory`. |
| Long-term memory write | `memory/base_memory_service.py` | `BaseMemoryService.add_session_to_memory` | Called from `CallbackContext.add_session_to_memory()` or web server. |
| Session persistence (append) | `sessions/base_session_service.py` | `BaseSessionService.append_event` | Updates state, appends event; subclasses persist to DB or in-memory dict. |

---

**References (package root: site-packages/google/adk):**

- `runners.py` – Runner, run_async, session load, invocation context, append_event loop.
- `sessions/session.py` – Session model.
- `sessions/state.py` – State (value/delta); prefixes.
- `sessions/base_session_service.py` – append_event, _update_session_state.
- `sessions/in_memory_session_service.py` – get_session, _merge_state, append_event.
- `sessions/database_session_service.py` – get_session, append_event, StorageSession/StorageEvent/to_session/to_event.
- `agents/invocation_context.py` – InvocationContext(session, memory_service, …).
- `flows/llm_flows/contents.py` – _get_contents, _ContentLlmRequestProcessor.
- `flows/llm_flows/base_llm_flow.py` – run_async, _preprocess_async.
- `memory/base_memory_service.py` – BaseMemoryService, SearchMemoryResponse.
- `memory/in_memory_memory_service.py` – add_session_to_memory, search_memory.
- `memory/memory_entry.py` – MemoryEntry.
- `events/event.py` – Event.
- `events/event_actions.py` – EventActions (state_delta, etc.).
- `agents/callback_context.py` – add_session_to_memory.
- `tools/tool_context.py` – search_memory.
