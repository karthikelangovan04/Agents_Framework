# Getting Trace and Invocation Details Programmatically

This document describes how to obtain the same kind of trace details you see in the ADK Web Dev UI (invocation timing, `invoke_agent`, `call_llm`, `execute_tool` spans, etc.) **programmatically**.

**Reference trace (from ADK Web):**

- **Invocation** `e-91919583-62ed-44c7-9d6e-852ed01a18ea` — start, total ~3200 ms  
- **invoke_agent** `root_agent` — ~3190 ms  
- **chat** **call_llm** — ~1803 ms, ~1376 ms  
- **execute_tool** `get_current_time` — ~5.65 ms  

These come from **OpenTelemetry (OTel) spans** emitted by the ADK when you run agents via the Runner (including when using `adk web`).

---

## 1. Summary: Three Ways to Get Trace Details

| Method | When to use | What you get |
|--------|-------------|---------------|
| **1. ADK Web debug API** | ADK Web server is running (`adk web`) | OTel spans for a session (same data as the Dev UI trace view) |
| **2. OpenTelemetry in your app** | You run the Runner yourself (e.g. custom API/server) | Spans via your own TracerProvider / span processor or exporter |
| **3. Session events + timing** | Any setup | Per-event timing and invocation grouping from `session.events` (no OTel dependency) |

---

## 2. Method 1: ADK Web Debug API (when using `adk web`)

When you start the ADK with **`adk web`**, the server registers **debug trace endpoints** and uses an **InMemoryExporter** (or similar) to keep OTel spans per session so the Dev UI can show them.

### Endpoints (from ADK Web interface analysis)

- **`GET /debug/trace/{event_id}`** — Trace info for a specific event (if exported).
- **`GET /debug/trace/session/{session_id}`** — **Spans for a session** (OTel). This is what backs the trace view (invocation, invoke_agent, call_llm, execute_tool, etc.).

The exact path may be **under the app/user** in some deployments (e.g. `/apps/{app_name}/users/{user_id}/...`). If the root path does not work, try:

- `GET /apps/{app_name}/users/{user_id}/debug/trace/session/{session_id}`  
  or  
- Query parameters: `?app_name=...&user_id=...` (implementation-dependent).

### Example: Fetching session trace via HTTP

```python
# Run this while adk web is running (e.g. http://localhost:8000)
import requests

BASE = "http://localhost:8000"
# If your server uses a url_prefix, e.g. /api/v1, use BASE = "http://localhost:8000/api/v1"

# Option A: Session spans (what the Dev UI trace view shows)
session_id = "your-session-id"
r = requests.get(f"{BASE}/debug/trace/session/{session_id}")
if r.ok:
    data = r.json()  # or inspect r.text; format is implementation-specific (OTel spans)
    print(data)
else:
    print(r.status_code, r.text)

# Option B: Trace by event_id (if you have an event id from an invocation)
event_id = "e-91919583-62ed-44c7-9d6e-852ed01a18ea"
r = requests.get(f"{BASE}/debug/trace/{event_id}")
if r.ok:
    print(r.json())
```

The response format is **implementation-specific** (typically OTel span-like structures). The Dev UI reads this to render the tree (invocation → invoke_agent → chat/call_llm, execute_tool, etc.) and durations.

### Getting `app_name` and `user_id`

- **app_name**: From your agent layout (directory name or `App` name when using `adk web [AGENTS_DIR]`). You can call **`GET /list-apps`** to see available apps.
- **user_id** / **session_id**: From your client or session creation (e.g. **`POST /apps/{app_name}/users/{user_id}/sessions`** returns or uses a session id). Use that **session_id** in the debug trace URL.

---

## 3. Method 2: OpenTelemetry in Your Own Application

When you **run the Runner yourself** (e.g. custom FastAPI/Starlette app, or a script using `Runner`/`InMemoryRunner`), the ADK still uses OpenTelemetry internally. To get the same kind of trace details programmatically:

### 3.1 Use a custom span processor or exporter

- Configure the **TracerProvider** used by the ADK (or the global one) with a **SpanProcessor** that buffers spans (e.g. in memory per trace/session).
- Or use an **OTLP exporter** (or **InMemorySpanExporter**) and read spans from it after a run.

The ADK uses standard OTel span names and attributes; the Dev UI names you see (e.g. `invoke_agent`, `call_llm`, `execute_tool`) correspond to span names or attributes emitted by the library.

### 3.2 Telemetry package (`google.adk.telemetry`)

From the existing ADK docs (e.g. **09-Other-Packages.md**, **03-Package-Listing.md**):

- **`trace_call_llm`** — Trace LLM calls  
- **`trace_tool_call`** — Trace tool calls  
- **`trace_send_data`**, **`trace_merged_tool_calls`** — Additional tracing helpers  

These are used **internally** by the ADK to create spans. You typically do not need to call them yourself; ensuring OTel is initialized and exported (e.g. to a custom exporter or OTLP) is enough to capture the same spans.

### 3.3 Initialize OTel before ADK

To capture ADK spans in your own backend:

1. Install: `opentelemetry-sdk`, your chosen exporter (e.g. `opentelemetry-exporter-otlp`), and optionally `opentelemetry-instrumentation-google-genai`.
2. Set up **TracerProvider** and **SpanProcessor** (e.g. **BatchSpanProcessor** with your exporter, or a custom in-memory processor).
3. **Initialize this before** importing or creating ADK agents/runners so that the ADK uses your tracer.

Then run your agent as usual; spans (invocation, invoke_agent, call_llm, execute_tool) will be emitted and can be read from your exporter or processor.

---

## 4. Method 3: Session Events and Timestamps (no OTel)

If you only need **timing and structure per invocation** (and not full OTel spans), you can derive a trace-like view from **session data** after a run.

### 4.1 Where this comes from

- **Runner** loads the session via **`session_service.get_session(app_name, user_id, session_id)`**.
- The returned **`Session`** has **`session.events`**: a chronological list of **`Event`** objects (see **ADK-Memory-and-Session-Runtime-Trace.md**).
- Each **`Event`** has (among others):
  - **`invocation_id`** — Groups events belonging to the same invocation.
  - **`author`** — e.g. `"user"`, `"model"`, or agent/tool name.
  - **`content`** — GenAI `Content` (e.g. text parts).
  - **`timestamp`** — Event time (when available).

### 4.2 Building a simple “trace” from events

- Group **`session.events`** by **`invocation_id`**.
- For each event, use **`event.timestamp`** and **`event.author`** (and any tool/agent info in content or actions) to compute:
  - Which “phase” it is (user turn, model/chat, tool call, etc.).
  - Relative or absolute timings per invocation.

This does not give you the exact same span names as OTel (e.g. `call_llm`, `execute_tool`), but you can infer “model” vs “tool” from `author` and content, and compute durations between events in the same invocation.

### 4.3 Example: list events with invocation and timing

```python
from google.adk.sessions import Session

def summarize_session_trace(session: Session):
    """Group events by invocation and show timing (trace-like summary)."""
    by_inv = {}
    for event in session.events:
        inv = event.invocation_id or "unknown"
        if inv not in by_inv:
            by_inv[inv] = []
        by_inv[inv].append(event)

    for inv_id, events in by_inv.items():
        print(f"Invocation {inv_id}")
        for e in events:
            ts = getattr(e, "timestamp", None) or ""
            print(f"  {ts} author={e.author} has_content={bool(e.content)}")
        print()
```

If your **SessionService** persists events (e.g. **DatabaseSessionService**), you can load the session after a run and run the same logic to get invocation-scoped timing without calling the debug API.

---

## 5. Mapping Dev UI Trace to Code

| What you see in Dev UI | Source |
|------------------------|--------|
| **Invocation** (root, with duration) | OTel root span for the run (e.g. from `_run_with_trace` in `runners.py`) |
| **invoke_agent** `root_agent` | OTel span for the agent run (e.g. `LlmAgent.run_async` → flow) |
| **chat** / **call_llm** | OTel span for the model call (from `google.adk.telemetry` / LLM flow) |
| **execute_tool** `get_current_time` | OTel span for tool execution (from `google.adk.telemetry` / tool execution path) |

So:

- **Programmatic OTel (Method 2)** gives you the same span names and hierarchy.
- **Debug API (Method 1)** returns the same OTel data the Dev UI uses for that session.
- **Session events (Method 3)** give you invocation grouping and timestamps without OTel.

---

## 6. Quick Reference

- **ADK Web debug endpoints**: **`GET /debug/trace/session/{session_id}`** (spans for session), **`GET /debug/trace/{event_id}`** (trace for event). Base URL = your `adk web` host (e.g. `http://localhost:8000`).
- **OTel**: ADK uses OpenTelemetry; configure TracerProvider/exporters before using ADK to capture spans in your own backend.
- **Telemetry helpers**: `google.adk.telemetry` — `trace_call_llm`, `trace_tool_call`, etc. (used internally; no need to call directly for standard traces).
- **Session-based timing**: Use **`session_service.get_session(...)`** then **`session.events`** grouped by **`event.invocation_id`** and **`event.timestamp`** for a trace-like view without OTel.

---

## 7. Example Script

In this repo, **`adk/examples/get_trace_details.py`** demonstrates:

- **Fetching trace from ADK Web**: `python get_trace_details.py --base-url http://localhost:8000 --session-id <session_id>` (or `--event-id <event_id>`). Optionally use `--app-name` and `--user-id` if your server mounts debug under `/apps/.../users/...`.
- **Session-based summary**: Use `get_trace_summary_from_session(session)` in your own code when you have a `Session` object (e.g. in a plugin or after loading the session).

## 8. Related documentation

- **14-ADK-Web-Interface-Analysis.md** — Web API and debug trace endpoints.
- **ADK-Memory-and-Session-Runtime-Trace.md** — Session load, events, and runtime flow.
- **10-Runners-Package.md** — Runner and `run_async` / `_run_with_trace`.
- **09-Other-Packages.md** — `google.adk.telemetry` and trace helpers.
- **20-Token-Usage-and-Context-Management.md** — Session events and invocation_id in context.  
- **examples/get_trace_details.py** — Script to fetch trace from ADK Web and summarize from session.
