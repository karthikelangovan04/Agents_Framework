---
title: markmap
markmap:
  colorFreezeLevel: 2
---

<!-- Open with Markmap (e.g. VSCode: Markmap extension) for mind-map view. No real project IDs or URLs used. -->

# Cloud Run ADK Agent + MCP Server

## 1. Agent Logic (ADK Agent)

### What It Is
The ADK agent is a FastAPI app that runs an LLM agent (Gemini) and connects to a remote MCP server to use tools (e.g. currency exchange). User requests hit the agent; the agent may call MCP tools and return the LLM response.

### Components

- **agent.py**
  - **What:** Defines the LLM agent and MCP tool connection.
  - **Why:** Central place for model, system instruction, and how the agent reaches the MCP server (URL, transport, auth).
  - **LlmAgent:** Wraps Gemini with instruction and tools.
  - **MCPToolset:** Loads tools from the remote MCP server (e.g. `get_exchange_rate`).
  - **SseConnectionParams:** Connects to MCP over SSE (URL + optional headers).
  - **header_provider:** Callback that returns auth headers when the MCP session is created (needed so ID token is fetched at connection time on Cloud Run, not at import time).

- **main.py**
  - **What:** FastAPI app exposing `/`, `/health`, `/chat`.
  - **Why:** Cloud Run needs an HTTP server; sessions and runner need to be wired once.
  - **Runner:** Runs the agent with a session service (run_async streams events).
  - **InMemorySessionService:** Stores conversation state per user/session (no DB).
  - **Session handling:** Before run_async we ensure a session exists (create if missing) so the runner does not fail with "Session not found".
  - **Port:** Uses `PORT` from env (Cloud Run sets it, e.g. 8080).

- **auth_helper.py**
  - **What:** Builds `Authorization: Bearer <id_token>` for requests to the MCP server.
  - **Why:** MCP server is private; Cloud Run validates the ID token. Agent runs as a service account and gets the token via ADC.
  - **get_id_token(audience):** Uses `id_token.fetch_id_token()` with Application Default Credentials; audience is the MCP service base URL (e.g. `https://mcp-server-xxx.run.app`).
  - **get_authenticated_headers(mcp_server_url):** Parses URL to get base (scheme + netloc), gets ID token for that audience, returns headers dict. Used by agent as `header_provider`.

### Flow (Request Path)

1. Request hits `/chat` with `message`, `session_id`, `user_id`.
2. Session is ensured (get or create).
3. Runner runs agent with the user message.
4. Agent may open MCP session (header_provider called → auth_helper → ID token → SSE connection with Bearer).
5. LLM may call MCP tools (e.g. get_exchange_rate); MCP server responds.
6. Response text is collected from runner events and returned as JSON.

---

## 2. MCP Server Logic

### What It Is
A small HTTP service that exposes MCP tools (here: currency exchange). It runs as a separate Cloud Run service and is called by the agent over HTTP (SSE transport).

### Components

- **server.py**
  - **What:** FastMCP app with one tool, served over SSE.
  - **Why:** Keeps tools in a separate service so the agent can call them remotely with auth.
  - **FastMCP:** MCP framework; we use `transport="sse"` and expose `/sse`.
  - **get_exchange_rate:** Tool that calls Frankfurter API and returns rate data.
  - **Host 0.0.0.0:** So Cloud Run can send traffic to the container.
  - **Port:** From `PORT` env (e.g. 8080).

### Flow (Tool Call)

1. Agent establishes SSE session to `MCP_SERVER_URL` (e.g. `https://mcp-server-xxx.run.app/sse`) with Bearer token.
2. Agent sends MCP protocol messages over SSE.
3. When the LLM decides to use a tool, the client sends a tools/call; server runs `get_exchange_rate` and returns result.
4. Agent gets result and continues LLM flow.

---

## 3. Authentication Between Agent and MCP Server

### What It Is
Service-to-service auth: the agent (Cloud Run service) proves to the MCP server (another Cloud Run service) that the request is from a trusted identity. No API keys; Cloud Run uses OIDC ID tokens.

### Why
- MCP server is deployed with `--no-allow-unauthenticated`, so every request must be authenticated.
- Cloud Run validates the `Authorization: Bearer <id_token>` and checks the token’s audience and issuer.

### How It Works

1. **Agent identity:** Agent runs as a service account (e.g. `PROJECT_ID@appspot.gserviceaccount.com` or compute default).
2. **Token:** `auth_helper.get_authenticated_headers(MCP_SERVER_URL)` uses ADC to get an ID token with audience = MCP service base URL (e.g. `https://mcp-server-xxx.run.app`).
3. **Request:** MCP client (SSE) sends this header when connecting. Cloud Run in front of the MCP server validates the token and allows or denies the request.
4. **IAM:** The agent’s service account must have `roles/run.invoker` on the MCP server. Otherwise Cloud Run returns 403 even with a valid token.

### Roles Summary

| Role | Where | Who Has It | Why |
|------|--------|------------|-----|
| **roles/run.invoker** | MCP server (Cloud Run resource) | Agent’s service account | Allows agent to call the MCP Cloud Run service. |
| **roles/aiplatform.user** | Project | Agent’s service account | Allows agent to call Vertex AI (Gemini). |
| (Optional) **roles/iam.serviceAccountUser** | Agent’s service account | Your user | So you can deploy the agent with that service account. |

---

## 4. Data Flow: Input to Final Response

End-to-end path of a user message: who is invoked, how auth and roles are used, and how the final response is returned.

### Step 1: User Input Reaches the Agent

- **Input:** Client sends HTTP POST to the agent’s `/chat` endpoint (e.g. `https://adk-agent-xxx.run.app/chat`).
- **Payload (example):** `{"message": "What is 100 USD in EUR?", "session_id": "test-1", "user_id": "user-1"}`.
- **Who receives it:** The **ADK Agent** Cloud Run service (FastAPI in `main.py`).
- **Auth at this step:** None required if the agent is deployed with `--allow-unauthenticated`. If the agent were private, the client would need to send a Bearer ID token; Cloud Run would validate it.

### Step 2: Agent Service Handles the Request

- **main.py** receives the request.
- **Session:** Looks up or creates a session for `(app_name, user_id, session_id)` via `InMemorySessionService` so the runner has a valid session.
- **Runner:** Calls `runner.run_async(user_id, session_id, new_message)` with the user message as `Content(role='user', parts=[...])`.
- **No external call yet:** Everything so far is inside the agent container.

### Step 3: Agent Needs MCP Tools → Authentication Flow Starts

- **Runner** starts the **LlmAgent** (Gemini) with the message.
- **LLM** may decide to use a tool (e.g. `get_exchange_rate`). The agent’s **MCPToolset** must then talk to the MCP server.
- **MCP client (in agent)** opens a session to `MCP_SERVER_URL` (e.g. `https://mcp-server-xxx.run.app/sse`).
  - **header_provider** is invoked: agent code calls `get_mcp_headers(context)`.
  - **auth_helper.get_authenticated_headers(MCP_SERVER_URL)** runs:
    - Parses `MCP_SERVER_URL` → base URL (e.g. `https://mcp-server-xxx.run.app`).
    - Calls **get_id_token(audience=base_url)**.
    - **get_id_token** uses **Application Default Credentials** (ADC): on Cloud Run, the container runs as a **service account**; ADC provides that identity.
    - **google.oauth2.id_token.fetch_id_token(request, audience)** returns an **OIDC ID token** for that audience.
  - Returns `{"Authorization": "Bearer <id_token>"}` to the MCP client.
- **MCP client** connects to the MCP server’s SSE endpoint with this `Authorization` header.

### Step 4: MCP Server Receives the Request (Auth Check by Cloud Run)

- **Request:** From the agent’s container to the MCP server’s public URL (e.g. `https://mcp-server-xxx.run.app/sse`), including `Authorization: Bearer <id_token>`.
- **Who validates auth:** **Cloud Run** (the MCP server’s front proxy), not the app code.
  - Cloud Run checks the ID token: signature, audience (must match MCP service URL), expiry, issuer.
  - Cloud Run checks **IAM:** the token’s subject (the agent’s **service account**) must have **roles/run.invoker** on the **mcp-server** Cloud Run service. If not → **403 Forbidden**.
- **If auth passes:** Request is forwarded to the MCP server container (FastMCP). The app code does not see the token; it just handles MCP protocol.

### Step 5: MCP Protocol and Tool Execution

- **MCP server** (FastMCP) receives MCP messages over the SSE connection.
- **Tools/list** (if needed): Server returns available tools (e.g. `get_exchange_rate`).
- **Tools/call:** When the LLM asks for a rate, the client sends a tool call; server runs **get_exchange_rate(currency_from="USD", currency_to="EUR", ...)**.
- **get_exchange_rate** in **server.py** calls the **Frankfurter API** (external HTTP), then returns the result in MCP format to the client.
- **Agent** receives the tool result and passes it back into the **LLM** (Gemini).

### Step 6: LLM and Vertex AI (Agent → Vertex)

- **Agent** sends the conversation (user message + tool result) to **Vertex AI (Gemini)** for the next turn.
- **Auth:** The agent uses ADC again (same service account). Vertex AI checks that the caller has **roles/aiplatform.user** on the **project**. No token is sent in the doc; the client library uses ADC under the hood.
- **Response:** Gemini returns the model reply (e.g. “100 USD is 84.56 EUR.”).

### Step 7: Agent Collects Response and Returns to Client

- **Runner** streams events back; **main.py** collects content from events (e.g. `event.content.parts[].text`).
- **Response body:** `{"response": "100 USD is 84.56 EUR.", "session_id": "test-1"}`.
- **HTTP:** FastAPI returns 200 and this JSON to the original client.

### Data Flow Summary (Services and Roles)

| Step | From | To | What happens | Role / auth |
|------|------|----|----------------|-------------|
| 1 | Client | ADK Agent (Cloud Run) | POST /chat with message | Optional: caller auth if agent is private |
| 2 | main.py | Runner / Agent | Session + run_async | None |
| 3 | Agent (MCP client) | auth_helper | Get ID token for MCP URL | ADC = agent’s service account |
| 4 | Agent | MCP Server (Cloud Run) | SSE connection with Bearer token | **roles/run.invoker** on mcp-server (agent SA) |
| 5 | MCP server | Frankfurter API | get_exchange_rate HTTP call | None (public API) |
| 6 | Agent | Vertex AI (Gemini) | LLM request | **roles/aiplatform.user** on project (agent SA) |
| 7 | Agent | Client | JSON response | None |

### Diagram (Linear)

```
[Client]
   | POST /chat { message, session_id, user_id }
   v
[ADK Agent - Cloud Run]
   | main.py: session get/create, runner.run_async
   v
[LlmAgent] --> needs tool? --> [header_provider] --> [auth_helper: get_id_token(MCP base URL)]
   |                                                    | ADC → ID token
   |                                                    v
   | MCP client connects to MCP_SERVER_URL/sse with Authorization: Bearer <token>
   v
[MCP Server - Cloud Run]
   | Cloud Run validates token + IAM (run.invoker for agent SA)
   v
[FastMCP] --> tools/call get_exchange_rate --> [Frankfurter API] --> result
   |
   v result back to agent
[LlmAgent] --> [Vertex AI / Gemini]  (ADC, roles/aiplatform.user)
   |
   v model reply
[main.py] --> collect events --> JSON { response, session_id }
   v
[Client]
```

---

## 5. Dockerfiles (What & Why)

### ADK Agent Dockerfile

- **Base image:** `python:3.12-slim`
  - **What:** Official slim Python 3.12 image.
  - **Why:** 3.12 has better async/task context behavior; helps avoid certain MCP/AnyIO issues; keeps image smaller than full Python image.
- **WORKDIR /app:** All app code and run context live here.
- **COPY requirements.txt** then **RUN pip install**
  - **What:** Install dependencies before copying code.
  - **Why:** Better layer caching; code changes don’t invalidate the dependency layer.
- **COPY agent.py main.py auth_helper.py**
  - **What:** Application code.
  - **Why:** Agent, FastAPI app, and auth helper must be in the image.
- **EXPOSE 8080:** Documents that the app listens on 8080; Cloud Run still sets `PORT`.
- **CMD ["python", "main.py"]:** Starts the FastAPI app (uvicorn inside main).

### MCP Server Dockerfile

- **Base image:** `python:3.11-slim`
  - **What:** Slim Python 3.11 image.
  - **Why:** Smaller image; MCP server is simple and doesn’t need 3.12 for the same reasons as the agent.
- **COPY requirements.txt** then **RUN pip install**
  - **What:** Install fastmcp, httpx, etc.
  - **Why:** Same caching benefit as agent.
- **COPY server.py:** Only app file.
- **EXPOSE 8080:** Cloud Run sets `PORT`; default 8080 for local consistency.
- **CMD ["python", "server.py"]:** Starts FastMCP with `transport="sse"`.

---

## 6. Onboarding: From Google Auth to Deployed Services

### 5.1 Google Auth (What & Why)

- **gcloud auth login**
  - **What:** Interactive login for your user account.
  - **Why:** Needed to use gcloud and to deploy (build, deploy, IAM).
- **gcloud config set project PROJECT_ID**
  - **What:** Sets default project for gcloud commands.
  - **Why:** All deploy and IAM commands target this project.
- **gcloud auth application-default login**
  - **What:** Writes Application Default Credentials (ADC) for your user to a well-known path.
  - **Why:** Agent and scripts that use client libraries (e.g. Vertex AI, ID token) use ADC when no explicit key is set. Required for local runs and for Cloud Build/service accounts that assume your identity during setup.

### 5.2 Enable APIs (What & Why)

- **Cloud Run API** (e.g. run.googleapis.com or cloudrun.googleapis.com)
  - **What:** Enables deploying and running services on Cloud Run.
  - **Why:** Both agent and MCP server are Cloud Run services.
- **Cloud Build API**
  - **What:** Builds container images from Dockerfile and pushes to the registry.
  - **Why:** `gcloud builds submit` uses Cloud Build.
- **Vertex AI API** (aiplatform.googleapis.com)
  - **What:** Enables use of Gemini (and other Vertex models).
  - **Why:** Agent uses Vertex AI for the LLM.
- **Artifact Registry / Container Registry**
  - **What:** Stores built images (e.g. gcr.io or Artifact Registry).
  - **Why:** Cloud Run runs images from a registry.

### 5.3 Create / Use Service Accounts

- **Default compute or appspot account**
  - **What:** e.g. `PROJECT_NUMBER-compute@developer.gserviceaccount.com` or `PROJECT_ID@appspot.gserviceaccount.com`.
  - **Why:** Cloud Run can run as this identity; we grant it `roles/run.invoker` on MCP and `roles/aiplatform.user` on the project.
- **No extra “creation” step** if you use the default; deployment creates or uses it.

### 5.4 Deploy MCP Server

- Build image (e.g. from mcp-server directory): `gcloud builds submit --tag gcr.io/PROJECT_ID/mcp-server`
  - **What:** Builds the MCP server Docker image and pushes it.
  - **Why:** Cloud Run needs an image in the project’s registry.
- Deploy: `gcloud run deploy mcp-server --image gcr.io/PROJECT_ID/mcp-server --no-allow-unauthenticated ...`
  - **What:** Creates/updates the MCP Cloud Run service, private (auth required).
  - **Why:** So only the agent (with valid ID token and run.invoker) can call it.
- Get URL: `gcloud run services describe mcp-server --format 'value(status.url)'`
  - **What:** Base URL of the service (e.g. `https://mcp-server-xxx.run.app`).
  - **Why:** Agent needs `MCP_SERVER_URL = base_url + "/sse"`.

### 5.5 Set MCP_SERVER_URL and Deploy Agent

- Export: `export MCP_SERVER_URL=https://mcp-server-xxx.run.app/sse` (example only).
- Deploy agent: run deploy script or `gcloud run deploy adk-agent ... --set-env-vars MCP_SERVER_URL=...,GOOGLE_GENAI_USE_VERTEXAI=TRUE,...`
  - **What:** Builds and deploys the agent with env vars.
  - **Why:** Agent must know where the MCP server is and that it uses Vertex AI.

### 5.6 IAM: Agent → MCP and Vertex

- **Grant run.invoker on MCP server to agent’s service account**
  - **What:** `gcloud run services add-iam-policy-binding mcp-server --member="serviceAccount:AGENT_SA" --role="roles/run.invoker" ...`
  - **Why:** Without this, MCP server returns 403 to the agent.
- **Grant aiplatform.user on project to agent’s service account**
  - **What:** `gcloud projects add-iam-policy-binding PROJECT_ID --member="serviceAccount:AGENT_SA" --role="roles/aiplatform.user"`
  - **Why:** Agent needs this to call Vertex AI (Gemini).

---

## 7. All Commands (Reference Only — Use Example Values)

### Auth and project

```bash
gcloud auth login
gcloud config set project YOUR_PROJECT_ID
gcloud auth application-default login
```

### APIs

```bash
gcloud services enable run.googleapis.com --project YOUR_PROJECT_ID
gcloud services enable cloudbuild.googleapis.com --project YOUR_PROJECT_ID
gcloud services enable aiplatform.googleapis.com --project YOUR_PROJECT_ID
gcloud services enable artifactregistry.googleapis.com --project YOUR_PROJECT_ID
```

### MCP server deploy

```bash
cd cloud-run-deployment/mcp-server
gcloud builds submit --tag gcr.io/YOUR_PROJECT_ID/mcp-server --project YOUR_PROJECT_ID
gcloud run deploy mcp-server --image gcr.io/YOUR_PROJECT_ID/mcp-server --platform managed --region REGION --no-allow-unauthenticated --memory 512Mi --cpu 1 --timeout 300 --max-instances 10 --project YOUR_PROJECT_ID
```

### Get MCP URL and set for agent

```bash
MCP_SERVER_URL=$(gcloud run services describe mcp-server --platform managed --region REGION --project YOUR_PROJECT_ID --format 'value(status.url)')
export MCP_SERVER_URL="${MCP_SERVER_URL}/sse"
```

### Agent deploy

```bash
cd cloud-run-deployment/adk-agent
gcloud builds submit --tag gcr.io/YOUR_PROJECT_ID/adk-agent --project YOUR_PROJECT_ID
gcloud run deploy adk-agent --image gcr.io/YOUR_PROJECT_ID/adk-agent --platform managed --region REGION --allow-unauthenticated --set-env-vars "GOOGLE_CLOUD_PROJECT=YOUR_PROJECT_ID,GOOGLE_CLOUD_LOCATION=REGION,GOOGLE_GENAI_USE_VERTEXAI=TRUE,MCP_SERVER_URL=${MCP_SERVER_URL},GOOGLE_MODEL=gemini-2.5-flash" ... --project YOUR_PROJECT_ID
```

### IAM (agent → MCP)

```bash
# Use the same REGION and YOUR_PROJECT_ID; AGENT_SA = service account used by adk-agent
gcloud run services add-iam-policy-binding mcp-server --member="serviceAccount:AGENT_SA" --role="roles/run.invoker" --region REGION --project YOUR_PROJECT_ID
```

### IAM (Vertex AI)

```bash
gcloud projects add-iam-policy-binding YOUR_PROJECT_ID --member="serviceAccount:AGENT_SA" --role="roles/aiplatform.user"
```

### Test (example only)

```bash
curl -X POST https://adk-agent-xxx.run.app/chat -H 'Content-Type: application/json' -d '{"message": "What is 100 USD in EUR?", "session_id": "test-1", "user_id": "test-user"}'
```

---

## 8. HTTP Stream (Streamable HTTP) vs SSE

### What Is Streamable HTTP (HTTP Stream)

- **What:** MCP transport where client and server exchange a long-lived HTTP request/response (or bidirectional stream) and send MCP messages over it.
- **Why used:** One of the standard MCP remote transports; efficient for some clients.
- **In ADK:** Implemented via `StreamableHTTPConnectionParams`; client uses a streamable HTTP connection to the MCP server endpoint (e.g. `/mcp`).

### What Is SSE (Server-Sent Events)

- **What:** HTTP-based, one-way stream: server sends events (text/event-stream) to the client; client sends requests (e.g. POST) for new operations. MCP can run on top of this.
- **Why used:** Simpler async model in some environments; single long-lived response from server; avoids some bidirectional streaming issues.
- **In ADK:** Implemented via `SseConnectionParams`; endpoint is typically `/sse`. FastMCP supports `transport="sse"`.

### Differences (Short)

| Aspect | Streamable HTTP | SSE |
|--------|------------------|-----|
| Direction | Bidirectional stream over HTTP | Server pushes events; client uses separate requests |
| Endpoint | Often `/mcp` | Often `/sse` |
| Connection params | StreamableHTTPConnectionParams | SseConnectionParams |
| Async context | Can trigger cancel-scope/task-boundary issues in some runtimes | Different code path; can avoid those issues |
| Auth | Same (e.g. Bearer ID token) | Same |

### Why We Switched to SSE

- With Streamable HTTP on Cloud Run we hit: “Attempted to exit cancel scope in a different task than it was entered in” (AnyIO/task boundaries).
- Switching to SSE uses a different client path and avoids that failure while keeping the same auth and IAM.

---

## 9. Issue We Hit (Cancel Scope / TaskGroup)

### What Happened

- **Symptom:** Agent on Cloud Run failed to create MCP session with errors like “unhandled errors in a TaskGroup” and “Attempted to exit cancel scope in a different task than it was entered in”.
- **Where:** MCP client code using Streamable HTTP; AnyIO cancel scope entered in one asyncio task and exited in another when running in Cloud Run’s request context.
- **Why:** Cloud Run’s request lifecycle and the way the runner/MCP client start tasks don’t align with AnyIO’s expectations for that transport.

### What We Did

- **Python 3.12:** Improved async context; issue persisted with Streamable HTTP.
- **Dynamic auth:** Switched to `header_provider` so ID token is fetched when the connection is established; fixed auth, not the crash.
- **Session and runner:** Ensured session exists and runner has `app_name`; fixed “Session not found”, not the crash.
- **Workaround:** Use **SSE** instead of Streamable HTTP (`SseConnectionParams`, MCP server with `transport="sse"`). Same auth and IAM; different transport path that doesn’t hit the cancel-scope bug.

### Doc

- See **KNOWN_ISSUES.md** in this repo for full description, stack trace, and references.

---

## 10. Cleanup Process and Scripts

### What Cleanup Does

- Removes Cloud Run services (adk-agent, mcp-server) so no more compute or request charges.
- Optionally deletes container images from the registry (saves a small storage cost).
- Optionally removes IAM bindings (run.invoker on mcp-server, aiplatform.user on project) so the project is back to a clean state.

### Script: cleanup.sh

- **Location:** `cloud-run-deployment/scripts/cleanup.sh`
- **Requires:** `GOOGLE_CLOUD_PROJECT` (and optionally `GOOGLE_CLOUD_REGION`) set; no real URLs or project IDs in the script, use env.
- **Steps:**
  1. Asks for confirmation (“yes”) before deleting.
  2. Deletes Cloud Run services: `adk-agent`, `mcp-server`.
  3. Deletes container images: e.g. `gcr.io/PROJECT_ID/adk-agent`, `gcr.io/PROJECT_ID/mcp-server`.
  4. Asks whether to remove IAM bindings; if yes, removes `roles/aiplatform.user` from project and `roles/run.invoker` from mcp-server for the service account used.
- **Note:** Does not disable APIs; documents how to disable Cloud Run, Vertex AI, Cloud Build if desired.

### Retaining for Fast Restart

- **Keep images and IAM:** Don’t run the image-delete steps; don’t remove IAM. Then you only delete the two Cloud Run services. Cost when “stopped”: ~\$0 for compute; small storage for images. To restart: redeploy MCP server, set `MCP_SERVER_URL`, redeploy agent (same images and IAM).
- **Full cleanup:** Run cleanup.sh and choose to remove IAM and delete images when prompted. Re-onboarding later: auth, APIs, deploy MCP, set URL, deploy agent, IAM again.

---

## 11. Summary Diagram (Conceptual)

- **User** → HTTP POST /chat → **ADK Agent (Cloud Run)**  
  - Agent uses **Vertex AI (Gemini)** for LLM.  
  - Agent uses **MCP client (SSE)** to call **MCP Server (Cloud Run)** with **Bearer ID token**.  
  - MCP server validates token (Cloud Run IAM) and runs **get_exchange_rate** (Frankfurter API).  
- **IAM:** Agent SA has `run.invoker` on MCP server and `aiplatform.user` on project.  
- **Transport:** SSE to `/sse`; auth and IAM unchanged from Streamable HTTP.
