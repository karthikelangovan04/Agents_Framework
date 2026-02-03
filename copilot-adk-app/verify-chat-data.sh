#!/bin/bash

# Verify Chat Data Script
# Fetches latest chat data from all tables to verify user ID linking

echo "=================================================="
echo "🔍 COPILOT ADK APP - DATABASE VERIFICATION"
echo "=================================================="
echo ""

DB_HOST="localhost"
DB_PORT="5433"
DB_NAME="copilot_adk_db"
DB_USER="adk_user"

echo "📊 1. USERS TABLE"
echo "--------------------------------------------------"
PGPASSWORD=adk_password psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -c "
SELECT id, username, created_at 
FROM users 
ORDER BY created_at DESC 
LIMIT 5;
" 2>/dev/null

echo ""
echo "📊 2. SESSIONS TABLE (Latest 5)"
echo "--------------------------------------------------"
PGPASSWORD=adk_password psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -c "
SELECT 
  app_name,
  user_id,
  id,
  create_time,
  CASE 
    WHEN user_id ~ '^[0-9]+$' THEN '✅ Numeric User ID'
    WHEN user_id LIKE 'thread_user_%' THEN '❌ Thread User (AG-UI Generated)'
    ELSE '⚠️ Unknown Format'
  END as status
FROM sessions 
WHERE app_name = 'copilot_adk_app'
ORDER BY create_time DESC 
LIMIT 5;
" 2>/dev/null

echo ""
echo "📊 3. USER_STATES TABLE"
echo "--------------------------------------------------"
PGPASSWORD=adk_password psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -c "
SELECT 
  app_name,
  user_id,
  update_time,
  CASE 
    WHEN user_id ~ '^[0-9]+$' THEN '✅ Numeric User ID'
    WHEN user_id LIKE 'thread_user_%' THEN '❌ Thread User (AG-UI Generated)'
    ELSE '⚠️ Unknown Format'
  END as status
FROM user_states 
WHERE app_name = 'copilot_adk_app'
ORDER BY update_time DESC;
" 2>/dev/null

echo ""
echo "📊 4. EVENTS TABLE (Latest 5)"
echo "--------------------------------------------------"
PGPASSWORD=adk_password psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -c "
SELECT 
  app_name,
  user_id,
  session_id,
  timestamp,
  CASE 
    WHEN user_id ~ '^[0-9]+$' THEN '✅ Numeric User ID'
    WHEN user_id LIKE 'thread_user_%' THEN '❌ Thread User (AG-UI Generated)'
    ELSE '⚠️ Unknown Format'
  END as status
FROM events 
WHERE app_name = 'copilot_adk_app'
ORDER BY timestamp DESC 
LIMIT 5;
" 2>/dev/null

echo ""
echo "=================================================="
echo "📈 SUMMARY"
echo "=================================================="

# Count sessions by user type
PGPASSWORD=adk_password psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -c "
SELECT 
  CASE 
    WHEN user_id ~ '^[0-9]+$' THEN 'Authenticated Users (✅)'
    WHEN user_id LIKE 'thread_user_%' THEN 'Thread Users (❌ AG-UI Generated)'
    ELSE 'Unknown Format'
  END as user_type,
  COUNT(*) as session_count
FROM sessions 
WHERE app_name = 'copilot_adk_app'
GROUP BY user_type
ORDER BY session_count DESC;
" 2>/dev/null

echo ""
echo "=================================================="
echo "🔍 EXPECTED vs ACTUAL"
echo "=================================================="
echo ""
echo "✅ EXPECTED: user_id should be '3' (for karthikelangovan04)"
echo "❌ ACTUAL:   If you see 'thread_user_xxx', cookies aren't set"
echo ""
echo "To fix:"
echo "1. Hard refresh browser: Cmd+Shift+R (Mac) or Ctrl+Shift+R (Windows)"
echo "2. Check cookies in DevTools → Application → Cookies"
echo "   - copilot_adk_user_id should be '3'"
echo "   - copilot_adk_session_id should be a UUID"
echo ""
echo "=================================================="
