#!/bin/bash
# Grant Service Account User role to current user

set -e

PROJECT_ID="${GOOGLE_CLOUD_PROJECT:-gen-lang-client-0707167243}"
SERVICE_ACCOUNT="${PROJECT_ID}@appspot.gserviceaccount.com"
CURRENT_USER=$(gcloud config get-value account)

echo "🔐 Granting Service Account User Permission"
echo "═══════════════════════════════════════════════════════════"
echo "Project: ${PROJECT_ID}"
echo "Service Account: ${SERVICE_ACCOUNT}"
echo "User: ${CURRENT_USER}"
echo ""

# Check if service account exists
SA_EXISTS=$(gcloud iam service-accounts describe ${SERVICE_ACCOUNT} --project ${PROJECT_ID} 2>/dev/null && echo "yes" || echo "no")

if [ "$SA_EXISTS" == "no" ]; then
  echo "⚠️  Service account ${SERVICE_ACCOUNT} does not exist yet."
  echo "   It will be created automatically when you deploy a Cloud Run service."
  echo ""
  echo "   You can either:"
  echo "   1. Deploy without --service-account flag (recommended)"
  echo "   2. Create the service account first:"
  echo "      gcloud iam service-accounts create compute-sa \\"
  echo "        --display-name=\"Compute Service Account\" \\"
  echo "        --project ${PROJECT_ID}"
  exit 0
fi

# Grant Service Account User role
echo "Granting roles/iam.serviceAccountUser to ${CURRENT_USER}..."
if gcloud iam service-accounts add-iam-policy-binding ${SERVICE_ACCOUNT} \
  --member="user:${CURRENT_USER}" \
  --role="roles/iam.serviceAccountUser" \
  --project ${PROJECT_ID} 2>/dev/null; then
  echo "✅ Service Account User permission granted!"
  echo ""
  echo "You can now deploy Cloud Run services using this service account."
else
  echo "⚠️  Failed to grant permission (may already be granted)"
  echo ""
  echo "Checking current permissions..."
  gcloud iam service-accounts get-iam-policy ${SERVICE_ACCOUNT} \
    --project ${PROJECT_ID} \
    --format="table(bindings.members,bindings.role)" | grep -E "${CURRENT_USER}|serviceAccountUser" || echo "  No matching bindings found"
fi

echo ""
