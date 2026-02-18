#!/bin/bash
# Workaround to enable APIs using CLI with proper account context

set -e

PROJECT_ID="${GOOGLE_CLOUD_PROJECT:-gen-lang-client-0707167243}"
REGION="${GOOGLE_CLOUD_REGION:-us-central1}"
CURRENT_ACCOUNT=$(gcloud config get-value account 2>/dev/null || echo "")

echo "🔧 API Enablement Workaround"
echo "═══════════════════════════════════════════════════════════"
echo ""
echo "Project: ${PROJECT_ID}"
echo "Account: ${CURRENT_ACCOUNT}"
echo ""

if [ -z "$CURRENT_ACCOUNT" ]; then
  echo "❌ No account authenticated"
  exit 1
fi

# Check if we can use serviceusage API directly
echo "📋 Attempting to enable APIs..."
echo ""

# Try enabling with explicit account and project
ENABLE_CMD="gcloud services enable --project=${PROJECT_ID}"

# Try each API individually with error handling
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
  if $ENABLE_CMD ${API} 2>&1; then
    echo "✅ ${API} enabled successfully"
    SUCCESS_COUNT=$((SUCCESS_COUNT + 1))
  else
    echo "⚠️  Failed to enable ${API} via CLI"
    FAILED_APIS+=("${API}")
  fi
  echo ""
done

echo "═══════════════════════════════════════════════════════════"
echo "Results: ${SUCCESS_COUNT}/${#APIS[@]} APIs enabled"
echo "═══════════════════════════════════════════════════════════"
echo ""

if [ ${#FAILED_APIS[@]} -gt 0 ]; then
  echo "⚠️  Failed APIs:"
  for API in "${FAILED_APIS[@]}"; do
    echo "  - ${API}"
  done
  echo ""
  echo "Alternative Solutions:"
  echo ""
  echo "Option 1: Use Incognito/Private Browser Window"
  echo "  1. Open incognito/private window"
  echo "  2. Sign in ONLY with: ${CURRENT_ACCOUNT}"
  echo "  3. Go to API Library and enable manually"
  echo ""
  echo "Option 2: Use Specific Account in Browser"
  echo "  Add ?authuser=0 to URL to force first account"
  echo "  Or sign out other accounts temporarily"
  echo ""
  echo "Option 3: Check if APIs are already enabled"
  echo "  Run: gcloud services list --enabled --project ${PROJECT_ID}"
fi

# Check current status
echo ""
echo "📊 Current API Status:"
gcloud services list --enabled --project ${PROJECT_ID} 2>/dev/null | grep -E "cloudrun|cloudbuild|aiplatform|artifactregistry" || echo "  (Checking...)"

echo ""
