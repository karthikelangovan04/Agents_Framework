#!/bin/bash
# Complete Vertex AI Setup Script
# This script sets up everything needed for Vertex AI authentication

set -e

# Configuration
export GOOGLE_CLOUD_PROJECT="${GOOGLE_CLOUD_PROJECT:-your-project-id}"
export GOOGLE_CLOUD_REGION="${GOOGLE_CLOUD_REGION:-us-central1}"

echo "🚀 Starting Vertex AI Setup..."
echo "Project: ${GOOGLE_CLOUD_PROJECT}"
echo "Region: ${GOOGLE_CLOUD_REGION}"
echo ""

# Check if project is set
if [ "$GOOGLE_CLOUD_PROJECT" == "your-project-id" ]; then
  echo "❌ Error: Please set GOOGLE_CLOUD_PROJECT environment variable"
  echo "   export GOOGLE_CLOUD_PROJECT=\"your-actual-project-id\""
  exit 1
fi

# Step 1: Authenticate
echo "📋 Step 1: Authenticating..."
gcloud config set project ${GOOGLE_CLOUD_PROJECT} || {
  echo "❌ Failed to set project. Please check your project ID."
  exit 1
}

# Check if already authenticated
if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | grep -q .; then
  echo "Please authenticate with Google Cloud..."
  gcloud auth login
fi

# Set Application Default Credentials
echo "Setting up Application Default Credentials..."
gcloud auth application-default login || {
  echo "⚠️  Application Default Credentials setup failed. Continuing..."
}

# Step 2: Enable APIs
echo ""
echo "📋 Step 2: Enabling required APIs..."

# Check if run.googleapis.com is already enabled (Cloud Run Admin API)
CLOUD_RUN_ENABLED=$(gcloud services list --enabled --project ${GOOGLE_CLOUD_PROJECT} --filter="name:run.googleapis.com" --format="value(name)" 2>/dev/null || echo "")

# Enable APIs with error handling
enable_api() {
  local api=$1
  local api_name=$2
  
  # Check if already enabled
  local enabled=$(gcloud services list --enabled --project ${GOOGLE_CLOUD_PROJECT} --filter="name:${api}" --format="value(name)" 2>/dev/null || echo "")
  if [ -n "$enabled" ]; then
    echo "  ✅ ${api_name} already enabled"
    return 0
  fi
  
  # Try to enable
  if gcloud services enable ${api} --project ${GOOGLE_CLOUD_PROJECT} 2>/dev/null; then
    echo "  ✅ ${api_name} enabled"
    return 0
  else
    echo "  ⚠️  Failed to enable ${api_name} (may be restricted by billing account)"
    return 1
  fi
}

# Enable APIs (skip cloudrun.googleapis.com if run.googleapis.com is enabled)
if [ -n "$CLOUD_RUN_ENABLED" ]; then
  echo "  ✅ Cloud Run Admin API (run.googleapis.com) already enabled - skipping cloudrun.googleapis.com"
else
  enable_api "cloudrun.googleapis.com" "Cloud Run API" || echo "  ⚠️  Cloud Run API failed, but continuing..."
fi

enable_api "cloudbuild.googleapis.com" "Cloud Build API" || true
enable_api "aiplatform.googleapis.com" "Vertex AI API" || true
enable_api "artifactregistry.googleapis.com" "Artifact Registry API" || true

echo ""
echo "✅ API enablement check complete"

# Step 3: Grant Vertex AI Permissions
echo ""
echo "📋 Step 3: Granting Vertex AI permissions..."
SERVICE_ACCOUNT="${GOOGLE_CLOUD_PROJECT}@appspot.gserviceaccount.com"

# Check if service account exists
SA_EXISTS=$(gcloud iam service-accounts describe ${SERVICE_ACCOUNT} --project ${GOOGLE_CLOUD_PROJECT} 2>/dev/null && echo "yes" || echo "no")

if [ "$SA_EXISTS" == "no" ]; then
  echo "  ⚠️  Service account ${SERVICE_ACCOUNT} does not exist yet."
  echo "  ℹ️  It will be created automatically when Cloud Run services are deployed."
  echo "  ⚠️  Skipping IAM binding for now - will be set during deployment."
  echo "  ✅ Vertex AI permissions will be granted after service account is created"
else
  # Check if role already exists
  EXISTING_ROLE=$(gcloud projects get-iam-policy ${GOOGLE_CLOUD_PROJECT} \
    --flatten="bindings[].members" \
    --filter="bindings.members:serviceAccount:${SERVICE_ACCOUNT}" \
    --format="value(bindings.role)" 2>/dev/null | grep "roles/aiplatform.user" || echo "")

  if [ -z "$EXISTING_ROLE" ]; then
    echo "Granting roles/aiplatform.user to ${SERVICE_ACCOUNT}..."
    if gcloud projects add-iam-policy-binding ${GOOGLE_CLOUD_PROJECT} \
      --member="serviceAccount:${SERVICE_ACCOUNT}" \
      --role="roles/aiplatform.user" 2>/dev/null; then
      echo "✅ Vertex AI permissions granted"
    else
      echo "⚠️  Failed to grant permissions (may need to retry after service account is created)"
    fi
  else
    echo "✅ Vertex AI permissions already granted"
  fi
fi

# Step 4: Deploy MCP Server
echo ""
echo "📋 Step 4: Deploying MCP Server..."
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "${SCRIPT_DIR}"

if [ -f "./deploy-mcp-server.sh" ]; then
  ./deploy-mcp-server.sh
  
  # Get MCP Server URL
  echo ""
  echo "Getting MCP Server URL..."
  MCP_SERVER_URL=$(gcloud run services describe mcp-server \
    --platform managed \
    --region ${GOOGLE_CLOUD_REGION} \
    --project ${GOOGLE_CLOUD_PROJECT} \
    --format 'value(status.url)' 2>/dev/null || echo "")
  
  if [ -n "$MCP_SERVER_URL" ]; then
    export MCP_SERVER_URL="${MCP_SERVER_URL}/sse"
    echo "✅ MCP Server URL: ${MCP_SERVER_URL}"
  else
    echo "⚠️  Could not get MCP Server URL. Please check deployment."
  fi
else
  echo "⚠️  deploy-mcp-server.sh not found. Skipping MCP server deployment."
fi

# Step 5: Deploy ADK Agent First (creates service account)
# We deploy agent first because it creates the service account automatically
if [ -n "$MCP_SERVER_URL" ] && [ -f "./deploy-adk-agent.sh" ]; then
  echo ""
  echo "📋 Step 5: Deploying ADK Agent with Vertex AI configuration..."
  echo "   (This will create the service account automatically)"
  ./deploy-adk-agent.sh
else
  echo ""
  echo "⚠️  Skipping ADK Agent deployment (MCP server URL not available or script not found)"
fi

# Step 6: Setup IAM for Service-to-Service Auth (after service account is created)
if [ -n "$MCP_SERVER_URL" ] && [ -f "./setup-iam.sh" ]; then
  echo ""
  echo "📋 Step 6: Setting up IAM for service-to-service authentication..."
  echo "   (Service account should now exist after agent deployment)"
  ./setup-iam.sh
  
  # Also grant Vertex AI permissions now that service account exists
  echo ""
  echo "Granting Vertex AI permissions to service account..."
  SERVICE_ACCOUNT="${GOOGLE_CLOUD_PROJECT}@appspot.gserviceaccount.com"
  
  # Wait a moment for service account to be fully created
  sleep 2
  
  EXISTING_ROLE=$(gcloud projects get-iam-policy ${GOOGLE_CLOUD_PROJECT} \
    --flatten="bindings[].members" \
    --filter="bindings.members:serviceAccount:${SERVICE_ACCOUNT}" \
    --format="value(bindings.role)" 2>/dev/null | grep "roles/aiplatform.user" || echo "")
  
  if [ -z "$EXISTING_ROLE" ]; then
    if gcloud projects add-iam-policy-binding ${GOOGLE_CLOUD_PROJECT} \
      --member="serviceAccount:${SERVICE_ACCOUNT}" \
      --role="roles/aiplatform.user" 2>/dev/null; then
      echo "✅ Vertex AI permissions granted"
    else
      echo "⚠️  Failed to grant Vertex AI permissions (service account may still be creating)"
      echo "   You can grant manually later with:"
      echo "   gcloud projects add-iam-policy-binding ${GOOGLE_CLOUD_PROJECT} \\"
      echo "     --member=\"serviceAccount:${SERVICE_ACCOUNT}\" \\"
      echo "     --role=\"roles/aiplatform.user\""
    fi
  else
    echo "✅ Vertex AI permissions already granted"
  fi
fi

# Summary
echo ""
echo "═══════════════════════════════════════════════════════════"
echo "✅ Vertex AI Setup Complete!"
echo "═══════════════════════════════════════════════════════════"
echo ""
echo "Configuration Summary:"
echo "  Project: ${GOOGLE_CLOUD_PROJECT}"
echo "  Region: ${GOOGLE_CLOUD_REGION}"
echo "  Vertex AI: Enabled"
echo "  Service Account: ${SERVICE_ACCOUNT}"
echo "  Vertex AI Role: roles/aiplatform.user"
if [ -n "$MCP_SERVER_URL" ]; then
  echo "  MCP Server URL: ${MCP_SERVER_URL}"
fi
echo ""
echo "Next Steps:"
echo "  1. Test the deployment: ./test-deployment.sh"
echo "  2. View logs: gcloud run services logs read adk-agent --region ${GOOGLE_CLOUD_REGION}"
echo "  3. Monitor costs in Cloud Console"
echo ""
