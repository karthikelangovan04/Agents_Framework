#!/bin/bash
# Check project restrictions and billing limitations

PROJECT_ID="${GOOGLE_CLOUD_PROJECT:-gen-lang-client-0707167243}"

echo "🔍 Checking Project Restrictions"
echo "═══════════════════════════════════════════════════════════"
echo "Project: ${PROJECT_ID}"
echo ""

# Check project state
echo "📋 Project Status:"
PROJECT_STATE=$(gcloud projects describe ${PROJECT_ID} --format="value(lifecycleState)" 2>/dev/null || echo "UNKNOWN")
echo "  State: ${PROJECT_STATE}"

if [ "$PROJECT_STATE" != "ACTIVE" ]; then
  echo "  ⚠️  Project is not ACTIVE!"
fi
echo ""

# Check billing
echo "💰 Billing Status:"
BILLING_ACCOUNT=$(gcloud billing projects describe ${PROJECT_ID} --format="value(billingAccountName)" 2>/dev/null || echo "")
if [ -n "$BILLING_ACCOUNT" ] && [ "$BILLING_ACCOUNT" != "" ]; then
  echo "  ✅ Billing Account: ${BILLING_ACCOUNT}"
  
  # Check billing account details
  BILLING_ID=$(echo ${BILLING_ACCOUNT} | sed 's|billingAccounts/||')
  echo "  Checking billing account restrictions..."
  
  # Note: Some billing accounts may have restrictions
  echo "  ⚠️  If this is a trial/credits account, it may have API restrictions"
else
  echo "  ❌ No billing account linked!"
fi
echo ""

# Check organization policies (if applicable)
echo "🏢 Organization Policies:"
ORG_ID=$(gcloud projects describe ${PROJECT_ID} --format="value(parent.id)" 2>/dev/null || echo "")
if [ -n "$ORG_ID" ] && [ "$ORG_ID" != "" ]; then
  echo "  Organization: ${ORG_ID}"
  echo "  ⚠️  Organization policies may restrict API enablement"
else
  echo "  No organization (standalone project)"
fi
echo ""

# Check currently enabled APIs
echo "📊 Currently Enabled APIs:"
ENABLED_APIS=$(gcloud services list --enabled --project ${PROJECT_ID} 2>/dev/null | grep -E "cloudrun|cloudbuild|aiplatform|artifactregistry" || echo "")
if [ -n "$ENABLED_APIS" ]; then
  echo "$ENABLED_APIS"
else
  echo "  None of the required APIs are enabled"
fi
echo ""

# Recommendations
echo "═══════════════════════════════════════════════════════════"
echo "💡 Recommendations:"
echo "═══════════════════════════════════════════════════════════"
echo ""

if [ -z "$ENABLED_APIS" ]; then
  echo "1. Try REST API method:"
  echo "   ./enable-apis-rest-api.sh"
  echo ""
  echo "2. If billing account has restrictions:"
  echo "   - Create a new project with full billing access"
  echo "   - Or contact billing account admin to enable APIs"
  echo ""
  echo "3. Check if this is a 'Gen AI only' billing account:"
  echo "   - Some accounts are restricted to AI services only"
  echo "   - You may need a different billing account"
  echo ""
  echo "4. Alternative: Use a different project"
  echo "   gcloud projects create my-adk-project-$(date +%s)"
  echo "   gcloud config set project my-adk-project-XXXXX"
else
  echo "✅ Some APIs are already enabled!"
  echo "   You may be able to proceed with deployment"
  echo "   Try: ./setup-vertex-ai.sh"
fi

echo ""
