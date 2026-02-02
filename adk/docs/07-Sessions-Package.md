# Google ADK Sessions Package Documentation

**File Path**: `docs/07-Sessions-Package.md`  
**Package**: `google.adk.sessions`

## Overview

The `google.adk.sessions` package provides session management for agents, allowing them to maintain context across multiple interactions. Sessions enable agents to remember previous conversations and maintain state.

## Key Classes

### Session

Represents a conversation session with an agent.

### BaseSessionService

Abstract base class for session services.

### InMemorySessionService

In-memory session service (for development/testing).

### VertexAiSessionService

Vertex AI-based session service (for production).

### DatabaseSessionService

A session service that uses SQLAlchemy-compatible databases for storage. Supports any database that SQLAlchemy supports, including SQLite, PostgreSQL, MySQL, Cloud Spanner, AlloyDB, and more.

**Requirements**: `sqlalchemy>=2.0` must be installed.

## Session API Usage

Sessions are created and managed through the **session service**, not through the `Session` class directly. The `Session` class is a data model that represents session state.

### Creating Sessions

```python
# Create a session using the session service
session = await session_service.create_session(
    app_name="my_app",      # Application name (required)
    user_id="user123",       # User identifier (required)
    session_id="session456", # Session ID (optional, auto-generated if not provided)
    state=None               # Initial state (optional)
)
```

### Retrieving Sessions

```python
# Get an existing session
session = await session_service.get_session(
    app_name="my_app",
    user_id="user123",
    session_id="session456"
)

# Returns None if session doesn't exist
if session:
    print(f"Session found: {session.id}")
```

### Get or Create Pattern

```python
# Get existing session or create a new one
session = await session_service.get_session(
    app_name="my_app",
    user_id="user123",
    session_id="session456"
)

if not session:
    session = await session_service.create_session(
        app_name="my_app",
        user_id="user123",
        session_id="session456"
    )
```

### Important Notes

- **Session is a data model**: The `Session` class is a Pydantic model, not a service class
- **No `Session.create()` method**: Use `session_service.create_session()` instead
- **No `Session.save()` method**: Sessions are automatically persisted when events are appended
- **All methods are async**: Use `await` when calling session service methods
- **Required parameters**: `app_name` and `user_id` are always required

## Example 1: Basic Session Usage

Create an agent with session management:

```python
import asyncio
from google.adk import Agent
from google.adk.sessions import InMemorySessionService
from google.adk.runners import Runner

# Create session service
session_service = InMemorySessionService()

# Create agent
agent = Agent(
    name="session_agent",
    description="An agent with session management",
    model="gemini-1.5-flash",
    instruction="You are a helpful assistant that remembers our conversation."
)

# Create runner with session service
runner = Runner(
    app_name="session_app",
    agent=agent,
    session_service=session_service
)

async def main():
    from google.genai import types
    
    # Create session
    session = await session_service.create_session(
        app_name="session_app",
        user_id="user123",
        session_id="session456"
    )
    
    # First interaction
    async for event in runner.run_async(
        user_id="user123",
        session_id=session.id,
        new_message=types.UserContent(parts=[types.Part(text="My name is Alice")])
    ):
        if event.content and event.content.parts:
            for part in event.content.parts:
                if part.text:
                    print(part.text)
    
    # Second interaction - agent remembers
    async for event in runner.run_async(
        user_id="user123",
        session_id=session.id,
        new_message=types.UserContent(parts=[types.Part(text="What's my name?")])
    ):
        if event.content and event.content.parts:
            for part in event.content.parts:
                if part.text:
                    print(part.text)

asyncio.run(main())
```

**Runnable Session:**

Save as `examples/session_agent.py`:

```python
#!/usr/bin/env python3
"""Agent with session management."""

import asyncio
from google.adk import Agent
from google.adk.sessions import InMemorySessionService
from google.adk.runners import Runner

async def main():
    # Create session service
    session_service = InMemorySessionService()
    
    # Create agent
    agent = Agent(
        name="session_agent",
        description="An agent that remembers conversations",
        model="gemini-1.5-flash",
        instruction="You are a helpful assistant that remembers our conversation."
    )
    
    # Create runner
    runner = Runner(
        app_name="session_app",
        agent=agent,
        session_service=session_service
    )
    
    # Create session
    session = await session_service.create_session(
        app_name="session_app",
        user_id="user123",
        session_id="session456"
    )
    print(f"Session created: {session.id}\n")
    
    from google.genai import types
    
    print("Session Agent: Hello! I'll remember our conversation.")
    print("Type 'quit' to exit.\n")
    
    while True:
        user_input = input("You: ")
        if user_input.lower() == 'quit':
            break
        
        print("\nAgent: ", end="", flush=True)
        async for event in runner.run_async(
            user_id="user123",
            session_id=session.id,
            new_message=types.UserContent(parts=[types.Part(text=user_input)])
        ):
            if event.content and event.content.parts:
                for part in event.content.parts:
                    if part.text:
                        print(part.text, end="", flush=True)
        print("\n")

if __name__ == "__main__":
    asyncio.run(main())
```

## Example 2: Vertex AI Session Service

Use Vertex AI for persistent session storage:

```python
import asyncio
from google.adk.sessions import VertexAiSessionService
from google.adk import Agent
from google.adk.runners import Runner

# Create Vertex AI session service
session_service = VertexAiSessionService(
    project_id="your-project-id",
    location="us-central1"
)

# Create agent
agent = Agent(
    name="persistent_agent",
    model="gemini-1.5-flash",
    instruction="You are a helpful assistant."
)

# Create runner
runner = Runner(
    app_name="vertex_app",
    agent=agent,
    session_service=session_service
)

async def main():
    from google.genai import types
    
    # Create session
    session = await session_service.create_session(
        app_name="vertex_app",
        user_id="user123",
        session_id="session456"
    )
    
    # Use session
    async for event in runner.run_async(
        user_id="user123",
        session_id=session.id,
        new_message=types.UserContent(parts=[types.Part(text="Hello")])
    ):
        if event.content and event.content.parts:
            for part in event.content.parts:
                if part.text:
                    print(part.text)

asyncio.run(main())
```

## Example 3: DatabaseSessionService - SQLite

Use SQLite for local persistent session storage:

```python
#!/usr/bin/env python3
"""Agent with SQLite session storage."""

import asyncio
from google.adk import Agent
from google.adk.sessions import DatabaseSessionService, Session
from google.adk.runners import Runner
from google.genai import types

async def main():
    # Create SQLite session service
    # SQLite file will be created at ./sessions.db
    session_service = DatabaseSessionService(
        db_url="sqlite+aiosqlite:///./sessions.db"
    )
    
    # Create agent
    agent = Agent(
        name="sqlite_agent",
        model="gemini-1.5-flash",
        instruction="You are a helpful assistant with persistent storage."
    )
    
    # Create runner
    runner = Runner(
        app_name="sqlite_app",
        agent=agent,
        session_service=session_service
    )
    
    # Create session
    session = await session_service.create_session(
        app_name="sqlite_app",
        user_id="user123",
        session_id="session456"
    )
    
    print(f"Session created: {session.id}")
    print("Type 'quit' to exit.\n")
    
    while True:
        user_input = input("You: ")
        if user_input.lower() == 'quit':
            break
        
        print("\nAgent: ", end="", flush=True)
        async for event in runner.run_async(
            user_id="user123",
            session_id="session456",
            new_message=types.UserContent(parts=[types.Part(text=user_input)])
        ):
            if event.content and event.content.parts:
                for part in event.content.parts:
                    if part.text:
                        print(part.text, end="", flush=True)
        print("\n")
    
    # Clean up
    await session_service.close()

if __name__ == "__main__":
    asyncio.run(main())
```

**SQLite URL Formats**:
- `sqlite+aiosqlite:///./sessions.db` - File-based SQLite
- `sqlite+aiosqlite:///:memory:` - In-memory SQLite (temporary)
- `sqlite:///./sessions.db` - Synchronous SQLite (not recommended for async)

## Example 4: DatabaseSessionService - PostgreSQL

Use PostgreSQL for production session storage:

```python
#!/usr/bin/env python3
"""Agent with PostgreSQL session storage."""

import asyncio
from google.adk import Agent
from google.adk.sessions import DatabaseSessionService
from google.adk.runners import Runner
from google.genai import types

async def main():
    # Create PostgreSQL session service
    # Install: pip install asyncpg
    session_service = DatabaseSessionService(
        db_url="postgresql+asyncpg://user:password@localhost:5432/adk_sessions"
    )
    
    # Alternative with connection pooling
    session_service = DatabaseSessionService(
        db_url="postgresql+asyncpg://user:password@localhost:5432/adk_sessions",
        pool_size=10,
        max_overflow=20
    )
    
    agent = Agent(
        name="postgres_agent",
        model="gemini-1.5-flash",
        instruction="You are a helpful assistant."
    )
    
    runner = Runner(
        app_name="postgres_app",
        agent=agent,
        session_service=session_service
    )
    
    # Create session
    session = await session_service.create_session(
        app_name="postgres_app",
        user_id="user123",
        session_id="session456"
    )
    
    # Use session
    async for event in runner.run_async(
        user_id="user123",
        session_id="session456",
        new_message=types.UserContent(parts=[types.Part(text="Hello!")])
    ):
        if event.content:
            print(event.content)
    
    await session_service.close()

if __name__ == "__main__":
    asyncio.run(main())
```

**PostgreSQL URL Formats**:
- `postgresql+asyncpg://user:password@host:port/database` - Using asyncpg (recommended)
- `postgresql+psycopg://user:password@host:port/database` - Using psycopg3
- `postgresql://user:password@host:port/database` - Default (may be synchronous)

**Required Package**: `pip install asyncpg` or `pip install psycopg[binary]`

## Example 5: DatabaseSessionService - MySQL

Use MySQL for session storage:

```python
#!/usr/bin/env python3
"""Agent with MySQL session storage."""

import asyncio
from google.adk import Agent
from google.adk.sessions import DatabaseSessionService
from google.adk.runners import Runner
from google.genai import types

async def main():
    # Create MySQL session service
    # Install: pip install aiomysql
    session_service = DatabaseSessionService(
        db_url="mysql+aiomysql://user:password@localhost:3306/adk_sessions"
    )
    
    agent = Agent(
        name="mysql_agent",
        model="gemini-1.5-flash",
        instruction="You are a helpful assistant."
    )
    
    runner = Runner(
        app_name="mysql_app",
        agent=agent,
        session_service=session_service
    )
    
    # Create and use session
    session = await session_service.create_session(
        app_name="mysql_app",
        user_id="user123",
        session_id="session456"
    )
    
    async for event in runner.run_async(
        user_id="user123",
        session_id="session456",
        new_message=types.UserContent(parts=[types.Part(text="Hello!")])
    ):
        if event.content:
            print(event.content)
    
    await session_service.close()

if __name__ == "__main__":
    asyncio.run(main())
```

**MySQL URL Formats**:
- `mysql+aiomysql://user:password@host:port/database` - Using aiomysql (recommended)
- `mysql+pymysql://user:password@host:port/database` - Using PyMySQL

**Required Package**: `pip install aiomysql` or `pip install pymysql`

## Example 6: DatabaseSessionService - Cloud Spanner

Use Google Cloud Spanner for scalable session storage:

```python
#!/usr/bin/env python3
"""Agent with Cloud Spanner session storage."""

import asyncio
from google.adk import Agent
from google.adk.sessions import DatabaseSessionService
from google.adk.runners import Runner
from google.genai import types

async def main():
    # Create Cloud Spanner session service
    # Install: pip install sqlalchemy-spanner
    # Format: spanner+spanner://projects/{project}/instances/{instance}/databases/{database}
    session_service = DatabaseSessionService(
        db_url="spanner+spanner://projects/my-project/instances/my-instance/databases/my-database"
    )
    
    agent = Agent(
        name="spanner_agent",
        model="gemini-1.5-flash",
        instruction="You are a helpful assistant."
    )
    
    runner = Runner(
        app_name="spanner_app",
        agent=agent,
        session_service=session_service
    )
    
    # Create and use session
    session = await session_service.create_session(
        app_name="spanner_app",
        user_id="user123",
        session_id="session456"
    )
    
    async for event in runner.run_async(
        user_id="user123",
        session_id="session456",
        new_message=types.UserContent(parts=[types.Part(text="Hello!")])
    ):
        if event.content:
            print(event.content)
    
    await session_service.close()

if __name__ == "__main__":
    asyncio.run(main())
```

**Cloud Spanner URL Format**:
- `spanner+spanner://projects/{project}/instances/{instance}/databases/{database}`

**Required Package**: `pip install sqlalchemy-spanner`

**Authentication**: Uses Google Cloud Application Default Credentials (ADC)

## Example 7: DatabaseSessionService - AlloyDB (PostgreSQL-compatible)

Use Google Cloud AlloyDB (PostgreSQL-compatible) for session storage:

```python
#!/usr/bin/env python3
"""Agent with AlloyDB session storage."""

import asyncio
from google.adk import Agent
from google.adk.sessions import DatabaseSessionService
from google.adk.runners import Runner
from google.genai import types

async def main():
    # Create AlloyDB session service
    # AlloyDB is PostgreSQL-compatible, so use PostgreSQL driver
    # Install: pip install asyncpg
    session_service = DatabaseSessionService(
        db_url="postgresql+asyncpg://user:password@alloydb-instance-ip:5432/database"
    )
    
    agent = Agent(
        name="alloydb_agent",
        model="gemini-1.5-flash",
        instruction="You are a helpful assistant."
    )
    
    runner = Runner(
        app_name="alloydb_app",
        agent=agent,
        session_service=session_service
    )
    
    # Create and use session
    session = await session_service.create_session(
        app_name="alloydb_app",
        user_id="user123",
        session_id="session456"
    )
    
    async for event in runner.run_async(
        user_id="user123",
        session_id="session456",
        new_message=types.UserContent(parts=[types.Part(text="Hello!")])
    ):
        if event.content:
            print(event.content)
    
    await session_service.close()

if __name__ == "__main__":
    asyncio.run(main())
```

**AlloyDB URL Format**: Same as PostgreSQL
- `postgresql+asyncpg://user:password@host:port/database`

## Example 7a: DatabaseSessionService - Supabase

Use Supabase (PostgreSQL-compatible) for session storage:

```python
#!/usr/bin/env python3
"""Agent with Supabase session storage."""

import asyncio
from google.adk import Agent
from google.adk.sessions import DatabaseSessionService
from google.adk.runners import Runner
from google.genai import types

async def main():
    # Create Supabase session service
    # Supabase uses PostgreSQL, so use PostgreSQL driver
    # Install: pip install asyncpg
    # Get connection string from Supabase dashboard: Settings > Database > Connection string
    session_service = DatabaseSessionService(
        db_url="postgresql+asyncpg://postgres:[YOUR-PASSWORD]@[YOUR-PROJECT-REF].supabase.co:5432/postgres"
    )
    
    # Alternative: Use connection pooling for better performance
    session_service = DatabaseSessionService(
        db_url="postgresql+asyncpg://postgres:[YOUR-PASSWORD]@[YOUR-PROJECT-REF].supabase.co:5432/postgres",
        pool_size=10,
        max_overflow=20
    )
    
    # Alternative: Use environment variable for security
    import os
    session_service = DatabaseSessionService(
        db_url=os.getenv("SUPABASE_DATABASE_URL"),
        pool_size=10,
        max_overflow=20
    )
    
    agent = Agent(
        name="supabase_agent",
        model="gemini-1.5-flash",
        instruction="You are a helpful assistant."
    )
    
    runner = Runner(
        app_name="supabase_app",
        agent=agent,
        session_service=session_service
    )
    
    # Create and use session
    session = await session_service.create_session(
        app_name="supabase_app",
        user_id="user123",
        session_id="session456"
    )
    
    async for event in runner.run_async(
        user_id="user123",
        session_id="session456",
        new_message=types.UserContent(parts=[types.Part(text="Hello!")])
    ):
        if event.content:
            print(event.content)
    
    await session_service.close()

if __name__ == "__main__":
    asyncio.run(main())
```

**Supabase URL Format**: Same as PostgreSQL
- `postgresql+asyncpg://postgres:[PASSWORD]@[PROJECT-REF].supabase.co:5432/postgres`
- Get your connection string from: Supabase Dashboard > Settings > Database > Connection string

**Required Package**: `pip install asyncpg`

**Note**: 
- Replace `[YOUR-PASSWORD]` with your Supabase database password
- Replace `[YOUR-PROJECT-REF]` with your Supabase project reference
- For production, use environment variables to store the connection string securely
- Supabase uses SSL by default, which is automatically handled by asyncpg

## Supported Databases

`DatabaseSessionService` supports **any database that SQLAlchemy supports**. Here are the commonly used ones:

### Fully Supported Databases

1. **SQLite**
   - **URL Format**: `sqlite+aiosqlite:///path/to/database.db`
   - **Driver**: `aiosqlite` (async)
   - **Install**: `pip install aiosqlite`
   - **Use Case**: Development, testing, small-scale production
   - **Pros**: No server required, easy setup
   - **Cons**: Not suitable for high concurrency

2. **PostgreSQL**
   - **URL Format**: `postgresql+asyncpg://user:password@host:port/database`
   - **Driver**: `asyncpg` (recommended) or `psycopg`
   - **Install**: `pip install asyncpg` or `pip install psycopg[binary]`
   - **Use Case**: Production applications
   - **Pros**: Robust, feature-rich, excellent performance
   - **Cons**: Requires database server

3. **MySQL / MariaDB**
   - **URL Format**: `mysql+aiomysql://user:password@host:port/database`
   - **Driver**: `aiomysql` (recommended) or `pymysql`
   - **Install**: `pip install aiomysql` or `pip install pymysql`
   - **Use Case**: Production applications
   - **Pros**: Widely used, good performance
   - **Cons**: Requires database server

4. **Google Cloud Spanner**
   - **URL Format**: `spanner+spanner://projects/{project}/instances/{instance}/databases/{database}`
   - **Driver**: `sqlalchemy-spanner`
   - **Install**: `pip install sqlalchemy-spanner`
   - **Use Case**: Large-scale, globally distributed applications
   - **Pros**: Scalable, globally distributed, ACID transactions
   - **Cons**: More expensive, Google Cloud only

5. **Google Cloud AlloyDB**
   - **URL Format**: `postgresql+asyncpg://user:password@host:port/database`
   - **Driver**: `asyncpg` (PostgreSQL-compatible)
   - **Install**: `pip install asyncpg`
   - **Use Case**: High-performance PostgreSQL workloads on Google Cloud
   - **Pros**: PostgreSQL-compatible, high performance, managed service
   - **Cons**: Google Cloud only

6. **Supabase**
   - **URL Format**: `postgresql+asyncpg://postgres:[PASSWORD]@[PROJECT-REF].supabase.co:5432/postgres`
   - **Driver**: `asyncpg` (PostgreSQL-compatible)
   - **Install**: `pip install asyncpg`
   - **Use Case**: Production applications with managed PostgreSQL
   - **Pros**: PostgreSQL-compatible, managed service, easy setup, free tier available
   - **Cons**: Third-party service dependency
   - **Note**: Get connection string from Supabase Dashboard > Settings > Database

### Other SQLAlchemy-Supported Databases

`DatabaseSessionService` can work with any database that SQLAlchemy supports, including:

- **Oracle**: `oracle+oracledb://...`
- **Microsoft SQL Server**: `mssql+aioodbc://...` or `mssql+pyodbc://...`
- **SQLite (in-memory)**: `sqlite+aiosqlite:///:memory:`
- **And more**: Any database with a SQLAlchemy dialect

## DatabaseSessionService Configuration

### Constructor Parameters

```python
DatabaseSessionService(
    db_url: str,              # Database URL (required)
    **kwargs: Any             # Additional SQLAlchemy engine arguments
)
```

### Common Engine Arguments

```python
session_service = DatabaseSessionService(
    db_url="postgresql+asyncpg://user:pass@host:5432/db",
    pool_size=10,              # Connection pool size
    max_overflow=20,           # Maximum overflow connections
    pool_timeout=30,           # Connection timeout
    pool_recycle=3600,           # Connection recycle time
    echo=False,                 # Log SQL queries (debug)
    future=True               # Use SQLAlchemy 2.0 style
)
```

### Using Async Context Manager

```python
async with DatabaseSessionService(
    db_url="sqlite+aiosqlite:///./sessions.db"
) as session_service:
    # Use session service
    session = await session_service.create_session(...)
    # Service automatically closes when exiting context
```

## Database Schema

`DatabaseSessionService` automatically creates the following tables:

1. **sessions**: Stores session metadata and state
2. **events**: Stores conversation events
3. **app_states**: Stores application-level state
4. **user_states**: Stores user-level state
5. **metadata**: Stores schema version and metadata (V1 schema)

The schema version is automatically managed. The service supports:
- **V0 Schema**: Legacy schema
- **V1 Schema**: Latest schema with improved features

## Example 8: Session State Management

Access and modify session state:

```python
import asyncio
from google.adk.sessions import InMemorySessionService

async def main():
    session_service = InMemorySessionService()
    
    # Create session
    session = await session_service.create_session(
        app_name="state_app",
        user_id="user123",
        session_id="session456"
    )
    
    # Get session state
    state = session.state
    
    # Update state
    state["user_name"] = "Alice"
    state["preferences"] = {"theme": "dark"}
    
    # Note: State is automatically persisted when events are appended to the session
    # To manually update state, you can create a new session with updated state:
    updated_session = await session_service.create_session(
        app_name="state_app",
        user_id="user123",
        session_id="session456",
        state=state
    )
    
    # Retrieve session later
    retrieved_session = await session_service.get_session(
        app_name="state_app",
        user_id="user123",
        session_id="session456"
    )
    
    if retrieved_session:
        print(f"Retrieved session: {retrieved_session.id}")
        print(f"State: {retrieved_session.state}")

asyncio.run(main())
```

## Example 9: Multiple Sessions

Manage multiple concurrent sessions:

```python
import asyncio
from google.adk.sessions import InMemorySessionService
from google.adk import Agent
from google.adk.runners import Runner

session_service = InMemorySessionService()
agent = Agent(name="multi_session_agent", model="gemini-1.5-flash")
runner = Runner(
    app_name="multi_session_app",
    agent=agent,
    session_service=session_service
)

async def handle_user(user_id: str, message: str):
    """Handle message for a specific user."""
    session_id = f"user_{user_id}"
    
    # Get or create session for user
    session = await session_service.get_session(
        app_name="multi_session_app",
        user_id=user_id,
        session_id=session_id
    )
    
    if not session:
        session = await session_service.create_session(
            app_name="multi_session_app",
            user_id=user_id,
            session_id=session_id
        )
    
    # Process message
    from google.genai import types
    
    async for event in runner.run_async(
        user_id=user_id,
        session_id=session.id,
        new_message=types.UserContent(parts=[types.Part(text=message)])
    ):
        if event.content and event.content.parts:
            for part in event.content.parts:
                if part.text:
                    return part.text
    return None

async def main():
    # Handle multiple users
    await handle_user("alice", "Hello")
    await handle_user("bob", "Hi there")
    await handle_user("alice", "Remember me?")  # Agent remembers Alice

asyncio.run(main())
```

## Best Practices

1. **Session IDs**: Use meaningful, unique session IDs
2. **Session Cleanup**: Clean up old sessions periodically
3. **State Size**: Keep session state small
4. **Privacy**: Don't store sensitive data in sessions
5. **Persistence**: 
   - Use `DatabaseSessionService` with PostgreSQL/MySQL for production
   - Use `VertexAiSessionService` for Google Cloud deployments
   - Use `InMemorySessionService` only for development/testing
6. **Connection Pooling**: Configure appropriate pool sizes for production databases
7. **Database URLs**: Store database URLs in environment variables, not in code
8. **Cleanup**: Always close `DatabaseSessionService` when done (use async context manager)

## Troubleshooting

### Issue: Session not persisting
- Check session service is properly configured
- Verify `create_session()` is called with correct `app_name`, `user_id`, and `session_id`
- Sessions are automatically persisted when events are appended (no manual save needed)
- Check Vertex AI credentials if using VertexAiSessionService
- For `DatabaseSessionService`, verify database connection and permissions
- Check that tables are created (they're created automatically on first use)

### Issue: Session state too large
- Limit state size
- Use external storage for large data
- Implement state compression

### Issue: DatabaseSessionService ImportError
**Error**: `DatabaseSessionService requires sqlalchemy>=2.0`

**Solution**: Install SQLAlchemy 2.0 or later:
```bash
pip install "sqlalchemy>=2.0"
```

### Issue: Database driver not found
**Error**: `Database related module not found for URL`

**Solution**: Install the appropriate database driver:
- PostgreSQL: `pip install asyncpg`
- MySQL: `pip install aiomysql`
- SQLite: `pip install aiosqlite`
- Cloud Spanner: `pip install sqlalchemy-spanner`

### Issue: Invalid database URL format
**Error**: `Invalid database URL format or argument`

**Solution**: Verify your database URL format:
- SQLite: `sqlite+aiosqlite:///./database.db`
- PostgreSQL: `postgresql+asyncpg://user:password@host:port/database`
- MySQL: `mysql+aiomysql://user:password@host:port/database`
- Spanner: `spanner+spanner://projects/{project}/instances/{instance}/databases/{database}`

### Issue: Connection pool exhausted
**Error**: Connection pool timeout or too many connections

**Solution**: Increase pool size or reduce concurrent operations:
```python
session_service = DatabaseSessionService(
    db_url="postgresql+asyncpg://...",
    pool_size=20,        # Increase pool size
    max_overflow=40      # Increase overflow
)
```

### Issue: Tables not created
**Error**: Table does not exist

**Solution**: Tables are created automatically on first use. If issues persist:
- Check database permissions (CREATE TABLE permission required)
- Verify database connection
- Check logs for creation errors

## Database URL Reference

### SQLite
```python
# File-based
"sqlite+aiosqlite:///./sessions.db"
"sqlite+aiosqlite:////absolute/path/to/sessions.db"

# In-memory (temporary)
"sqlite+aiosqlite:///:memory:"
```

### PostgreSQL
```python
# Basic
"postgresql+asyncpg://user:password@localhost:5432/database"

# With connection parameters
"postgresql+asyncpg://user:password@localhost:5432/database?ssl=require"

# Cloud SQL (via Unix socket)
"postgresql+asyncpg://user:password@/database?host=/cloudsql/project:region:instance"
```

### MySQL
```python
# Basic
"mysql+aiomysql://user:password@localhost:3306/database"

# With charset
"mysql+aiomysql://user:password@localhost:3306/database?charset=utf8mb4"
```

### Cloud Spanner
```python
# Full path format
"spanner+spanner://projects/my-project/instances/my-instance/databases/my-database"
```

### Environment Variables

Best practice: Store database URLs in environment variables:

```python
import os
from google.adk.sessions import DatabaseSessionService

db_url = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./sessions.db")
session_service = DatabaseSessionService(db_url=db_url)
```

## Related Documentation

- [Memory Package](08-Memory-Package.md)
- [Apps Package](05-Apps-Package.md)
- [Runners Package](10-Runners-Package.md) - How sessions are used in runners
