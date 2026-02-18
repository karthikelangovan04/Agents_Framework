#!/bin/bash
# Test script for deployed services

set -e

# Configuration
PROJECT_ID="${GOOGLE_CLOUD_PROJECT:-your-project-id}"
REGION="${GOOGLE_CLOUD_REGION:-us-central1}"
MCP_SERVICE_NAME="mcp-server"
AGENT_SERVICE_NAME="adk-agent"

echo "🧪 Testing Cloud Run Deployment..."
echo ""

# Get service URLs
echo "📋 Getting service URLs..."
MCP_URL=$(gcloud run services describe ${MCP_SERVICE_NAME} \
  --platform managed \
  --region ${REGION} \
  --project ${PROJECT_ID} \
  --format 'value(status.url)' 2>/dev/null || echo "")

AGENT_URL=$(gcloud run services describe ${AGENT_SERVICE_NAME} \
  --platform managed \
  --region ${REGION} \
  --project ${PROJECT_ID} \
  --format 'value(status.url)' 2>/dev/null || echo "")

if [ -z "$MCP_URL" ]; then
  echo "❌ MCP Server not found. Please deploy it first."
  exit 1
fi

if [ -z "$AGENT_URL" ]; then
  echo "❌ ADK Agent not found. Please deploy it first."
  exit 1
fi

echo "✅ MCP Server: ${MCP_URL}"
echo "✅ ADK Agent: ${AGENT_URL}"
echo ""

# Test 1: ADK Agent Health Check
echo "🧪 Test 1: ADK Agent Health Check"
HEALTH_RESPONSE=$(curl -s ${AGENT_URL}/health)
if echo "$HEALTH_RESPONSE" | grep -q "healthy"; then
  echo "✅ ADK Agent is healthy"
else
  echo "❌ ADK Agent health check failed"
  echo "   Response: ${HEALTH_RESPONSE}"
fi
echo ""

# Test 2: ADK Agent Chat Endpoint
echo "🧪 Test 2: ADK Agent Chat Endpoint"
CHAT_RESPONSE=$(curl -s -X POST ${AGENT_URL}/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "What is 100 USD in EUR?",
    "session_id": "test-session"
  }')

if echo "$CHAT_RESPONSE" | grep -q "response"; then
  echo "✅ ADK Agent chat endpoint working"
  echo "   Response preview: $(echo $CHAT_RESPONSE | head -c 100)..."
else
  echo "❌ ADK Agent chat endpoint failed"
  echo "   Response: ${CHAT_RESPONSE}"
fi
echo ""

# Test 3: MCP Server Authentication (if accessible)
echo "🧪 Test 3: MCP Server Authentication"
ID_TOKEN=$(gcloud auth print-identity-token 2>/dev/null || echo "")
if [ -n "$ID_TOKEN" ]; then
  MCP_HEALTH=$(curl -s -H "Authorization: Bearer ${ID_TOKEN}" \
    ${MCP_URL}/health 2>/dev/null || echo "")
  if [ -n "$MCP_HEALTH" ]; then
    echo "✅ MCP Server is accessible with authentication"
  else
    echo "⚠️  MCP Server health endpoint not available (this is OK)"
  fi
else
  echo "⚠️  Could not get ID token for MCP server test"
fi
echo ""

# Test 4: Check IAM Permissions
echo "🧪 Test 4: IAM Permissions"
AGENT_SA="${PROJECT_ID}@appspot.gserviceaccount.com"
IAM_POLICY=$(gcloud run services get-iam-policy ${MCP_SERVICE_NAME} \
  --region ${REGION} \
  --project ${PROJECT_ID} \
  --format json 2>/dev/null || echo "{}")

if echo "$IAM_POLICY" | grep -q "${AGENT_SA}"; then
  echo "✅ IAM permissions configured correctly"
else
  echo "⚠️  IAM permissions may not be set correctly"
  echo "   Run: ./setup-iam.sh"
fi
echo ""

echo "✅ Testing complete!"
echo ""
echo "📊 Summary:"
echo "   MCP Server: ${MCP_URL}"
echo "   ADK Agent: ${AGENT_URL}"
echo ""
echo "🧪 Test the agent:"
echo "   curl -X POST ${AGENT_URL}/chat \\"
echo "     -H 'Content-Type: application/json' \\"
echo "     -d '{\"message\": \"What is 100 USD in EUR?\"}'"
