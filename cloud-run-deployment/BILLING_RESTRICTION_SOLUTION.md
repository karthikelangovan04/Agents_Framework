# Solution for Billing Account Restrictions

## Issue
Your billing account (`billingAccounts/016611-0A8F44-568A02`) appears to be restricted - possibly a "Gen AI only" account that only allows AI-related services.

## Confirmation
- ✅ Vertex AI API is enabled (AI service)
- ❌ Cloud Run API cannot be enabled (infrastructure service)
- ❌ Cloud Build API cannot be enabled (infrastructure service)
- ❌ Artifact Registry API cannot be enabled (infrastructure service)

## Solutions

### Solution 1: Create New Project with Different Billing (Recommended)

Create a new project that can use a different billing account or has full access:

```bash
# Create new project
NEW_PROJECT="adk-deployment-$(date +%s)"
gcloud projects create ${NEW_PROJECT} --name="ADK Deployment Project"

# Set as current project
gcloud config set project ${NEW_PROJECT}
export GOOGLE_CLOUD_PROJECT=${NEW_PROJECT}
export GOOGLE_CLOUD_REGION="us-central1"

# Link billing (you'll need a billing account with full access)
# Option A: Use Console
# Go to: https://console.cloud.google.com/billing?project=${NEW_PROJECT}
# Link a billing account with full access

# Option B: If you have another billing account ID
# gcloud billing projects link ${NEW_PROJECT} --billing-account=BILLING_ACCOUNT_ID

# Then enable APIs
gcloud services enable cloudrun.googleapis.com --project ${NEW_PROJECT}
gcloud services enable cloudbuild.googleapis.com --project ${NEW_PROJECT}
gcloud services enable aiplatform.googleapis.com --project ${NEW_PROJECT}
gcloud services enable artifactregistry.googleapis.com --project ${NEW_PROJECT}

# Continue with setup
cd "/Users/karthike/Desktop/Vibe Coding/Google-ADK-A2A-Explore/cloud-run-deployment/scripts"
./setup-vertex-ai.sh
```

### Solution 2: Use Existing Project with Full Access

If you have access to `graphite-hook-480801-d6` (My First Project), try that:

```bash
# Switch to other project
gcloud config set project graphite-hook-480801-d6
export GOOGLE_CLOUD_PROJECT="graphite-hook-480801-d6"
export GOOGLE_CLOUD_REGION="us-central1"

# Check billing
gcloud billing projects describe graphite-hook-480801-d6

# If billing is linked, try enabling APIs
gcloud services enable cloudrun.googleapis.com --project graphite-hook-480801-d6
gcloud services enable cloudbuild.googleapis.com --project graphite-hook-480801-d6
gcloud services enable aiplatform.googleapis.com --project graphite-hook-480801-d6
gcloud services enable artifactregistry.googleapis.com --project graphite-hook-480801-d6

# If successful, continue with setup
cd "/Users/karthike/Desktop/Vibe Coding/Google-ADK-A2A-Explore/cloud-run-deployment/scripts"
./setup-vertex-ai.sh
```

### Solution 3: Request Billing Account Access

If you need to use `gen-lang-client-0707167243`:

1. **Contact billing account administrator** to:
   - Enable Cloud Run, Cloud Build, and Artifact Registry APIs
   - Or grant you access to a billing account with full access

2. **Check billing account type**:
   - Go to: https://console.cloud.google.com/billing
   - Check if account has restrictions
   - Some trial/credit accounts are limited to specific services

### Solution 4: Use Google Cloud Free Trial

If you don't have a billing account with full access:

1. **Sign up for Google Cloud Free Trial**:
   - Go to: https://cloud.google.com/free
   - This gives you $300 credit and full API access

2. **Create new project** with trial billing:
   ```bash
   gcloud projects create my-adk-trial-project
   gcloud config set project my-adk-trial-project
   # Link trial billing account via Console
   ```

## Quick Decision Guide

**If you have another billing account:**
→ Use Solution 1 (Create new project)

**If `graphite-hook-480801-d6` has different billing:**
→ Use Solution 2 (Switch to that project)

**If you need to use current project:**
→ Use Solution 3 (Request access)

**If starting fresh:**
→ Use Solution 4 (Free trial)

## Verify Billing Account Type

Check what services your billing account supports:

```bash
# Check billing account
BILLING_ID="016611-0A8F44-568A02"
echo "Billing Account: ${BILLING_ID}"

# Note: Some billing accounts are restricted to:
# - AI/ML services only (Vertex AI, etc.)
# - Specific service categories
# - Trial accounts with limitations
```

## Next Steps

1. **Decide which solution works for you**
2. **Create/switch to appropriate project**
3. **Enable APIs**
4. **Run setup script**: `./setup-vertex-ai.sh`

The key is using a billing account that supports infrastructure services (Cloud Run, Cloud Build), not just AI services.
