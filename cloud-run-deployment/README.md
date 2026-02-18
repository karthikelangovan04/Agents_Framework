# Cloud Run Deployment Guide: MCP Server and ADK Agent

This guide provides step-by-step instructions for deploying an MCP server and an ADK agent as separate Cloud Run services with service-to-service authentication.

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    Cloud Run Services                         │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌──────────────────┐         ┌──────────────────┐         │
│  │   MCP Server     │◄────────│   ADK Agent      │         │
│  │  (Private)       │  Auth   │  (Public/Private)│         │
│  │                  │  Token  │                  │         │
│  │  - FastMCP       │         │  - LlmAgent       │         │
│  │  - Currency API  │         │  - MCPToolset     │         │
│  └──────────────────┘         └──────────────────┘         │
│         │                              │                      │
│         │                              │                      │
│         └──────────┬───────────────────┘                      │
│                    │                                            │
│                    ▼                                            │
│         ┌──────────────────────┐                              │
│         │  Vertex AI / Gemini  │                              │
│         │  (for LLM)           │                              │
│         └──────────────────────┘                              │
└─────────────────────────────────────────────────────────────┘
```

## Prerequisites

1. **Google Cloud Project** with billing enabled
2. **gcloud CLI** installed and authenticated
3. **Required APIs enabled**:
   - Cloud Run API
   - Cloud Build API
   - Vertex AI API
   - Artifact Registry API

## Step 1: Initial Setup

### 1.1 Set Environment Variables

```bash
export GOOGLE_CLOUD_PROJECT="your-project-id"
export GOOGLE_CLOUD_REGION="us-central1"
```

### 1.2 Enable Required APIs

```bash
gcloud services enable \
  cloudrun.googleapis.com \
  cloudbuild.googleapis.com \
  aiplatform.googleapis.com \
  artifactregistry.googleapis.com \
  --project ${GOOGLE_CLOUD_PROJECT}
```

### 1.3 Authenticate gcloud

```bash
gcloud auth login
gcloud config set project ${GOOGLE_CLOUD_PROJECT}
```

### 1.4 Set Up Application Default Credentials

For local testing and Cloud Run service-to-service authentication:

```bash
gcloud auth application-default login
```

## Step 2: Deploy MCP Server

The MCP server will be deployed as a **private** Cloud Run service (authentication required).

### 2.1 Navigate to MCP Server Directory

```bash
cd cloud-run-deployment/mcp-server
```

### 2.2 Review Configuration

- **server.py**: FastMCP server exposing currency exchange rate tool
- **requirements.txt**: Python dependencies
- **Dockerfile**: Container configuration

### 2.3 Deploy Using Script

```bash
cd ../scripts
./deploy-mcp-server.sh
```

**Or manually:**

```bash
cd ../mcp-server

# Build and push image
gcloud builds submit --tag gcr.io/${GOOGLE_CLOUD_PROJECT}/mcp-server

# Deploy to Cloud Run (private - requires authentication)
gcloud run deploy mcp-server \
  --image gcr.io/${GOOGLE_CLOUD_PROJECT}/mcp-server \
  --platform managed \
  --region ${GOOGLE_CLOUD_REGION} \
  --no-allow-unauthenticated \
  --memory 512Mi \
  --cpu 1 \
  --timeout 300 \
  --max-instances 10
```

### 2.4 Get MCP Server URL

After deployment, get the service URL:

```bash
MCP_SERVER_URL=$(gcloud run services describe mcp-server \
  --platform managed \
  --region ${GOOGLE_CLOUD_REGION} \
  --format 'value(status.url)')

echo "MCP Server URL: ${MCP_SERVER_URL}/sse"
```

**Save this URL** - you'll need it for the ADK agent configuration.

## Step 3: Set Up Service-to-Service Authentication

The ADK agent needs permission to invoke the MCP server.

### 3.1 Grant IAM Permissions

Run the setup script:

```bash
cd scripts
./setup-iam.sh
```

**Or manually:**

```bash
# Get the service account (default compute service account)
AGENT_SERVICE_ACCOUNT="${GOOGLE_CLOUD_PROJECT}@appspot.gserviceaccount.com"

# Grant Cloud Run Invoker role
gcloud run services add-iam-policy-binding mcp-server \
  --member="serviceAccount:${AGENT_SERVICE_ACCOUNT}" \
  --role="roles/run.invoker" \
  --region ${GOOGLE_CLOUD_REGION}
```

This allows the ADK agent's service account to authenticate and invoke the MCP server.

## Step 4: Configure ADK Agent

### 4.1 Set MCP Server URL

Update the environment variables for the ADK agent:

```bash
cd ../adk-agent

# Create .env file from example
cp .env.example .env

# Edit .env and set:
# MCP_SERVER_URL=https://mcp-server-xxx-uc.a.run.app/sse
```

Or set it as an environment variable:

```bash
export MCP_SERVER_URL="https://mcp-server-xxx-uc.a.run.app/sse"
```

### 4.2 Configure LLM Authentication

The ADK agent needs to authenticate to Vertex AI for the LLM. Choose one:

#### Option A: Vertex AI (Recommended for Production)

Uses Application Default Credentials (ADC) - automatically available in Cloud Run:

```bash
# In .env or environment variables:
GOOGLE_GENAI_USE_VERTEXAI=TRUE
GOOGLE_CLOUD_PROJECT=your-project-id
GOOGLE_CLOUD_LOCATION=us-central1
```

#### Option B: Google AI Studio API Key

For development/testing:

```bash
# Get API key from: https://aistudio.google.com/app/apikey
# In .env or environment variables:
GOOGLE_GENAI_USE_VERTEXAI=FALSE
GOOGLE_API_KEY=your-api-key-here
```

**Note:** For Cloud Run deployment, Vertex AI (Option A) is recommended as it uses the service account automatically.

## Step 5: Deploy ADK Agent

### 5.1 Review Configuration

- **agent.py**: ADK agent with MCP toolset
- **main.py**: FastAPI application
- **auth_helper.py**: Service-to-service authentication helper
- **requirements.txt**: Python dependencies
- **Dockerfile**: Container configuration

### 5.2 Deploy Using Script

```bash
cd ../scripts

# Set MCP_SERVER_URL if not already set
export MCP_SERVER_URL="https://mcp-server-xxx-uc.a.run.app/sse"

./deploy-adk-agent.sh
```

**Or manually:**

```bash
cd ../adk-agent

# Build and push image
gcloud builds submit --tag gcr.io/${GOOGLE_CLOUD_PROJECT}/adk-agent

# Deploy to Cloud Run
gcloud run deploy adk-agent \
  --image gcr.io/${GOOGLE_CLOUD_PROJECT}/adk-agent \
  --platform managed \
  --region ${GOOGLE_CLOUD_REGION} \
  --allow-unauthenticated \
  --memory 1Gi \
  --cpu 2 \
  --timeout 300 \
  --max-instances 10 \
  --set-env-vars "GOOGLE_CLOUD_PROJECT=${GOOGLE_CLOUD_PROJECT},GOOGLE_CLOUD_LOCATION=${GOOGLE_CLOUD_REGION},GOOGLE_GENAI_USE_VERTEXAI=TRUE,MCP_SERVER_URL=${MCP_SERVER_URL},GOOGLE_MODEL=gemini-2.5-flash" \
  --service-account "${GOOGLE_CLOUD_PROJECT}@appspot.gserviceaccount.com"
```

### 5.3 Get ADK Agent URL

```bash
AGENT_URL=$(gcloud run services describe adk-agent \
  --platform managed \
  --region ${GOOGLE_CLOUD_REGION} \
  --format 'value(status.url)')

echo "ADK Agent URL: ${AGENT_URL}"
```

## Step 6: Test the Deployment

### 6.1 Test ADK Agent Endpoint

```bash
curl -X POST ${AGENT_URL}/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "What is 100 USD in EUR?",
    "session_id": "test-session"
  }'
```

Expected response:

```json
{
  "response": "Based on the current exchange rate, 100 USD is approximately X EUR...",
  "session_id": "test-session"
}
```

### 6.2 Test Health Endpoints

```bash
# ADK Agent health check
curl ${AGENT_URL}/health

# MCP Server (requires authentication)
curl ${MCP_SERVER_URL}/health \
  -H "Authorization: Bearer $(gcloud auth print-identity-token)"
```

## Step 7: Verify Authentication Flow

### 7.1 Check Service Logs

**ADK Agent logs:**

```bash
gcloud run services logs read adk-agent \
  --region ${GOOGLE_CLOUD_REGION} \
  --limit 50
```

**MCP Server logs:**

```bash
gcloud run services logs read mcp-server \
  --region ${GOOGLE_CLOUD_REGION} \
  --limit 50
```

Look for:
- ✅ Successfully obtained ID token
- ✅ Tool calls to MCP server
- ✅ Successful API responses

### 7.2 Verify IAM Permissions

```bash
# Check MCP server IAM policy
gcloud run services get-iam-policy mcp-server \
  --region ${GOOGLE_CLOUD_REGION}
```

You should see the agent's service account with `roles/run.invoker`.

## Authentication Details

### When is the Cloud Run proxy needed?

| Client location | MCP server | Proxy needed? |
|-----------------|------------|----------------|
| **Your laptop** (local dev/test) | Private Cloud Run MCP server | **Yes** — run `gcloud run services proxy mcp-server --region=REGION` and connect to `http://127.0.0.1:8080/sse`. |
| **ADK Agent on Cloud Run** | Private Cloud Run MCP server | **No** — agent uses ID tokens (see auth_helper.py) and calls the MCP server URL directly. |

So: **proxy = for local testing only**. Production service-to-service (agent → MCP) uses ID tokens, not the proxy. See [Deploy a remote MCP server on Cloud Run](https://docs.cloud.google.com/run/docs/tutorials/deploy-remote-mcp-server#authenticate).

### How Service-to-Service Authentication Works

1. **ADK Agent** needs to call **MCP Server**
2. **MCP Server** is deployed with `--no-allow-unauthenticated` (private)
3. **ADK Agent** uses its service account identity
4. **auth_helper.py** gets an ID token from Google Auth:
   - Audience: MCP server URL
   - Uses Application Default Credentials (ADC)
5. **ID token** is included in `Authorization: Bearer <token>` header
6. **Cloud Run** validates the token and checks IAM permissions
7. If authorized, request proceeds; otherwise, returns 403

### ID Token Acquisition

The `auth_helper.py` module uses Google's `id_token.fetch_id_token()`:

```python
from google.oauth2 import id_token
from google.auth.transport import requests

request = google.auth.transport.requests.Request()
token = id_token.fetch_id_token(request, audience="https://mcp-server-xxx.run.app")  # Base URL, not /sse path
```

This works automatically in Cloud Run because:
- Cloud Run services have Application Default Credentials (ADC)
- The service account identity is automatically available
- No manual credential files needed

### LLM Authentication

For Vertex AI (recommended):

- Uses **Application Default Credentials (ADC)**
- Automatically available in Cloud Run
- No API keys needed
- Set `GOOGLE_GENAI_USE_VERTEXAI=TRUE`

For Google AI Studio:

- Requires API key
- Set `GOOGLE_GENAI_USE_VERTEXAI=FALSE`
- Set `GOOGLE_API_KEY=your-key`
- Less secure for production

## Troubleshooting

> **⚠️ Important**: Before troubleshooting, check [KNOWN_ISSUES.md](KNOWN_ISSUES.md) for current known bugs and limitations.

## Known Issues

### Issue: 403 Forbidden when agent calls MCP server

**Solution:**
1. Verify IAM permissions are set:
   ```bash
   gcloud run services get-iam-policy mcp-server --region ${REGION}
   ```
2. Ensure agent service account has `roles/run.invoker`
3. Check that MCP_SERVER_URL is correct (full URL with /sse path)

### Issue: Authentication token not obtained

**Solution:**
1. Verify Application Default Credentials are set:
   ```bash
   gcloud auth application-default print-access-token
   ```
2. Check service account has necessary permissions
3. Review logs for authentication errors

### Issue: LLM API errors

**Solution:**
1. Verify Vertex AI API is enabled:
   ```bash
   gcloud services enable aiplatform.googleapis.com
   ```
2. Check environment variables are set correctly
3. Verify service account has Vertex AI User role:
   ```bash
   gcloud projects add-iam-policy-binding ${PROJECT_ID} \
     --member="serviceAccount:${PROJECT_ID}@appspot.gserviceaccount.com" \
     --role="roles/aiplatform.user"
   ```

### Issue: MCP tool not found

**Solution:**
1. Verify MCP_SERVER_URL includes `/sse` path
2. Check MCP server is running and accessible
3. Review MCP server logs for errors
4. Test MCP server directly with authenticated request

### Issue: MCP Connection Async Context Error

**Status:** 🔴 Known Issue - See [KNOWN_ISSUES.md](KNOWN_ISSUES.md)

If you encounter:
```
ConnectionError: Failed to create MCP session: unhandled errors in a TaskGroup
```

This is a known issue with MCP client library and Cloud Run's async context management. See [KNOWN_ISSUES.md](KNOWN_ISSUES.md) for details and potential workarounds.

## Local Testing

### Test MCP Server Locally

```bash
cd mcp-server
python server.py
# Server runs on http://localhost:8080
```

### Test ADK Agent Locally

```bash
cd adk-agent

# Set environment variables
export MCP_SERVER_URL="http://localhost:8080/sse"
export GOOGLE_GENAI_USE_VERTEXAI=FALSE
export GOOGLE_API_KEY="your-api-key"

# Run agent
python main.py
# Agent runs on http://localhost:8080
```

### Test with Cloud Run Proxy (for private MCP server, local testing)

If your MCP server is deployed with **private** access (`--no-allow-unauthenticated`) and you want to test **from your laptop**, you must use the **Cloud Run proxy** to get an authenticated tunnel. The proxy is **not** used when the client is another Cloud Run service (e.g. ADK agent on Cloud Run).

From the [official tutorial](https://docs.cloud.google.com/run/docs/tutorials/deploy-remote-mcp-server#authenticate):

1. Grant yourself `roles/run.invoker` on the MCP server (so the proxy can invoke it).
2. Start the proxy (installs the proxy if needed):
   ```bash
   gcloud run services proxy mcp-server --region=${REGION}
   ```
3. In another terminal, point your client at the proxy:
   ```bash
   export MCP_SERVER_URL="http://127.0.0.1:8080/sse"
   # Then run your local ADK agent or test script; it will use the proxy.
   ```

The proxy authenticates traffic to `http://127.0.0.1:8080` and forwards it to the remote MCP server. Your local client connects to `http://127.0.0.1:8080/sse` (or `http://localhost:8080/sse`).

## Cleanup

To remove all deployed services:

```bash
# Delete ADK agent
gcloud run services delete adk-agent \
  --region ${GOOGLE_CLOUD_REGION}

# Delete MCP server
gcloud run services delete mcp-server \
  --region ${GOOGLE_CLOUD_REGION}

# Delete container images (optional)
gcloud container images delete gcr.io/${PROJECT_ID}/adk-agent
gcloud container images delete gcr.io/${PROJECT_ID}/mcp-server
```

## Security Best Practices

1. **MCP Server**: Keep it private (`--no-allow-unauthenticated`)
2. **IAM**: Use least privilege (only grant `roles/run.invoker`)
3. **Secrets**: Use Secret Manager for API keys (not environment variables)
4. **Monitoring**: Enable Cloud Logging and Monitoring
5. **Audit**: Review Cloud Audit Logs regularly

## References

- [Cloud Run Service-to-Service Authentication](https://docs.cloud.google.com/run/docs/authenticating/service-to-service)
- [ADK Documentation](https://google.github.io/adk-docs)
- [MCP Protocol](https://modelcontextprotocol.io)
- [Vertex AI Authentication](https://cloud.google.com/vertex-ai/docs/authentication)

## Support

For issues or questions:
- Check Cloud Run logs
- Review ADK documentation
- Consult Google Cloud support
