#!/bin/bash
# Deploy ADK Agent to Cloud Run
#
# This script builds and deploys the ADK agent to Cloud Run with:
# - Python 3.12 for better async context handling
# - Dynamic header provider for MCP authentication
# - Proper session management
# - Vertex AI integration
#
# Prerequisites:
# - MCP server must be deployed first
# - IAM permissions must be configured (run setup-iam.sh)
# - Vertex AI API must be enabled

set -e

# Configuration
PROJECT_ID="${GOOGLE_CLOUD_PROJECT:-your-project-id}"
REGION="${GOOGLE_CLOUD_REGION:-us-central1}"
SERVICE_NAME="adk-agent"
IMAGE_NAME="gcr.io/${PROJECT_ID}/${SERVICE_NAME}"
MCP_SERVER_URL="${MCP_SERVER_URL:-}"

# Check if MCP_SERVER_URL is set
if [ -z "$MCP_SERVER_URL" ]; then
  echo "❌ Error: MCP_SERVER_URL environment variable is not set"
  echo "   Please set it to your MCP server URL (e.g., https://mcp-server-xxx.run.app/sse)"
  echo ""
  echo "   Example:"
  echo "   export MCP_SERVER_URL=\"https://mcp-server-xxx.run.app/sse\""
  exit 1
fi

echo "🚀 Deploying ADK Agent to Cloud Run..."
echo "Project: ${PROJECT_ID}"
echo "Region: ${REGION}"
echo "Service: ${SERVICE_NAME}"
echo "MCP Server: ${MCP_SERVER_URL}"
echo ""

# Navigate to ADK agent directory
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "${SCRIPT_DIR}/../adk-agent"

# Verify Dockerfile uses Python 3.12
if ! grep -q "FROM python:3.12" Dockerfile; then
  echo "⚠️  Warning: Dockerfile may not be using Python 3.12"
  echo "   Recommended: FROM python:3.12-slim"
fi

# Build and push container image
echo "📦 Building container image..."
echo "   Image: ${IMAGE_NAME}"
gcloud builds submit --tag ${IMAGE_NAME} --project ${PROJECT_ID}

# Check if service account exists
# Cloud Run uses the default compute service account if not specified
PROJECT_NUMBER=$(gcloud projects describe ${PROJECT_ID} --format="value(projectNumber)" 2>/dev/null || echo "")
if [ -n "$PROJECT_NUMBER" ]; then
  # Try to get service account from deployed service
  DEPLOYED_SA=$(gcloud run services describe ${SERVICE_NAME} \
    --platform managed \
    --region ${REGION} \
    --project ${PROJECT_ID} \
    --format="value(spec.template.spec.serviceAccountName)" 2>/dev/null || echo "")
  
  if [ -n "$DEPLOYED_SA" ] && [ "$DEPLOYED_SA" != "" ]; then
    SERVICE_ACCOUNT="${DEPLOYED_SA}"
    echo "📋 Using existing service account: ${SERVICE_ACCOUNT}"
    SA_EXISTS="yes"
  else
    # Use default compute service account
    SERVICE_ACCOUNT="${PROJECT_NUMBER}-compute@developer.gserviceaccount.com"
    SA_EXISTS=$(gcloud iam service-accounts describe ${SERVICE_ACCOUNT} --project ${PROJECT_ID} 2>/dev/null && echo "yes" || echo "no")
  fi
else
  # Fallback to appspot service account
  SERVICE_ACCOUNT="${PROJECT_ID}@appspot.gserviceaccount.com"
  SA_EXISTS=$(gcloud iam service-accounts describe ${SERVICE_ACCOUNT} --project ${PROJECT_ID} 2>/dev/null && echo "yes" || echo "no")
fi

# Grant Service Account User role to current user if service account exists
if [ "$SA_EXISTS" == "yes" ]; then
  CURRENT_USER=$(gcloud config get-value account)
  echo "🔐 Granting Service Account User role to ${CURRENT_USER}..."
  gcloud iam service-accounts add-iam-policy-binding ${SERVICE_ACCOUNT} \
    --member="user:${CURRENT_USER}" \
    --role="roles/iam.serviceAccountUser" \
    --project ${PROJECT_ID} 2>/dev/null || echo "  (May already have permission)"
fi

# Deploy to Cloud Run
echo "☁️ Deploying to Cloud Run..."
if [ "$SA_EXISTS" == "yes" ]; then
  # Use service account if it exists
  gcloud run deploy ${SERVICE_NAME} \
    --image ${IMAGE_NAME} \
    --platform managed \
    --region ${REGION} \
    --allow-unauthenticated \
    --project ${PROJECT_ID} \
    --memory 1Gi \
    --cpu 2 \
    --timeout 300 \
    --max-instances 10 \
    --set-env-vars "GOOGLE_CLOUD_PROJECT=${PROJECT_ID},GOOGLE_CLOUD_LOCATION=${REGION},GOOGLE_GENAI_USE_VERTEXAI=TRUE,MCP_SERVER_URL=${MCP_SERVER_URL},GOOGLE_MODEL=gemini-2.5-flash" \
    --service-account "${SERVICE_ACCOUNT}"
else
  # Deploy without specifying service account (Cloud Run will use default compute service account)
  echo "  Service account doesn't exist yet - deploying without --service-account flag"
  echo "  Cloud Run will use the default compute service account automatically"
  gcloud run deploy ${SERVICE_NAME} \
    --image ${IMAGE_NAME} \
    --platform managed \
    --region ${REGION} \
    --allow-unauthenticated \
    --project ${PROJECT_ID} \
    --memory 1Gi \
    --cpu 2 \
    --timeout 300 \
    --max-instances 10 \
    --set-env-vars "GOOGLE_CLOUD_PROJECT=${PROJECT_ID},GOOGLE_CLOUD_LOCATION=${REGION},GOOGLE_GENAI_USE_VERTEXAI=TRUE,MCP_SERVER_URL=${MCP_SERVER_URL},GOOGLE_MODEL=gemini-2.5-flash"
fi

# Get the service URL
SERVICE_URL=$(gcloud run services describe ${SERVICE_NAME} \
  --platform managed \
  --region ${REGION} \
  --project ${PROJECT_ID} \
  --format 'value(status.url)')

echo ""
echo "✅ ADK Agent deployed successfully!"
echo "📍 Service URL: ${SERVICE_URL}"
echo ""
echo "📋 Next Steps:"
echo "   1. Verify IAM permissions (run: ./setup-iam.sh)"
echo "   2. Grant Vertex AI permissions (run: ./setup-vertex-ai.sh or grant manually)"
echo "   3. Test the agent (see below)"
echo ""
echo "🧪 Test the agent:"
echo "   curl -X POST ${SERVICE_URL}/chat \\"
echo "     -H 'Content-Type: application/json' \\"
echo "     -d '{\"message\": \"What is 100 USD in EUR?\", \"session_id\": \"test-1\", \"user_id\": \"test-user\"}'"
echo ""
echo "🔍 Check health:"
echo "   curl ${SERVICE_URL}/health"
echo ""
echo "⚠️  Note: If you encounter MCP connection errors, see KNOWN_ISSUES.md"
