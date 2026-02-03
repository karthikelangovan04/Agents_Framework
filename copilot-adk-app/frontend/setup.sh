#!/bin/bash
# Frontend setup script
# This script automates the installation and verification of frontend dependencies

set -e  # Exit on error

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "🚀 Frontend Setup Script"
echo "========================"
echo ""

# Step 1: Clean old dependencies
echo "🧹 Step 1/3: Cleaning old dependencies..."
if [ -d "node_modules" ]; then
    echo "  Removing node_modules..."
    rm -rf node_modules
fi
if [ -f "package-lock.json" ]; then
    echo "  Removing package-lock.json..."
    rm -f package-lock.json
fi
echo "  ✓ Cleanup complete"
echo ""

# Step 2: Install dependencies
echo "📦 Step 2/3: Installing npm packages..."
echo "  This may take 2-3 minutes..."
npm install
echo "  ✓ Installation complete"
echo ""

# Step 3: Verify installation
echo "🔍 Step 3/3: Verifying installation..."
if [ -d "node_modules/@ag-ui/client" ]; then
    AG_UI_VERSION=$(node -p "require('./node_modules/@ag-ui/client/package.json').version" 2>/dev/null || echo "unknown")
    echo "  ✓ @ag-ui/client installed (v$AG_UI_VERSION)"
else
    echo "  ✗ @ag-ui/client not found"
    exit 1
fi

if [ -d "node_modules/@copilotkit/runtime" ]; then
    COPILOT_VERSION=$(node -p "require('./node_modules/@copilotkit/runtime/package.json').version" 2>/dev/null || echo "unknown")
    echo "  ✓ @copilotkit/runtime installed (v$COPILOT_VERSION)"
else
    echo "  ✗ @copilotkit/runtime not found"
    exit 1
fi

if [ -d "node_modules/next" ]; then
    NEXT_VERSION=$(node -p "require('./node_modules/next/package.json').version" 2>/dev/null || echo "unknown")
    echo "  ✓ Next.js installed (v$NEXT_VERSION)"
else
    echo "  ✗ Next.js not found"
    exit 1
fi

echo ""
echo "✅ Frontend setup complete!"
echo ""
echo "Next steps:"
echo "  • Test build:  npm run build"
echo "  • Start dev:   npm run dev"
echo "  • Open app:    http://localhost:3000"
echo ""
