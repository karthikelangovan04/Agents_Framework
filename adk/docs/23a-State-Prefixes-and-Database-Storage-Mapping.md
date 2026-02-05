# State Prefixes and Database Storage Mapping in ADK

**File Path**: `docs/23a-State-Prefixes-and-Database-Storage-Mapping.md`  
**Related Docs**: 
- [State Management](11-State-Management.md)
- [State Updates Guide](23-State-Updates-in-ADK-Web-and-Programmatically.md)
- [DatabaseSessionService Schema](21-DatabaseSessionService-Schema.md)

## Overview

This document explains the relationship between state prefixes (`app:`, `user:`) used in code and how state is actually stored in `DatabaseSessionService` tables (`app_states`, `user_states`). It clarifies why you see empty state `{}` in database tables and how state updates work programmatically.

---

## Table of Contents

1. [Understanding State Prefixes vs Database Columns](#understanding-state-prefixes-vs-database-columns)
2. [How State is Stored in Database Tables](#how-state-is-stored-in-database-tables)
3. [Why State Shows as `{}` (Empty)](#why-state-shows-as-empty)
4. [How State Updates Work](#how-state-updates-work)
5. [Real Database Examples](#real-database-examples)
6. [Predefining State in Database](#predefining-state-in-database)
7. [Programmatic State Updates](#programmatic-state-updates)
8. [Best Practices](#best-practices)

---

## Understanding State Prefixes vs Database Columns

### Key Concept: Prefixes are NOT Database Columns

**Important**: The prefixes `app:` and `user:` are **NOT** database column names. They are **key prefixes** used within the `state` JSON column to distinguish state scopes.

### How It Works

1. **In Code**: You use prefixes like `State.APP_PREFIX + "tax_rate"` which becomes `"app:tax_rate"`
2. **In Database**: The `app_name` and `user_id` are **separate columns** that identify which row to store/retrieve state from
3. **State Storage**: The actual state values (with prefixes) are stored in the `state` JSON column

### Database Schema Structure

```sql
-- app_states table
CREATE TABLE app_states (
    app_name VARCHAR(128) PRIMARY KEY,  -- ← This is the app identifier column
    state JSONB DEFAULT '{}',           -- ← State JSON stored here (with "app:" prefixes)
    update_time TIMESTAMP
);

-- user_states table  
CREATE TABLE user_states (
    app_name VARCHAR(128),              -- ← App identifier column
    user_id VARCHAR(128),                -- ← User identifier column
    state JSONB DEFAULT '{}',            -- ← State JSON stored here (with "user:" prefixes)
    update_time TIMESTAMP,
    PRIMARY KEY (app_name, user_id)
);
```

### Mapping Example

```python
# In your code:
state[State.APP_PREFIX + "tax_rate"] = 0.08
state[State.USER_PREFIX + "preferred_language"] = "en"

# In database app_states table:
# Row: app_name="my_app", state={"app:tax_rate": 0.08}

# In database user_states table:
# Row: app_name="my_app", user_id="user_001", state={"user:preferred_language": "en"}
```

**Key Points**:
- `app_name` column = identifies which application (e.g., `"mcp_tool_agent_app"`)
- `user_id` column = identifies which user (e.g., `"user_001"`)
- `state` JSON column = contains the actual state keys with prefixes (e.g., `{"app:tax_rate": 0.08}`)

---

## How State is Stored in Database Tables

### State Storage Flow

When you update state with prefixes, ADK automatically:

1. **Extracts state by prefix** using `extract_state_delta()` function
2. **Routes to appropriate table** based on prefix:
   - Keys with `app:` prefix → `app_states` table
   - Keys with `user:` prefix → `user_states` table
   - Keys without prefix → `sessions.state` column
3. **Stores in correct row** based on `app_name` and `user_id` columns

### Example: State Update Flow

```python
# Code: Update state with different scopes
state_delta = {
    "message_count": 5,                          # Session-level (no prefix)
    State.APP_PREFIX + "tax_rate": 0.08,         # App-level (app: prefix)
    State.USER_PREFIX + "preferred_language": "en"  # User-level (user: prefix)
}

# ADK automatically splits and routes:
# 1. Session-level → sessions.state column
#    WHERE app_name="my_app" AND user_id="user_001" AND id="session_123"
#    UPDATE sessions SET state = {"message_count": 5}
#
# 2. App-level → app_states table
#    WHERE app_name="my_app"
#    UPDATE app_states SET state = {"app:tax_rate": 0.08}
#
# 3. User-level → user_states table
#    WHERE app_name="my_app" AND user_id="user_001"
#    UPDATE user_states SET state = {"user:preferred_language": "en"}
```

### State Merging on Retrieval

When you retrieve a session, ADK automatically merges state from all three sources:

```python
session = await session_service.get_session(
    app_name="my_app",
    user_id="user_001",
    session_id="session_123"
)

# Behind the scenes:
# 1. Query sessions table → session-level state: {"message_count": 5}
# 2. Query app_states table → app-level state: {"app:tax_rate": 0.08}
# 3. Query user_states table → user-level state: {"user:preferred_language": "en"}
# 4. Merge all three → session.state = {
#     "message_count": 5,
#     "app:tax_rate": 0.08,
#     "user:preferred_language": "en"
# }
```

---

## Why State Shows as `{}` (Empty)

### Common Reasons for Empty State

#### 1. **State Not Initialized**

When a session is created without initial state, or when `app_states`/`user_states` rows are created automatically, they start with empty state:

```python
# Creating session without state
session = await session_service.create_session(
    app_name="my_app",
    user_id="user_001",
    session_id="session_123"
    # No state parameter → defaults to {}
)

# Result in database:
# app_states: app_name="my_app", state={}
# user_states: app_name="my_app", user_id="user_001", state={}
```

#### 2. **State Created But Never Updated**

Rows in `app_states` and `user_states` are created automatically when:
- First session is created for an `app_name`
- First session is created for a `(app_name, user_id)` combination

But if state is never updated with `app:` or `user:` prefixes, the `state` column remains `{}`.

#### 3. **State Updates Only Happen When Using Prefixes**

State only populates in `app_states`/`user_states` tables when you explicitly use prefixes:

```python
# ❌ This does NOT update app_states or user_states
state_delta = {
    "message_count": 5,  # No prefix → goes to sessions.state only
    "tax_rate": 0.08     # No prefix → goes to sessions.state only
}

# ✅ This DOES update app_states and user_states
state_delta = {
    State.APP_PREFIX + "tax_rate": 0.08,           # Updates app_states
    State.USER_PREFIX + "preferred_language": "en"  # Updates user_states
}
```

### Your Database Observation

Based on your database query results:

```sql
-- app_states table (mostly empty)
app_name                          | state | update_time
postgres_agent_app                | {}    | 2026-01-18 10:51:19
google_search_postgres_agent_app  | {}    | 2026-01-18 13:44:17
simple_tool_agent_app             | {}    | 2026-01-18 14:14:25
mcp_tool_agent_app                | {}    | 2026-01-26 15:05:24

-- user_states table (mostly empty, one populated)
app_name                    | user_id        | state                                    | update_time
postgres_agent_app          | user_001       | {}                                       | 2026-01-18 10:51:19
mcp_tool_agent_app          | user_001       | {"mcp_servers": [...]}                  | 2026-01-26 15:15:05
```

**Analysis**:
- Most rows have `state={}` because state was never updated with `app:` or `user:` prefixes
- The `mcp_tool_agent_app` / `user_001` row has populated state because MCP configuration was stored using `user:` prefix (likely `user:mcp_servers`)

---

## How State Updates Work

### Automatic State Extraction and Routing

ADK uses the `extract_state_delta()` function to split state by prefix:

```python
from google.adk.sessions._session_util import extract_state_delta
from google.adk.sessions.state import State

state_delta = {
    "message_count": 5,                          # No prefix
    State.APP_PREFIX + "tax_rate": 0.08,         # app: prefix
    State.USER_PREFIX + "preferred_language": "en"  # user: prefix
}

# Extract and split
result = extract_state_delta(state_delta)
# Returns:
# {
#     "app": {"tax_rate": 0.08},           # Prefix removed
#     "user": {"preferred_language": "en"}, # Prefix removed
#     "session": {"message_count": 5}      # No prefix
# }
```

### Database Update Process

When `append_event()` is called with `state_delta`:

```python
# 1. Event is created with state_delta
event = Event(
    invocation_id="inv_001",
    author="user",
    actions={"state_delta": state_delta}
)

# 2. append_event() extracts state by prefix
app_delta, user_delta, session_delta = extract_state_delta(state_delta)

# 3. Updates appropriate tables
# app_states table
if app_delta:
    # Merge with existing state
    existing_app_state = get_app_state(app_name)
    updated_app_state = {**existing_app_state, **{f"app:{k}": v for k, v in app_delta.items()}}
    UPDATE app_states SET state = updated_app_state WHERE app_name = app_name

# user_states table
if user_delta:
    existing_user_state = get_user_state(app_name, user_id)
    updated_user_state = {**existing_user_state, **{f"user:{k}": v for k, v in user_delta.items()}}
    UPDATE user_states SET state = updated_user_state 
    WHERE app_name = app_name AND user_id = user_id

# sessions table
if session_delta:
    UPDATE sessions SET state = merge(sessions.state, session_delta)
    WHERE app_name = app_name AND user_id = user_id AND id = session_id
```

### Example: MCP Configuration Update

Based on your database, here's how the `mcp_servers` state was likely updated:

```python
# Code that updated user_states for mcp_tool_agent_app / user_001
from google.adk.sessions.state import State

# Update user-level state with MCP configuration
state_delta = {
    State.USER_PREFIX + "mcp_servers": [
        {
            "name": "calculator",
            "type": "stdio",
            "command": "python",
            "args": ["-m", "postgres_agent.mcp_servers.calculator"],
            "enabled": True,
            # ... other config
        }
    ]
}

# When event is appended:
# 1. extract_state_delta() splits it:
#    user_delta = {"mcp_servers": [...]}
#
# 2. Updates user_states table:
#    UPDATE user_states 
#    SET state = jsonb_set(
#        COALESCE(state, '{}'::jsonb),
#        '{user:mcp_servers}',
#        '[...]'::jsonb
#    )
#    WHERE app_name = 'mcp_tool_agent_app' AND user_id = 'user_001'
#
# 3. Result in database:
#    state = {"user:mcp_servers": [...]}
```

---

## Real Database Examples

### Example 1: Empty State Tables

**Scenario**: Most of your `app_states` and `user_states` rows show `{}`

**Why**: State was never updated with `app:` or `user:` prefixes. Only session-level state (no prefix) was used.

```python
# Code that creates empty state
async for event in runner.run_async(
    user_id="user_001",
    session_id="session_123",
    new_message=types.UserContent(parts=[types.Part(text="Hello")]),
    state_delta={
        "message_count": 1,  # No prefix → only updates sessions.state
        "conversation_topic": "greeting"  # No prefix → only updates sessions.state
    }
)

# Result:
# - sessions.state = {"message_count": 1, "conversation_topic": "greeting"}
# - app_states.state = {}  (not updated)
# - user_states.state = {}  (not updated)
```

### Example 2: Populated User State

**Scenario**: `mcp_tool_agent_app` / `user_001` has populated state

**Why**: MCP configuration was stored using `user:` prefix

```python
# Code that populated user_states
from google.adk.sessions.state import State

async for event in runner.run_async(
    user_id="user_001",
    session_id="session_123",
    new_message=types.UserContent(parts=[types.Part(text="Configure MCP")]),
    state_delta={
        State.USER_PREFIX + "mcp_servers": [
            {
                "name": "calculator",
                "type": "stdio",
                "command": "python",
                "args": ["-m", "postgres_agent.mcp_servers.calculator"],
                "enabled": True
            }
        ]
    }
)

# Result:
# - sessions.state = {}  (no session-level updates)
# - app_states.state = {}  (no app-level updates)
# - user_states.state = {"user:mcp_servers": [...]}  (updated!)
```

### Example 3: Populating App-Level State

**Scenario**: You want to set application-wide configuration

```python
from google.adk.sessions.state import State

async for event in runner.run_async(
    user_id="user_001",
    session_id="session_123",
    new_message=types.UserContent(parts=[types.Part(text="Set app config")]),
    state_delta={
        State.APP_PREFIX + "version": "1.0.0",
        State.APP_PREFIX + "tax_rate": 0.08,
        State.APP_PREFIX + "feature_enabled": True
    }
)

# Result in database:
# app_states table:
#   app_name = "my_app"
#   state = {
#     "app:version": "1.0.0",
#     "app:tax_rate": 0.08,
#     "app:feature_enabled": True
#   }
```

---

## Predefining State in Database

### Method 1: Direct SQL Insert

You can predefine state directly in the database:

```sql
-- Predefine app-level state
INSERT INTO app_states (app_name, state, update_time)
VALUES (
    'my_app',
    '{"app:version": "1.0.0", "app:tax_rate": 0.08}'::jsonb,
    NOW()
)
ON CONFLICT (app_name) 
DO UPDATE SET 
    state = app_states.state || EXCLUDED.state,
    update_time = NOW();

-- Predefine user-level state
INSERT INTO user_states (app_name, user_id, state, update_time)
VALUES (
    'my_app',
    'user_001',
    '{"user:preferred_language": "en", "user:loyalty_points": 1000}'::jsonb,
    NOW()
)
ON CONFLICT (app_name, user_id)
DO UPDATE SET
    state = user_states.state || EXCLUDED.state,
    update_time = NOW();
```

### Method 2: Initialize on Session Creation

```python
from google.adk.sessions import DatabaseSessionService
from google.adk.sessions.state import State

session_service = DatabaseSessionService(db_url="...")

# Create session with initial state
session = await session_service.create_session(
    app_name="my_app",
    user_id="user_001",
    session_id="session_123",
    state={
        # Session-level
        "message_count": 0,
        
        # User-level (will create/update user_states row)
        State.USER_PREFIX + "preferred_language": "en",
        State.USER_PREFIX + "loyalty_points": 1000,
        
        # App-level (will create/update app_states row)
        State.APP_PREFIX + "version": "1.0.0",
        State.APP_PREFIX + "tax_rate": 0.08
    }
)

# Result:
# - app_states: app_name="my_app", state={"app:version": "1.0.0", "app:tax_rate": 0.08}
# - user_states: app_name="my_app", user_id="user_001", state={"user:preferred_language": "en", "user:loyalty_points": 1000}
# - sessions: state={"message_count": 0}
```

### Method 3: Update Existing Rows

```python
# Update app-level state programmatically
async for event in runner.run_async(
    user_id="user_001",
    session_id="session_123",
    new_message=types.UserContent(parts=[types.Part(text="Update config")]),
    state_delta={
        State.APP_PREFIX + "version": "1.1.0",  # Updates app_states
        State.APP_PREFIX + "new_feature": True   # Adds to app_states
    }
)

# Updates existing app_states row:
# state = {"app:version": "1.1.0", "app:tax_rate": 0.08, "app:new_feature": True}
```

---

## Programmatic State Updates

### Using REST API (PATCH Endpoint)

```python
import httpx
import asyncio

async def update_app_state():
    """Update app-level state via REST API."""
    async with httpx.AsyncClient() as client:
        response = await client.patch(
            "http://localhost:8000/apps/my_app/users/user_001/sessions/session_123",
            json={
                "state_delta": {
                    State.APP_PREFIX + "version": "1.0.0",
                    State.APP_PREFIX + "tax_rate": 0.08
                }
            }
        )
        print(response.json())

asyncio.run(update_app_state())
```

### Using Session Service Directly

```python
from google.adk.sessions import DatabaseSessionService
from google.adk.sessions.state import State
from google.adk.events import Event

async def update_state_directly():
    session_service = DatabaseSessionService(db_url="...")
    
    # Create event with state_delta
    event = Event(
        invocation_id="inv_001",
        author="system",
        actions={
            "state_delta": {
                State.APP_PREFIX + "version": "1.0.0",
                State.USER_PREFIX + "preferred_language": "en"
            }
        }
    )
    
    # Append event (automatically updates app_states and user_states)
    await session_service.append_event(
        app_name="my_app",
        user_id="user_001",
        session_id="session_123",
        event=event
    )

asyncio.run(update_state_directly())
```

### Using Callbacks to Update State

```python
from google.adk.agents import LlmAgent
from google.adk.agents.callback_context import CallbackContext
from google.adk.models import LlmRequest
from google.adk.sessions.state import State
from typing import Optional

def before_model_update_state(
    callback_context: CallbackContext,
    llm_request: LlmRequest
) -> Optional[LlmResponse]:
    """Update state in callback."""
    session = callback_context.session
    state = session.state
    
    # Update user-level state
    state[State.USER_PREFIX + "last_model_call"] = "2024-01-15"
    state[State.USER_PREFIX + "total_calls"] = state.get(State.USER_PREFIX + "total_calls", 0) + 1
    
    # Update app-level state
    state[State.APP_PREFIX + "total_model_calls"] = state.get(State.APP_PREFIX + "total_model_calls", 0) + 1
    
    # State will be persisted when event is appended
    return None

agent = LlmAgent(
    name="StateTrackingAgent",
    model="gemini-2.0-flash",
    before_model_callback=before_model_update_state
)
```

---

## Best Practices

### 1. Always Use Prefixes for App/User State

```python
# ✅ Good: Uses prefixes
state_delta = {
    State.APP_PREFIX + "version": "1.0.0",
    State.USER_PREFIX + "preferred_language": "en"
}

# ❌ Bad: No prefixes (only updates sessions.state)
state_delta = {
    "version": "1.0.0",  # Goes to sessions.state, not app_states
    "preferred_language": "en"  # Goes to sessions.state, not user_states
}
```

### 2. Initialize State on First Use

```python
# Initialize app-level state when app starts
async def initialize_app_state(session_service, app_name):
    session = await session_service.create_session(
        app_name=app_name,
        user_id="system",
        session_id="init",
        state={
            State.APP_PREFIX + "version": "1.0.0",
            State.APP_PREFIX + "initialized": True
        }
    )
```

### 3. Check State Before Using

```python
# Always check if state exists
app_version = session.state.get(State.APP_PREFIX + "version", "1.0.0")
user_lang = session.state.get(State.USER_PREFIX + "preferred_language", "en")
```

### 4. Use Consistent Naming

```python
# ✅ Good: Consistent naming
State.APP_PREFIX + "tax_rate"
State.APP_PREFIX + "api_version"
State.USER_PREFIX + "preferred_language"
State.USER_PREFIX + "loyalty_points"

# ❌ Bad: Inconsistent
State.APP_PREFIX + "taxRate"  # camelCase
State.APP_PREFIX + "api-version"  # kebab-case
```

### 5. Understand State Merging

Remember that state is automatically merged when retrieving sessions:

```python
# When you get a session:
session = await session_service.get_session(
    app_name="my_app",
    user_id="user_001",
    session_id="session_123"
)

# session.state contains:
# - Session-level state from sessions.state
# - User-level state from user_states.state (for user_001)
# - App-level state from app_states.state (for my_app)
# All merged into one dictionary
```

---

## Summary

### Key Takeaways

1. **Prefixes are NOT database columns**: `app:` and `user:` are key prefixes, not column names
2. **Database columns**: `app_name` and `user_id` are separate columns that identify rows
3. **State storage**: Actual state (with prefixes) is stored in the `state` JSON column
4. **Empty state `{}`**: Appears when state was never updated with `app:` or `user:` prefixes
5. **State routing**: ADK automatically routes state to correct tables based on prefixes
6. **State merging**: State is automatically merged from all three sources when retrieving sessions

### Database Table Mapping

| Code Prefix | Database Table | Identifying Columns | State Column |
|-------------|----------------|---------------------|--------------|
| `app:` | `app_states` | `app_name` | `state` (JSON with `app:` keys) |
| `user:` | `user_states` | `app_name`, `user_id` | `state` (JSON with `user:` keys) |
| (no prefix) | `sessions` | `app_name`, `user_id`, `id` | `state` (JSON without prefixes) |

### Example Flow

```python
# 1. Code: Update state with prefixes
state_delta = {
    State.APP_PREFIX + "tax_rate": 0.08,
    State.USER_PREFIX + "language": "en"
}

# 2. ADK extracts and routes:
#    app_delta = {"tax_rate": 0.08} → app_states table
#    user_delta = {"language": "en"} → user_states table

# 3. Database updates:
#    app_states: app_name="my_app", state={"app:tax_rate": 0.08}
#    user_states: app_name="my_app", user_id="user_001", state={"user:language": "en"}

# 4. On retrieval: State is merged
#    session.state = {"app:tax_rate": 0.08, "user:language": "en"}
```

---

## Related Documentation

- [State Management](11-State-Management.md) - Comprehensive state management guide
- [State Updates Guide](23-State-Updates-in-ADK-Web-and-Programmatically.md) - How to update state
- [DatabaseSessionService Schema](21-DatabaseSessionService-Schema.md) - Complete database schema reference
- [Sessions Package](07-Sessions-Package.md) - Session management details

---

**Last Updated**: 2025-02-05  
**Related**: State Management, Database Schema, State Updates
