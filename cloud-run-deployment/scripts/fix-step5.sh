#!/bin/bash
# Fix Step 5 - Deploy agent first, then setup IAM

set -e

export GOOGLE_CLOUD_PROJECT="${GOOGLE_CLOUD_PROJECT:-gen-lang-client-0707167243}"
export GOOGLE_CLOUD_REGION="${GOOGLE_CLOUD_REGION:-us-central1}"
export MCP_SERVER_URL="${MCP_SERVER_URL:-https://mcp-server-szbewwqnrq-uc.a.run.app/sse}"

echo "🔧 Fixing Step 5 - Correct Order"
echo "═══════════════════════════════════════════════════════════"
echo "Project: ${GOOGLE_CLOUD_PROJECT}"
echo "MCP Server: ${MCP_SERVER_URL}"
echo ""

# Step 1: Deploy ADK Agent (this creates the service account)
echo "📋 Step 1: Deploying ADK Agent..."
echo "   (This will create the service account: ${GOOGLE_CLOUD_PROJECT}@appspot.gserviceaccount.com)"
echo ""

if [ -f "./deploy-adk-agent.sh" ]; then
  ./deploy-adk-agent.sh
else
  echo "❌ deploy-adk-agent.sh not found"
  exit 1
fi

# Wait a moment for service account to be fully created
echo ""
echo "⏳ Waiting for service account to be fully created..."
sleep 5

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
    echo "   Try again in a few seconds:"
    echo "   gcloud projects add-iam-policy-binding ${GOOGLE_CLOUD_PROJECT} \\"
    echo "     --member=\"serviceAccount:${SERVICE_ACCOUNT}\" \\"
    echo "     --role=\"roles/aiplatform.user\""
  fi
else
  echo "✅ Vertex AI permissions already granted"
fi

echo ""
echo "═══════════════════════════════════════════════════════════"
echo "✅ Setup Complete!"
echo "═══════════════════════════════════════════════════════════"
echo ""
echo "Test the deployment:"
echo "  ./test-deployment.sh"
echo ""
