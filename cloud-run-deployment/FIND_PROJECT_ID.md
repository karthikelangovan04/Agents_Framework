# How to Find Your Google Cloud Project ID

## Method 1: Google Cloud Console (Web UI)

### Step-by-Step:

1. **Go to Google Cloud Console**
   - Open your browser and go to: https://console.cloud.google.com
   - Sign in with your Google account (email authentication required)

2. **Find Project ID**
   - Look at the top of the page - you'll see a project selector dropdown
   - Click on the project name/selector at the top
   - Your **Project ID** is shown in the list (it's usually different from the project name)
   - Example: Project Name might be "My Project" but Project ID is "my-project-123456"

3. **Copy the Project ID**
   - Click on your project to select it
   - The Project ID is displayed in the project selector
   - Copy it (it looks like: `my-project-123456`)

### Visual Guide:
```
Google Cloud Console
┌─────────────────────────────────────────┐
│ ☰  Google Cloud Platform  [Project ▼] │ ← Click here
│                                         │
│   Project Name: My Project              │
│   Project ID: my-project-123456         │ ← This is what you need
└─────────────────────────────────────────┘
```

## Method 2: Using gcloud CLI (After Authentication)

### If you're already authenticated:

```bash
# List all projects you have access to
gcloud projects list

# Get current project
gcloud config get-value project

# Set a project (if you know the ID)
gcloud config set project YOUR_PROJECT_ID
```

### Output Example:
```
PROJECT_ID          NAME              PROJECT_NUMBER
my-project-123456   My Project        123456789012
another-project     Another Project   987654321098
```

## Method 3: From Project Settings

1. Go to: https://console.cloud.google.com/iam-admin/settings
2. The **Project ID** is displayed at the top of the page

## Method 4: From Cloud Shell

1. Open Cloud Shell: https://shell.cloud.google.com
2. Run: `gcloud config get-value project`
3. Or run: `gcloud projects list`

## Authentication Process

### Yes, Email Authentication is Required

When you run `gcloud auth login`, here's what happens:

1. **Command**: `gcloud auth login`
2. **Browser Opens**: Automatically opens your default browser
3. **Google Sign-In Page**: You'll see Google's sign-in page
4. **Email Authentication**: You must sign in with your Google account email
5. **Permissions**: You'll be asked to grant permissions to gcloud CLI
6. **Authorization Code**: After signing in, you'll get an authorization code
7. **Return to Terminal**: The code is automatically captured (or you copy-paste it)
8. **Authenticated**: You're now authenticated!

### Step-by-Step Authentication:

```bash
# Step 1: Run this command
gcloud auth login

# Step 2: Browser opens automatically
# If browser doesn't open, copy the URL from terminal and paste in browser

# Step 3: Sign in with your Google account email
# Example: yourname@gmail.com or yourname@company.com

# Step 4: Grant permissions when prompted
# Click "Allow" to grant gcloud CLI access

# Step 5: Return to terminal
# You'll see: "You are now authenticated"

# Step 6: Verify authentication
gcloud auth list
```

### Expected Output After Authentication:

```
Credentialed Accounts
ACTIVE  ACCOUNT
*       yourname@gmail.com

To set the active account, run:
    $ gcloud config set account `ACCOUNT`
```

## Complete Setup Flow

### 1. First Time Setup:

```bash
# Step 1: Authenticate (requires email login)
gcloud auth login
# → Browser opens → Sign in with email → Grant permissions

# Step 2: Set Application Default Credentials
gcloud auth application-default login
# → Browser opens again → Sign in → Grant permissions

# Step 3: Find your project ID
gcloud projects list
# → Copy the PROJECT_ID from the output

# Step 4: Set your project
export GOOGLE_CLOUD_PROJECT="your-project-id-from-step-3"
gcloud config set project ${GOOGLE_CLOUD_PROJECT}

# Step 5: Verify
gcloud config get-value project
# → Should show your project ID
```

## Authentication Methods Explained

### 1. `gcloud auth login`
- **Purpose**: Authenticates gcloud CLI commands
- **Method**: Browser-based OAuth flow
- **Email Required**: Yes, your Google account email
- **When Needed**: First time setup, or when token expires

### 2. `gcloud auth application-default login`
- **Purpose**: Sets up Application Default Credentials (ADC)
- **Method**: Browser-based OAuth flow
- **Email Required**: Yes, same Google account
- **When Needed**: For applications using Google Cloud libraries (like Vertex AI)
- **Why Needed**: ADK agent needs this to authenticate to Vertex AI

### 3. Service Account (Alternative)
- **Purpose**: For automated/CI/CD scenarios
- **Method**: JSON key file
- **Email Required**: No (uses service account email)
- **When Needed**: Production deployments, CI/CD pipelines

## Troubleshooting

### Issue: Browser doesn't open automatically

**Solution:**
```bash
# Copy the URL from terminal output and paste in browser manually
gcloud auth login --no-launch-browser

# Or use the URL shown in terminal
```

### Issue: "Permission denied" errors

**Solution:**
```bash
# Check if you're authenticated
gcloud auth list

# Re-authenticate if needed
gcloud auth login

# Check if you have access to the project
gcloud projects list
```

### Issue: Wrong project selected

**Solution:**
```bash
# List all projects
gcloud projects list

# Set correct project
gcloud config set project CORRECT_PROJECT_ID

# Verify
gcloud config get-value project
```

### Issue: Multiple Google accounts

**Solution:**
```bash
# List all authenticated accounts
gcloud auth list

# Set active account
gcloud config set account your-email@gmail.com

# Verify
gcloud auth list
```

## Quick Reference

### Find Project ID:
```bash
# Method 1: Console (web)
https://console.cloud.google.com → Click project selector

# Method 2: CLI
gcloud projects list

# Method 3: Current project
gcloud config get-value project
```

### Authenticate:
```bash
# User authentication (requires email)
gcloud auth login

# Application Default Credentials (requires email)
gcloud auth application-default login

# Verify
gcloud auth list
```

### Set Project:
```bash
# Set project ID
export GOOGLE_CLOUD_PROJECT="your-project-id"
gcloud config set project ${GOOGLE_CLOUD_PROJECT}

# Verify
gcloud config get-value project
```

## Security Notes

1. **Email Authentication**: Required for security - Google needs to verify your identity
2. **OAuth Flow**: Uses secure OAuth 2.0 protocol
3. **Permissions**: You can revoke access anytime at: https://myaccount.google.com/permissions
4. **Service Accounts**: For production, consider using service accounts instead

## Next Steps After Finding Project ID

Once you have your Project ID:

```bash
# 1. Set environment variable
export GOOGLE_CLOUD_PROJECT="your-project-id-here"
export GOOGLE_CLOUD_REGION="us-central1"

# 2. Authenticate (if not done)
gcloud auth login
gcloud auth application-default login

# 3. Set project
gcloud config set project ${GOOGLE_CLOUD_PROJECT}

# 4. Run setup
cd "/Users/karthike/Desktop/Vibe Coding/Google-ADK-A2A-Explore/cloud-run-deployment/scripts"
./setup-vertex-ai.sh
```
