# ADK Memory Services: InMemoryMemoryService vs VertexAiMemoryBankService

Findings from the ADK library (`adk-python-lib/src/google/adk/memory/`). Use this file for reference; do not add long notes to `agent.py`.

---

## Summary: Smart storage and retrieval

| Aspect | InMemoryMemoryService | VertexAiMemoryBankService |
|--------|------------------------|---------------------------|
| **Storage** | Raw events stored as-is in a Python dict | Events sent to Vertex API; **memory is generated** (consolidation/fact extraction) |
| **What is stored** | Full event content (every user/model/tool message) | Vertex generates **memories** from events (backend does the work) |
| **Retrieval** | Keyword match (word overlap) | **Similarity search** (semantic) |
| **What is returned** | **Raw conversation snippets** (full event content) | **Facts** (`retrieved_memory.memory.fact`) – short, extracted text |
| **Result limit** | None (all matches returned) | Iterator / service-defined (effectively top-k by similarity) |
| **Token impact** | High – full messages in tool result | Lower – facts are concise, and fewer results |

**Conclusion:** VertexAiMemoryBankService uses **smart storing** (generate memories from events) and **smart retrieval** (similarity search, returns facts). InMemoryMemoryService is dumb storage (raw events) and keyword retrieval (raw events back).

---

## InMemoryMemoryService (library behavior)

**Source:** `adk-python-lib/src/google/adk/memory/in_memory_memory_service.py`

### Storage (`add_session_to_memory`)

- Builds key `app_name/user_id` and stores `session.id → list[Event]`.
- Each event is stored in full: `event.content`, `event.author`, `event.timestamp` (events with no content/parts are skipped).
- No transformation: **raw session events** only.

### Retrieval (`search_memory`)

- Splits query into words (regex `[A-Za-z]+`, lowercased).
- For every stored event, extracts words from event text; if **any** query word appears in the event, the **entire event** is added to the result.
- Returns `SearchMemoryResponse(memories=[MemoryEntry(content=event.content, ...), ...])`.
- **No limit** – every matching event is returned.
- **Token impact:** The whole tool result (all matching full messages) is sent to the model → can be large.

---

## VertexAiMemoryBankService (library behavior)

**Source:** `adk-python-lib/src/google/adk/memory/vertex_ai_memory_bank_service.py`

### Storage (`add_session_to_memory` → `_add_events_to_memory_from_events`)

- Requires `agent_engine_id` (Vertex AI Agent Engine / Memory Bank).
- Filters events (skips those with no text/inline_data/file_data).
- Sends events to Vertex with:
  - `api_client.agent_engines.memories.generate(...)`
  - `direct_contents_source={'events': direct_events}`
  - `scope={'app_name': app_name, 'user_id': user_id}`
  - Optional `config` (e.g. `revision_ttl`, `metadata`, `wait_for_completion`).
- **“Generate”** means the backend **produces memories from the events** (e.g. consolidation, fact extraction, dedup). So storage is **smart**: not raw events stored as-is, but **generated memories** in the Memory Bank.

### Retrieval (`search_memory`)

- Calls `api_client.agent_engines.memories.retrieve(...)` with:
  - `similarity_search_params={'search_query': query}`
  - Same `scope` (app_name, user_id).
- **Similarity search** = semantic (e.g. embeddings + vector search), not keyword match.
- Response is consumed as:
  - `async for retrieved_memory in retrieved_memories_iterator`
  - Each item is turned into a `MemoryEntry` with **`content=types.Content(parts=[types.Part(text=retrieved_memory.memory.fact)])`**.
- So the service returns **facts** (`memory.fact`), not raw event content. Typically a limited set (iterator / top-k), so **fewer, shorter** strings back → **lower token use** than InMemory.

---

## Comparison table (from library code)

| Feature | InMemoryMemoryService | VertexAiMemoryBankService |
|---------|------------------------|----------------------------|
| **Storage** | Raw events in RAM dict | Events → Vertex **generate** → stored memories |
| **Stored unit** | Event (full content) | Backend-generated memory (e.g. fact) |
| **Search** | Keyword (word overlap) | **Similarity search** (semantic) |
| **Returned unit** | Full event content | **Fact** text (`memory.fact`) |
| **Limit** | No limit | Iterator / top-k (service-side) |
| **Persistence** | Lost on process exit | Persistent (Vertex) |
| **Token usage** | High (many full messages) | Lower (fewer, shorter facts) |

---

## When to use which

- **InMemoryMemoryService:** Local dev, tests, prototyping; no setup; accepts high token usage and no persistence.
- **VertexAiMemoryBankService:** Production; need semantic search, controlled token usage, and persistence; have Vertex Agent Engine / Memory Bank and credentials.

---

## References

- `adk-python-lib/src/google/adk/memory/in_memory_memory_service.py`
- `adk-python-lib/src/google/adk/memory/vertex_ai_memory_bank_service.py`
- `adk/docs/18-Memory-Services-Comparison.md`
- `adk/docs/08-Memory-Package.md`
