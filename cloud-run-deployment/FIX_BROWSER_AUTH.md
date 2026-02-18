# Fix Browser Authentication Issues with Multiple Google Accounts

## Problem
Multiple Google accounts logged into browser causing authentication conflicts when accessing Google Cloud Console.

## Solutions

### Solution 1: Use Incognito/Private Browser Window (Recommended)

1. **Open Incognito/Private Window**
   - Chrome: `Cmd+Shift+N` (Mac) or `Ctrl+Shift+N` (Windows)
   - Safari: `Cmd+Shift+N` (Mac)
   - Firefox: `Cmd+Shift+P` (Mac) or `Ctrl+Shift+P` (Windows)

2. **Sign in with ONLY the account you need**
   - Go to: https://accounts.google.com
   - Sign in with: `karthikelangovanpadma04@gmail.com`
   - **Don't sign in with other accounts**

3. **Open Google Cloud Console**
   - Go to: https://console.cloud.google.com
   - Select project: `gen-lang-client-0707167243`

4. **Enable APIs**
   - Cloud Run: https://console.cloud.google.com/apis/library/cloudrun.googleapis.com?project=gen-lang-client-0707167243
   - Cloud Build: https://console.cloud.google.com/apis/library/cloudbuild.googleapis.com?project=gen-lang-client-0707167243
   - Vertex AI: https://console.cloud.google.com/apis/library/aiplatform.googleapis.com?project=gen-lang-client-0707167243
   - Artifact Registry: https://console.cloud.google.com/apis/library/artifactregistry.googleapis.com?project=gen-lang-client-0707167243

### Solution 2: Force Specific Account in URL

Add `authuser=0` to force the first account, or use the account index:

```bash
# For first account (authuser=0)
https://console.cloud.google.com/apis/library/cloudrun.googleapis.com?authuser=0&project=gen-lang-client-0707167243

# For second account (authuser=1)
https://console.cloud.google.com/apis/library/cloudrun.googleapis.com?authuser=1&project=gen-lang-client-0707167243
```

**To find which account index to use:**
1. Go to: https://myaccount.google.com
2. Check the account order
3. Use the index (0, 1, 2, etc.) for the account you want

### Solution 3: Sign Out Other Accounts Temporarily

1. Go to: https://myaccount.google.com
2. Click on your profile picture (top right)
3. Click "Sign out" for accounts you don't need
4. Keep only `karthikelangovanpadma04@gmail.com` signed in
5. Try accessing Console again

### Solution 4: Use Browser Profile/User

Create a separate browser profile for Google Cloud:

**Chrome:**
1. Click profile icon → "Add"
2. Create new profile named "Google Cloud"
3. Sign in with only `karthikelangovanpadma04@gmail.com`
4. Use this profile for Google Cloud Console

**Firefox:**
1. Use Firefox Multi-Account Containers extension
2. Create container for Google Cloud
3. Sign in with only the needed account in that container

### Solution 5: Check if APIs Are Already Enabled

Sometimes APIs are already enabled but CLI shows errors. Check:

```bash
# Check enabled APIs
gcloud services list --enabled --project gen-lang-client-0707167243

# Filter for our APIs
gcloud services list --enabled --project gen-lang-client-0707167243 | grep -E "cloudrun|cloudbuild|aiplatform|artifactregistry"
```

If APIs are already enabled, you can skip this step and continue with deployment!

### Solution 6: Use CLI Workaround Script

Try the CLI workaround script:

```bash
cd "/Users/karthike/Desktop/Vibe Coding/Google-ADK-A2A-Explore/cloud-run-deployment/scripts"
./enable-apis-cli-workaround.sh
```

## Quick Fix Commands

### Check Current Account
```bash
gcloud config get-value account
```

### Verify APIs Status
```bash
PROJECT_ID="gen-lang-client-0707167243"
gcloud services list --enabled --project ${PROJECT_ID} | grep -E "cloudrun|cloudbuild|aiplatform|artifactregistry"
```

### If APIs Are Already Enabled
If the APIs show as enabled, you can proceed with deployment even if the enable command failed:

```bash
export GOOGLE_CLOUD_PROJECT="gen-lang-client-0707167243"
export GOOGLE_CLOUD_REGION="us-central1"
cd "/Users/karthike/Desktop/Vibe Coding/Google-ADK-A2A-Explore/cloud-run-deployment/scripts"
./setup-vertex-ai.sh
```

## Recommended Approach

**Best solution:** Use Incognito window with only one account:

1. Open incognito window
2. Sign in with `karthikelangovanpadma04@gmail.com` only
3. Enable APIs in Console
4. Verify with CLI: `gcloud services list --enabled --project gen-lang-client-0707167243`
5. Continue with setup script

This avoids all browser account conflicts!
