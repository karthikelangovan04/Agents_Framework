# Session History Display Fix

## Problem
When switching between chat sessions, the previous conversation history was not being loaded or displayed. Users would see an empty chat even though the messages were stored in the database.

## Root Cause
- **Backend**: ADK agent correctly stores session state in the database
- **Frontend**: CopilotKit starts with a fresh, empty conversation when remounted with a new `key`
- **Missing**: No mechanism to fetch and display existing messages when switching sessions

## Solution
Added session history loading using the `/agents/state` endpoint that's automatically provided by `ag-ui-adk`.

---

## Changes Made

### 1. Frontend API Client (`frontend/lib/api.ts`)

Added `getSessionHistory()` function:
```typescript
export interface SessionHistory {
  threadId: string;
  threadExists: boolean;
  state: Record<string, any>;
  messages: Array<{
    role: string;
    content: string;
  }>;
}

export async function getSessionHistory(
  sessionId: string,
  userId: number
): Promise<SessionHistory | null>
```

This function calls the `/agents/state` endpoint to fetch:
- Session state
- Full message history
- Thread existence status

### 2. Chat Page (`frontend/app/chat/page.tsx`)

#### Added State:
```typescript
const [sessionHistory, setSessionHistory] = useState<SessionHistory | null>(null);
const [historyLoading, setHistoryLoading] = useState(false);
```

#### Added History Loading:
When `currentSessionId` changes, the page now:
1. Sets the session cookie (existing behavior)
2. **NEW**: Fetches session history from `/agents/state`
3. **NEW**: Displays the loaded messages in the main content area

#### Enhanced UI:
- Shows "Loading conversation history..." while fetching
- Displays previous messages in a chat-like format:
  - User messages: Blue background, right-aligned
  - Assistant messages: Card background, left-aligned
- Shows message count
- Indicates when to continue in CopilotKit panel

---

## How It Works

### Flow:
```
1. User clicks on a session → setCurrentSessionId(sessionId)
2. useEffect detects change → calls getSessionHistory(sessionId, userId)
3. Backend /agents/state endpoint → queries database for session
4. Returns { threadId, threadExists, state, messages }
5. Frontend displays messages in main content area
6. User continues conversation in CopilotKit sidebar
```

### Backend Endpoint:
- **URL**: `POST /agents/state`
- **Body**: `{ threadId, appName, userId }`
- **Returns**: Session state and full message history
- **Provider**: Automatically added by `add_adk_fastapi_endpoint()`

---

## User Experience

### Before:
```
1. User in Session A (has chat history)
2. Creates Session B, chats
3. Switches back to Session A
4. ❌ Sees empty chat - history lost!
```

### After:
```
1. User in Session A (has chat history)
2. Creates Session B, chats  
3. Switches back to Session A
4. ✅ Sees all previous messages loaded
5. Can continue conversation seamlessly
```

---

## Testing

### Test Steps:
1. **Create Session 1**: Send a few messages (e.g., "Tell me a joke")
2. **Create Session 2**: Send different messages (e.g., "What's the weather?")
3. **Switch to Session 1**: Should see the joke conversation
4. **Switch to Session 2**: Should see the weather conversation
5. **Continue chatting**: New messages append to history

### Expected Behavior:
- ✅ History loads within 1-2 seconds
- ✅ Messages display in chronological order
- ✅ User/assistant messages visually distinct
- ✅ Can continue conversation in CopilotKit panel
- ✅ New messages persist across session switches

---

## Technical Notes

### Why This Approach?
1. **CopilotKit Limitation**: CopilotKit doesn't have an `initialMessages` prop to pre-load history
2. **Backend Ready**: The `/agents/state` endpoint already exists and provides full history
3. **Minimal Changes**: Only needed to add history fetching and display logic
4. **User Experience**: Shows context immediately, no waiting for CopilotKit to load

### Alternative Approaches Considered:
1. ❌ **Store messages in frontend state**: Would lose history on page refresh
2. ❌ **Use CopilotKit's internal state**: Not exposed via public API
3. ✅ **Fetch from backend on switch**: Best balance of correctness and UX

---

## Database Query

The `/agents/state` endpoint uses:
```python
session = await session_service.get_session(
    session_id=session_id,
    app_name=app_name,
    user_id=user_id
)

# Returns session.state (contains _ag_ui_* metadata and messages)
```

**Tables Queried:**
- `sessions` - Session metadata (id, user_id, app_name)
- `user_states` - Session state (includes message history)

---

## Files Modified

1. **frontend/lib/api.ts** (+50 lines)
   - Added `SessionHistory` interface
   - Added `getSessionHistory()` function

2. **frontend/app/chat/page.tsx** (+45 lines)
   - Added history state and loading logic
   - Enhanced UI to display message history
   - Added logging for debugging

---

## Verification

Check browser console logs when switching sessions:
```
🍪 SET SESSION COOKIE: copilot_adk_session_id=5feece44...
📚 Loading history for session: 5feece44...
✅ Loaded 6 messages from session
```

Or for new sessions:
```
📝 New session - no previous history
```

---

## Future Improvements

1. **Pagination**: For sessions with many messages (>100)
2. **Search**: Add ability to search within session history
3. **Export**: Allow users to export conversation history
4. **Timestamps**: Display message timestamps
5. **Editing**: Allow editing of previous messages
6. **Streaming**: Show new messages being typed in real-time

---

## Related Issues Fixed

- ✅ Session history not persisting across switches
- ✅ "No chat history" message when returning to old sessions
- ✅ Messages not rendered when switching sessions
- ✅ Context not maintained between sessions

---

**Status**: ✅ Implemented and Ready for Testing
**Date**: 2026-02-03
**Version**: v2.2-session-history-fix
