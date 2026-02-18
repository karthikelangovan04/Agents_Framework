#!/bin/bash
# Script to open Google Cloud Console for API enablement

PROJECT_ID=$(gcloud config get-value project 2>/dev/null || echo "gen-lang-client-0707167243")

echo "🌐 Opening Google Cloud Console for API Enablement"
echo "═══════════════════════════════════════════════════════════"
echo ""
echo "Project: ${PROJECT_ID}"
echo ""
echo "Please enable these APIs in the Console:"
echo ""
echo "1. Cloud Run API"
echo "   https://console.cloud.google.com/apis/library/cloudrun.googleapis.com?project=${PROJECT_ID}"
echo ""
echo "2. Cloud Build API"
echo "   https://console.cloud.google.com/apis/library/cloudbuild.googleapis.com?project=${PROJECT_ID}"
echo ""
echo "3. Vertex AI API"
echo "   https://console.cloud.google.com/apis/library/aiplatform.googleapis.com?project=${PROJECT_ID}"
echo ""
echo "4. Artifact Registry API"
echo "   https://console.cloud.google.com/apis/library/artifactregistry.googleapis.com?project=${PROJECT_ID}"
echo ""

# Try to open browser (macOS)
if command -v open &> /dev/null; then
  read -p "Open Cloud Run API page in browser? (yes/no): " open_browser
  if [ "$open_browser" == "yes" ]; then
    open "https://console.cloud.google.com/apis/library/cloudrun.googleapis.com?project=${PROJECT_ID}"
    echo "✅ Browser opened!"
    echo ""
    echo "After enabling Cloud Run API, press Enter to open next API..."
    read
    
    open "https://console.cloud.google.com/apis/library/cloudbuild.googleapis.com?project=${PROJECT_ID}"
    echo "✅ Cloud Build API page opened"
    echo "After enabling, press Enter..."
    read
    
    open "https://console.cloud.google.com/apis/library/aiplatform.googleapis.com?project=${PROJECT_ID}"
    echo "✅ Vertex AI API page opened"
    echo "After enabling, press Enter..."
    read
    
    open "https://console.cloud.google.com/apis/library/artifactregistry.googleapis.com?project=${PROJECT_ID}"
    echo "✅ Artifact Registry API page opened"
  fi
fi

echo ""
echo "After enabling all APIs, verify with:"
echo "  gcloud services list --enabled --project ${PROJECT_ID} | grep -E 'cloudrun|cloudbuild|aiplatform|artifactregistry'"
echo ""
echo "Then run: ./setup-vertex-ai.sh"
echo ""
