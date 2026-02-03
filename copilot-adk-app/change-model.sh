#!/bin/bash
# Script to change the Gemini model

BACKEND_ENV="/Users/karthike/Desktop/Vibe Coding/Google-ADK-A2A-Explore/copilot-adk-app/backend/.env"

echo "🔧 Gemini Model Changer"
echo "======================="
echo ""
echo "Current model: $(grep GEMINI_MODEL "$BACKEND_ENV" | cut -d= -f2)"
echo ""
echo "Available models (for Google ADK):"
echo "  1) gemini-2.5-flash         (Newest, 1K RPM limit, RECOMMENDED) ⭐"
echo "  2) gemini-2.0-flash         (Fast, 2K RPM limit, very stable)"
echo "  3) gemini-1.5-pro           (High quality, stable)"
echo "  4) gemini-1.5-flash         (Fast, stable)"
echo ""
echo "Your current rate limits:"
echo "  - Gemini 2.5 Flash: 1,000 RPM"
echo "  - Gemini 2.0 Flash: 2,000 RPM"
echo ""
echo "Note: To use other providers (OpenAI, Anthropic, etc.):"
echo "      Install: pip install google-adk[extensions]"
echo "      Then use: openai/gpt-4, anthropic/claude-3-opus, etc."
echo ""
echo -n "Choose a model (1-4): "
read choice

case $choice in
  1)
    MODEL="gemini-2.5-flash"
    ;;
  2)
    MODEL="gemini-2.0-flash"
    ;;
  3)
    MODEL="gemini-1.5-pro"
    ;;
  4)
    MODEL="gemini-1.5-flash"
    ;;
  *)
    echo "Invalid choice"
    exit 1
    ;;
esac

echo ""
echo "Updating model to: $MODEL"

# Update or add GEMINI_MODEL in .env
if grep -q "GEMINI_MODEL=" "$BACKEND_ENV"; then
  # Update existing line
  sed -i '' "s/GEMINI_MODEL=.*/GEMINI_MODEL=$MODEL/" "$BACKEND_ENV"
else
  # Add new line
  echo "GEMINI_MODEL=$MODEL" >> "$BACKEND_ENV"
fi

echo "✅ Model updated!"
echo ""
echo "Next steps:"
echo "  1. Restart the backend server"
echo "  2. Test with: curl http://localhost:8000/health"
echo ""
echo "To restart backend:"
echo "  lsof -ti:8000 | xargs kill -9"
echo "  .venv/bin/python3 -m uvicorn main:app --app-dir backend --host 0.0.0.0 --port 8000"
