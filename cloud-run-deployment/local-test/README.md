# Local Test (No Authentication)

Same setup as Cloud Run deployment but runs **locally** with **no authentication**. Uses **SSE** transport for MCP (avoids Streamable HTTP cancel-scope issues).

## Setup

### 1. Create venv (Python)

```bash
cd cloud-run-deployment/local-test
python3 -m venv .venv
source .venv/bin/activate   # On Windows: .venv\Scripts\activate
```

### 2. Install dependencies

```bash
# MCP server
pip install -r mcp-server/requirements.txt

# ADK agent (from local-test root)
pip install -r adk-agent/requirements.txt
```

### 3. Configure environment

```bash
cp .env.example .env
# Edit .env:
#   GOOGLE_API_KEY=your-actual-key
#   MCP_SERVER_URL=http://localhost:9090/sse   (required for SSE)
```

Get your API key: https://aistudio.google.com/apikey

## Run (2 terminals)

**Terminal 1 – MCP server (port 9090):**
```bash
cd local-test
source .venv/bin/activate
python mcp-server/server.py
```

**Terminal 2 – ADK agent (port 8081):**
```bash
cd local-test
source .venv/bin/activate
export $(grep -v '^#' .env | xargs)
# If .env has MCP_SERVER_URL=.../mcp, override for SSE:
export MCP_SERVER_URL=http://localhost:9090/sse
python adk-agent/main.py
```

## Test

```bash
curl -X POST http://localhost:8081/chat \
  -H 'Content-Type: application/json' \
  -d '{"message": "What is 100 USD in EUR?", "session_id": "test1"}'
```

## Using UV instead of pip/venv

You can use UV for faster installs:

```bash
# Install UV: curl -LsSf https://astral.sh/uv/install.sh | sh
uv venv .venv
source .venv/bin/activate
uv pip install -r mcp-server/requirements.txt
uv pip install -r adk-agent/requirements.txt
```

**Python vs UV**: UV is a package manager (like pip). It uses the same Python interpreter. The MCP async issue seen on Cloud Run is **not** caused by UV vs pip—it comes from Cloud Run’s request handling and AnyIO’s CancelScope. Locally, both pip and UV behave the same.

## Differences from Cloud Run deployment

| Aspect | Local test | Cloud Run |
|--------|------------|-----------|
| Auth | None | ID tokens (service-to-service) |
| LLM | Gemini API key | Vertex AI (ADC) |
| MCP server | localhost:9090 | Private Cloud Run service |
| ADK agent | localhost:8081 | Cloud Run service |
