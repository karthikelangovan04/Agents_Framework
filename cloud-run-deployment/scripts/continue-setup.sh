#!/bin/bash
# Continue setup after MCP server deployment

set -e

export GOOGLE_CLOUD_PROJECT="${GOOGLE_CLOUD_PROJECT:-gen-lang-client-0707167243}"
export GOOGLE_CLOUD_REGION="${GOOGLE_CLOUD_REGION:-us-central1}"
export MCP_SERVER_URL="${MCP_SERVER_URL:-https://mcp-server-szbewwqnrq-uc.a.run.app/sse}"

echo "🚀 Continuing Setup After MCP Server Deployment"
echo "═══════════════════════════════════════════════════════════"
echo "Project: ${GOOGLE_CLOUD_PROJECT}"
echo "Region: ${GOOGLE_CLOUD_REGION}"
echo "MCP Server: ${MCP_SERVER_URL}"
echo ""

# Step 1: Deploy ADK Agent (this will create the service account)
echo "📋 Step 1: Deploying ADK Agent..."
echo "   (This will create the service account automatically)"
echo ""

if [ -f "./deploy-adk-agent.sh" ]; then
  ./deploy-adk-agent.sh
else
  echo "❌ deploy-adk-agent.sh not found"
  exit 1
fi

# Step 2: Setup IAM (now that service account exists)
echo ""
echo "📋 Step 2: Setting up IAM permissions..."
if [ -f "./setup-iam.sh" ]; then
  ./setup-iam.sh
else
  echo "⚠️  setup-iam.sh not found"
fi

# Step 3: Grant Vertex AI permissions
echo ""
echo "📋 Step 3: Granting Vertex AI permissions..."
SERVICE_ACCOUNT="${GOOGLE_CLOUD_PROJECT}@appspot.gserviceaccount.com"

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
    echo "⚠️  Failed to grant Vertex AI permissions"
  fi
else
  echo "✅ Vertex AI permissions already granted"
fi

# Summary
echo ""
echo "═══════════════════════════════════════════════════════════"
echo "✅ Setup Complete!"
echo "═══════════════════════════════════════════════════════════"
echo ""
echo "Next Steps:"
echo "  1. Test the deployment: ./test-deployment.sh"
echo "  2. View logs: gcloud run services logs read adk-agent --region ${GOOGLE_CLOUD_REGION}"
echo ""
