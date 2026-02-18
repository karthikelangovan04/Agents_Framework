# How to Change Google Account in gcloud CLI

## Quick Method (Recommended)

### Step 1: Add New Account

```bash
# Add a new Google account
gcloud auth login

# This will:
# 1. Open your browser
# 2. Ask you to sign in with the NEW Google account email
# 3. Grant permissions
```

### Step 2: Switch to New Account

```bash
# List all authenticated accounts
gcloud auth list

# Set the new account as active
gcloud config set account NEW_EMAIL@gmail.com

# Verify the switch
gcloud auth list
```

### Step 3: Set Application Default Credentials

```bash
# Set Application Default Credentials for the new account
gcloud auth application-default login

# This will open browser again - sign in with the NEW account
```

## Complete Account Switch Script

Run these commands in order:

```bash
# 1. Add new account (opens browser - sign in with NEW account)
gcloud auth login

# 2. List accounts to see both old and new
gcloud auth list

# 3. Set new account as active (replace with your new email)
gcloud config set account your-new-email@gmail.com

# 4. Set Application Default Credentials (opens browser - sign in with NEW account)
gcloud auth application-default login

# 5. Verify everything
gcloud auth list
gcloud config get-value account
```

## Remove Old Account (Optional)

If you want to remove the old account completely:

```bash
# List accounts
gcloud auth list

# Revoke old account
gcloud auth revoke old-email@gmail.com

# Verify it's removed
gcloud auth list
```

## Switch Project After Account Change

After changing accounts, you may need to set a different project:

```bash
# List projects for the new account
gcloud projects list

# Set the project you want to use
gcloud config set project YOUR_PROJECT_ID

# Verify
gcloud config get-value project
```

## Troubleshooting

### Issue: "Account not found" when switching

**Solution:**
```bash
# Make sure you've added the account first
gcloud auth login

# Then switch
gcloud config set account NEW_EMAIL@gmail.com
```

### Issue: Still using old account

**Solution:**
```bash
# Check current account
gcloud config get-value account

# Switch explicitly
gcloud config set account NEW_EMAIL@gmail.com

# Verify
gcloud auth list
```

### Issue: Application Default Credentials still using old account

**Solution:**
```bash
# Re-run application default login with new account
gcloud auth application-default login

# Make sure you sign in with the NEW account in the browser
```

## Step-by-Step Example

Here's a complete example:

```bash
# Current account: karthikelangovan04@gmail.com
# Want to switch to: newaccount@gmail.com

# Step 1: Add new account
gcloud auth login
# → Browser opens → Sign in with newaccount@gmail.com → Grant permissions

# Step 2: Verify both accounts are listed
gcloud auth list
# Output:
# ACTIVE  ACCOUNT
# *       karthikelangovan04@gmail.com
#         newaccount@gmail.com

# Step 3: Switch to new account
gcloud config set account newaccount@gmail.com

# Step 4: Verify switch
gcloud auth list
# Output:
# ACTIVE  ACCOUNT
#         karthikelangovan04@gmail.com
# *       newaccount@gmail.com

# Step 5: Set Application Default Credentials
gcloud auth application-default login
# → Browser opens → Sign in with newaccount@gmail.com → Grant permissions

# Step 6: Set project (if different)
gcloud projects list
gcloud config set project NEW_PROJECT_ID

# Step 7: Verify everything
gcloud auth list
gcloud config get-value account
gcloud config get-value project
```
