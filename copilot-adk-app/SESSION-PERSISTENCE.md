# Session Persistence & History Retention

## Problem: Session History Disappearing

Sessions and their conversation history were being automatically deleted after 1 hour of inactivity, causing users to lose their chat history.

### What Was Happening

1. **Session Created**: User starts a chat, ADK stores it in Postgres
2. **User Leaves**: User closes browser or stops chatting
3. **1 Hour Later**: ADK SessionManager runs cleanup
4. **Session Deleted**: Inactive session removed from database
5. **History Lost**: When user returns, all messages are gone

### Root Cause

The ADK `SessionManager` has automatic cleanup that deletes sessions after `session_timeout_seconds` of inactivity. This was set to **3600 seconds (1 hour)** by default.

---

## ✅ Solution: Extended Session Timeout

Changed `SESSION_TIMEOUT_SECONDS` from **1 hour** to **7 days** (604,800 seconds).

### Configuration Changes

**File**: `backend/config.py`
```python
# Before (1 hour):
SESSION_TIMEOUT_SECONDS = int(os.getenv("SESSION_TIMEOUT_SECONDS", "3600"))

# After (7 days):
SESSION_TIMEOUT_SECONDS = int(os.getenv("SESSION_TIMEOUT_SECONDS", "604800"))
```

**File**: `backend/env.example`
```bash
# Session Timeout (seconds)
# How long sessions remain active before cleanup
# 3600 = 1 hour, 86400 = 1 day, 604800 = 7 days
# Set to very large number (e.g., 31536000 = 1 year) to effectively disable
SESSION_TIMEOUT_SECONDS=604800
```

---

## 📊 Timeout Options

| Duration | Seconds | Use Case |
|----------|---------|----------|
| 1 hour | 3600 | Short demo sessions |
| 1 day | 86400 | Daily active users |
| **7 days** | **604800** | **Weekly retention (recommended)** |
| 30 days | 2592000 | Monthly retention |
| 1 year | 31536000 | Effectively permanent |

### Recommendation

- **Development**: 7 days (current setting)
- **Production**: 30 days or more
- **Long-term projects**: 1 year

---

## 🔄 How ADK SessionManager Cleanup Works

### Cleanup Process

1. **Periodic Check**: SessionManager runs cleanup every 5 minutes (default)
2. **Age Calculation**: Checks `current_time - session.last_update_time`
3. **Timeout Comparison**: If age > `session_timeout_seconds`, mark for deletion
4. **Deletion**: Remove session from database (sessions, events, user_states)

### What Gets Deleted

When a session expires and is cleaned up:
- ✅ Session metadata (from `sessions` table)
- ✅ Session state (from `user_states` table)
- ✅ **All events/messages** (from `events` table)
- ✅ Conversation history

**Result**: User cannot see old chat history.

---

## 🛡️ Preventing History Loss

### Option 1: Increase Timeout (Current Solution)

**Pros:**
- Simple configuration change
- No code changes needed
- Works with existing setup

**Cons:**
- Sessions still eventually expire
- Database grows with inactive sessions

### Option 2: Disable Cleanup Entirely

Set timeout to a very large number (effectively infinite):

```bash
# .env
SESSION_TIMEOUT_SECONDS=31536000  # 1 year
```

**Pros:**
- Sessions never expire
- History always available

**Cons:**
- Database size grows indefinitely
- May need manual cleanup

### Option 3: Implement Manual Archival (Future)

Create a background job to:
1. Archive old sessions to cold storage
2. Keep recent sessions in hot database
3. Restore on-demand

**Pros:**
- Best of both worlds
- Efficient database usage

**Cons:**
- Requires additional implementation

---

## 📈 Database Impact

### Storage Estimates

**Per session:**
- Session metadata: ~500 bytes
- User state: ~1-2 KB
- Events/messages: ~100-500 bytes per message

**Example:**
- 1000 users
- 10 sessions each
- Average 50 messages per session
- **Total**: ~250-500 MB

With 7-day retention:
- Active sessions: Much smaller subset
- **Estimated**: 50-100 MB for most applications

---

## 🧪 Testing Session Persistence

### Test Scenario

1. **Create session**: Log in, start chat, send messages
2. **Wait 2 hours**: Leave app idle
3. **Return**: Refresh browser, log in again
4. **Verify**: Previous chat should still be visible
5. **Result**: ✅ History persists (with 7-day timeout)

### Before Fix (1-hour timeout):
```
Time 0:00 - Create session, chat
Time 1:01 - Session deleted by cleanup
Time 2:00 - Return → ❌ History lost
```

### After Fix (7-day timeout):
```
Time 0:00 - Create session, chat
Day 1 - Session still active
Day 7 - Session still active
Day 8 - Return → ✅ History available
Day 7+ - Session deleted after 7 days of inactivity
```

---

## ⚙️ Advanced Configuration

### Disable Cleanup Completely

If you want to keep sessions forever and manage cleanup manually:

```python
# backend/main.py
ADKAgent(
    ...,
    session_timeout_seconds=31536000,  # 1 year
    cleanup_interval_seconds=86400,     # Check once per day (efficiency)
    delete_session_on_cleanup=False,    # Don't delete sessions
)
```

**Note**: This requires modifying `backend/main.py` to pass additional parameters.

### Custom Cleanup Logic

For fine-grained control, implement custom cleanup:

```python
# Example: Keep sessions but archive events
from datetime import datetime, timedelta

async def custom_cleanup():
    # Archive sessions older than 30 days
    cutoff = datetime.now() - timedelta(days=30)
    old_sessions = await get_sessions_before(cutoff)
    
    for session in old_sessions:
        # Archive to cold storage
        await archive_session(session)
        # Keep metadata but remove events
        await delete_session_events(session.id)
```

---

## 📝 Environment Variable

To change the timeout without code changes, set in `.env`:

```bash
# backend/.env
SESSION_TIMEOUT_SECONDS=604800  # 7 days
```

Or in production (Cloud Run):
```bash
gcloud run services update copilot-backend \
  --set-env-vars SESSION_TIMEOUT_SECONDS=2592000  # 30 days
```

---

## 🎯 Recommendations

### For This Application

**Current Setting**: 7 days ✅

**Rationale:**
- Users return to chats within a week
- Balances retention with database size
- Automatic cleanup of truly abandoned sessions

### If You Need Longer Retention

Change to 30 days or 1 year:
```bash
# .env
SESSION_TIMEOUT_SECONDS=2592000  # 30 days
```

### If You Need Immediate Fix for Lost History

Unfortunately, **deleted sessions cannot be recovered**. The data is permanently removed from the database.

**Going forward:**
- New sessions will persist for 7 days
- Users won't lose recent history
- Old chats (>7 days inactive) will still be cleaned up

---

## 🚀 Production Deployment

### Cloud Run Configuration

```bash
# Set environment variable for production
gcloud run services update copilot-backend \
  --set-env-vars SESSION_TIMEOUT_SECONDS=2592000
```

### Docker Compose

```yaml
environment:
  - SESSION_TIMEOUT_SECONDS=2592000  # 30 days
```

---

## ✅ Summary

- **Problem**: Sessions deleted after 1 hour → history lost
- **Solution**: Increased timeout to 7 days (604,800 seconds)
- **Result**: Chat history persists for a week of inactivity
- **Trade-off**: Slightly larger database, but manageable
- **Future**: Consider archival for very old sessions

**Status**: ✅ Fixed - Sessions now persist for 7 days
**Date**: 2026-02-03
**Version**: v2.4-session-persistence
