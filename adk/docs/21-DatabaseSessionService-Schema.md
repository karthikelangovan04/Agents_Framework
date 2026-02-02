# Google ADK: DatabaseSessionService Database Schema

**File Path**: `docs/21-DatabaseSessionService-Schema.md`  
**Package**: `google.adk.sessions.DatabaseSessionService`  
**Related Docs**: [Sessions Package](07-Sessions-Package.md)

## Overview

This document provides a comprehensive reference for the database schema used by `DatabaseSessionService`. The schema is automatically created when you initialize a `DatabaseSessionService` instance.

---

## Schema Versions

`DatabaseSessionService` supports two schema versions:

- **V0 Schema**: Legacy schema (ADK 1.19.0 - 1.21.0)
  - Events stored with individual columns (22 fields)
  - Uses pickle serialization for `actions` field
  - More complex but allows direct SQL queries on individual fields
  
- **V1 Schema**: Latest schema (ADK 1.22.0+)
  - Events stored as JSON in single `event_data` column (7 fields)
  - Uses JSON serialization (database-agnostic)
  - Simpler schema, easier to maintain

The service automatically detects and uses the appropriate schema version. New databases will use V1 schema by default.

### Key Differences

| Aspect | V0 Schema | V1 Schema |
|--------|----------|-----------|
| **Events Table Columns** | 22 columns | 7 columns |
| **Event Storage** | Individual columns | Single JSON column |
| **Actions Serialization** | Pickle (Python-specific) | JSON (universal) |
| **Query Flexibility** | Can query individual fields | Query via JSON functions |
| **Schema Complexity** | More complex | Simpler |
| **Database Compatibility** | Works but pickle is Python-specific | Fully database-agnostic |
| **Migration** | Legacy, no migration needed | Current default |

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

### Schema Versions

The `events` table structure differs between V0 and V1 schemas:

- **V0 Schema**: Stores event fields as individual columns (22 fields)
- **V1 Schema**: Stores complete event data in a single JSON column (`event_data`)

---

### V0 Schema Fields (Individual Columns)

| Field Name | Type | Constraints | Description |
|------------|------|-------------|-------------|
| `id` | VARCHAR(128) | PRIMARY KEY | Event ID (UUID) |
| `app_name` | VARCHAR(128) | PRIMARY KEY, FOREIGN KEY | Application name |
| `user_id` | VARCHAR(128) | PRIMARY KEY, FOREIGN KEY | User identifier |
| `session_id` | VARCHAR(128) | PRIMARY KEY, FOREIGN KEY | Session ID |
| `invocation_id` | VARCHAR(256) | | Invocation ID (groups related events) |
| `author` | VARCHAR(256) | | Author of the event ('user' or agent name) |
| `actions` | BYTEA/PICKLE | | EventActions object (pickle serialized) |
| `long_running_tool_ids_json` | TEXT | NULLABLE | JSON array of long-running tool IDs |
| `branch` | VARCHAR(256) | NULLABLE | Agent branch path (e.g., "agent1.agent2") |
| `timestamp` | TIMESTAMP | DEFAULT `NOW()` | Event timestamp |
| `content` | JSON/JSONB/TEXT | NULLABLE | Event content (messages, tool calls) |
| `grounding_metadata` | JSON/JSONB/TEXT | NULLABLE | Grounding metadata |
| `custom_metadata` | JSON/JSONB/TEXT | NULLABLE | Custom metadata dictionary |
| `usage_metadata` | JSON/JSONB/TEXT | NULLABLE | Token usage metadata |
| `citation_metadata` | JSON/JSONB/TEXT | NULLABLE | Citation metadata |
| `partial` | BOOLEAN | NULLABLE | Whether content is partial (streaming) |
| `turn_complete` | BOOLEAN | NULLABLE | Whether turn is complete |
| `error_code` | VARCHAR(256) | NULLABLE | Error code if event represents an error |
| `error_message` | TEXT | NULLABLE | Error message if event represents an error |
| `interrupted` | BOOLEAN | NULLABLE | Whether generation was interrupted |
| `input_transcription` | JSON/JSONB/TEXT | NULLABLE | Audio input transcription |
| `output_transcription` | JSON/JSONB/TEXT | NULLABLE | Audio output transcription |

### V1 Schema Fields (JSON Column)

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

### SQL Definition - V0 Schema (PostgreSQL)

```sql
CREATE TABLE events (
    id VARCHAR(128) NOT NULL,
    app_name VARCHAR(128) NOT NULL,
    user_id VARCHAR(128) NOT NULL,
    session_id VARCHAR(128) NOT NULL,
    invocation_id VARCHAR(256),
    author VARCHAR(256),
    actions BYTEA,  -- Pickle serialized EventActions
    long_running_tool_ids_json TEXT,
    branch VARCHAR(256),
    timestamp TIMESTAMP DEFAULT NOW(),
    content JSONB,
    grounding_metadata JSONB,
    custom_metadata JSONB,
    usage_metadata JSONB,
    citation_metadata JSONB,
    partial BOOLEAN,
    turn_complete BOOLEAN,
    error_code VARCHAR(256),
    error_message TEXT,
    interrupted BOOLEAN,
    input_transcription JSONB,
    output_transcription JSONB,
    PRIMARY KEY (id, app_name, user_id, session_id),
    FOREIGN KEY (app_name, user_id, session_id) 
        REFERENCES sessions(app_name, user_id, id) 
        ON DELETE CASCADE
);
```

### SQL Definition - V1 Schema (PostgreSQL)

```sql
CREATE TABLE events (
    id VARCHAR(128) NOT NULL,
    app_name VARCHAR(128) NOT NULL,
    user_id VARCHAR(128) NOT NULL,
    session_id VARCHAR(128) NOT NULL,
    invocation_id VARCHAR(256),
    timestamp TIMESTAMP DEFAULT NOW(),
    event_data JSONB,  -- Complete Event object as JSON
    PRIMARY KEY (id, app_name, user_id, session_id),
    FOREIGN KEY (app_name, user_id, session_id) 
        REFERENCES sessions(app_name, user_id, id) 
        ON DELETE CASCADE
);
```

### SQL Definition - V0 Schema (SQLite)

```sql
CREATE TABLE events (
    id VARCHAR(128) NOT NULL,
    app_name VARCHAR(128) NOT NULL,
    user_id VARCHAR(128) NOT NULL,
    session_id VARCHAR(128) NOT NULL,
    invocation_id VARCHAR(256),
    author VARCHAR(256),
    actions BLOB,  -- Pickle serialized
    long_running_tool_ids_json TEXT,
    branch VARCHAR(256),
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    content TEXT,  -- JSON serialized
    grounding_metadata TEXT,
    custom_metadata TEXT,
    usage_metadata TEXT,
    citation_metadata TEXT,
    partial BOOLEAN,
    turn_complete BOOLEAN,
    error_code VARCHAR(256),
    error_message TEXT,
    interrupted BOOLEAN,
    input_transcription TEXT,
    output_transcription TEXT,
    PRIMARY KEY (id, app_name, user_id, session_id),
    FOREIGN KEY (app_name, user_id, session_id) 
        REFERENCES sessions(app_name, user_id, id) 
        ON DELETE CASCADE
);
```

### SQL Definition - V1 Schema (SQLite)

```sql
CREATE TABLE events (
    id VARCHAR(128) NOT NULL,
    app_name VARCHAR(128) NOT NULL,
    user_id VARCHAR(128) NOT NULL,
    session_id VARCHAR(128) NOT NULL,
    invocation_id VARCHAR(256),
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    event_data TEXT,  -- Complete Event object as JSON
    PRIMARY KEY (id, app_name, user_id, session_id),
    FOREIGN KEY (app_name, user_id, session_id) 
        REFERENCES sessions(app_name, user_id, id) 
        ON DELETE CASCADE
);
```

### SQL Definition - V0 Schema (MySQL)

```sql
CREATE TABLE events (
    id VARCHAR(128) NOT NULL,
    app_name VARCHAR(128) NOT NULL,
    user_id VARCHAR(128) NOT NULL,
    session_id VARCHAR(128) NOT NULL,
    invocation_id VARCHAR(256),
    author VARCHAR(256),
    actions LONGBLOB,  -- Pickle serialized
    long_running_tool_ids_json LONGTEXT,
    branch VARCHAR(256),
    timestamp DATETIME(6) DEFAULT CURRENT_TIMESTAMP(6),
    content LONGTEXT,  -- JSON serialized
    grounding_metadata LONGTEXT,
    custom_metadata LONGTEXT,
    usage_metadata LONGTEXT,
    citation_metadata LONGTEXT,
    partial BOOLEAN,
    turn_complete BOOLEAN,
    error_code VARCHAR(256),
    error_message LONGTEXT,
    interrupted BOOLEAN,
    input_transcription LONGTEXT,
    output_transcription LONGTEXT,
    PRIMARY KEY (id, app_name, user_id, session_id),
    FOREIGN KEY (app_name, user_id, session_id) 
        REFERENCES sessions(app_name, user_id, id) 
        ON DELETE CASCADE
);
```

### SQL Definition - V1 Schema (MySQL)

```sql
CREATE TABLE events (
    id VARCHAR(128) NOT NULL,
    app_name VARCHAR(128) NOT NULL,
    user_id VARCHAR(128) NOT NULL,
    session_id VARCHAR(128) NOT NULL,
    invocation_id VARCHAR(256),
    timestamp DATETIME(6) DEFAULT CURRENT_TIMESTAMP(6),
    event_data LONGTEXT,  -- Complete Event object as JSON
    PRIMARY KEY (id, app_name, user_id, session_id),
    FOREIGN KEY (app_name, user_id, session_id) 
        REFERENCES sessions(app_name, user_id, id) 
        ON DELETE CASCADE
);
```

### V0 Schema Field Details

#### `author`
- **Type**: VARCHAR(256)
- **Description**: Author of the event
- **Values**: `"user"` or agent name (e.g., `"my_agent"`)
- **Example**: `"user"`, `"assistant_agent"`

#### `actions`
- **Type**: BYTEA (PostgreSQL) / BLOB (SQLite) / LONGBLOB (MySQL)
- **Description**: EventActions object serialized with pickle
- **Contains**: State deltas, artifact deltas, compaction info, agent transfers, etc.
- **Note**: Pickle serialization allows storing complex Python objects

#### `long_running_tool_ids_json`
- **Type**: TEXT
- **Description**: JSON array of long-running tool call IDs
- **Format**: `'["tool_id_1", "tool_id_2"]'`
- **Example**: `'["func_call_abc123", "func_call_xyz789"]'`

#### `branch`
- **Type**: VARCHAR(256), NULLABLE
- **Description**: Agent branch path indicating agent hierarchy
- **Format**: `"agent1.agent2.agent3"` (dot-separated)
- **Example**: `"orchestrator.math_agent"`, `NULL` (for root agent)

#### `content`
- **Type**: JSON/JSONB/TEXT
- **Description**: Event content (messages, tool calls, responses)
- **Structure**: 
  ```json
  {
    "role": "user" | "model",
    "parts": [
      {"text": "..."},
      {"function_call": {...}},
      {"function_response": {...}}
    ]
  }
  ```

#### `usage_metadata`
- **Type**: JSON/JSONB/TEXT
- **Description**: Token usage information
- **Structure**:
  ```json
  {
    "prompt_token_count": 150,
    "candidates_token_count": 200,
    "total_token_count": 350
  }
  ```

#### `grounding_metadata`
- **Type**: JSON/JSONB/TEXT
- **Description**: Grounding metadata for RAG/retrieval
- **Contains**: Source citations, confidence scores, etc.

#### `citation_metadata`
- **Type**: JSON/JSONB/TEXT
- **Description**: Citation metadata for referenced sources
- **Contains**: Citation information, source URLs, etc.

#### `custom_metadata`
- **Type**: JSON/JSONB/TEXT
- **Description**: Custom key-value metadata
- **Format**: `{"key1": "value1", "key2": "value2"}`

#### `partial`
- **Type**: BOOLEAN, NULLABLE
- **Description**: Whether content is partial (streaming mode)
- **Values**: `true` (partial), `false` (complete), `NULL`

#### `turn_complete`
- **Type**: BOOLEAN, NULLABLE
- **Description**: Whether the turn is complete (streaming mode)
- **Values**: `true` (complete), `false` (incomplete), `NULL`

#### `error_code` and `error_message`
- **Type**: VARCHAR(256) / TEXT, NULLABLE
- **Description**: Error information if event represents an error
- **Example**: `error_code: "BLOCKED"`, `error_message: "Content was blocked"`

#### `interrupted`
- **Type**: BOOLEAN, NULLABLE
- **Description**: Whether generation was interrupted (e.g., user interruption)
- **Values**: `true` (interrupted), `false` (not interrupted), `NULL`

#### `input_transcription` and `output_transcription`
- **Type**: JSON/JSONB/TEXT, NULLABLE
- **Description**: Audio transcription data
- **Structure**: Transcription object with text, language, confidence, etc.

### V1 Schema Event Data Structure

The `event_data` column (V1 schema only) contains a JSON-serialized `Event` object with the following structure:

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

### Example Data - V0 Schema

```json
{
  "id": "evt_abc123",
  "app_name": "my_app",
  "user_id": "user123",
  "session_id": "session456",
  "invocation_id": "inv_xyz789",
  "author": "user",
  "branch": null,
  "timestamp": "2024-01-15 10:30:15",
  "content": {
    "role": "user",
    "parts": [{"text": "Hello!"}]
  },
  "usage_metadata": {
    "prompt_token_count": 10,
    "candidates_token_count": 0,
    "total_token_count": 10
  },
  "partial": false,
  "turn_complete": true,
  "actions": {...},  // Pickle serialized
  "long_running_tool_ids_json": null
}
```

### Example Data - V1 Schema

```json
{
  "id": "evt_abc123",
  "app_name": "my_app",
  "user_id": "user123",
  "session_id": "session456",
  "invocation_id": "inv_xyz789",
  "timestamp": "2024-01-15 10:30:15",
  "event_data": {
    "id": "evt_abc123",
    "invocation_id": "inv_xyz789",
    "author": "user",
    "content": {
      "role": "user",
      "parts": [{"text": "Hello!"}]
    },
    "actions": {...},
    "timestamp": 1705315215.123456,
    "usage_metadata": {...},
    "partial": false,
    "turn_complete": true
  }
}
```

### Notes

#### V0 Schema
- **Individual Columns**: Each event field is stored in its own column
- **Pickle Serialization**: `actions` field uses pickle (Python-specific)
- **More Columns**: 22 columns total (more complex schema)
- **Query Flexibility**: Can query individual fields directly (e.g., `WHERE author = 'user'`)
- **Legacy**: Used in ADK versions 1.19.0 to 1.21.0

#### V1 Schema
- **JSON Column**: Complete event stored as JSON in `event_data` column
- **Simpler Schema**: Only 7 columns (simpler structure)
- **JSON Serialization**: All data uses JSON (database-agnostic)
- **Modern**: Current default schema for new databases

#### Common Notes
- **Cascade Delete**: Events are automatically deleted when their parent session is deleted
- **Indexing**: Consider adding indexes on `session_id`, `timestamp`, and `invocation_id` for better query performance
- **Schema Detection**: ADK automatically detects and uses the appropriate schema version

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

## Checking Your Schema Version

### Method 1: Check Metadata Table (V1 Schema)

If you have V1 schema, check the metadata table:

```sql
SELECT * FROM adk_internal_metadata WHERE key = 'schema_version';
```

**Result**:
- `v1` = V1 schema (new, JSON-based)
- No rows = V0 schema (legacy, individual columns)

### Method 2: Check Events Table Structure

Query your database to see which columns exist:

**PostgreSQL**:
```sql
SELECT column_name, data_type 
FROM information_schema.columns 
WHERE table_name = 'events' 
ORDER BY ordinal_position;
```

**SQLite**:
```sql
PRAGMA table_info(events);
```

**MySQL**:
```sql
DESCRIBE events;
```

**V0 Schema Indicators**:
- Has `author` column
- Has `actions` column (BYTEA/BLOB)
- Has `content` column (separate from event_data)
- Has `usage_metadata` column
- Has `long_running_tool_ids_json` column
- **Total: ~22 columns**

**V1 Schema Indicators**:
- Has `event_data` column (JSON)
- No `author` column (it's inside event_data)
- No `actions` column (it's inside event_data)
- **Total: 7 columns**

### Method 3: Count Columns

```sql
-- PostgreSQL
SELECT COUNT(*) as column_count 
FROM information_schema.columns 
WHERE table_name = 'events';

-- If column_count ≈ 22 → V0 Schema
-- If column_count = 7 → V1 Schema
```

## Schema Migration

### V0 to V1 Migration

If you have an existing V0 schema database, ADK will:
1. Detect the schema version automatically
2. Continue using V0 schema (backward compatible)
3. New databases use V1 schema by default

**Important**: V0 and V1 schemas are **not automatically migrated**. ADK will use whichever schema version your database already has.

### Manual Migration

**Note**: Manual migration from V0 to V1 is complex and not officially supported. It requires:
1. Extracting data from individual columns
2. Reconstructing Event objects
3. Serializing to JSON
4. Creating new V1 tables
5. Migrating data

**Recommendation**: 
- If starting fresh, use V1 schema (default)
- If you have V0 schema, continue using it (it's fully supported)
- Only migrate if you have specific requirements

### Creating New Database with V1 Schema

To ensure V1 schema is used:

```python
from google.adk.sessions import DatabaseSessionService

# Create new database - will use V1 schema by default
session_service = DatabaseSessionService(
    db_url="postgresql+asyncpg://user:pass@localhost/new_database"
)

# The metadata table will be created with schema_version = 'v1'
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

### Query Events by Author (V0 Schema)
```sql
SELECT * FROM events 
WHERE app_name = 'my_app' 
  AND user_id = 'user123' 
  AND session_id = 'session456'
  AND author = 'user'
ORDER BY timestamp ASC;
```

### Query Events with Token Usage (V0 Schema)
```sql
SELECT 
    id,
    author,
    timestamp,
    usage_metadata->>'prompt_token_count' as input_tokens,
    usage_metadata->>'candidates_token_count' as output_tokens
FROM events 
WHERE app_name = 'my_app' 
  AND user_id = 'user123' 
  AND session_id = 'session456'
  AND usage_metadata IS NOT NULL
ORDER BY timestamp ASC;
```

### Query Events from Event Data (V1 Schema)
```sql
-- Extract author from event_data JSON
SELECT 
    id,
    event_data->>'author' as author,
    timestamp,
    event_data->'usage_metadata'->>'prompt_token_count' as input_tokens
FROM events 
WHERE app_name = 'my_app' 
  AND user_id = 'user123' 
  AND session_id = 'session456'
ORDER BY timestamp ASC;
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

## Complete V0 Events Table Field Reference

If you're using V0 schema, here are all 22 fields you'll see:

| # | Field Name | Type | Nullable | Description |
|---|------------|------|----------|-------------|
| 1 | `id` | VARCHAR(128) | NO | Event ID (UUID) |
| 2 | `app_name` | VARCHAR(128) | NO | Application name |
| 3 | `user_id` | VARCHAR(128) | NO | User identifier |
| 4 | `session_id` | VARCHAR(128) | NO | Session ID |
| 5 | `invocation_id` | VARCHAR(256) | YES | Invocation ID |
| 6 | `author` | VARCHAR(256) | YES | Author ('user' or agent name) |
| 7 | `actions` | BYTEA/BLOB | YES | EventActions (pickle serialized) |
| 8 | `long_running_tool_ids_json` | TEXT | YES | JSON array of tool IDs |
| 9 | `branch` | VARCHAR(256) | YES | Agent branch path |
| 10 | `timestamp` | TIMESTAMP | NO | Event timestamp |
| 11 | `content` | JSON/JSONB/TEXT | YES | Event content |
| 12 | `grounding_metadata` | JSON/JSONB/TEXT | YES | Grounding metadata |
| 13 | `custom_metadata` | JSON/JSONB/TEXT | YES | Custom metadata |
| 14 | `usage_metadata` | JSON/JSONB/TEXT | YES | Token usage metadata |
| 15 | `citation_metadata` | JSON/JSONB/TEXT | YES | Citation metadata |
| 16 | `partial` | BOOLEAN | YES | Partial content flag |
| 17 | `turn_complete` | BOOLEAN | YES | Turn complete flag |
| 18 | `error_code` | VARCHAR(256) | YES | Error code |
| 19 | `error_message` | TEXT | YES | Error message |
| 20 | `interrupted` | BOOLEAN | YES | Interrupted flag |
| 21 | `input_transcription` | JSON/JSONB/TEXT | YES | Input audio transcription |
| 22 | `output_transcription` | JSON/JSONB/TEXT | YES | Output audio transcription |

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

### Issue: Seeing V0 Schema Instead of V1

**Solution**: 
- V0 schema is used if your database was created with an older ADK version
- This is normal and expected - V0 schema is fully supported
- To use V1 schema, create a new database (V1 is default for new databases)
- ADK automatically detects and uses the correct schema version

---

## Summary

| Table | Purpose | Key Fields | Relationships |
|-------|---------|------------|---------------|
| `sessions` | Session metadata and state | `app_name`, `user_id`, `id`, `state` | One-to-many with `events` |
| `events` (V0) | Conversation events | `id`, `session_id`, `author`, `content`, `actions`, `usage_metadata`, etc. (22 fields) | Many-to-one with `sessions` |
| `events` (V1) | Conversation events | `id`, `session_id`, `event_data`, `timestamp` (7 fields) | Many-to-one with `sessions` |
| `app_states` | Application-level state | `app_name`, `state` | None |
| `user_states` | User-level state | `app_name`, `user_id`, `state` | None |
| `adk_internal_metadata` | Schema version info | `key`, `value` | None (V1 only) |

### Events Table Field Count

- **V0 Schema**: 22 fields (individual columns)
- **V1 Schema**: 7 fields (with JSON `event_data` containing all event information)

---

## Related Documentation

- [Sessions Package](07-Sessions-Package.md) - Complete session management guide
- [State Management](11-State-Management.md) - Understanding state scopes
- [DatabaseSessionService Event Filters](DatabaseSessionService-Event-Filters.md) - Event filtering
