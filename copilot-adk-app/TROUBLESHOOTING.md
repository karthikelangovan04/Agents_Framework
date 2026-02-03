# Troubleshooting Guide

## AG-UI Creating Its Own User IDs

### Problem
AG-UI creates user IDs like `thread_user_xxx` instead of using your actual user ID from the database. Sessions are not linked to authenticated users.

### Root Cause
The `copilot_adk_user_id` cookie was not being set when the chat page loads or when switching sessions.

### Solution
✅ **FIXED** - The frontend now properly sets both cookies:
- `copilot_adk_user_id` - Your actual user ID from the database
- `copilot_adk_session_id` - The current chat session ID

These cookies are set:
1. When the chat page first loads
2. When creating a new chat
3. When switching between chat sessions

### Verification
Check your browser cookies (DevTools → Application → Cookies):
- `copilot_adk_user_id` should be `3` (for user karthikelangovan04)
- `copilot_adk_session_id` should be a UUID like `9d5c89f6-d3e0-4263-96fc-94e7f2698438`

Check Postgres `sessions` table:
```sql
SELECT app_name, user_id, id FROM sessions WHERE app_name='copilot_adk_app';
```
You should see `user_id = 3` instead of `thread_user_xxx`.

---

## Sessions Loading Forever / Stuck on "Loading..."

### Problem
Left sidebar shows "Loading..." forever and never displays chat sessions.

### Root Cause
1. Missing `lib/api.ts` and `lib/auth.ts` files
2. Frontend couldn't fetch sessions from backend

### Solution
✅ **FIXED** - Created missing library files:
- `frontend/lib/auth.ts` - Authentication utilities
- `frontend/lib/api.ts` - Backend API client functions

### Verification
1. Refresh the page: http://localhost:3000/chat
2. Left sidebar should show your username and list of chat sessions (or "No chats yet")
3. Check browser console (F12) for any errors

---

## "New Chat" Button Not Working

### Problem
Clicking "New chat" button does nothing.

### Root Cause
Missing API functions to create sessions.

### Solution
✅ **FIXED** - The `createSession()` function now works correctly and also sets both user and session cookies.

### Verification
1. Go to http://localhost:3000/chat
2. Click "New chat" button
3. A new session should appear at the top of the sidebar
4. The chat interface should be ready for messages

---

## Logout Infinite Loop

### Problem
After logout, the page keeps loading and redirecting in a loop.

### Root Cause
1. Using `window.location.href` instead of Next.js router
2. Cookies not being cleared properly
3. Multiple `useEffect` hooks triggering redirects

### Solution
✅ **FIXED** - Changed to use Next.js `router.replace()` and proper cleanup:
- Logout clears all cookies via API
- Uses `redirectedRef` to prevent multiple redirects
- Client-side navigation prevents full page reloads

### Verification
1. Click "Logout" button
2. Should smoothly redirect to `/login`
3. No loading loop or multiple redirects

---

## Webpack Cache Errors

### Problem
```
[webpack.cache.PackFileCacheStrategy] Caching failed for pack
ENOENT: no such file or directory, lstat '.../.next/server/vendor-chunks/@opentelemetry.js'
```

### Root Cause
Corrupted Next.js build cache from previous incomplete builds.

### Solution
```bash
cd frontend
rm -rf .next
npm run dev
```

The `.next` directory will be automatically regenerated clean.

---

## How to Clear Everything and Start Fresh

If you're experiencing multiple issues:

### 1. Clear Browser Data
- Press `Cmd+Shift+Delete` (Mac) or `Ctrl+Shift+Delete` (Windows)
- Clear cookies and cache for `localhost`

### 2. Clear Frontend Cache
```bash
cd /Users/karthike/Desktop/Vibe\ Coding/Google-ADK-A2A-Explore/copilot-adk-app/frontend
rm -rf .next
npm run dev
```

### 3. Clear Postgres Data (Optional - CAUTION!)
This will delete all users and sessions:
```sql
TRUNCATE users, sessions, events, user_states CASCADE;
```

### 4. Restart Everything
```bash
# Terminal 1 - Backend
cd /Users/karthike/Desktop/Vibe\ Coding/Google-ADK-A2A-Explore/copilot-adk-app
source .venv/bin/activate
cd backend
uvicorn main:app --reload

# Terminal 2 - Frontend
cd /Users/karthike/Desktop/Vibe\ Coding/Google-ADK-A2A-Explore/copilot-adk-app/frontend
npm run dev
```

---

## Database Connection Issues

### Problem
```
asyncpg.exceptions.InvalidPasswordError: password authentication failed
```

### Solution
Check your `backend/.env`:
```
DATABASE_URL=postgresql+asyncpg://adk_user:adk_password@localhost:5433/copilot_adk_db
```

Verify Postgres is running on the correct port:
```bash
lsof -i :5433
```

---

## AG-UI Integration Checklist

When messages are sent to the AI, the backend should receive:
- ✅ `X-User-Id` header with your actual user ID (e.g., `3`)
- ✅ `X-Session-Id` header with the current session UUID

Check backend logs for:
```
INFO:     127.0.0.1:xxxxx - "POST /ag-ui HTTP/1.1" 200 OK
```

If you see `thread_user_xxx` in the database, the cookies are not being sent correctly.

---

## Common Mistakes

### ❌ Don't use user_id/session_id in ADKAgent constructor
```python
# WRONG
agent = ADKAgent(adk_agent=my_agent, user_id=3, session_id="abc")
```

The AG-UI protocol passes these dynamically via headers at runtime.

### ❌ Don't forget to set cookies before CopilotKit initializes
```typescript
// WRONG - CopilotKit mounts before cookies are set
<CopilotKit ...>

// RIGHT - Set cookies in useEffect before render
useEffect(() => {
  setUserAndSessionCookies(user.user_id, sessionId);
}, [user, sessionId]);
```

### ❌ Don't use window.location for navigation in Next.js
```typescript
// WRONG
window.location.href = "/login";

// RIGHT
router.replace("/login");
```

---

## Getting Help

1. Check browser console (F12) for frontend errors
2. Check backend terminal for Python errors
3. Check Postgres logs if database issues
4. Verify cookies are set correctly (DevTools → Application → Cookies)
5. Check the database directly:
   ```bash
   psql -U adk_user -h localhost -p 5433 -d copilot_adk_db
   \dt
   SELECT * FROM users;
   SELECT * FROM sessions WHERE app_name='copilot_adk_app';
   ```
