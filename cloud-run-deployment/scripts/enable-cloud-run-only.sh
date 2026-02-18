#!/bin/bash
# Enable only Cloud Run API (other APIs are already enabled)

set -e

PROJECT_ID="${GOOGLE_CLOUD_PROJECT:-gen-lang-client-0707167243}"
PROJECT_NUMBER=$(gcloud projects describe ${PROJECT_ID} --format="value(projectNumber)" 2>/dev/null || echo "")

echo "🔧 Enabling Cloud Run API"
echo "═══════════════════════════════════════════════════════════"
echo "Project: ${PROJECT_ID}"
echo "Project Number: ${PROJECT_NUMBER}"
echo ""

# Check current status
echo "📊 Current API Status:"
for api in cloudrun.googleapis.com cloudbuild.googleapis.com aiplatform.googleapis.com artifactregistry.googleapis.com; do
  status=$(gcloud services list --enabled --project ${PROJECT_ID} --filter="name:${api}" --format="value(name)" 2>/dev/null)
  if [ -n "$status" ]; then
    echo "  ✅ ${api}"
  else
    echo "  ❌ ${api}"
  fi
done
echo ""

# Try enabling Cloud Run via REST API
echo "Attempting to enable Cloud Run API..."
ACCESS_TOKEN=$(gcloud auth print-access-token)

if [ -z "$ACCESS_TOKEN" ]; then
  echo "❌ Could not get access token"
  exit 1
fi

TEMP_FILE=$(mktemp)
HTTP_CODE=$(curl -s -o "${TEMP_FILE}" -w "%{http_code}" -X POST \
  "https://serviceusage.googleapis.com/v1/projects/${PROJECT_NUMBER}/services/cloudrun.googleapis.com:enable" \
  -H "Authorization: Bearer ${ACCESS_TOKEN}" \
  -H "Content-Type: application/json")

BODY=$(cat "${TEMP_FILE}")
rm -f "${TEMP_FILE}"

if [ "$HTTP_CODE" == "200" ]; then
  echo "✅ Cloud Run API enabled successfully!"
elif [ "$HTTP_CODE" == "409" ]; then
  echo "✅ Cloud Run API is already enabled!"
elif [ "$HTTP_CODE" == "403" ]; then
  echo "❌ Permission denied - billing account may not support Cloud Run"
  echo ""
  echo "Error details:"
  echo "$BODY" | grep -o '"message":"[^"]*"' | head -1
  echo ""
  echo "Solutions:"
  echo "  1. Try enabling via Console (incognito window):"
  echo "     https://console.cloud.google.com/apis/library/cloudrun.googleapis.com?project=${PROJECT_ID}"
  echo ""
  echo "  2. Use a different project with full billing access"
  echo ""
  echo "  3. Contact billing account admin to enable Cloud Run"
else
  echo "⚠️  Unexpected response (HTTP ${HTTP_CODE})"
  echo "Response: ${BODY}"
fi

echo ""
echo "📊 Updated API Status:"
for api in cloudrun.googleapis.com cloudbuild.googleapis.com aiplatform.googleapis.com artifactregistry.googleapis.com; do
  status=$(gcloud services list --enabled --project ${PROJECT_ID} --filter="name:${api}" --format="value(name)" 2>/dev/null)
  if [ -n "$status" ]; then
    echo "  ✅ ${api}"
  else
    echo "  ❌ ${api}"
  fi
done
echo ""
