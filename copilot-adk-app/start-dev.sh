#!/bin/bash
# Development startup script
# Starts both backend and frontend servers

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "🚀 CopilotKit + ADK Development Startup"
echo "======================================="
echo ""

# Check if .env files exist
if [ ! -f "backend/.env" ]; then
    echo "❌ Error: backend/.env not found"
    echo "   Create it with: cp backend/env.example backend/.env"
    exit 1
fi

if [ ! -f "frontend/.env.local" ]; then
    echo "⚠️  Warning: frontend/.env.local not found (optional)"
    echo "   You can create it with: cp frontend/env.example frontend/.env.local"
fi

# Check if venv exists
if [ ! -d ".venv" ]; then
    echo "❌ Error: .venv not found"
    echo "   Create it with: uv venv && uv pip install -r backend/requirements.txt"
    exit 1
fi

# Check if frontend node_modules exists
if [ ! -d "frontend/node_modules" ]; then
    echo "❌ Error: frontend/node_modules not found"
    echo "   Run: cd frontend && ./setup.sh"
    exit 1
fi

echo "✅ Prerequisites check passed"
echo ""

# Function to cleanup on exit
cleanup() {
    echo ""
    echo "🛑 Shutting down servers..."
    kill $BACKEND_PID 2>/dev/null || true
    kill $FRONTEND_PID 2>/dev/null || true
    exit 0
}

trap cleanup INT TERM

# Start backend
echo "📡 Starting backend server (port 8000)..."
.venv/bin/python3 -m uvicorn main:app --app-dir backend --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!

# Wait for backend to be ready
echo "   Waiting for backend to start..."
for i in {1..30}; do
    if curl -s http://localhost:8000/health > /dev/null 2>&1; then
        echo "   ✓ Backend ready!"
        break
    fi
    sleep 1
    if [ $i -eq 30 ]; then
        echo "   ❌ Backend failed to start"
        kill $BACKEND_PID 2>/dev/null || true
        exit 1
    fi
done

echo ""

# Start frontend
echo "🎨 Starting frontend server (port 3000)..."
cd frontend
npm run dev &
FRONTEND_PID=$!
cd ..

echo ""
echo "✅ Both servers started!"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🌐 Backend:  http://localhost:8000"
echo "🎨 Frontend: http://localhost:3000"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "📊 Backend logs:  Backend PID $BACKEND_PID"
echo "📊 Frontend logs: Frontend PID $FRONTEND_PID"
echo ""
echo "Press Ctrl+C to stop both servers"
echo ""

# Wait for user interrupt
wait
