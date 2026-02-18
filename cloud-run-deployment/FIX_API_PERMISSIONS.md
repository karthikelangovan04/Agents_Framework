# Fix API Permission Denied Error

## Issue
You're getting `PERMISSION_DENIED` when trying to enable APIs, even though you have `roles/owner`.

## Common Causes

### 1. Billing Not Enabled (Most Common)

APIs require billing to be enabled. Check and fix:

```bash
# Check billing status
gcloud billing projects describe gen-lang-client-0707167243

# If no billing account, you need to:
# Option A: Enable via Console
# Go to: https://console.cloud.google.com/billing
# Link a billing account to your project

# Option B: Enable via CLI (if you have billing account ID)
gcloud billing projects link gen-lang-client-0707167243 \
  --billing-account=YOUR_BILLING_ACCOUNT_ID
```

### 2. Project Organization Restrictions

If the project is in an organization, there might be organization policies blocking API enablement.

**Solution:** Check organization policies or use a project outside the organization.

### 3. Try Enabling APIs One by One

Sometimes enabling all APIs at once fails. Try individually:

```bash
PROJECT_ID="gen-lang-client-0707167243"

# Enable APIs one by one
gcloud services enable cloudrun.googleapis.com --project ${PROJECT_ID}
gcloud services enable cloudbuild.googleapis.com --project ${PROJECT_ID}
gcloud services enable aiplatform.googleapis.com --project ${PROJECT_ID}
gcloud services enable artifactregistry.googleapis.com --project ${PROJECT_ID}
```

### 4. Enable via Google Cloud Console

Sometimes the Console works when CLI doesn't:

1. Go to: https://console.cloud.google.com/apis/library
2. Search for each API:
   - Cloud Run API
   - Cloud Build API
   - Vertex AI API
   - Artifact Registry API
3. Click "Enable" for each

### 5. Check Project Status

```bash
# Check if project is active
gcloud projects describe gen-lang-client-0707167243

# Check project number
gcloud projects describe gen-lang-client-0707167243 --format="value(projectNumber)"
```

## Quick Fix Script

Run this to check everything:

```bash
cd "/Users/karthike/Desktop/Vibe Coding/Google-ADK-A2A-Explore/cloud-run-deployment/scripts"
./check-permissions.sh
```

## Manual Steps

### Step 1: Verify Billing

```bash
# Check billing
gcloud billing projects describe gen-lang-client-0707167243

# If empty, enable billing via Console:
# https://console.cloud.google.com/billing
```

### Step 2: Enable APIs via Console (Recommended)

1. Go to: https://console.cloud.google.com/apis/library/cloudrun.googleapis.com?project=gen-lang-client-0707167243
2. Click "Enable"
3. Repeat for:
   - Cloud Build: https://console.cloud.google.com/apis/library/cloudbuild.googleapis.com
   - Vertex AI: https://console.cloud.google.com/apis/library/aiplatform.googleapis.com
   - Artifact Registry: https://console.cloud.google.com/apis/library/artifactregistry.googleapis.com

### Step 3: Verify APIs Enabled

```bash
gcloud services list --enabled --project gen-lang-client-0707167243 | grep -E "cloudrun|cloudbuild|aiplatform|artifactregistry"
```

### Step 4: Continue Setup

Once APIs are enabled, continue with:

```bash
export GOOGLE_CLOUD_PROJECT="gen-lang-client-0707167243"
export GOOGLE_CLOUD_REGION="us-central1"
./setup-vertex-ai.sh
```

## Alternative: Use Different Project

If you continue having issues, create a new project:

```bash
# Create new project
gcloud projects create my-adk-project-$(date +%s) \
  --name="ADK Deployment Project"

# Set as current project
gcloud config set project my-adk-project-XXXXX

# Enable billing (via Console)
# Then enable APIs
```

## Still Having Issues?

1. **Check Organization Policies**: If project is in an org, policies might block API enablement
2. **Try Console**: Sometimes Console works when CLI doesn't
3. **Wait a few minutes**: API enablement can take time to propagate
4. **Check Service Account**: Make sure you're using the right account
