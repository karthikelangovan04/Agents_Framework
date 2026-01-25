# Runnable vs API Execution Models in Google ADK

**File Path**: `docs/12-Runnable-vs-API-Execution-Models.md`

## Overview

Google ADK supports two distinct ways to run agents:

1. **Runnable (direct execution)** — You use a `Runner` and call `runner.run()` (or `run_async()`). The agent runs **in your process**, and you consume events directly. Typical for CLIs, scripts, and local demos.

2. **API (server execution)** — You use `App` + uvicorn. The agent is exposed as an **HTTP API**. There is no `Runner` in your code; the agent runs when **clients send HTTP requests** to the server. Typical for web apps, A2A remote agents, and production services.

This document explains both models, how they differ, and when to use each. It does not change any existing documentation.

---

## The Key Difference

| Aspect | Runnable (Runner) | API (App + uvicorn) |
|--------|-------------------|----------------------|
| **Execution trigger** | Your code calls `runner.run(...)` | HTTP requests hit the server |
| **Runner in your code?** | Yes — you create and use `Runner` | No — you only create `App(agent=...)` |
| **Where agent runs** | Same process as your script | Server process (invoked per request) |
| **Interaction** | Loop: `input` → `runner.run` → print events | Clients call endpoints (e.g. `/generate`, `/agent_card.json`) |
| **Typical use** | CLI, scripts, local testing | Web app, A2A server, production API |

---

## Model 1: Runnable (Runner) — Direct Execution

### What “runnable” means here

“Runnable” here means **you explicitly run the agent** by creating a `Runner`, passing it an `Agent`, and calling `runner.run()` (or `run_async()`). The Runner is the **execution engine**: it runs the agent, manages sessions, and streams events back to you.

### Flow

```
Your script  →  Runner(agent=...)  →  runner.run(user_input)  →  agent runs in-process  →  you iterate over events
```

### Example: `simple_agent.py`

```python
from google.adk import Agent
from google.adk.runners import Runner

agent = Agent(name="simple_agent", model="gemini-1.5-flash", ...)
runner = Runner(agent=agent)   # Runner executes the agent

# You trigger execution
async for event in runner.run(user_input):
    if hasattr(event, 'content') and event.content:
        print(event.content)
```

- **Runner**: You create it and use it.
- **Execution**: Happens when **your code** calls `runner.run(...)`.
- **Output**: You handle events (e.g. `content`) directly in the same process.

Other **runnable-style** examples in this repo: `tool_agent.py`, `multi_agent.py`. They all use `Runner` + `runner.run()` and run the agent **locally** in the same process.

---

## Model 2: API (App) — Server / HTTP Execution

### What “API” means here

The agent is exposed as an **HTTP API**. You create an `App` with an `Agent` and run it with **uvicorn**. You do **not** create or use a `Runner` in your own code. The framework uses its own machinery to execute the agent when **HTTP requests** arrive.

### Flow

```
Client  →  HTTP request  →  App (uvicorn)  →  server handles request  →  agent runs in server process  →  HTTP response
```

### Example: `remote_agent_server.py`

```python
from google.adk import Agent
from google.adk.apps import App
import uvicorn

math_agent = Agent(name="remote_math_agent", model="gemini-1.5-flash", ...)
app = App(agent=math_agent)   # App exposes agent as API — no Runner in your code

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

- **Runner**: Not used in **your** code. The server runs the agent via its own execution path when requests come in.
- **Execution**: Triggered by **clients** calling the API (e.g. `/generate`, A2A endpoints, or `/agent_card.json`).
- **Output**: Returned as HTTP responses (e.g. JSON, streams) to the client.

So this example **does not use Runner** and **does use the API**: the agent is run only when the API is called.

Other **API-style** examples: `web_app.py`. Both `remote_agent_server` and `web_app` use `App` + uvicorn and no `Runner`.

---

## Why `remote_agent_server` Has No Runner

`remote_agent_server.py` is an **A2A remote agent**: it is meant to be **invoked by other agents or clients** over the network, not by a local REPL loop.

- **Goal**: Expose the math agent as a **service** (HTTP API).
- **Means**: `App` + uvicorn. The App registers routes (e.g. for A2A, agent card, generate). When a client sends a request, the **server** runs the agent and responds.
- **No Runner in code**: You don’t call `runner.run()` anywhere. Execution is **request-driven**, not **script-driven**.

So it’s “not runnable” in the sense of “no Runner + `runner.run()` in your code,” and it “uses the API” in the sense that the only way to use the agent is via **HTTP**.

---

## The Client Side: `remote_agent_client.py` (Hybrid)

The **client** that talks to `remote_agent_server` **does** use a Runner:

```python
remote_math = RemoteA2aAgent(name="remote_math", agent_card_url="http://localhost:8000/agent_card.json")
local_agent = Agent(..., sub_agents=[remote_math])
runner = Runner(agent=local_agent)

async for event in runner.run(user_input):
    ...
```

- **Locally**: The client uses **Runnable-style** execution — `Runner` + `runner.run()`. Your code drives the loop.
- **Remotely**: When the coordinator delegates to `remote_math`, that **invocation goes over HTTP** to `remote_agent_server`’s API. The **remote** agent runs in the **server** process via the API.

So:

- **Client** = Runnable (Runner) + **API** (HTTP) to call the remote agent.
- **Server** = API only (App + uvicorn, no Runner in your code).

---

## Side-by-Side Summary

| Example | Runner? | Execution model | How the agent is used |
|--------|--------|------------------|------------------------|
| `simple_agent.py` | Yes | Runnable | Your script calls `runner.run()`, agent runs locally. |
| `tool_agent.py` | Yes | Runnable | Same as above, with tools. |
| `multi_agent.py` | Yes | Runnable | Same as above, with sub-agents. |
| `remote_agent_client.py` | Yes | Runnable + API | Client uses Runner; remote agent is called via API. |
| `remote_agent_server.py` | No | API only | Server exposes agent as HTTP API; no Runner in code. |
| `web_app.py` | No | API only | Same as above; browser or clients use HTTP. |

---

## Is Runner Only for Dev and Testing?

**No.** The **Runner** is the execution engine for agents. It is used in **both development and production**.

What differs is *how* you use it:

| Use case | Runner? | Details |
|----------|---------|---------|
| **Production** | Yes | Use **`run_async()`** (not the sync `run()`). Configure proper services: `session_service`, `memory_service`, `artifact_service`, etc. |
| **Production (HTTP API)** | Yes, under the hood | **App** + uvicorn uses a Runner internally to execute the agent when HTTP requests arrive. You don’t create a Runner yourself, but it’s still there. |
| **Development / testing** | Yes | Use **`Runner`** with **`run_async()`**, or **`InMemoryRunner`** for quick local runs (in-memory services, no GCP/session setup). |
| **Dev-only** | — | The sync **`run()`** method is a “local testing and convenience” wrapper; prefer **`run_async()`** for production. **`InMemoryRunner`** is for testing/prototyping only. |

So: **Runner** is not “dev only.” Use **`run_async()`** and proper services for production. Use **App** when you want an HTTP API; it still runs agents via Runner internally.

---

## When to Use Which

**Use Runnable (Runner) directly:**

- CLI tools, REPL-style demos, local scripts.
- Quick experimentation, debugging, tutorials.
- Backend services where your code calls `runner.run_async()` (e.g. your own API that wraps the Runner). Use proper services and `run_async()` for production.

**Use API (App + uvicorn):**

- Web apps, REST APIs, or A2A remote agents.
- Production services that others call over HTTP.
- When you want the agent to run only in response to **HTTP requests**, without writing Runner loops yourself. App handles Runner usage internally.

---

## Summary

- **Runnable** = you use **`Runner`** and **`runner.run()`** to execute the agent **in your process**. Examples: `simple_agent`, `tool_agent`, `multi_agent`; the **client** in `remote_agent_client` also uses this.
- **API** = you use **`App`** + **uvicorn** to expose the agent as an **HTTP API**. No Runner in your code; the agent runs when **clients hit the API**. Examples: `remote_agent_server`, `web_app`.

`remote_agent_server` is “not runnable” (no Runner, no `runner.run()`) and “uses the API” because it only runs the agent via the HTTP API served by `App` + uvicorn.

---

## Related Documentation

- [Runners Package](10-Runners-Package.md) — Runner and execution engine
- [Apps Package](05-Apps-Package.md) — App and web/API deployment
- [A2A Package](04-A2A-Package.md) — Agent-to-Agent and remote agents
