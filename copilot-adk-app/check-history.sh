#!/bin/bash

# Check history for user 4
echo "=== CHECKING SESSION HISTORY FOR USER 4 ==="
echo ""

cd "/Users/karthike/Desktop/Vibe Coding/Google-ADK-A2A-Explore/copilot-adk-app"

# Load environment
if [ -f backend/.env ]; then
  export $(grep -v '^#' backend/.env | xargs)
fi

echo "1. Recent sessions for user 4:"
psql "$DATABASE_URL" -t -c "
SELECT 
  id, 
  state->>'_ag_ui_thread_id' as thread_id,
  update_time
FROM sessions 
WHERE user_id = '4' 
ORDER BY update_time DESC 
LIMIT 5;
"

echo ""
echo "2. Events per session (user 4):"
psql "$DATABASE_URL" -t -c "
SELECT 
  session_id, 
  COUNT(*) as events,
  MAX(timestamp) as last_event
FROM events 
WHERE user_id = '4' 
GROUP BY session_id 
ORDER BY last_event DESC 
LIMIT 5;
"

echo ""
echo "3. Sample event data (latest session):"
psql "$DATABASE_URL" -t -c "
SELECT 
  e.session_id,
  e.event_type,
  LEFT(e.event_data::text, 100) as data_preview
FROM events e
WHERE e.user_id = '4'
ORDER BY e.timestamp DESC
LIMIT 5;
"

echo ""
echo "=== TEST /agents/state ENDPOINT ==="
echo ""

# Get the latest session ID
SESSION_ID=$(psql "$DATABASE_URL" -t -c "SELECT id FROM sessions WHERE user_id = '4' ORDER BY update_time DESC LIMIT 1;" | xargs)

echo "Testing session: $SESSION_ID"
echo ""

curl -s -X POST http://localhost:8000/agents/state \
  -H "Content-Type: application/json" \
  -d "{
    \"threadId\": \"$SESSION_ID\",
    \"appName\": \"copilot_adk_app\",
    \"userId\": \"4\"
  }" | jq '.'

echo ""
echo "=== DONE ==="
