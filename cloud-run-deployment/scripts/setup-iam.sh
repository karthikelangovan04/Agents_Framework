#!/bin/bash
# Setup IAM permissions for service-to-service authentication

set -e

# Configuration
PROJECT_ID="${GOOGLE_CLOUD_PROJECT:-your-project-id}"
REGION="${GOOGLE_CLOUD_REGION:-us-central1}"
MCP_SERVICE_NAME="mcp-server"
AGENT_SERVICE_NAME="adk-agent"

echo "🔐 Setting up IAM permissions for service-to-service authentication..."
echo "Project: ${PROJECT_ID}"

# Get the service account email for the ADK agent service
# Cloud Run services use the default compute service account by default
# First try to get the actual service account from the deployed service
PROJECT_NUMBER=$(gcloud projects describe ${PROJECT_ID} --format="value(projectNumber)" 2>/dev/null || echo "")
if [ -n "$PROJECT_NUMBER" ]; then
  # Try to get service account from deployed service
  DEPLOYED_SA=$(gcloud run services describe adk-agent \
    --platform managed \
    --region ${REGION} \
    --project ${PROJECT_ID} \
    --format="value(spec.template.spec.serviceAccountName)" 2>/dev/null || echo "")
  
  if [ -n "$DEPLOYED_SA" ] && [ "$DEPLOYED_SA" != "" ]; then
    AGENT_SERVICE_ACCOUNT="${DEPLOYED_SA}"
    echo "  Using service account from deployed service: ${AGENT_SERVICE_ACCOUNT}"
  else
    # Fallback to compute service account
    AGENT_SERVICE_ACCOUNT="${PROJECT_NUMBER}-compute@developer.gserviceaccount.com"
    echo "  Using default compute service account: ${AGENT_SERVICE_ACCOUNT}"
  fi
else
  # Fallback to appspot service account
  AGENT_SERVICE_ACCOUNT="${PROJECT_ID}@appspot.gserviceaccount.com"
fi

# Check if service account exists
SA_EXISTS=$(gcloud iam service-accounts describe ${AGENT_SERVICE_ACCOUNT} --project ${PROJECT_ID} 2>/dev/null && echo "yes" || echo "no")

if [ "$SA_EXISTS" == "no" ]; then
  echo "⚠️  Service account ${AGENT_SERVICE_ACCOUNT} does not exist yet."
  echo "   It will be created automatically when ADK agent is deployed."
  echo "   Run this script again after deploying the ADK agent."
  echo ""
  echo "   Or deploy ADK agent first, then run this script."
  exit 0
fi

echo "📋 Granting Cloud Run Invoker role to agent service account..."
echo "   Service Account: ${AGENT_SERVICE_ACCOUNT}"
echo "   Target Service: ${MCP_SERVICE_NAME}"

# Grant the agent's service account permission to invoke the MCP server
if gcloud run services add-iam-policy-binding ${MCP_SERVICE_NAME} \
  --member="serviceAccount:${AGENT_SERVICE_ACCOUNT}" \
  --role="roles/run.invoker" \
  --region ${REGION} \
  --project ${PROJECT_ID} 2>/dev/null; then
  echo ""
  echo "✅ IAM permissions configured successfully!"
  echo ""
  echo "The ADK agent service account can now invoke the MCP server."
else
  echo ""
  echo "⚠️  Failed to grant IAM permissions. The binding may already exist."
  echo "   Verifying current IAM policy..."
  gcloud run services get-iam-policy ${MCP_SERVICE_NAME} \
    --region ${REGION} \
    --project ${PROJECT_ID} \
    --format="table(bindings.members,bindings.role)" | grep -E "${AGENT_SERVICE_ACCOUNT}|run.invoker" || echo "   No matching bindings found"
fi
