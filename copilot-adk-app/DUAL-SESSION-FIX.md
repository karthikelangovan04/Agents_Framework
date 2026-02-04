# Dual Session Creation Bug Fix

## 🐛 **Problem: Two Sessions Created for Each Chat**

When users created a new chat session, TWO sessions were being created in the database:

1. **Empty shell session** - Created by `/api/sessions`, with empty state
2. **Actual conversation session** - Created by ADK SessionManager, with proper state

This caused history loading failures and data fragmentation.

---

## 🔍 **Investigation**

### User's Discovery

Looking at the database for session `e862dec2-6acf-4d28-a411-0d52458aa738`:

#### **Sessions Table - TWO Entries:**

**Session 1** (Empty):
```sql
id: e862dec2-6acf-4d28-a411-0d52458aa738
user_id: 4
state: {}  ← EMPTY STATE!
create_time: 2026-02-04 00:43:56
update_time: 2026-02-04 00:43:56  ← Never updated
```

**Session 2** (Actual conversation):
```sql
id: bc00278f-fd32-4e9c-aec7-16b2530a9206  ← Different ID!
user_id: 4
state: {
  "_ag_ui_user_id": "4",
  "_ag_ui_app_name": "copilot_adk_app",
  "_ag_ui_thread_id": "e862dec2-6acf-4d28-a411-0d52458aa738",  ← References Session 1
  "_ag_ui_session_id": "e862dec2-6acf-4d28-a411-0d52458aa738"
}
create_time: 2026-02-04 00:51:57
update_time: 2026-02-04 06:21:59  ← Updated during conversation
```

#### **Events Table:**
```sql
All events have session_id = bc00278f-fd32-4e9c-aec7-16b2530a9206
```

**Result**: Frontend thinks it's using `e862dec2...`, but all conversation data is in `bc00278f...`!

---

## 🔄 **What Was Happening**

### Flow Before Fix:

```
1. User clicks "New Chat" in frontend
   ↓
2. Frontend → POST /api/sessions
   ↓
3. Backend creates session in database:
   - session_id: e862dec2...
   - state: {}  ← EMPTY!
   ↓
4. Frontend → Sends first message with threadId=e862dec2...
   ↓
5. CopilotKit → Backend /ag-ui endpoint
   ↓
6. ADK SessionManager searches for session:
   - Looks for session where state contains "_ag_ui_thread_id": "e862dec2..."
   - Doesn't find it! (Session 1 has empty state)
   ↓
7. ADK creates NEW session:
   - session_id: bc00278f...  ← DIFFERENT!
   - state: { "_ag_ui_thread_id": "e862dec2...", ... }
   ↓
8. All messages stored in bc00278f... (Session 2)
   ↓
9. Frontend tries to load history from e862dec2... (Session 1)
   ↓
10. ❌ No history found! (Wrong session)
```

---

## ✅ **Root Cause**

The `/api/sessions` endpoint was creating sessions **without initializing AG-UI state metadata**:

```python
# BEFORE - Missing state initialization:
session = await session_service.create_session(
    app_name=APP_NAME,
    user_id=user_id,
    session_id=session_id,
    # state parameter NOT provided → defaults to {}
)
```

When ADK SessionManager receives `threadId=e862dec2...`, it searches for a session containing:
```json
{ "_ag_ui_thread_id": "e862dec2..." }
```

But Session 1 has `state = {}`, so the search fails and ADK creates a new session.

---

## ✅ **The Fix**

Initialize session state with AG-UI metadata when creating via `/api/sessions`:

```python
# AFTER - Proper state initialization:
initial_state = {
    "_ag_ui_user_id": user_id,
    "_ag_ui_app_name": APP_NAME,
    "_ag_ui_thread_id": session_id,  # thread_id = session_id
    "_ag_ui_session_id": session_id,
}

session = await session_service.create_session(
    app_name=APP_NAME,
    user_id=user_id,
    session_id=session_id,
    state=initial_state,  # ← Initialize with AG-UI metadata
)
```

---

## 🎯 **Flow After Fix**

```
1. User clicks "New Chat"
   ↓
2. Frontend → POST /api/sessions
   ↓
3. Backend creates session with PROPER state:
   - session_id: e862dec2...
   - state: {
       "_ag_ui_thread_id": "e862dec2...",
       "_ag_ui_session_id": "e862dec2...",
       "_ag_ui_user_id": "4",
       "_ag_ui_app_name": "copilot_adk_app"
     }
   ↓
4. Frontend → Sends first message with threadId=e862dec2...
   ↓
5. ADK SessionManager searches for session:
   - Looks for "_ag_ui_thread_id": "e862dec2..."
   - ✅ FINDS IT! (Session 1 now has proper state)
   ↓
6. ADK uses EXISTING session e862dec2...
   - No duplicate session created!
   ↓
7. All messages stored in e862dec2... (Same session)
   ↓
8. Frontend loads history from e862dec2...
   ↓
9. ✅ History loads correctly!
```

---

## 📊 **Impact**

### Before Fix:
- ❌ Two sessions per chat
- ❌ History lookup fails (wrong session)
- ❌ Database fragmentation
- ❌ Confusion about which session is "real"
- ❌ Potential data loss

### After Fix:
- ✅ One session per chat
- ✅ History loads correctly
- ✅ Clean database structure
- ✅ Frontend session ID = Backend session ID
- ✅ All data in correct place

---

## 🧪 **How to Verify the Fix**

### Test Steps:

1. **Create new chat session** (after backend restart)
2. **Check sessions table**:
   ```sql
   SELECT id, state FROM sessions WHERE user_id = '4' ORDER BY create_time DESC LIMIT 1;
   ```
3. **Verify state is NOT empty**:
   ```json
   {
     "_ag_ui_thread_id": "abc123...",
     "_ag_ui_session_id": "abc123...",
     "_ag_ui_user_id": "4",
     "_ag_ui_app_name": "copilot_adk_app"
   }
   ```
4. **Send first message**
5. **Check sessions table again** - Should be SAME session (no new session created)
6. **Check events table**:
   ```sql
   SELECT session_id, COUNT(*) FROM events WHERE user_id = '4' GROUP BY session_id;
   ```
7. **Verify**: All events for that chat should have the SAME session_id as shown in frontend

### Expected Results:

**Before Fix**:
```sql
-- Two sessions for same chat:
e862dec2... | state: {} | create_time: 00:43:56
bc00278f... | state: {...} | create_time: 00:51:57

-- Events point to second session:
session_id: bc00278f...
```

**After Fix**:
```sql
-- One session for chat:
e862dec2... | state: {...} | create_time: 00:43:56

-- Events point to same session:
session_id: e862dec2...
```

---

## 🔑 **Key Concepts**

### AG-UI State Metadata

ADK SessionManager uses these state fields to identify and manage sessions:

| Field | Purpose |
|-------|---------|
| `_ag_ui_thread_id` | AG-UI protocol identifier (= session_id) |
| `_ag_ui_session_id` | AG-UI session identifier (= session_id) |
| `_ag_ui_user_id` | User who owns the session |
| `_ag_ui_app_name` | Application name |

### Session Lookup Logic

When ADK receives a message with `threadId=X`:

1. Search for session where `state["_ag_ui_thread_id"] == X`
2. If found → Use existing session
3. If NOT found → Create new session with that thread_id

**Problem**: Empty state (`{}`) means `state["_ag_ui_thread_id"]` doesn't exist → Search fails → New session created

**Solution**: Initialize state with proper metadata → Search succeeds → No duplicate session

---

## 📝 **Files Changed**

### `backend/main.py`

**Added state initialization in create_session endpoint:**

```python
@app.post("/api/sessions", response_model=SessionItem)
async def create_session(user_id: str = Depends(get_current_user_id)):
    """Create a new chat session (new conversation) with proper AG-UI state."""
    session_id = str(uuid.uuid4())
    
    # Initialize with AG-UI metadata (NEW)
    initial_state = {
        "_ag_ui_user_id": user_id,
        "_ag_ui_app_name": APP_NAME,
        "_ag_ui_thread_id": session_id,
        "_ag_ui_session_id": session_id,
    }
    
    session = await session_service.create_session(
        app_name=APP_NAME,
        user_id=user_id,
        session_id=session_id,
        state=initial_state,  # ← KEY FIX
    )
    
    print(f"✅ Created session {session_id[:8]}... with initial state for user {user_id}")
    return SessionItem(...)
```

---

## 🎯 **What This Fixes**

1. ✅ **Duplicate sessions** - Only one session created per chat
2. ✅ **History loading** - Frontend session ID = Backend session ID
3. ✅ **Data consistency** - All events in correct session
4. ✅ **Database cleanliness** - No orphaned empty sessions
5. ✅ **Session switching** - Works correctly with single session per chat

---

## 🔮 **Future Considerations**

### Cleanup Old Duplicate Sessions

For sessions created before this fix, you may have:
- Empty "shell" sessions with `state = {}`
- Duplicate conversation sessions

**Optional cleanup query**:
```sql
-- Find empty sessions (potentially duplicates)
SELECT * FROM sessions WHERE state::text = '{}';

-- Verify they have no events
SELECT s.id, COUNT(e.id) as event_count 
FROM sessions s 
LEFT JOIN events e ON s.id = e.session_id 
WHERE s.state::text = '{}' 
GROUP BY s.id;

-- Delete empty sessions with no events (CAREFUL!)
DELETE FROM sessions 
WHERE state::text = '{}' 
AND id NOT IN (SELECT DISTINCT session_id FROM events);
```

**WARNING**: Only run cleanup queries if you understand the implications!

---

## ✅ **Summary**

**Problem**: Two sessions created per chat due to missing state initialization

**Root Cause**: `/api/sessions` endpoint didn't initialize AG-UI state metadata

**Fix**: Initialize state with proper metadata when creating session

**Result**: One session per chat, history loads correctly

**Status**: ✅ Fixed and deployed
**Date**: 2026-02-04
**Version**: v2.5-dual-session-fix
