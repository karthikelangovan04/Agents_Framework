#!/bin/bash
# Fix project access issue

echo "🔧 Fixing Project Access"
echo "═══════════════════════════════════════════════════════════"
echo ""

# Get current account
CURRENT_ACCOUNT=$(gcloud config get-value account)
echo "Current Account: ${CURRENT_ACCOUNT}"
echo ""

# List available projects
echo "📋 Projects available to this account:"
echo "───────────────────────────────────────────────────────────"
gcloud projects list --format="table(projectId,name,projectNumber)"
echo ""

# Get projects
PROJECTS=$(gcloud projects list --format="value(projectId)")

if [ -z "$PROJECTS" ]; then
  echo "❌ No projects found for this account."
  echo "   You may need to create a project or be granted access."
  exit 1
fi

# Show projects with numbers
echo "Available Projects:"
COUNT=1
echo "$PROJECTS" | while read project; do
  echo "  ${COUNT}) ${project}"
  COUNT=$((COUNT + 1))
done

echo ""
read -p "Enter project ID to use (or press Enter for first project): " SELECTED_PROJECT

# Use first project if nothing entered
if [ -z "$SELECTED_PROJECT" ]; then
  SELECTED_PROJECT=$(echo "$PROJECTS" | head -1)
fi

# Verify project exists in list
if ! echo "$PROJECTS" | grep -q "^${SELECTED_PROJECT}$"; then
  echo "❌ Project '${SELECTED_PROJECT}' not found in available projects"
  exit 1
fi

# Set project
echo ""
echo "⚙️  Setting project to: ${SELECTED_PROJECT}"
gcloud config set project ${SELECTED_PROJECT}

# Set quota project for Application Default Credentials
echo "Setting quota project for Application Default Credentials..."
gcloud auth application-default set-quota-project ${SELECTED_PROJECT} || {
  echo "⚠️  Could not set quota project. You may need to run:"
  echo "   gcloud auth application-default login"
}

# Verify
VERIFIED_PROJECT=$(gcloud config get-value project)
if [ "$VERIFIED_PROJECT" == "$SELECTED_PROJECT" ]; then
  echo "✅ Project set successfully!"
else
  echo "❌ Failed to set project"
  exit 1
fi

# Export for scripts
export GOOGLE_CLOUD_PROJECT=${SELECTED_PROJECT}
export GOOGLE_CLOUD_REGION="us-central1"

echo ""
echo "═══════════════════════════════════════════════════════════"
echo "✅ Project Access Fixed!"
echo "═══════════════════════════════════════════════════════════"
echo ""
echo "Project: ${GOOGLE_CLOUD_PROJECT}"
echo "Region: ${GOOGLE_CLOUD_REGION}"
echo ""
echo "To use in your terminal session:"
echo "  export GOOGLE_CLOUD_PROJECT=\"${GOOGLE_CLOUD_PROJECT}\""
echo "  export GOOGLE_CLOUD_REGION=\"us-central1\""
echo ""
echo "Now you can run: ./setup-vertex-ai.sh"
echo ""
