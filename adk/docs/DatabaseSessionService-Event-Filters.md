# DatabaseSessionService: Event Filters and Programmatic Usage

This document describes the filters available when loading a session (and its events) via **DatabaseSessionService** (and other session services), how they behave, and how to use them programmatically with examples.

**Source:** Google ADK Python SDK (`google.adk.sessions`).  
**Config type:** `GetSessionConfig` in `sessions/base_session_service.py`.

---

## 1. GetSessionConfig: Available Filters

All session services that implement `BaseSessionService` accept an optional **`config`** argument of type **`GetSessionConfig`** when calling **`get_session()`**.

**Definition** (`sessions/base_session_service.py`):

```python
class GetSessionConfig(BaseModel):
  """The configuration of getting a session."""

  num_recent_events: Optional[int] = None
  """Limit the number of events returned to the N most recent. None = no limit."""

  after_timestamp: Optional[float] = None
  """Only include events with timestamp >= this value (Unix timestamp, seconds). None = no filter."""
```

| Field | Type | Default | Effect |
|-------|------|---------|--------|
| **num_recent_events** | `int \| None` | `None` | Return at most the **N most recent** events (by timestamp). No limit when `None`. |
| **after_timestamp** | `float \| None` | `None` | Include only events whose **timestamp >=** this value (Unix time, seconds). No filter when `None`. |

- You can use **one**, **both**, or **neither**.
- When **both** are set: first filter by `after_timestamp`, then take the top **num_recent_events** by timestamp (descending), then the service returns them in **chronological order** (oldest first) in `session.events`.

---

## 2. How Each Service Applies the Filters

### 2.1 DatabaseSessionService

**File:** `sessions/database_session_service.py`  
**Method:** `get_session(..., config: Optional[GetSessionConfig] = None)`

Behavior:

1. Load **StorageSession** by `(app_name, user_id, session_id)`.
2. Build a **StorageEvent** query:
   - Filter by `app_name`, `session_id`, `user_id`.
   - If **after_timestamp** is set: `StorageEvent.timestamp >= datetime.fromtimestamp(config.after_timestamp)`.
   - **Order:** `StorageEvent.timestamp.desc()` (newest first).
   - If **num_recent_events** is set: `.limit(config.num_recent_events)`.
3. Execute query → list of **StorageEvent** (newest first).
4. **Reverse** the list so that `session.events` is **chronological** (oldest first).
5. Merge app/user/session state and return `Session(state=merged_state, events=events)`.

So:

- **after_timestamp**: SQL/ORM filter `timestamp >= after_dt`; only events at or after that time.
- **num_recent_events**: SQL `LIMIT N` on the descending-ordered events; at most N most recent events (after the timestamp filter, if any).

### 2.2 InMemorySessionService

**File:** `sessions/in_memory_session_service.py`  
**Method:** `_get_session_impl(..., config: Optional[GetSessionConfig] = None)`

Behavior (on a **copy** of the stored session):

1. If **num_recent_events** is set:  
   `copied_session.events = copied_session.events[-config.num_recent_events:]`  
   (last N events; list is already chronological).
2. If **after_timestamp** is set:  
   Walk from the **end** of the list, find the last index `i` where `events[i].timestamp < config.after_timestamp`, then keep `events[i + 1:]` (events at or after that time).

So:

- **num_recent_events**: last N events.
- **after_timestamp**: drop events strictly before that time; keep events with `timestamp >= after_timestamp`.

### 2.3 VertexAiSessionService / SqliteSessionService

- **VertexAiSessionService** and **SqliteSessionService** also accept `GetSessionConfig` and apply **num_recent_events** and **after_timestamp** in a logically similar way (filter by time, then cap by count, then expose chronological `session.events`).

---

## 3. Programmatic Usage

The **Runner** does **not** pass `config` when it calls `session_service.get_session()`. So by default, every run loads the **full** event history for the session.

To apply filters you must:

1. Call **`session_service.get_session(..., config=GetSessionConfig(...))`** yourself, **or**
2. Use a custom wrapper (e.g. a subclass or a helper that fetches the session with config before starting a run).

You need to import:

```python
from google.adk.sessions import DatabaseSessionService  # or InMemorySessionService, etc.
from google.adk.sessions.base_session_service import GetSessionConfig
```

Then pass **`config`** into **`get_session`**:

```python
config = GetSessionConfig(
    num_recent_events=50,        # optional
    after_timestamp=1699000000.0 # optional, Unix time
)
session = await session_service.get_session(
    app_name="my_app",
    user_id="user123",
    session_id="session456",
    config=config,
)
# session.events is at most 50 events, each with timestamp >= 1699000000.0, in chronological order
```

---

## 4. Examples

### Example 1: Load only the last N events (e.g. for context window)

Use **num_recent_events** to cap history size (e.g. to fit a model context window).

```python
import asyncio
from google.adk.sessions import DatabaseSessionService
from google.adk.sessions.base_session_service import GetSessionConfig

async def main():
    session_service = DatabaseSessionService(
        db_url="sqlite+aiosqlite:///./sessions.db"
    )

    # Load session with only the 20 most recent events
    config = GetSessionConfig(num_recent_events=20)
    session = await session_service.get_session(
        app_name="my_app",
        user_id="user123",
        session_id="session456",
        config=config,
    )

    if session:
        print(f"Session {session.id}: {len(session.events)} events (capped at 20)")
        for e in session.events:
            print(f"  {e.timestamp}: {e.author}")
    await session_service.close()

asyncio.run(main())
```

### Example 2: Load only events after a given time

Use **after_timestamp** (Unix seconds) to load events from a certain time onward (e.g. “this week”).

```python
import asyncio
import time
from google.adk.sessions import DatabaseSessionService
from google.adk.sessions.base_session_service import GetSessionConfig

async def main():
    session_service = DatabaseSessionService(
        db_url="sqlite+aiosqlite:///./sessions.db"
    )

    # Events from the last hour (3600 seconds)
    one_hour_ago = time.time() - 3600
    config = GetSessionConfig(after_timestamp=one_hour_ago)

    session = await session_service.get_session(
        app_name="my_app",
        user_id="user123",
        session_id="session456",
        config=config,
    )

    if session:
        print(f"Session {session.id}: {len(session.events)} events since last hour")
    await session_service.close()

asyncio.run(main())
```

### Example 3: Combine both filters (recent events after a timestamp)

Use both **after_timestamp** and **num_recent_events**: only events at or after the timestamp, then at most N most recent, returned in chronological order.

```python
import asyncio
import time
from google.adk.sessions import DatabaseSessionService
from google.adk.sessions.base_session_service import GetSessionConfig

async def main():
    session_service = DatabaseSessionService(
        db_url="sqlite+aiosqlite:///./sessions.db"
    )

    # At most 30 most recent events, and only those from the last 24 hours
    one_day_ago = time.time() - (24 * 3600)
    config = GetSessionConfig(
        after_timestamp=one_day_ago,
        num_recent_events=30,
    )

    session = await session_service.get_session(
        app_name="my_app",
        user_id="user123",
        session_id="session456",
        config=config,
    )

    if session:
        print(f"Session {session.id}: up to 30 events since last 24h, got {len(session.events)}")
    await session_service.close()

asyncio.run(main())
```

### Example 4: Custom “run with truncated history” (without changing Runner)

Runner always calls `get_session(..., config=None)`. To run the agent with a **filtered** session you can either:

- Use a **custom session service** that wraps the real one and injects a default `GetSessionConfig`, or
- **Bypass Runner for the load step** and run with a pre-fetched session (if your setup supports injecting a session).

Below is a **wrapper session service** that always applies a config when delegating `get_session`:

```python
import asyncio
from typing import Optional

from google.adk.sessions import DatabaseSessionService, Session
from google.adk.sessions.base_session_service import (
    BaseSessionService,
    GetSessionConfig,
    ListSessionsResponse,
)
from google.adk.events.event import Event

class FilteredDatabaseSessionService(BaseSessionService):
    """Wraps DatabaseSessionService and applies GetSessionConfig on every get_session."""

    def __init__(
        self,
        db_url: str,
        *,
        num_recent_events: Optional[int] = None,
        after_timestamp: Optional[float] = None,
        **kwargs,
    ):
        self._inner = DatabaseSessionService(db_url, **kwargs)
        self._default_config = GetSessionConfig(
            num_recent_events=num_recent_events,
            after_timestamp=after_timestamp,
        )

    async def create_session(self, *, app_name: str, user_id: str, state=None, session_id=None) -> Session:
        return await self._inner.create_session(
            app_name=app_name, user_id=user_id, state=state, session_id=session_id
        )

    async def get_session(
        self,
        *,
        app_name: str,
        user_id: str,
        session_id: str,
        config: Optional[GetSessionConfig] = None,
    ) -> Optional[Session]:
        # Use provided config or the default (truncated) config
        effective_config = config if config is not None else self._default_config
        return await self._inner.get_session(
            app_name=app_name,
            user_id=user_id,
            session_id=session_id,
            config=effective_config,
        )

    async def list_sessions(self, *, app_name: str, user_id: Optional[str] = None) -> ListSessionsResponse:
        return await self._inner.list_sessions(app_name=app_name, user_id=user_id)

    async def delete_session(self, *, app_name: str, user_id: str, session_id: str) -> None:
        return await self._inner.delete_session(
            app_name=app_name, user_id=user_id, session_id=session_id
        )

    async def append_event(self, session: Session, event: Event) -> Event:
        return await self._inner.append_event(session=session, event=event)

    async def close(self):
        await self._inner.close()


async def main():
    # Runner will now always get sessions with at most 50 recent events
    session_service = FilteredDatabaseSessionService(
        "sqlite+aiosqlite:///./sessions.db",
        num_recent_events=50,
    )
    # Use session_service in Runner as usual; get_session will apply num_recent_events=50
    # ...
    await session_service.close()

asyncio.run(main())
```

### Example 5: InMemorySessionService with the same config

Filters work the same way for **InMemorySessionService**; only the backend changes.

```python
import asyncio
import time
from google.adk.sessions import InMemorySessionService
from google.adk.sessions.base_session_service import GetSessionConfig

async def main():
    session_service = InMemorySessionService()

    # Create and populate a session (e.g. via Runner)...
    session = await session_service.create_session(
        app_name="my_app", user_id="user1", session_id="s1"
    )

    # Later: load with only last 10 events
    config = GetSessionConfig(num_recent_events=10)
    loaded = await session_service.get_session(
        app_name="my_app",
        user_id="user1",
        session_id="s1",
        config=config,
    )
    if loaded:
        print(f"Loaded {len(loaded.events)} events (max 10)")
```

---

## 5. Summary Table

| Filter | Type | Effect (DatabaseSessionService) | Effect (InMemorySessionService) |
|--------|------|----------------------------------|----------------------------------|
| **num_recent_events** | `int \| None` | SQL `LIMIT N` after ordering by `timestamp DESC`; at most N most recent events (after any timestamp filter). | `events[-N:]` (last N events). |
| **after_timestamp** | `float \| None` | `WHERE timestamp >= datetime.fromtimestamp(after_timestamp)`. | Keep only events with `event.timestamp >= after_timestamp`. |
| **Both** | — | First filter by timestamp, then take top N by timestamp desc, then reverse to chronological. | Apply num_recent_events on full list, then drop events before after_timestamp (or equivalent logic). |
| **None** | — | Full event history. | Full event history. |

- **Event order in `session.events`:** Always **chronological** (oldest first) for all services.
- **Runner:** Does **not** pass `config`; to use filters you must call `get_session(..., config=GetSessionConfig(...))` yourself or use a wrapper like **Example 4**.

---

## 6. References (ADK source)

- **GetSessionConfig:** `google.adk.sessions.base_session_service.GetSessionConfig`
- **DatabaseSessionService.get_session:** `google.adk.sessions.database_session_service.DatabaseSessionService.get_session`
- **InMemorySessionService._get_session_impl:** `google.adk.sessions.in_memory_session_service.InMemorySessionService._get_session_impl`

All session services that implement `BaseSessionService.get_session(..., config=...)` accept `GetSessionConfig`; DatabaseSessionService applies the filters at the SQL/ORM layer (timestamp filter + order + limit), then returns events in chronological order.
