#!/bin/bash
# Cleanup Script for Cloud Run Deployment
# Removes all deployed resources

set -e

export GOOGLE_CLOUD_PROJECT="${GOOGLE_CLOUD_PROJECT:-your-project-id}"
export GOOGLE_CLOUD_REGION="${GOOGLE_CLOUD_REGION:-us-central1}"

echo "🧹 Cloud Run Deployment Cleanup"
echo "═══════════════════════════════════════════════════════════"
echo "Project: ${GOOGLE_CLOUD_PROJECT}"
echo "Region: ${GOOGLE_CLOUD_REGION}"
echo ""

# Check if project is set
if [ "$GOOGLE_CLOUD_PROJECT" == "your-project-id" ]; then
  echo "❌ Error: Please set GOOGLE_CLOUD_PROJECT environment variable"
  echo "   export GOOGLE_CLOUD_PROJECT=\"your-actual-project-id\""
  exit 1
fi

# Confirmation
read -p "⚠️  Are you sure you want to delete ALL resources? (yes/no): " confirm
if [ "$confirm" != "yes" ]; then
  echo "Cleanup cancelled."
  exit 0
fi

echo ""
echo "Starting cleanup..."

# Delete Cloud Run services
echo ""
echo "📋 Deleting Cloud Run services..."
gcloud run services delete adk-agent \
  --region ${GOOGLE_CLOUD_REGION} \
  --project ${GOOGLE_CLOUD_PROJECT} \
  --quiet 2>/dev/null && echo "  ✅ Deleted adk-agent" || echo "  ⚠️  adk-agent not found"

gcloud run services delete mcp-server \
  --region ${GOOGLE_CLOUD_REGION} \
  --project ${GOOGLE_CLOUD_PROJECT} \
  --quiet 2>/dev/null && echo "  ✅ Deleted mcp-server" || echo "  ⚠️  mcp-server not found"

# Delete container images
echo ""
echo "📋 Deleting container images..."
gcloud container images delete gcr.io/${GOOGLE_CLOUD_PROJECT}/adk-agent \
  --quiet \
  --project ${GOOGLE_CLOUD_PROJECT} 2>/dev/null && echo "  ✅ Deleted adk-agent image" || echo "  ⚠️  adk-agent image not found"

gcloud container images delete gcr.io/${GOOGLE_CLOUD_PROJECT}/mcp-server \
  --quiet \
  --project ${GOOGLE_CLOUD_PROJECT} 2>/dev/null && echo "  ✅ Deleted mcp-server image" || echo "  ⚠️  mcp-server image not found"

# Optional: Remove IAM bindings
echo ""
read -p "Remove IAM bindings? (yes/no): " remove_iam
if [ "$remove_iam" == "yes" ]; then
  echo "📋 Removing IAM bindings..."
  SERVICE_ACCOUNT="${GOOGLE_CLOUD_PROJECT}@appspot.gserviceaccount.com"
  
  # Remove Vertex AI User role
  gcloud projects remove-iam-policy-binding ${GOOGLE_CLOUD_PROJECT} \
    --member="serviceAccount:${SERVICE_ACCOUNT}" \
    --role="roles/aiplatform.user" \
    --quiet 2>/dev/null && echo "  ✅ Removed Vertex AI User role" || echo "  ⚠️  Vertex AI User role not found"
  
  # Remove Cloud Run Invoker role (if service still exists in policy)
  gcloud run services remove-iam-policy-binding mcp-server \
    --member="serviceAccount:${SERVICE_ACCOUNT}" \
    --role="roles/run.invoker" \
    --region ${GOOGLE_CLOUD_REGION} \
    --project ${GOOGLE_CLOUD_PROJECT} \
    --quiet 2>/dev/null && echo "  ✅ Removed Cloud Run Invoker role" || echo "  ⚠️  Cloud Run Invoker role not found (service may already be deleted)"
else
  echo "  ⏭️  Skipping IAM binding removal"
fi

echo ""
echo "═══════════════════════════════════════════════════════════"
echo "✅ Cleanup complete!"
echo "═══════════════════════════════════════════════════════════"
echo ""
echo "Note: APIs remain enabled. To disable them:"
echo "  gcloud services disable cloudrun.googleapis.com --project ${GOOGLE_CLOUD_PROJECT}"
echo "  gcloud services disable aiplatform.googleapis.com --project ${GOOGLE_CLOUD_PROJECT}"
echo "  gcloud services disable cloudbuild.googleapis.com --project ${GOOGLE_CLOUD_PROJECT}"
echo ""
