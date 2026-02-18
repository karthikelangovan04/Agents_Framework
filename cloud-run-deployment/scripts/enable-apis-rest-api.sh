#!/bin/bash
# Alternative method: Enable APIs using REST API directly

set -e

PROJECT_ID="${GOOGLE_CLOUD_PROJECT:-gen-lang-client-0707167243}"
PROJECT_NUMBER=$(gcloud projects describe ${PROJECT_ID} --format="value(projectNumber)" 2>/dev/null || echo "")

if [ -z "$PROJECT_NUMBER" ]; then
  echo "❌ Could not get project number"
  exit 1
fi

echo "🔧 Enabling APIs via REST API"
echo "═══════════════════════════════════════════════════════════"
echo "Project: ${PROJECT_ID}"
echo "Project Number: ${PROJECT_NUMBER}"
echo ""

# Get access token
echo "Getting access token..."
ACCESS_TOKEN=$(gcloud auth print-access-token)

if [ -z "$ACCESS_TOKEN" ]; then
  echo "❌ Could not get access token"
  exit 1
fi

# APIs to enable
APIS=(
  "cloudrun.googleapis.com"
  "cloudbuild.googleapis.com"
  "aiplatform.googleapis.com"
  "artifactregistry.googleapis.com"
)

SUCCESS_COUNT=0
FAILED_APIS=()

for API in "${APIS[@]}"; do
  echo "Enabling ${API}..."
  
  # Use REST API to enable service
  TEMP_FILE=$(mktemp)
  HTTP_CODE=$(curl -s -o "${TEMP_FILE}" -w "%{http_code}" -X POST \
    "https://serviceusage.googleapis.com/v1/projects/${PROJECT_NUMBER}/services/${API}:enable" \
    -H "Authorization: Bearer ${ACCESS_TOKEN}" \
    -H "Content-Type: application/json")
  
  BODY=$(cat "${TEMP_FILE}")
  rm -f "${TEMP_FILE}"
  
  if [ "$HTTP_CODE" == "200" ] || [ "$HTTP_CODE" == "409" ]; then
    # 200 = success, 409 = already enabled
    echo "✅ ${API} enabled (HTTP ${HTTP_CODE})"
    SUCCESS_COUNT=$((SUCCESS_COUNT + 1))
  else
    echo "⚠️  Failed to enable ${API} (HTTP ${HTTP_CODE})"
    echo "   Response: ${BODY}"
    FAILED_APIS+=("${API}")
  fi
  echo ""
done

echo "═══════════════════════════════════════════════════════════"
echo "Results: ${SUCCESS_COUNT}/${#APIS[@]} APIs processed"
echo "═══════════════════════════════════════════════════════════"
echo ""

if [ ${#FAILED_APIS[@]} -gt 0 ]; then
  echo "⚠️  Failed APIs:"
  for API in "${FAILED_APIS[@]}"; do
    echo "  - ${API}"
  done
fi

# Verify
echo ""
echo "📊 Verifying enabled APIs..."
gcloud services list --enabled --project ${PROJECT_ID} 2>/dev/null | grep -E "cloudrun|cloudbuild|aiplatform|artifactregistry" || echo "  (Some APIs may still be enabling...)"

echo ""
