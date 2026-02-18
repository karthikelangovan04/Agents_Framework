#!/bin/bash
# Check and fix permissions for API enablement

echo "🔐 Checking Project Permissions"
echo "═══════════════════════════════════════════════════════════"
echo ""

PROJECT_ID=$(gcloud config get-value project 2>/dev/null)
CURRENT_ACCOUNT=$(gcloud config get-value account 2>/dev/null)

if [ -z "$PROJECT_ID" ]; then
  echo "❌ No project set. Please set a project first."
  exit 1
fi

if [ -z "$CURRENT_ACCOUNT" ]; then
  echo "❌ No account authenticated. Please authenticate first."
  exit 1
fi

echo "Project: ${PROJECT_ID}"
echo "Account: ${CURRENT_ACCOUNT}"
echo ""

# Check IAM permissions
echo "📋 Checking IAM Permissions..."
echo "───────────────────────────────────────────────────────────"
ROLES=$(gcloud projects get-iam-policy ${PROJECT_ID} \
  --flatten="bindings[].members" \
  --filter="bindings.members:user:${CURRENT_ACCOUNT}" \
  --format="value(bindings.role)" 2>/dev/null)

if [ -z "$ROLES" ]; then
  echo "❌ No IAM roles found for this account!"
  echo ""
  echo "You need one of these roles to enable APIs:"
  echo "  - roles/owner"
  echo "  - roles/editor"
  echo "  - roles/serviceusage.serviceUsageAdmin"
  echo ""
  echo "Solutions:"
  echo "  1. Ask project owner to grant you 'Editor' or 'Owner' role"
  echo "  2. Or grant yourself 'Service Usage Admin' role (if you're owner)"
  echo "  3. Or use a different project where you have permissions"
  exit 1
fi

echo "Your roles:"
echo "$ROLES" | while read role; do
  echo "  ✅ ${role}"
done
echo ""

# Check if user has necessary permissions
HAS_PERMISSION=false
if echo "$ROLES" | grep -qE "roles/owner|roles/editor|roles/serviceusage.serviceUsageAdmin"; then
  HAS_PERMISSION=true
fi

if [ "$HAS_PERMISSION" = false ]; then
  echo "⚠️  You don't have permission to enable APIs!"
  echo ""
  echo "Required roles (one of):"
  echo "  - roles/owner"
  echo "  - roles/editor"
  echo "  - roles/serviceusage.serviceUsageAdmin"
  echo ""
  echo "Current roles don't include any of the above."
  echo ""
  echo "Solutions:"
  echo "  1. Ask project owner to grant you 'Editor' role:"
  echo "     gcloud projects add-iam-policy-binding ${PROJECT_ID} \\"
  echo "       --member=\"user:${CURRENT_ACCOUNT}\" \\"
  echo "       --role=\"roles/editor\""
  echo ""
  echo "  2. Or use a project where you're the owner"
  echo "  3. Or create a new project:"
  echo "     gcloud projects create YOUR_NEW_PROJECT_ID"
  exit 1
fi

# Check billing
echo "💰 Checking Billing Status..."
echo "───────────────────────────────────────────────────────────"
BILLING_ACCOUNT=$(gcloud billing projects describe ${PROJECT_ID} --format="value(billingAccountName)" 2>/dev/null || echo "")

if [ -z "$BILLING_ACCOUNT" ] || [ "$BILLING_ACCOUNT" == "" ]; then
  echo "⚠️  No billing account linked!"
  echo ""
  echo "To enable APIs, billing must be enabled:"
  echo "  1. Go to: https://console.cloud.google.com/billing"
  echo "  2. Link a billing account to project: ${PROJECT_ID}"
  echo ""
  echo "Or link via CLI (if you have billing account ID):"
  echo "  gcloud billing projects link ${PROJECT_ID} --billing-account=BILLING_ACCOUNT_ID"
  echo ""
  read -p "Do you want to continue anyway? (yes/no): " continue_anyway
  if [ "$continue_anyway" != "yes" ]; then
    exit 1
  fi
else
  echo "✅ Billing account linked: ${BILLING_ACCOUNT}"
fi

echo ""
echo "═══════════════════════════════════════════════════════════"
echo "✅ Permission Check Complete"
echo "═══════════════════════════════════════════════════════════"
echo ""
echo "If you have the required roles, you can proceed with setup."
echo "If not, you'll need to:"
echo "  1. Get permissions from project owner, OR"
echo "  2. Create/use a project where you're the owner"
echo ""
