# AG-UI User ID Issue

## Problem

AG-UI creates its own `thread_user_xxx` IDs instead of using the authenticated user IDs from our application.

## What We've Verified

### ✅ Working Correctly

1. **Cookies are set in browser:**
   - `copilot_adk_user_id=3`
   - `copilot_adk_session_id=<uuid>`

2. **Frontend sends headers correctly:**
   - `/api/copilotkit` receives cookies
   - Creates `HttpAgent` with headers: `X-User-Id: 3` and `X-Session-Id: <uuid>`

3. **Backend receives headers:**
   - `/ag-ui` endpoint logs show: `X-User-Id=3, X-Session-Id=<uuid>`

4. **Backend uses Postgres:**
   - ADKAgent initialized with `session_service` (not in-memory)

### ❌ Not Working

**Database shows `thread_user_xxx` instead of user_id=3**

Even though we send `X-User-Id: 3`, the `ag-ui-adk` library creates:
```
user_id = thread_user_54af7703-a550-4d35-b2a2-e85f59ee3d4d
```

## Root Cause

The `ag-ui-adk` library appears to **ignore** the `X-User-Id` and `X-Session-Id` headers and generates its own thread-based IDs from the AG-UI protocol.

## Logs Showing The Issue

### Frontend (working):
```
🔌 CopilotKit API: userId=3, sessionId=38e1f168...
🍪 Cookies received: ['copilot_adk_user_id=3', 'copilot_adk_session_id=38e1f168...']
```

### Backend (working):
```
🔍 Backend /ag-ui: X-User-Id=3, X-Session-Id=38e1f168...
✅ ADKAgent initialized with Postgres session service
```

### Database (not working):
```
user_id: thread_user_54af7703-a550-4d35-b2a2-e85f59ee3d4d  ❌
```

## Potential Solutions

### Option 1: Post-process User ID Mapping
Create a middleware to map `thread_user_xxx` to actual user IDs in the database.

### Option 2: Custom AG-UI Handler
Implement a custom handler that intercepts AG-UI requests and injects the user_id.

### Option 3: Use ADK Without AG-UI
Implement a direct ADK integration without the AG-UI protocol layer.

### Option 4: Wait for Library Update
The `ag-ui-adk` library might need to be updated to respect these headers.

## Current Workaround

For now, we can:
1. Use the `thread_user_xxx` IDs as-is
2. Create a mapping table: `thread_user_id → actual_user_id`
3. Query sessions by looking up the mapping

## Files Modified

- `frontend/app/api/copilotkit/route.ts` - Sends X-User-Id and X-Session-Id headers
- `frontend/contexts/AuthContext.tsx` - Sets cookies on login and restore
- `frontend/app/chat/page.tsx` - Triple cookie setting (login/restore/chat)
- `backend/main.py` - Logs headers received at /ag-ui endpoint

All cookie and header passing is working correctly. The issue is in the `ag-ui-adk` library itself.
