#!/bin/bash
# Helper script to find and set your Google Cloud Project ID

echo "🔍 Finding Your Google Cloud Project ID"
echo "═══════════════════════════════════════════════════════════"
echo ""

# Check if already authenticated
if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | grep -q .; then
  echo "⚠️  Not authenticated. Please authenticate first:"
  echo "   gcloud auth login"
  echo ""
  echo "This will:"
  echo "  1. Open your browser"
  echo "  2. Ask you to sign in with your Google account email"
  echo "  3. Grant permissions to gcloud CLI"
  echo ""
  read -p "Do you want to authenticate now? (yes/no): " auth_now
  
  if [ "$auth_now" == "yes" ]; then
    gcloud auth login
    echo ""
    echo "✅ Authentication complete!"
    echo ""
  else
    echo "Please run 'gcloud auth login' first, then run this script again."
    exit 1
  fi
fi

# Show current account
CURRENT_ACCOUNT=$(gcloud auth list --filter=status:ACTIVE --format="value(account)" | head -1)
echo "Authenticated as: ${CURRENT_ACCOUNT}"
echo ""

# List all projects
echo "📋 Available Projects:"
echo "───────────────────────────────────────────────────────────"
gcloud projects list --format="table(projectId,name,projectNumber)" || {
  echo "❌ Error listing projects. Make sure you're authenticated."
  exit 1
}
echo ""

# Get current project
CURRENT_PROJECT=$(gcloud config get-value project 2>/dev/null || echo "")

if [ -n "$CURRENT_PROJECT" ]; then
  echo "✅ Current Project: ${CURRENT_PROJECT}"
  echo ""
  read -p "Do you want to use this project? (yes/no): " use_current
  
  if [ "$use_current" == "yes" ]; then
    SELECTED_PROJECT=$CURRENT_PROJECT
  else
    echo ""
    read -p "Enter Project ID to use: " SELECTED_PROJECT
  fi
else
  echo "⚠️  No project currently set."
  echo ""
  read -p "Enter Project ID to use: " SELECTED_PROJECT
fi

# Validate project ID
if [ -z "$SELECTED_PROJECT" ]; then
  echo "❌ Project ID cannot be empty."
  exit 1
fi

# Verify project exists and user has access
echo ""
echo "🔍 Verifying project access..."
if gcloud projects describe ${SELECTED_PROJECT} &>/dev/null; then
  echo "✅ Project '${SELECTED_PROJECT}' is accessible"
else
  echo "❌ Cannot access project '${SELECTED_PROJECT}'"
  echo "   Make sure:"
  echo "   1. Project ID is correct"
  echo "   2. You have access to this project"
  echo "   3. Project exists"
  exit 1
fi

# Set project
echo ""
echo "⚙️  Setting project..."
gcloud config set project ${SELECTED_PROJECT}
export GOOGLE_CLOUD_PROJECT=${SELECTED_PROJECT}

# Verify
VERIFIED_PROJECT=$(gcloud config get-value project)
if [ "$VERIFIED_PROJECT" == "$SELECTED_PROJECT" ]; then
  echo "✅ Project set successfully!"
else
  echo "❌ Failed to set project"
  exit 1
fi

# Display summary
echo ""
echo "═══════════════════════════════════════════════════════════"
echo "✅ Configuration Complete!"
echo "═══════════════════════════════════════════════════════════"
echo ""
echo "Project ID: ${GOOGLE_CLOUD_PROJECT}"
echo "Account: ${CURRENT_ACCOUNT}"
echo ""
echo "To use this in your terminal session, run:"
echo "  export GOOGLE_CLOUD_PROJECT=\"${GOOGLE_CLOUD_PROJECT}\""
echo "  export GOOGLE_CLOUD_REGION=\"us-central1\""
echo ""
echo "Or add to your shell profile (~/.bashrc or ~/.zshrc):"
echo "  export GOOGLE_CLOUD_PROJECT=\"${GOOGLE_CLOUD_PROJECT}\""
echo "  export GOOGLE_CLOUD_REGION=\"us-central1\""
echo ""
