#!/bin/bash
# Security check script - Run before committing to GitHub

set -e

REPO_DIR="/Users/karthike/Desktop/Vibe Coding/Google-ADK-A2A-Explore/copilot-adk-app"
cd "$REPO_DIR"

echo "🔒 Security Check - GitHub Commit Safety"
echo "========================================"
echo ""

# Check 1: Verify .env files are gitignored
echo "1️⃣ Checking .env files are gitignored..."
if git check-ignore backend/.env frontend/.env.local > /dev/null 2>&1; then
    echo "   ✅ .env files are properly gitignored"
else
    echo "   ❌ ERROR: .env files are NOT gitignored!"
    echo "   Run: echo '.env' >> .gitignore"
    exit 1
fi

# Check 2: Search for potential API keys in tracked files
echo ""
echo "2️⃣ Scanning for potential secrets in code..."
SECRETS_FOUND=0

# Search for Google API key pattern
if git ls-files | xargs grep -l "AIzaSy" 2>/dev/null; then
    echo "   ❌ WARNING: Google API key pattern found!"
    SECRETS_FOUND=1
fi

# Search for OpenAI key pattern
if git ls-files | xargs grep -l "sk-[a-zA-Z0-9]\{32\}" 2>/dev/null; then
    echo "   ❌ WARNING: OpenAI API key pattern found!"
    SECRETS_FOUND=1
fi

# Search for hardcoded secrets (excluding env variable references)
if git ls-files | xargs grep -i "api_key\s*=\s*['\"][a-zA-Z0-9]" 2>/dev/null | grep -v "os.getenv" | grep -v ".example"; then
    echo "   ❌ WARNING: Hardcoded API key found!"
    SECRETS_FOUND=1
fi

if [ $SECRETS_FOUND -eq 0 ]; then
    echo "   ✅ No API keys or secrets found in tracked files"
fi

# Check 3: Verify example files exist
echo ""
echo "3️⃣ Checking example environment files..."
if [ -f "backend/env.example" ]; then
    echo "   ✅ backend/env.example exists"
else
    echo "   ⚠️  backend/env.example missing (recommended)"
fi

if [ -f "frontend/env.example" ]; then
    echo "   ✅ frontend/env.example exists"
else
    echo "   ⚠️  frontend/env.example missing (recommended)"
fi

# Check 4: Show what would be committed
echo ""
echo "4️⃣ Files that would be committed:"
git status --short | head -20
if [ $(git status --short | wc -l) -gt 20 ]; then
    echo "   ... ($(git status --short | wc -l) files total)"
fi

# Check 5: Verify critical files are gitignored
echo ""
echo "5️⃣ Verifying sensitive directories are ignored..."
IGNORE_CHECK=0

if git check-ignore .venv > /dev/null 2>&1; then
    echo "   ✅ .venv/ is gitignored"
else
    echo "   ⚠️  .venv/ is not gitignored (should be)"
    IGNORE_CHECK=1
fi

if git check-ignore frontend/node_modules > /dev/null 2>&1; then
    echo "   ✅ node_modules/ is gitignored"
else
    echo "   ⚠️  node_modules/ is not gitignored (should be)"
    IGNORE_CHECK=1
fi

# Final summary
echo ""
echo "========================================"
if [ $SECRETS_FOUND -eq 0 ] && [ $IGNORE_CHECK -eq 0 ]; then
    echo "✅ SAFE TO COMMIT"
    echo ""
    echo "You can now run:"
    echo "  git add ."
    echo "  git commit -m \"Your commit message\""
    echo "  git push"
    exit 0
else
    echo "⚠️  WARNINGS FOUND"
    echo ""
    echo "Please review the warnings above before committing."
    echo "If everything looks good, you can proceed with:"
    echo "  git add ."
    echo "  git commit -m \"Your commit message\""
    exit 1
fi
