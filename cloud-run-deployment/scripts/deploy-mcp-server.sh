#!/bin/bash
# Deploy MCP Server to Cloud Run

set -e

# Configuration
PROJECT_ID="${GOOGLE_CLOUD_PROJECT:-your-project-id}"
REGION="${GOOGLE_CLOUD_REGION:-us-central1}"
SERVICE_NAME="mcp-server"
IMAGE_NAME="gcr.io/${PROJECT_ID}/${SERVICE_NAME}"

echo "🚀 Deploying MCP Server to Cloud Run..."
echo "Project: ${PROJECT_ID}"
echo "Region: ${REGION}"
echo "Service: ${SERVICE_NAME}"

# Navigate to MCP server directory
cd "$(dirname "$0")/../mcp-server"

# Build and push container image
echo "📦 Building container image..."
gcloud builds submit --tag ${IMAGE_NAME} --project ${PROJECT_ID}

# Deploy to Cloud Run with authentication required
echo "☁️ Deploying to Cloud Run..."
gcloud run deploy ${SERVICE_NAME} \
  --image ${IMAGE_NAME} \
  --platform managed \
  --region ${REGION} \
  --no-allow-unauthenticated \
  --project ${PROJECT_ID} \
  --memory 512Mi \
  --cpu 1 \
  --timeout 300 \
  --max-instances 10

# Get the service URL
SERVICE_URL=$(gcloud run services describe ${SERVICE_NAME} \
  --platform managed \
  --region ${REGION} \
  --project ${PROJECT_ID} \
  --format 'value(status.url)')

echo ""
echo "✅ MCP Server deployed successfully!"
echo "📍 Service URL: ${SERVICE_URL}"
echo "🔗 MCP Endpoint: ${SERVICE_URL}/sse"
echo ""
echo "⚠️  IMPORTANT: Update MCP_SERVER_URL in adk-agent/.env with:"
echo "   MCP_SERVER_URL=${SERVICE_URL}/sse"
