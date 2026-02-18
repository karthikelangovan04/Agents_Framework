#!/bin/bash
# Script to switch Google Cloud account

echo "🔄 Google Cloud Account Switcher"
echo "═══════════════════════════════════════════════════════════"
echo ""

# Show current account
CURRENT_ACCOUNT=$(gcloud config get-value account 2>/dev/null || echo "")
if [ -n "$CURRENT_ACCOUNT" ]; then
  echo "Current Account: ${CURRENT_ACCOUNT}"
else
  echo "No account currently set"
fi
echo ""

# Show all authenticated accounts
echo "📋 All Authenticated Accounts:"
echo "───────────────────────────────────────────────────────────"
gcloud auth list
echo ""

# Ask what user wants to do
echo "What would you like to do?"
echo "  1) Add a new account"
echo "  2) Switch to existing account"
echo "  3) Remove an account"
echo "  4) Exit"
echo ""
read -p "Enter choice (1-4): " choice

case $choice in
  1)
    echo ""
    echo "Adding new account..."
    echo "A browser will open - please sign in with the NEW account"
    gcloud auth login
    
    echo ""
    echo "Setting Application Default Credentials..."
    echo "Browser will open again - sign in with the NEW account"
    gcloud auth application-default login
    
    echo ""
    echo "✅ New account added!"
    echo ""
    echo "📋 Updated account list:"
    gcloud auth list
    echo ""
    read -p "Do you want to switch to this new account? (yes/no): " switch_now
    if [ "$switch_now" == "yes" ]; then
      NEW_ACCOUNT=$(gcloud auth list --filter=status:ACTIVE --format="value(account)" | tail -1)
      if [ -n "$NEW_ACCOUNT" ]; then
        gcloud config set account "${NEW_ACCOUNT}"
        echo "✅ Switched to: ${NEW_ACCOUNT}"
      fi
    fi
    ;;
    
  2)
    echo ""
    echo "📋 Available Accounts:"
    ACCOUNTS=$(gcloud auth list --format="value(account)")
    if [ -z "$ACCOUNTS" ]; then
      echo "❌ No accounts found. Please add an account first (option 1)."
      exit 1
    fi
    
    # Show accounts with numbers
    COUNT=1
    echo "$ACCOUNTS" | while read account; do
      echo "  ${COUNT}) ${account}"
      COUNT=$((COUNT + 1))
    done
    
    echo ""
    read -p "Enter account email to switch to: " SWITCH_ACCOUNT
    
    if [ -z "$SWITCH_ACCOUNT" ]; then
      echo "❌ Account email cannot be empty"
      exit 1
    fi
    
    # Verify account exists
    if echo "$ACCOUNTS" | grep -q "^${SWITCH_ACCOUNT}$"; then
      gcloud config set account "${SWITCH_ACCOUNT}"
      echo "✅ Switched to: ${SWITCH_ACCOUNT}"
      
      echo ""
      read -p "Update Application Default Credentials for this account? (yes/no): " update_adc
      if [ "$update_adc" == "yes" ]; then
        gcloud auth application-default login
        echo "✅ Application Default Credentials updated"
      fi
    else
      echo "❌ Account '${SWITCH_ACCOUNT}' not found in authenticated accounts"
      echo "   Available accounts:"
      echo "$ACCOUNTS"
      exit 1
    fi
    ;;
    
  3)
    echo ""
    echo "📋 Accounts to Remove:"
    ACCOUNTS=$(gcloud auth list --format="value(account)")
    if [ -z "$ACCOUNTS" ]; then
      echo "❌ No accounts found"
      exit 1
    fi
    
    COUNT=1
    echo "$ACCOUNTS" | while read account; do
      echo "  ${COUNT}) ${account}"
      COUNT=$((COUNT + 1))
    done
    
    echo ""
    read -p "Enter account email to remove: " REMOVE_ACCOUNT
    
    if [ -z "$REMOVE_ACCOUNT" ]; then
      echo "❌ Account email cannot be empty"
      exit 1
    fi
    
    # Check if it's the current account
    CURRENT=$(gcloud config get-value account 2>/dev/null || echo "")
    if [ "$REMOVE_ACCOUNT" == "$CURRENT" ]; then
      echo "⚠️  This is the current active account."
      read -p "Are you sure you want to remove it? (yes/no): " confirm
      if [ "$confirm" != "yes" ]; then
        echo "Cancelled."
        exit 0
      fi
    fi
    
    gcloud auth revoke "${REMOVE_ACCOUNT}"
    echo "✅ Removed account: ${REMOVE_ACCOUNT}"
    ;;
    
  4)
    echo "Exiting..."
    exit 0
    ;;
    
  *)
    echo "❌ Invalid choice"
    exit 1
    ;;
esac

# Final status
echo ""
echo "═══════════════════════════════════════════════════════════"
echo "✅ Account Management Complete"
echo "═══════════════════════════════════════════════════════════"
echo ""
echo "Current Status:"
echo "  Active Account: $(gcloud config get-value account 2>/dev/null || echo 'None')"
echo "  Current Project: $(gcloud config get-value project 2>/dev/null || echo 'None')"
echo ""
echo "Next Steps:"
echo "  1. Set your project: gcloud config set project YOUR_PROJECT_ID"
echo "  2. List projects: gcloud projects list"
echo "  3. Run setup: ./setup-vertex-ai.sh"
echo ""
