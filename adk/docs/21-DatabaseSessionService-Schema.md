# Google ADK: DatabaseSessionService Database Schema

**File Path**: `docs/21-DatabaseSessionService-Schema.md`  
**Package**: `google.adk.sessions.DatabaseSessionService`  
**Related Docs**: [Sessions Package](07-Sessions-Package.md)

## Overview

This document provides a comprehensive reference for the database schema used by `DatabaseSessionService`. The schema is automatically created when you initialize a `DatabaseSessionService` instance.

---

## Schema Versions

`DatabaseSessionService` supports two schema versions:

- **V0 Schema**: Legacy schema (deprecated)
- **V1 Schema**: Latest schema with improved features (current default)

The service automatically detects and uses the appropriate schema version. New databases will use V1 schema by default.

---

## Tables Overview

`DatabaseSessionService` automatically creates the following tables:

1. **`sessions`**: Stores session metadata and state
2. **`events`**: Stores conversation events
3. **`app_states`**: Stores application-level state
4. **`user_states`**: Stores user-level state
5. **`adk_internal_metadata`**: Stores schema version and metadata (V1 schema only)

---

## Table 1: `sessions`

Stores session metadata and session-level state.

### Table Name
```sql
sessions
```

### Fields

| Field Name | Type | Constraints | Description |
|------------|------|-------------|-------------|
| `app_name` | VARCHAR(128) | PRIMARY KEY | Application name identifier |
| `user_id` | VARCHAR(128) | PRIMARY KEY | User identifier |
| `id` | VARCHAR(128) | PRIMARY KEY | Session ID (auto-generated UUID if not provided) |
| `state` | JSON/JSONB/TEXT | DEFAULT `{}` | Session-level state (JSON object) |
| `create_time` | TIMESTAMP | DEFAULT `NOW()` | Session creation timestamp |
| `update_time` | TIMESTAMP | DEFAULT `NOW()`, ON UPDATE | Last update timestamp |

### Primary Key
```sql
PRIMARY KEY (app_name, user_id, id)
```

### Relationships
- **One-to-Many** with `events` table (cascade delete)

### SQL Definition (PostgreSQL)
```sql
CREATE TABLE sessions (
    app_name VARCHAR(128) NOT NULL,
    user_id VARCHAR(128) NOT NULL,
    id VARCHAR(128) NOT NULL DEFAULT gen_random_uuid()::text,
    state JSONB DEFAULT '{}'::jsonb,
    create_time TIMESTAMP DEFAULT NOW(),
    update_time TIMESTAMP DEFAULT NOW(),
    PRIMARY KEY (app_name, user_id, id)
);
```

### SQL Definition (SQLite)
```sql
CREATE TABLE sessions (
    app_name VARCHAR(128) NOT NULL,
    user_id VARCHAR(128) NOT NULL,
    id VARCHAR(128) NOT NULL,
    state TEXT DEFAULT '{}',
    create_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    update_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (app_name, user_id, id)
);
```

### SQL Definition (MySQL)
```sql
CREATE TABLE sessions (
    app_name VARCHAR(128) NOT NULL,
    user_id VARCHAR(128) NOT NULL,
    id VARCHAR(128) NOT NULL,
    state LONGTEXT DEFAULT '{}',
    create_time DATETIME(6) DEFAULT CURRENT_TIMESTAMP(6),
    update_time DATETIME(6) DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
    PRIMARY KEY (app_name, user_id, id)
);
```

### Example Data
```json
{
  "app_name": "my_app",
  "user_id": "user123",
  "id": "session456",
  "state": {
    "conversation_topic": "Python programming",
    "message_count": 5
  },
  "create_time": "2024-01-15 10:30:00",
  "update_time": "2024-01-15 10:35:00"
}
```

### Notes
- **State Storage**: Session-level state (no prefix) is stored in the `state` column
- **Composite Primary Key**: Uses three-part key: `(app_name, user_id, id)`
- **Auto-Generated ID**: If `session_id` is not provided, a UUID is automatically generated
- **Cascade Delete**: Deleting a session automatically deletes all associated events

---

## Table 2: `events`

Stores conversation events (messages, tool calls, agent responses, etc.).

### Table Name
```sql
events
```

### Fields

| Field Name | Type | Constraints | Description |
|------------|------|-------------|-------------|
| `id` | VARCHAR(128) | PRIMARY KEY | Event ID (UUID) |
| `app_name` | VARCHAR(128) | PRIMARY KEY, FOREIGN KEY | Application name |
| `user_id` | VARCHAR(128) | PRIMARY KEY, FOREIGN KEY | User identifier |
| `session_id` | VARCHAR(128) | PRIMARY KEY, FOREIGN KEY | Session ID |
| `invocation_id` | VARCHAR(256) | | Invocation ID (groups related events) |
| `timestamp` | TIMESTAMP | DEFAULT `NOW()` | Event timestamp |
| `event_data` | JSON/JSONB/TEXT | NULLABLE | Complete event data (JSON serialized Event object) |

### Primary Key
```sql
PRIMARY KEY (id, app_name, user_id, session_id)
```

### Foreign Key
```sql
FOREIGN KEY (app_name, user_id, session_id) 
REFERENCES sessions(app_name, user_id, id) 
ON DELETE CASCADE
```

### SQL Definition (PostgreSQL)
```sql
CREATE TABLE events (
    id VARCHAR(128) NOT NULL,
    app_name VARCHAR(128) NOT NULL,
    user_id VARCHAR(128) NOT NULL,
    session_id VARCHAR(128) NOT NULL,
    invocation_id VARCHAR(256),
    timestamp TIMESTAMP DEFAULT NOW(),
    event_data JSONB,
    PRIMARY KEY (id, app_name, user_id, session_id),
    FOREIGN KEY (app_name, user_id, session_id) 
        REFERENCES sessions(app_name, user_id, id) 
        ON DELETE CASCADE
);
```

### SQL Definition (SQLite)
```sql
CREATE TABLE events (
    id VARCHAR(128) NOT NULL,
    app_name VARCHAR(128) NOT NULL,
    user_id VARCHAR(128) NOT NULL,
    session_id VARCHAR(128) NOT NULL,
    invocation_id VARCHAR(256),
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    event_data TEXT,
    PRIMARY KEY (id, app_name, user_id, session_id),
    FOREIGN KEY (app_name, user_id, session_id) 
        REFERENCES sessions(app_name, user_id, id) 
        ON DELETE CASCADE
);
```

### SQL Definition (MySQL)
```sql
CREATE TABLE events (
    id VARCHAR(128) NOT NULL,
    app_name VARCHAR(128) NOT NULL,
    user_id VARCHAR(128) NOT NULL,
    session_id VARCHAR(128) NOT NULL,
    invocation_id VARCHAR(256),
    timestamp DATETIME(6) DEFAULT CURRENT_TIMESTAMP(6),
    event_data LONGTEXT,
    PRIMARY KEY (id, app_name, user_id, session_id),
    FOREIGN KEY (app_name, user_id, session_id) 
        REFERENCES sessions(app_name, user_id, id) 
        ON DELETE CASCADE
);
```

### Event Data Structure

The `event_data` column contains a JSON-serialized `Event` object with the following structure:

```json
{
  "id": "event-uuid",
  "invocation_id": "invocation-uuid",
  "author": "user" | "agent_name",
  "content": {
    "role": "user" | "model",
    "parts": [
      {
        "text": "message text",
        "function_call": {...},
        "function_response": {...}
      }
    ]
  },
  "actions": {
    "state_delta": {...},
    "artifact_delta": {...},
    "compaction": {...},
    "transfer_to_agent": "...",
    "end_of_agent": true
  },
  "branch": "agent1.agent2",
  "timestamp": 1705315200.123456,
  "partial": false,
  "turn_complete": true,
  "finish_reason": "STOP",
  "usage_metadata": {
    "prompt_token_count": 150,
    "candidates_token_count": 200,
    "total_token_count": 350
  }
}
```

### Example Data
```json
{
  "id": "evt_abc123",
  "app_name": "my_app",
  "user_id": "user123",
  "session_id": "session456",
  "invocation_id": "inv_xyz789",
  "timestamp": "2024-01-15 10:30:15",
  "event_data": {
    "author": "user",
    "content": {
      "role": "user",
      "parts": [{"text": "Hello!"}]
    },
    "timestamp": 1705315215.123456
  }
}
```

### Notes
- **Cascade Delete**: Events are automatically deleted when their parent session is deleted
- **Event Data**: Complete event information is stored as JSON in `event_data` column
- **Indexing**: Consider adding indexes on `session_id`, `timestamp`, and `invocation_id` for better query performance
- **V1 Schema**: Uses JSON serialization for event data (simpler than V0's multiple columns)

---

## Table 3: `app_states`

Stores application-level state (shared across all users in an application).

### Table Name
```sql
app_states
```

### Fields

| Field Name | Type | Constraints | Description |
|------------|------|-------------|-------------|
| `app_name` | VARCHAR(128) | PRIMARY KEY | Application name identifier |
| `state` | JSON/JSONB/TEXT | DEFAULT `{}` | Application-level state (JSON object) |
| `update_time` | TIMESTAMP | DEFAULT `NOW()`, ON UPDATE | Last update timestamp |

### Primary Key
```sql
PRIMARY KEY (app_name)
```

### SQL Definition (PostgreSQL)
```sql
CREATE TABLE app_states (
    app_name VARCHAR(128) NOT NULL PRIMARY KEY,
    state JSONB DEFAULT '{}'::jsonb,
    update_time TIMESTAMP DEFAULT NOW()
);
```

### SQL Definition (SQLite)
```sql
CREATE TABLE app_states (
    app_name VARCHAR(128) NOT NULL PRIMARY KEY,
    state TEXT DEFAULT '{}',
    update_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### SQL Definition (MySQL)
```sql
CREATE TABLE app_states (
    app_name VARCHAR(128) NOT NULL PRIMARY KEY,
    state LONGTEXT DEFAULT '{}',
    update_time DATETIME(6) DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6)
);
```

### Example Data
```json
{
  "app_name": "my_app",
  "state": {
    "app:tax_rate": 0.08,
    "app:max_level": 100,
    "app:feature_enabled": true
  },
  "update_time": "2024-01-15 10:30:00"
}
```

### Notes
- **Scope**: One row per application (`app_name`)
- **State Prefix**: App-level state keys should use `app:` prefix (e.g., `app:tax_rate`)
- **Shared State**: All users in the same application share this state
- **Use Cases**: Global configuration, feature flags, app-wide settings

---

## Table 4: `user_states`

Stores user-level state (persists across all sessions for a specific user).

### Table Name
```sql
user_states
```

### Fields

| Field Name | Type | Constraints | Description |
|------------|------|-------------|-------------|
| `app_name` | VARCHAR(128) | PRIMARY KEY | Application name identifier |
| `user_id` | VARCHAR(128) | PRIMARY KEY | User identifier |
| `state` | JSON/JSONB/TEXT | DEFAULT `{}` | User-level state (JSON object) |
| `update_time` | TIMESTAMP | DEFAULT `NOW()`, ON UPDATE | Last update timestamp |

### Primary Key
```sql
PRIMARY KEY (app_name, user_id)
```

### SQL Definition (PostgreSQL)
```sql
CREATE TABLE user_states (
    app_name VARCHAR(128) NOT NULL,
    user_id VARCHAR(128) NOT NULL,
    state JSONB DEFAULT '{}'::jsonb,
    update_time TIMESTAMP DEFAULT NOW(),
    PRIMARY KEY (app_name, user_id)
);
```

### SQL Definition (SQLite)
```sql
CREATE TABLE user_states (
    app_name VARCHAR(128) NOT NULL,
    user_id VARCHAR(128) NOT NULL,
    state TEXT DEFAULT '{}',
    update_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (app_name, user_id)
);
```

### SQL Definition (MySQL)
```sql
CREATE TABLE user_states (
    app_name VARCHAR(128) NOT NULL,
    user_id VARCHAR(128) NOT NULL,
    state LONGTEXT DEFAULT '{}',
    update_time DATETIME(6) DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
    PRIMARY KEY (app_name, user_id)
);
```

### Example Data
```json
{
  "app_name": "my_app",
  "user_id": "user123",
  "state": {
    "user:preferred_language": "en",
    "user:loyalty_points": 1000,
    "user:total_purchases": 15
  },
  "update_time": "2024-01-15 10:30:00"
}
```

### Notes
- **Scope**: One row per user per application (`app_name`, `user_id`)
- **State Prefix**: User-level state keys should use `user:` prefix (e.g., `user:preferred_language`)
- **Persistence**: State persists across all sessions for the same user
- **Use Cases**: User preferences, user profile, user statistics

---

## Table 5: `adk_internal_metadata` (V1 Schema Only)

Stores internal ADK metadata, including schema version information.

### Table Name
```sql
adk_internal_metadata
```

### Fields

| Field Name | Type | Constraints | Description |
|------------|------|-------------|-------------|
| `key` | VARCHAR(128) | PRIMARY KEY | Metadata key |
| `value` | VARCHAR(256) | | Metadata value |

### Primary Key
```sql
PRIMARY KEY (key)
```

### SQL Definition (PostgreSQL)
```sql
CREATE TABLE adk_internal_metadata (
    key VARCHAR(128) NOT NULL PRIMARY KEY,
    value VARCHAR(256)
);
```

### SQL Definition (SQLite)
```sql
CREATE TABLE adk_internal_metadata (
    key VARCHAR(128) NOT NULL PRIMARY KEY,
    value VARCHAR(256)
);
```

### SQL Definition (MySQL)
```sql
CREATE TABLE adk_internal_metadata (
    key VARCHAR(128) NOT NULL PRIMARY KEY,
    value VARCHAR(256)
);
```

### Example Data
```json
{
  "key": "schema_version",
  "value": "v1"
}
```

### Notes
- **V1 Schema Only**: This table exists only in V1 schema
- **Internal Use**: Used by ADK to track schema version and manage migrations
- **Not User-Accessible**: This table is managed internally by `DatabaseSessionService`

---

## State Merging Logic

When retrieving a session, `DatabaseSessionService` automatically merges state from three sources:

1. **App-level state** (`app_states` table) → `state["app:key"]`
2. **User-level state** (`user_states` table) → `state["user:key"]`
3. **Session-level state** (`sessions.state` column) → `state["key"]`

### Example

```python
# App state
app_states.state = {"app:tax_rate": 0.08}

# User state
user_states.state = {"user:loyalty_points": 1000}

# Session state
sessions.state = {"cart_items": ["item1", "item2"]}

# Merged state (returned to user)
session.state = {
    "app:tax_rate": 0.08,        # From app_states
    "user:loyalty_points": 1000,  # From user_states
    "cart_items": ["item1", "item2"]  # From sessions
}
```

---

## Database-Specific Notes

### PostgreSQL

- **JSON Storage**: Uses `JSONB` type for efficient JSON storage and querying
- **Indexes**: Can create GIN indexes on JSONB columns for faster queries
- **Timezone**: Timestamps are timezone-aware

### SQLite

- **JSON Storage**: Uses `TEXT` type with JSON serialization
- **Timezone**: Timestamps are stored as naive datetime (converted to UTC internally)
- **Foreign Keys**: Must enable with `PRAGMA foreign_keys=ON`

### MySQL

- **JSON Storage**: Uses `LONGTEXT` type with JSON serialization
- **Precision**: Timestamps support microsecond precision (`DATETIME(6)`)
- **Timezone**: Timestamps are timezone-aware

---

## Recommended Indexes

For better query performance, consider adding these indexes:

### Sessions Table
```sql
-- Index for listing sessions by user
CREATE INDEX idx_sessions_user ON sessions(app_name, user_id);

-- Index for finding sessions by update time
CREATE INDEX idx_sessions_update_time ON sessions(update_time);
```

### Events Table
```sql
-- Index for querying events by session
CREATE INDEX idx_events_session ON events(app_name, user_id, session_id);

-- Index for querying events by timestamp (for filtering)
CREATE INDEX idx_events_timestamp ON events(timestamp);

-- Index for querying events by invocation
CREATE INDEX idx_events_invocation ON events(invocation_id);
```

### App States Table
```sql
-- Already indexed by primary key (app_name)
-- No additional indexes needed
```

### User States Table
```sql
-- Already indexed by primary key (app_name, user_id)
-- Consider index for querying by user_id across apps
CREATE INDEX idx_user_states_user ON user_states(user_id);
```

---

## Schema Migration

### V0 to V1 Migration

If you have an existing V0 schema database, ADK will:
1. Detect the schema version
2. Continue using V0 schema (backward compatible)
3. New databases use V1 schema by default

### Manual Migration

To migrate from V0 to V1:

1. **Backup your database**
2. **Check current schema version**:
   ```sql
   SELECT * FROM adk_internal_metadata WHERE key = 'schema_version';
   ```
3. **Update schema version** (if needed):
   ```sql
   INSERT INTO adk_internal_metadata (key, value) 
   VALUES ('schema_version', 'v1')
   ON CONFLICT (key) DO UPDATE SET value = 'v1';
   ```

---

## Example Queries

### Get All Sessions for a User
```sql
SELECT * FROM sessions 
WHERE app_name = 'my_app' AND user_id = 'user123';
```

### Get Events for a Session (Recent First)
```sql
SELECT * FROM events 
WHERE app_name = 'my_app' 
  AND user_id = 'user123' 
  AND session_id = 'session456'
ORDER BY timestamp DESC;
```

### Get Events After a Timestamp
```sql
SELECT * FROM events 
WHERE app_name = 'my_app' 
  AND user_id = 'user123' 
  AND session_id = 'session456'
  AND timestamp >= '2024-01-15 10:00:00'
ORDER BY timestamp ASC;
```

### Get User State
```sql
SELECT state FROM user_states 
WHERE app_name = 'my_app' AND user_id = 'user123';
```

### Get App State
```sql
SELECT state FROM app_states 
WHERE app_name = 'my_app';
```

### Count Events per Session
```sql
SELECT session_id, COUNT(*) as event_count 
FROM events 
WHERE app_name = 'my_app' AND user_id = 'user123'
GROUP BY session_id;
```

---

## Best Practices

1. **Use Appropriate Data Types**: Let ADK handle JSON serialization automatically
2. **Add Indexes**: Add indexes on frequently queried columns
3. **Monitor Table Sizes**: Events table can grow large; consider archiving old events
4. **Backup Regularly**: Sessions and events contain important conversation history
5. **Use Connection Pooling**: Configure appropriate pool sizes for production
6. **Enable Foreign Keys**: Ensure foreign key constraints are enabled (especially SQLite)
7. **State Prefixes**: Always use `app:` and `user:` prefixes for hierarchical state

---

## Troubleshooting

### Issue: Tables Not Created

**Solution**: Tables are created automatically on first use. Ensure:
- Database connection is valid
- User has CREATE TABLE permissions
- Database URL is correct

### Issue: Foreign Key Violations

**Solution**: 
- Ensure foreign keys are enabled (SQLite: `PRAGMA foreign_keys=ON`)
- Check that referenced sessions exist before inserting events

### Issue: JSON Serialization Errors

**Solution**: 
- Ensure state values are JSON-serializable
- Avoid storing non-serializable objects (use strings or dicts)

### Issue: Large Event Data

**Solution**: 
- Events table can grow large
- Consider archiving old events
- Use database-specific optimizations (e.g., PostgreSQL JSONB compression)

---

## Summary

| Table | Purpose | Key Fields | Relationships |
|-------|---------|------------|---------------|
| `sessions` | Session metadata and state | `app_name`, `user_id`, `id`, `state` | One-to-many with `events` |
| `events` | Conversation events | `id`, `session_id`, `event_data`, `timestamp` | Many-to-one with `sessions` |
| `app_states` | Application-level state | `app_name`, `state` | None |
| `user_states` | User-level state | `app_name`, `user_id`, `state` | None |
| `adk_internal_metadata` | Schema version info | `key`, `value` | None (V1 only) |

---

## Related Documentation

- [Sessions Package](07-Sessions-Package.md) - Complete session management guide
- [State Management](11-State-Management.md) - Understanding state scopes
- [DatabaseSessionService Event Filters](DatabaseSessionService-Event-Filters.md) - Event filtering
