# Vertex AI Setup Guide - Complete CLI Commands

This guide provides all CLI commands needed to set up Vertex AI authentication and deploy the services from Cursor terminal.

## Prerequisites Check

First, verify you have the necessary tools installed:

```bash
# Check gcloud CLI
gcloud --version

# Check if authenticated
gcloud auth list

# Check current project
gcloud config get-value project
```

## Step 1: Google Cloud Authentication & Project Setup

### 1.1 Authenticate with Google Cloud

```bash
# Login to Google Cloud (opens browser)
gcloud auth login

# Set Application Default Credentials (required for Vertex AI)
gcloud auth application-default login

# Verify authentication
gcloud auth list
```

### 1.2 Set Your Project

```bash
# Set your project ID (replace with your actual project ID)
export GOOGLE_CLOUD_PROJECT="your-project-id"
export GOOGLE_CLOUD_REGION="us-central1"

# Configure gcloud to use this project
gcloud config set project ${GOOGLE_CLOUD_PROJECT}

# Verify project is set
gcloud config get-value project
```

### 1.3 Enable Billing (if not already enabled)

```bash
# Check billing account
gcloud billing accounts list

# Link billing account to project (replace BILLING_ACCOUNT_ID)
# gcloud billing projects link ${GOOGLE_CLOUD_PROJECT} --billing-account=BILLING_ACCOUNT_ID
```

## Step 2: Enable Required APIs

Enable all necessary Google Cloud APIs:

```bash
# Enable Cloud Run API
gcloud services enable cloudrun.googleapis.com --project ${GOOGLE_CLOUD_PROJECT}

# Enable Cloud Build API
gcloud services enable cloudbuild.googleapis.com --project ${GOOGLE_CLOUD_PROJECT}

# Enable Vertex AI API (CRITICAL for LLM)
gcloud services enable aiplatform.googleapis.com --project ${GOOGLE_CLOUD_PROJECT}

# Enable Artifact Registry API
gcloud services enable artifactregistry.googleapis.com --project ${GOOGLE_CLOUD_PROJECT}

# Verify APIs are enabled
gcloud services list --enabled --project ${GOOGLE_CLOUD_PROJECT} | grep -E "cloudrun|cloudbuild|aiplatform|artifactregistry"
```

## Step 3: Grant Vertex AI Permissions

Grant the default compute service account permission to use Vertex AI:

```bash
# Get the default compute service account email
SERVICE_ACCOUNT="${GOOGLE_CLOUD_PROJECT}@appspot.gserviceaccount.com"

# Grant Vertex AI User role
gcloud projects add-iam-policy-binding ${GOOGLE_CLOUD_PROJECT} \
  --member="serviceAccount:${SERVICE_ACCOUNT}" \
  --role="roles/aiplatform.user"

# Verify the role was granted
gcloud projects get-iam-policy ${GOOGLE_CLOUD_PROJECT} \
  --flatten="bindings[].members" \
  --filter="bindings.members:serviceAccount:${SERVICE_ACCOUNT}" \
  --format="table(bindings.role)"
```

## Step 4: Deploy MCP Server

Navigate to the deployment directory and deploy the MCP server:

```bash
# Navigate to scripts directory
cd "/Users/karthike/Desktop/Vibe Coding/Google-ADK-A2A-Explore/cloud-run-deployment/scripts"

# Deploy MCP Server
./deploy-mcp-server.sh

# Wait for deployment to complete, then get the MCP server URL
MCP_SERVER_URL=$(gcloud run services describe mcp-server \
  --platform managed \
  --region ${GOOGLE_CLOUD_REGION} \
  --project ${GOOGLE_CLOUD_PROJECT} \
  --format 'value(status.url)')

echo "MCP Server URL: ${MCP_SERVER_URL}/sse"
export MCP_SERVER_URL="${MCP_SERVER_URL}/sse"
```

## Step 5: Configure IAM for Service-to-Service Authentication

Set up permissions so the ADK agent can call the MCP server:

```bash
# Run IAM setup script
./setup-iam.sh

# Verify IAM policy
gcloud run services get-iam-policy mcp-server \
  --region ${GOOGLE_CLOUD_REGION} \
  --project ${GOOGLE_CLOUD_PROJECT} \
  --format="table(bindings.members,bindings.role)"
```

## Step 6: Deploy ADK Agent with Vertex AI Configuration

Deploy the ADK agent configured to use Vertex AI:

```bash
# Ensure MCP_SERVER_URL is set (from Step 4)
if [ -z "$MCP_SERVER_URL" ]; then
  echo "Error: MCP_SERVER_URL not set. Please run Step 4 first."
  exit 1
fi

# Deploy ADK Agent with Vertex AI configuration
./deploy-adk-agent.sh

# Alternative: Manual deployment with Vertex AI env vars
cd "/Users/karthike/Desktop/Vibe Coding/Google-ADK-A2A-Explore/cloud-run-deployment/adk-agent"

# Build and push image
gcloud builds submit --tag gcr.io/${GOOGLE_CLOUD_PROJECT}/adk-agent --project ${GOOGLE_CLOUD_PROJECT}

# Deploy with Vertex AI configuration
gcloud run deploy adk-agent \
  --image gcr.io/${GOOGLE_CLOUD_PROJECT}/adk-agent \
  --platform managed \
  --region ${GOOGLE_CLOUD_REGION} \
  --allow-unauthenticated \
  --project ${GOOGLE_CLOUD_PROJECT} \
  --memory 1Gi \
  --cpu 2 \
  --timeout 300 \
  --max-instances 10 \
  --set-env-vars "GOOGLE_CLOUD_PROJECT=${GOOGLE_CLOUD_PROJECT},GOOGLE_CLOUD_LOCATION=${GOOGLE_CLOUD_REGION},GOOGLE_GENAI_USE_VERTEXAI=TRUE,MCP_SERVER_URL=${MCP_SERVER_URL},GOOGLE_MODEL=gemini-2.5-flash" \
  --service-account "${GOOGLE_CLOUD_PROJECT}@appspot.gserviceaccount.com"
```

## Step 7: Verify Deployment

Test that everything is working:

```bash
# Run test script
cd "/Users/karthike/Desktop/Vibe Coding/Google-ADK-A2A-Explore/cloud-run-deployment/scripts"
./test-deployment.sh

# Or test manually
AGENT_URL=$(gcloud run services describe adk-agent \
  --platform managed \
  --region ${GOOGLE_CLOUD_REGION} \
  --project ${GOOGLE_CLOUD_PROJECT} \
  --format 'value(status.url)')

# Test the agent
curl -X POST ${AGENT_URL}/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "What is 100 USD in EUR?",
    "session_id": "test-session"
  }'
```

## Step 8: Verify Vertex AI Configuration

Check that Vertex AI is properly configured:

```bash
# Check environment variables
gcloud run services describe adk-agent \
  --platform managed \
  --region ${GOOGLE_CLOUD_REGION} \
  --project ${GOOGLE_CLOUD_PROJECT} \
  --format="value(spec.template.spec.containers[0].env)" | grep -E "VERTEXAI|GOOGLE_CLOUD"

# Check logs for Vertex AI usage
gcloud run services logs read adk-agent \
  --platform managed \
  --region ${GOOGLE_CLOUD_REGION} \
  --project ${GOOGLE_CLOUD_PROJECT} \
  --limit 50 | grep -i "vertex\|gemini\|llm"
```

## Complete Setup Script

Here's a complete script you can run all at once (after setting GOOGLE_CLOUD_PROJECT):

```bash
#!/bin/bash
# Complete Vertex AI Setup Script

set -e

# Configuration
export GOOGLE_CLOUD_PROJECT="your-project-id"  # CHANGE THIS
export GOOGLE_CLOUD_REGION="us-central1"

echo "🚀 Starting Vertex AI Setup..."
echo "Project: ${GOOGLE_CLOUD_PROJECT}"
echo "Region: ${GOOGLE_CLOUD_REGION}"
echo ""

# Step 1: Authenticate
echo "📋 Step 1: Authenticating..."
gcloud config set project ${GOOGLE_CLOUD_PROJECT}
gcloud auth application-default login

# Step 2: Enable APIs
echo "📋 Step 2: Enabling APIs..."
gcloud services enable cloudrun.googleapis.com --project ${GOOGLE_CLOUD_PROJECT}
gcloud services enable cloudbuild.googleapis.com --project ${GOOGLE_CLOUD_PROJECT}
gcloud services enable aiplatform.googleapis.com --project ${GOOGLE_CLOUD_PROJECT}
gcloud services enable artifactregistry.googleapis.com --project ${GOOGLE_CLOUD_PROJECT}

# Step 3: Grant Vertex AI Permissions
echo "📋 Step 3: Granting Vertex AI permissions..."
SERVICE_ACCOUNT="${GOOGLE_CLOUD_PROJECT}@appspot.gserviceaccount.com"
gcloud projects add-iam-policy-binding ${GOOGLE_CLOUD_PROJECT} \
  --member="serviceAccount:${SERVICE_ACCOUNT}" \
  --role="roles/aiplatform.user"

# Step 4: Deploy MCP Server
echo "📋 Step 4: Deploying MCP Server..."
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

# Step 5: Setup IAM
echo "📋 Step 5: Setting up IAM..."
./setup-iam.sh

# Step 6: Deploy ADK Agent
echo "📋 Step 6: Deploying ADK Agent..."
./deploy-adk-agent.sh

# Step 7: Test
echo "📋 Step 7: Testing deployment..."
./test-deployment.sh

echo ""
echo "✅ Setup complete!"
```

## Cleanup Steps

### Complete Cleanup (Remove All Resources)

```bash
# Set your project
export GOOGLE_CLOUD_PROJECT="your-project-id"
export GOOGLE_CLOUD_REGION="us-central1"

echo "🧹 Starting cleanup..."

# Delete Cloud Run services
echo "Deleting Cloud Run services..."
gcloud run services delete adk-agent \
  --region ${GOOGLE_CLOUD_REGION} \
  --project ${GOOGLE_CLOUD_PROJECT} \
  --quiet

gcloud run services delete mcp-server \
  --region ${GOOGLE_CLOUD_REGION} \
  --project ${GOOGLE_CLOUD_PROJECT} \
  --quiet

# Delete container images
echo "Deleting container images..."
gcloud container images delete gcr.io/${GOOGLE_CLOUD_PROJECT}/adk-agent \
  --quiet \
  --project ${GOOGLE_CLOUD_PROJECT} || true

gcloud container images delete gcr.io/${GOOGLE_CLOUD_PROJECT}/mcp-server \
  --quiet \
  --project ${GOOGLE_CLOUD_PROJECT} || true

# Remove IAM bindings (optional - only if you want to remove permissions)
echo "Removing IAM bindings..."
SERVICE_ACCOUNT="${GOOGLE_CLOUD_PROJECT}@appspot.gserviceaccount.com"

# Remove Vertex AI User role
gcloud projects remove-iam-policy-binding ${GOOGLE_CLOUD_PROJECT} \
  --member="serviceAccount:${SERVICE_ACCOUNT}" \
  --role="roles/aiplatform.user" \
  --quiet || true

# Remove Cloud Run Invoker role from MCP server (service already deleted, but policy might remain)
# This will fail if service doesn't exist, which is OK
gcloud run services remove-iam-policy-binding mcp-server \
  --member="serviceAccount:${SERVICE_ACCOUNT}" \
  --role="roles/run.invoker" \
  --region ${GOOGLE_CLOUD_REGION} \
  --project ${GOOGLE_CLOUD_PROJECT} \
  --quiet || true

echo "✅ Cleanup complete!"
```

### Partial Cleanup (Keep Services, Remove IAM Only)

```bash
# Remove only IAM bindings (keep services running)
export GOOGLE_CLOUD_PROJECT="your-project-id"
export GOOGLE_CLOUD_REGION="us-central1"
SERVICE_ACCOUNT="${GOOGLE_CLOUD_PROJECT}@appspot.gserviceaccount.com"

# Remove Vertex AI User role
gcloud projects remove-iam-policy-binding ${GOOGLE_CLOUD_PROJECT} \
  --member="serviceAccount:${SERVICE_ACCOUNT}" \
  --role="roles/aiplatform.user"

# Remove Cloud Run Invoker role
gcloud run services remove-iam-policy-binding mcp-server \
  --member="serviceAccount:${SERVICE_ACCOUNT}" \
  --role="roles/run.invoker" \
  --region ${GOOGLE_CLOUD_REGION} \
  --project ${GOOGLE_CLOUD_PROJECT}
```

### Cleanup Script

Save this as `cleanup.sh`:

```bash
#!/bin/bash
# Cleanup Script for Cloud Run Deployment

set -e

export GOOGLE_CLOUD_PROJECT="${GOOGLE_CLOUD_PROJECT:-your-project-id}"
export GOOGLE_CLOUD_REGION="${GOOGLE_CLOUD_REGION:-us-central1}"

echo "🧹 Cleaning up Cloud Run deployment..."
echo "Project: ${GOOGLE_CLOUD_PROJECT}"
echo "Region: ${GOOGLE_CLOUD_REGION}"
echo ""

read -p "Are you sure you want to delete all resources? (yes/no): " confirm
if [ "$confirm" != "yes" ]; then
  echo "Cleanup cancelled."
  exit 0
fi

# Delete services
echo "Deleting Cloud Run services..."
gcloud run services delete adk-agent \
  --region ${GOOGLE_CLOUD_REGION} \
  --project ${GOOGLE_CLOUD_PROJECT} \
  --quiet || echo "ADK Agent service not found"

gcloud run services delete mcp-server \
  --region ${GOOGLE_CLOUD_REGION} \
  --project ${GOOGLE_CLOUD_PROJECT} \
  --quiet || echo "MCP Server service not found"

# Delete images
echo "Deleting container images..."
gcloud container images delete gcr.io/${GOOGLE_CLOUD_PROJECT}/adk-agent \
  --quiet \
  --project ${GOOGLE_CLOUD_PROJECT} || echo "ADK Agent image not found"

gcloud container images delete gcr.io/${GOOGLE_CLOUD_PROJECT}/mcp-server \
  --quiet \
  --project ${GOOGLE_CLOUD_PROJECT} || echo "MCP Server image not found"

echo "✅ Cleanup complete!"
```

## Verification Commands

After setup, verify everything is configured correctly:

```bash
# Check Vertex AI API is enabled
gcloud services list --enabled --project ${GOOGLE_CLOUD_PROJECT} | grep aiplatform

# Check service account has Vertex AI User role
gcloud projects get-iam-policy ${GOOGLE_CLOUD_PROJECT} \
  --flatten="bindings[].members" \
  --filter="bindings.members:serviceAccount:${GOOGLE_CLOUD_PROJECT}@appspot.gserviceaccount.com" \
  --format="table(bindings.role)" | grep aiplatform

# Check services are running
gcloud run services list --region ${GOOGLE_CLOUD_REGION} --project ${GOOGLE_CLOUD_PROJECT}

# Check ADK agent environment variables
gcloud run services describe adk-agent \
  --region ${GOOGLE_CLOUD_REGION} \
  --project ${GOOGLE_CLOUD_PROJECT} \
  --format="value(spec.template.spec.containers[0].env)" | grep VERTEXAI
```

## Troubleshooting Vertex AI Issues

### Issue: "Permission denied" when calling Vertex AI

```bash
# Verify service account has the role
gcloud projects get-iam-policy ${GOOGLE_CLOUD_PROJECT} \
  --flatten="bindings[].members" \
  --filter="bindings.members:serviceAccount:${GOOGLE_CLOUD_PROJECT}@appspot.gserviceaccount.com"

# Re-grant the role if missing
gcloud projects add-iam-policy-binding ${GOOGLE_CLOUD_PROJECT} \
  --member="serviceAccount:${GOOGLE_CLOUD_PROJECT}@appspot.gserviceaccount.com" \
  --role="roles/aiplatform.user"
```

### Issue: Vertex AI API not enabled

```bash
# Enable the API
gcloud services enable aiplatform.googleapis.com --project ${GOOGLE_CLOUD_PROJECT}

# Wait a few seconds, then verify
gcloud services list --enabled --project ${GOOGLE_CLOUD_PROJECT} | grep aiplatform
```

### Issue: Wrong project configured

```bash
# Check current project
gcloud config get-value project

# Set correct project
gcloud config set project YOUR_PROJECT_ID

# Update environment variable
export GOOGLE_CLOUD_PROJECT="YOUR_PROJECT_ID"
```

## Next Steps

After successful setup:

1. **Test the agent**: Use the test script or curl commands
2. **Monitor logs**: Check Cloud Run logs for any issues
3. **Review costs**: Monitor Cloud Run and Vertex AI usage
4. **Customize**: Modify the agent or MCP server for your needs

## Notes

- **Vertex AI uses Application Default Credentials (ADC)**: No API keys needed when running in Cloud Run
- **Service Account**: The default compute service account is automatically used
- **Costs**: Vertex AI charges per API call. Monitor usage in Cloud Console
- **Region**: Make sure Vertex AI is available in your chosen region (us-central1 is recommended)
