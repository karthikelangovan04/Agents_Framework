## Long-Term and Short-Term Memory Patterns in ADK (26)

This document explores how to model **episodic, semantic, procedural, and short-term / working memory** using Google ADK’s primitives:

- **Sessions & State** (`SessionService`, `state`) – scratchpad / working memory  
  → `https://google.github.io/adk-docs/sessions/`  
  → `https://google.github.io/adk-docs/sessions/state/`
- **MemoryService** – long‑term, searchable memory  
  → `https://google.github.io/adk-docs/sessions/memory/`
- **Artifacts** – versioned binary/file memory (e.g., reports, diagrams)  
  → `https://google.github.io/adk-docs/artifacts/`

The goal is not to introduce new primitives, but to **layer cognitive memory types on top of ADK’s existing session, state, memory, and artifact services**.

---

## 1. ADK Building Blocks Recap

From the ADK memory docs and blog [`https://google.github.io/adk-docs/sessions/`](https://google.github.io/adk-docs/sessions/), [`https://google.github.io/adk-docs/sessions/memory/`](https://google.github.io/adk-docs/sessions/memory/), [`https://google.github.io/adk-docs/sessions/state/`](https://google.github.io/adk-docs/sessions/state/), [`https://cloud.google.com/blog/topics/developers-practitioners/remember-this-agent-state-and-memory-with-adk`](https://cloud.google.com/blog/topics/developers-practitioners/remember-this-agent-state-and-memory-with-adk):

- **Session**:
  - Represents a single conversational thread.
  - Tracks the chronological history of **events** (messages, tool calls, etc.).
  - Scoped by `(app_name, user_id, session_id)`.

- **State**:
  - A **structured key–value scratchpad** attached to a session.
  - Holds short-lived data: current task progress, cached tool results, active plan, UI state, etc.
  - Backed by the configured `SessionService` (e.g., `InMemorySessionService`, `DatabaseSessionService`, `VertexAiSessionService`).

- **Memory / MemoryService**:
  - A **long-term knowledge store** (multi-session, cross-session, or external).
  - ADK offers:
    - `InMemoryMemoryService` (ephemeral, basic keyword search).
    - `VertexAiMemoryBankService` (persistent, semantic search, LLM-powered memory extraction).
  - The LLM can query Memory to recall facts beyond the active session.

- **Artifacts**:
  - Named, versioned **binary objects** (images, PDFs, CSVs, etc.).
  - Managed by an `ArtifactService` (e.g., `InMemoryArtifactService`, `GcsArtifactService`).
  - Represent “file-like” memory that is too large or structured to live directly in state.

These are the **raw materials** we’ll combine to emulate different human memory types.

---

## 2. Short-Term vs Long-Term Memory in ADK

Before we break down the cognitive types, it is useful to fix a **global mapping** between “short-term” and “long-term” memory in ADK terms:

- **Short-term / Working memory (per session)**:
  - **Primary primitives**:
    - `state` (session state)
    - Current session’s **contents / event history**
  - **Characteristics**:
    - Fast, local to a single `(app_name, user_id, session_id)`.
    - Automatically available to the agent while a session is active.
    - Typically cleared when the session is reset or expires.

- **Long-term memory (cross-session / persistent)**:
  - **Primary primitives**:
    - `MemoryService` (e.g., `VertexAiMemoryBankService`) for **searchable text/structured memories**.
    - `ArtifactService` for **file/binary memories** (images, PDFs, large reports, logs).
  - **Characteristics**:
    - Lives beyond a single session.
    - Can be queried semantically and/or by key.
    - Can be shared across multiple sessions for the same user, org, or app.

This lines up with the **Sessions Package** doc (`07-Sessions-Package.md`):

- That doc focuses on how to configure **`SessionService` backends** (in-memory, database, Vertex AI) and how session **state and events** are stored and retrieved over time.
- Even if you use a **persistent** `SessionService` (e.g., `DatabaseSessionService`, `VertexAiSessionService`), conceptually you should still treat:
  - **Session + state** as **short-term / working memory for one conversation thread**, and
  - **MemoryService + Artifacts** as your **true long-term memory layer** for facts and large artifacts that span many sessions.

You can think of the overall layering this way:

- **Short-term memory** = “what the agent is actively thinking about *right now* in this session”  
  → **session + state** (as described in `07-Sessions-Package.md`).
- **Long-term memory** = “what the agent can look up from prior experiences or knowledge across sessions”  
  → **MemoryService + Artifacts** (see `08-Memory-Package.md` and the Artifacts docs).

The following sections (episodic, semantic, procedural) show how to specialize this split into more refined cognitive types on top of the same ADK primitives.

---

## 3. Short-Term / Working Memory with ADK State

---

## 3. Short-Term / Working Memory with ADK State

**Cognitive analogy:**  
Short-term or working memory holds information currently being thought about (current question, temporary results, focus of attention).

**ADK implementation:**  
Use **`state`** (via `SessionService`) as the working memory:

- **Per-session scratchpad**, cleared when:
  - The session ends, or
  - You choose to reset it.
- Low-latency key–value store, available to:
  - Agent instructions (via `{state.var}` templating),
  - Tools and callbacks (`context.state[...]`),
  - Multi-agent workflows.

**Patterns:**

- **Current task context**:
  - `state["current_task"] = { "goal": "...", "steps": [...], "status": "in_progress" }`
- **User’s in-progress form / UI state**:
  - `state["draft_deal_config"] = {...}` in your Copilot/ADK web flows.
- **Scratch intermediate results**:
  - Tool outputs that don’t warrant long-term memory.

**Best practices:**

- Treat `state` as **working set**:
  - Small, focused, relevant to the **current** conversation.
- If something should last **beyond** the session, **promote** it to Memory or Artifacts (see below).

---

## 4. Episodic Memory: Past Sessions & Events

**Cognitive analogy:**  
Episodic memory is memory for **events in time** – “what happened in that conversation last week?”, “what steps did we follow for customer X?”.

**ADK implementation:**  
Use:

- **Session history** (events) per session, and
- **MemoryService entries tagged with session metadata**

to represent episodic memory.

### 4.1. Session-centric episodic memory

Each **session** is itself an **episode**:

- ADK tracks events for that session:
  - User messages,
  - Model responses,
  - Tool invocations.
- You can:
  - **Rewind** or **resume** sessions,
  - Use the session’s history as context for follow-up questions.

This gives you **short-horizon episodic memory** out of the box.

### 4.2. Cross-session episodic memory with MemoryService

To model **long-horizon episodic memory** (e.g., “all support cases for User 123”):

- Use **MemoryService** entries that encode:
  - **What happened** (summary),
  - **When / where** (timestamps, session IDs),
  - **Who** (user, app).

**Example structure stored via MemoryService:**

```json
{
  "type": "episode",
  "user_id": "user_123",
  "session_id": "sess_2025_01_10_abc",
  "timestamp": "2025-01-10T15:23:10Z",
  "summary": "User configured ADK + MCP for diagram generation and tested 2K/4K outputs.",
  "key_entities": ["ADK", "MCP", "diagrams", "architecture diagrams", "2K", "4K"],
  "outcome": "Success"
}
```

With **VertexAiMemoryBankService**:

- You can **embed** these episodes and later search semantically:
  - “Show previous architecture-diagram design sessions for this user.”
  - “Recall the last time we configured Vertex AI Memory for this tenant.”

**Pattern:**

- After important flows or milestones, write a **callback** that:
  - Summarizes that segment of the conversation,
  - Extracts structured fields (user id, entities, timestamps),
  - Saves it as a **MemoryService record** of type `"episode"`.

---

## 5. Semantic Memory: Facts, Concepts, and Knowledge

**Cognitive analogy:**  
Semantic memory is **fact-like knowledge**: “what is ADK?”, “how does MCP integration work?”, “what is the customer’s default region?”.

**ADK implementation:**  
Use **MemoryService** as **semantic memory**:

- Facts about the **user** or **org**:
  - `"user_123 prefers region us-central1, default model gemini-2.0-flash"`
- Facts about the **domain**:
  - How to set up ADK packages, RAG settings, safety policies.
- Facts about **policies and constraints**:
  - Allowed data sources, cost thresholds, SLAs.

### 5.1. Semantic memory schema

You can design a simple schema per memory entry:

```json
{
  "type": "semantic",
  "scope": "user",                // "user", "org", "global"
  "user_id": "user_123",
  "key": "default_region",
  "value": "us-central1",
  "explanation": "User selected us-central1 in setup wizard.",
  "source": "setup_flow",
  "created_at": "2025-01-10T15:10:00Z"
}
```

Or for **general knowledge**:

```json
{
  "type": "semantic",
  "scope": "global",
  "key": "adk_memory_definition",
  "value": "ADK MemoryService provides long-term, searchable memory across sessions.",
  "tags": ["adk", "memory", "docs"],
  "source": "internal_docs"
}
```

### 5.2. Populating semantic memory

- From **setup flows**:
  - Persist configuration choices into MemoryService.
- From **external systems**:
  - Import CRM / config / policy facts as Memory entries.
- From **LLM itself**:
  - Use a summarization tool/agent that:
    - Reads conversation segments,
    - Extracts stable facts (“user has Azure + GCP,” “prefers diagrams in 4K”),
    - Writes them into MemoryService.

### 5.3. Querying semantic memory

At runtime, your agent:

- Queries MemoryService for **relevant semantic entries**:
  - “semantic + user_123 + region” for user preferences.
  - “semantic + global + ADK memory” for internal docs.
- Injects them into the prompt via:
  - **context contents**, or
  - **state variables** referenced by `{state.var}` in `instruction`.

This yields a clear separation:

- **Working memory** = `state`
- **Long-lived facts** = `MemoryService` semantic entries

---

## 6. Procedural Memory: Skills and Routines

**Cognitive analogy:**  
Procedural memory is “how to do things” – skills, routines, workflows (e.g., “how to provision a new tenant”, “how to set up ADK + MCP + artifacts”).

**ADK implementation:**  
Procedural knowledge fits naturally into:

- **Tools** (FunctionTool, AgentTool, MCP tools),
- **Workflow agents** (sequential / loop / parallel),
- **Code + configuration** (apps, flows).

The **“memory”** aspect comes from:

- Storing **procedural templates** and **plans** in Memory or Artifacts,
- Giving the agent access to these when planning or executing tasks.

### 6.1. Encoding procedures as tools and workflows

- Each **procedure** → an **ADK tool** or **workflow agent**:
  - `provision_customer_tenant`
  - `generate_adk_mcp_diagram`
  - `run_rag_refresh_pipeline`

These are **executable skills**. To make them *adaptive* and *remembered*:

- Store **patterns and variants** of procedures in MemoryService:
  - “For enterprise customers, use GCS bucket X and region Y.”
  - “For this tenant, we must always enable safety profile Z.”

### 6.2. Procedural templates in Memory or Artifacts

You can store:

- **Textual recipes** / step lists as semantic memories:

```json
{
  "type": "procedure_template",
  "name": "setup_adk_mcp_diagram_server",
  "steps": [
    "Create MCP server Python script with diagram libraries installed.",
    "Add generate_arch_diagram MCP tool using graphviz/diagrams/plantuml.",
    "Wire McpToolset into ADK agent.",
    "Configure ArtifactService to store images."
  ],
  "tags": ["adk", "mcp", "diagrams", "setup"]
}
```

- **Code templates / notebooks / diagrams** as Artifacts:
  - `setup_mcp_diagrams_notebook.ipynb`
  - `reference_architecture_2k.png` / `4k.png`

When the agent needs to “remember how to do X”, it:

- Searches Memory for `procedure_template` with relevant tags,
- Optionally loads code/diagram artifacts,
- Uses these as **procedural hints** while planning or calling tools.

---

## 7. Combining Memory Types in a Single ADK App

Here is how a **real ADK app** can combine all four memory types:

### 7.1. Short-term / working memory

- Use `state` for:
  - Current user intent,
  - Active plan,
  - Step-level progress,
  - Temporary tool outputs.

Example:

```python
state["current_plan"] = {
    "goal": "Deploy ADK + MCP diagram agent",
    "steps": ["analyze requirements", "configure MCP", "wire artifacts"],
    "step_index": 1,
}
```

### 7.2. Episodic memory

- After important segments:
  - Summarize the episode and store it in MemoryService with:
    - `type`: `"episode"`,
    - `session_id`, `user_id`,
    - `summary`, `outcome`.
- Allows:
  - “Recall what we did last time for this user.”
  - “Show all diagram deployments we’ve done.”

### 7.3. Semantic memory

- Store facts:
  - User preferences (regions, resolutions, tools),
  - Organization policies,
  - Domain knowledge (e.g., how ADK memory works).
- Use Vertex AI Memory Bank for:
  - Better semantic search,
  - LLM-based extraction and retrieval.

### 7.4. Procedural memory

- Implement skills as:
  - Tools + workflow agents,
  - Backed by stored **procedural templates** in Memory and code artifacts.
- The agent can:
  - Look up “how to do X” in Memory,
  - Then execute or adapt the corresponding tool/workflow.

---

## 8. Design Recommendations

- **Keep working memory small and focused**:
  - Use `state` for what the model needs *right now*.
  - Periodically **distill** from state/session history into Memory or Artifacts.

- **Separate facts from episodes**:
  - **Facts** → semantic (`type: "semantic"`).
  - **Stories / past runs** → episodic (`type: "episode"`).

- **Model procedures explicitly**:
  - Don’t hide everything in prompt instructions.
  - Use tools/workflows as executable “skills”.
  - Use Memory to store templates and variations of those skills.

- **Use Artifacts for heavy or binary memory**:
  - Long reports, images (e.g., 2K/4K diagrams), logs, notebooks.
  - Reference them via filenames/versions from semantic or episodic memories.

- **Leverage Vertex AI Memory for production**:
  - `InMemoryMemoryService` is fine for dev,
  - Use `VertexAiMemoryBankService` for persistent, cross-session semantic & episodic memory.

By composing **Sessions, State, MemoryService, Tools, and Artifacts**, you can approximate the full spectrum of **short-term, episodic, semantic, and procedural memory** in a principled and operational way inside ADK.

