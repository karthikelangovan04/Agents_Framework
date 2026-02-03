# Thread ID vs Session ID Fix

## Problem
Session history wasn't loading because:
1. **Session ID** (database UUID): `b7e82bc3-5e4f-43e2-89a8-bb240cc41c63`
2. **Thread ID** (AG-UI protocol): `9b3ec552-c67c-41c...` (different!)

The `/agents/state` endpoint searches by `thread_id`, but we were passing `session_id`.

## Root Cause
CopilotKit was generating its own `thread_id` instead of using our `session_id`.

## Solution
Configure CopilotKit to use our session ID as the thread ID:

```tsx
<CopilotKit 
  key={currentSessionId}
  threadId={currentSessionId || undefined}  // ← Forces threadId = sessionId
  runtimeUrl="/api/copilotkit" 
  agent="my_agent"
>
```

## Impact

### ✅ NEW Sessions (created after fix):
- `thread_id` == `session_id` 
- History loads correctly
- Session switching works

### ⚠️ OLD Sessions (created before fix):
- `thread_id` != `session_id`
- History won't load (shows "No previous messages")
- Can still chat, but won't see previous messages in UI
- Messages are still in database, just not displayed

## Testing

1. **Create a new session** (after this fix)
2. **Send some messages** (e.g., "Tell me a joke")
3. **Create another new session** 
4. **Send different messages** (e.g., "What's 2+2?")
5. **Switch back to first session**
6. ✅ Should see the joke conversation loaded

## Migration for Old Sessions

Old sessions will continue to work but won't show history. Options:

### Option 1: Create Fresh Sessions (Recommended)
Just create new chat sessions. The old ones will still exist in the database.

### Option 2: Keep Using Old Sessions
Old sessions work fine for new messages, they just won't display history from before the fix.

### Option 3: Database Migration (Advanced)
```sql
-- Update existing sessions to sync thread_id with session_id
UPDATE sessions 
SET state = jsonb_set(
  state, 
  '{_ag_ui_thread_id}', 
  to_jsonb(id::text)
)
WHERE app_name = 'copilot_adk_app';
```

**Warning**: Only run this if you understand the implications!

## Files Changed

1. **frontend/app/chat/page.tsx**
   - Added `threadId={currentSessionId}` to CopilotKit

2. **frontend/lib/api.ts**
   - Enhanced error handling in `getSessionHistory()`
   - Better logging for missing threads

## Verification

Check browser console when switching to a NEW session:
```
🍪 SET SESSION COOKIE: copilot_adk_session_id=abc123...
📚 Loading history for session: abc123...
✅ Loaded 3 messages from session
```

Or for new/empty sessions:
```
Session abc123... has no messages yet (new session)
📝 New session - no previous history
```

## Expected Behavior (After Fix)

1. ✅ Create new session → Send messages
2. ✅ Create another session → Send different messages  
3. ✅ Switch back → See previous messages
4. ✅ Continue conversation → Context maintained
5. ✅ Refresh page → History persists

---

**Status**: ✅ Fixed
**Date**: 2026-02-03
**Affects**: All new sessions created after this fix
