# Quick Commands Reference - Copy & Paste Ready

## 🔍 Find Your Project ID First!

### Option 1: Use Helper Script (Easiest)
```bash
cd "/Users/karthike/Desktop/Vibe Coding/Google-ADK-A2A-Explore/cloud-run-deployment/scripts"
./find-project-id.sh
```

### Option 2: Manual Method
```bash
# Authenticate first (will open browser, requires email login)
gcloud auth login

# List all your projects
gcloud projects list

# Copy the PROJECT_ID from the output
```

### Option 3: From Google Cloud Console
1. Go to: https://console.cloud.google.com
2. Click the project selector at the top
3. Copy the **Project ID** (not the project name)

## 🚀 Complete Setup (One Script)

```bash
# Set your project ID
export GOOGLE_CLOUD_PROJECT="your-project-id"
export GOOGLE_CLOUD_REGION="us-central1"

# Run complete setup
cd "/Users/karthike/Desktop/Vibe Coding/Google-ADK-A2A-Explore/cloud-run-deployment/scripts"
./setup-vertex-ai.sh
```

## 📋 Step-by-Step Commands

### Step 1: Authenticate & Set Project

```bash
# Set your project
export GOOGLE_CLOUD_PROJECT="your-project-id"
export GOOGLE_CLOUD_REGION="us-central1"

# Authenticate
gcloud auth login
gcloud auth application-default login
gcloud config set project ${GOOGLE_CLOUD_PROJECT}
```

### Step 2: Enable APIs

```bash
gcloud services enable cloudrun.googleapis.com --project ${GOOGLE_CLOUD_PROJECT}
gcloud services enable cloudbuild.googleapis.com --project ${GOOGLE_CLOUD_PROJECT}
gcloud services enable aiplatform.googleapis.com --project ${GOOGLE_CLOUD_PROJECT}
gcloud services enable artifactregistry.googleapis.com --project ${GOOGLE_CLOUD_PROJECT}
```

### Step 3: Grant Vertex AI Permissions

```bash
SERVICE_ACCOUNT="${GOOGLE_CLOUD_PROJECT}@appspot.gserviceaccount.com"
gcloud projects add-iam-policy-binding ${GOOGLE_CLOUD_PROJECT} \
  --member="serviceAccount:${SERVICE_ACCOUNT}" \
  --role="roles/aiplatform.user"
```

### Step 4: Deploy MCP Server

```bash
cd "/Users/karthike/Desktop/Vibe Coding/Google-ADK-A2A-Explore/cloud-run-deployment/scripts"
./deploy-mcp-server.sh

# Get MCP Server URL
MCP_SERVER_URL=$(gcloud run services describe mcp-server \
  --platform managed \
  --region ${GOOGLE_CLOUD_REGION} \
  --project ${GOOGLE_CLOUD_PROJECT} \
  --format 'value(status.url)')
export MCP_SERVER_URL="${MCP_SERVER_URL}/sse"
echo "MCP Server URL: ${MCP_SERVER_URL}"
```

### Step 5: Setup IAM

```bash
./setup-iam.sh
```

### Step 6: Deploy ADK Agent

```bash
./deploy-adk-agent.sh
```

### Step 7: Test

```bash
./test-deployment.sh
```

## 🧹 Cleanup Commands

### Complete Cleanup (All Resources)

```bash
export GOOGLE_CLOUD_PROJECT="your-project-id"
export GOOGLE_CLOUD_REGION="us-central1"

cd "/Users/karthike/Desktop/Vibe Coding/Google-ADK-A2A-Explore/cloud-run-deployment/scripts"
./cleanup.sh
```

### Manual Cleanup

```bash
# Delete services
gcloud run services delete adk-agent --region ${GOOGLE_CLOUD_REGION} --project ${GOOGLE_CLOUD_PROJECT} --quiet
gcloud run services delete mcp-server --region ${GOOGLE_CLOUD_REGION} --project ${GOOGLE_CLOUD_PROJECT} --quiet

# Delete images
gcloud container images delete gcr.io/${GOOGLE_CLOUD_PROJECT}/adk-agent --quiet --project ${GOOGLE_CLOUD_PROJECT}
gcloud container images delete gcr.io/${GOOGLE_CLOUD_PROJECT}/mcp-server --quiet --project ${GOOGLE_CLOUD_PROJECT}

# Remove IAM (optional)
SERVICE_ACCOUNT="${GOOGLE_CLOUD_PROJECT}@appspot.gserviceaccount.com"
gcloud projects remove-iam-policy-binding ${GOOGLE_CLOUD_PROJECT} \
  --member="serviceAccount:${SERVICE_ACCOUNT}" \
  --role="roles/aiplatform.user" --quiet
```

## ✅ Verification Commands

```bash
# Check Vertex AI API enabled
gcloud services list --enabled --project ${GOOGLE_CLOUD_PROJECT} | grep aiplatform

# Check IAM permissions
gcloud projects get-iam-policy ${GOOGLE_CLOUD_PROJECT} \
  --flatten="bindings[].members" \
  --filter="bindings.members:serviceAccount:${GOOGLE_CLOUD_PROJECT}@appspot.gserviceaccount.com"

# Check services running
gcloud run services list --region ${GOOGLE_CLOUD_REGION} --project ${GOOGLE_CLOUD_PROJECT}

# Check ADK agent env vars
gcloud run services describe adk-agent \
  --region ${GOOGLE_CLOUD_REGION} \
  --project ${GOOGLE_CLOUD_PROJECT} \
  --format="value(spec.template.spec.containers[0].env)" | grep VERTEXAI

# View logs
gcloud run services logs read adk-agent --region ${GOOGLE_CLOUD_REGION} --limit 50
```

## 🧪 Test Commands

```bash
# Get agent URL
AGENT_URL=$(gcloud run services describe adk-agent \
  --platform managed \
  --region ${GOOGLE_CLOUD_REGION} \
  --project ${GOOGLE_CLOUD_PROJECT} \
  --format 'value(status.url)')

# Test agent
curl -X POST ${AGENT_URL}/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "What is 100 USD in EUR?", "session_id": "test"}'

# Health check
curl ${AGENT_URL}/health
```

## 📊 Monitoring Commands

```bash
# View real-time logs
gcloud run services logs tail adk-agent --region ${GOOGLE_CLOUD_REGION}

# View MCP server logs
gcloud run services logs tail mcp-server --region ${GOOGLE_CLOUD_REGION}

# Check service status
gcloud run services describe adk-agent --region ${GOOGLE_CLOUD_REGION}
```
