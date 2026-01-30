# Python A2A Conversation Storage Guide

**File Path**: `A2A/docs/06-Conversation-Storage.md`

## Overview

Similar to how Google ADK uses `DatabaseSessionService` to store agent sessions in databases, Python A2A conversations can also be persisted to databases. This guide covers multiple approaches for storing A2A conversations.

## Comparison: ADK Sessions vs A2A Conversations

| Feature | ADK Sessions | A2A Conversations |
|---------|-------------|-------------------|
| **Storage Class** | `DatabaseSessionService` | Custom implementation or `a2a-session-manager` |
| **Data Model** | `Session` (with state) | `Conversation` (with messages) |
| **Built-in Storage** | ✅ Yes (DatabaseSessionService) | ⚠️ No (but easy to implement) |
| **Serialization** | Automatic | `to_json()`, `to_dict()`, `from_json()`, `from_dict()` |
| **Database Support** | PostgreSQL, MySQL, SQLite, Spanner, etc. | Any database (via custom implementation) |

## Approach 1: Using Conversation Serialization Methods

Python A2A's `Conversation` class provides built-in serialization methods that make database storage straightforward.

### Conversation Serialization Methods

```python
from python_a2a import Conversation

# Convert to JSON string
json_str = conversation.to_json()

# Convert to dictionary
conversation_dict = conversation.to_dict()

# Load from JSON string
conversation = Conversation.from_json(json_str)

# Load from dictionary
conversation = Conversation.from_dict(conversation_dict)
```

### Example: SQLite Storage

```python
import sqlite3
import json
from python_a2a import Conversation, Message, TextContent, MessageRole
from datetime import datetime
from typing import Optional

class ConversationStorage:
    """Simple SQLite-based conversation storage."""
    
    def __init__(self, db_path: str = "a2a_conversations.db"):
        self.db_path = db_path
        self._init_db()
    
    def _init_db(self):
        """Initialize database tables."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS conversations (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                agent_id TEXT,
                conversation_data TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()
        conn.close()
    
    def save_conversation(
        self,
        conversation_id: str,
        user_id: str,
        conversation: Conversation,
        agent_id: Optional[str] = None
    ):
        """Save a conversation to the database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        conversation_json = conversation.to_json()
        
        cursor.execute("""
            INSERT OR REPLACE INTO conversations 
            (id, user_id, agent_id, conversation_data, updated_at)
            VALUES (?, ?, ?, ?, ?)
        """, (
            conversation_id,
            user_id,
            agent_id,
            conversation_json,
            datetime.utcnow().isoformat()
        ))
        
        conn.commit()
        conn.close()
    
    def load_conversation(
        self,
        conversation_id: str
    ) -> Optional[Conversation]:
        """Load a conversation from the database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT conversation_data FROM conversations
            WHERE id = ?
        """, (conversation_id,))
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return Conversation.from_json(row[0])
        return None
    
    def list_conversations(self, user_id: str) -> list:
        """List all conversations for a user."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, agent_id, created_at, updated_at
            FROM conversations
            WHERE user_id = ?
            ORDER BY updated_at DESC
        """, (user_id,))
        
        rows = cursor.fetchall()
        conn.close()
        
        return [
            {
                "id": row[0],
                "agent_id": row[1],
                "created_at": row[2],
                "updated_at": row[3]
            }
            for row in rows
        ]

# Usage example
storage = ConversationStorage()

# Create a conversation
conversation = Conversation(
    messages=[
        Message(
            role=MessageRole.USER,
            content=[TextContent(text="Hello!")]
        ),
        Message(
            role=MessageRole.AGENT,
            content=[TextContent(text="Hi! How can I help?")]
        )
    ]
)

# Save conversation
storage.save_conversation(
    conversation_id="conv_123",
    user_id="user_456",
    conversation=conversation,
    agent_id="agent_789"
)

# Load conversation
loaded_conv = storage.load_conversation("conv_123")
print(f"Loaded {len(loaded_conv.messages)} messages")
```

## Approach 2: PostgreSQL Storage (Similar to ADK DatabaseSessionService)

```python
import asyncpg
import json
from python_a2a import Conversation
from typing import Optional
from datetime import datetime

class PostgreSQLConversationStorage:
    """PostgreSQL-based conversation storage (similar to ADK DatabaseSessionService)."""
    
    def __init__(self, db_url: str):
        self.db_url = db_url
        self.pool = None
    
    async def initialize(self):
        """Initialize database connection pool."""
        self.pool = await asyncpg.create_pool(self.db_url)
        await self._create_tables()
    
    async def _create_tables(self):
        """Create database tables."""
        async with self.pool.acquire() as conn:
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS a2a_conversations (
                    id VARCHAR PRIMARY KEY,
                    user_id VARCHAR NOT NULL,
                    agent_id VARCHAR,
                    app_name VARCHAR,
                    conversation_data JSONB NOT NULL,
                    metadata JSONB,
                    created_at TIMESTAMP DEFAULT NOW(),
                    updated_at TIMESTAMP DEFAULT NOW()
                );
                
                CREATE INDEX IF NOT EXISTS idx_user_id 
                ON a2a_conversations(user_id);
                
                CREATE INDEX IF NOT EXISTS idx_agent_id 
                ON a2a_conversations(agent_id);
                
                CREATE INDEX IF NOT EXISTS idx_app_name 
                ON a2a_conversations(app_name);
            """)
    
    async def save_conversation(
        self,
        conversation_id: str,
        user_id: str,
        conversation: Conversation,
        agent_id: Optional[str] = None,
        app_name: Optional[str] = None,
        metadata: Optional[dict] = None
    ):
        """Save a conversation to PostgreSQL."""
        conversation_dict = conversation.to_dict()
        
        async with self.pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO a2a_conversations 
                (id, user_id, agent_id, app_name, conversation_data, metadata, updated_at)
                VALUES ($1, $2, $3, $4, $5, $6, NOW())
                ON CONFLICT (id) DO UPDATE SET
                    conversation_data = $5,
                    metadata = $6,
                    updated_at = NOW()
            """, conversation_id, user_id, agent_id, app_name, 
                json.dumps(conversation_dict), json.dumps(metadata))
    
    async def load_conversation(
        self,
        conversation_id: str
    ) -> Optional[Conversation]:
        """Load a conversation from PostgreSQL."""
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow("""
                SELECT conversation_data FROM a2a_conversations
                WHERE id = $1
            """, conversation_id)
            
            if row:
                conversation_dict = json.loads(row['conversation_data'])
                return Conversation.from_dict(conversation_dict)
            return None
    
    async def list_user_conversations(
        self,
        user_id: str,
        app_name: Optional[str] = None
    ) -> list:
        """List all conversations for a user."""
        async with self.pool.acquire() as conn:
            if app_name:
                rows = await conn.fetch("""
                    SELECT id, agent_id, created_at, updated_at
                    FROM a2a_conversations
                    WHERE user_id = $1 AND app_name = $2
                    ORDER BY updated_at DESC
                """, user_id, app_name)
            else:
                rows = await conn.fetch("""
                    SELECT id, agent_id, created_at, updated_at
                    FROM a2a_conversations
                    WHERE user_id = $1
                    ORDER BY updated_at DESC
                """, user_id)
            
            return [dict(row) for row in rows]
    
    async def close(self):
        """Close the connection pool."""
        if self.pool:
            await self.pool.close()

# Usage example
import asyncio

async def main():
    storage = PostgreSQLConversationStorage(
        db_url="postgresql://user:password@localhost:5432/a2a_db"
    )
    await storage.initialize()
    
    # Save conversation
    conversation = Conversation(messages=[...])
    await storage.save_conversation(
        conversation_id="conv_123",
        user_id="user_456",
        conversation=conversation,
        app_name="my_app"
    )
    
    # Load conversation
    loaded = await storage.load_conversation("conv_123")
    
    await storage.close()

asyncio.run(main())
```

## Approach 3: Using a2a-session-manager Library

There's a dedicated library `a2a-session-manager` that provides session storage similar to ADK's DatabaseSessionService.

### Installation

```bash
pip install a2a-session-manager
# Or with Redis support
pip install a2a-session-manager[redis]
```

### Usage

```python
from a2a_session_manager.storage import (
    InMemorySessionStore,
    create_file_session_store,
    SessionStoreProvider
)
from a2a_session_manager.models.session import Session
from a2a_session_manager.models.session_event import SessionEvent, EventSource
from python_a2a import Conversation, Message, TextContent, MessageRole

# Option 1: In-memory storage (for testing)
store = InMemorySessionStore()
SessionStoreProvider.set_store(store)

# Option 2: File-based storage
store = create_file_session_store(directory="./sessions")
SessionStoreProvider.set_store(store)

# Create and save session
session = Session()
session.add_event(SessionEvent(
    message="Hello",
    source=EventSource.USER
))
store.save(session)

# Load session
retrieved_session = store.get(session.id)
```

## Approach 4: SQLAlchemy Integration (Like ADK)

For a more ADK-like experience, you can use SQLAlchemy:

```python
from sqlalchemy import create_engine, Column, String, DateTime, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from python_a2a import Conversation
from datetime import datetime

Base = declarative_base()

class ConversationModel(Base):
    __tablename__ = 'a2a_conversations'
    
    id = Column(String, primary_key=True)
    user_id = Column(String, nullable=False)
    agent_id = Column(String)
    app_name = Column(String)
    conversation_data = Column(JSON, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class SQLAlchemyConversationStorage:
    """SQLAlchemy-based conversation storage."""
    
    def __init__(self, db_url: str):
        self.engine = create_engine(db_url)
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)
    
    def save_conversation(
        self,
        conversation_id: str,
        user_id: str,
        conversation: Conversation,
        agent_id: str = None,
        app_name: str = None
    ):
        """Save conversation."""
        session = self.Session()
        try:
            conv_data = conversation.to_dict()
            
            conv_model = ConversationModel(
                id=conversation_id,
                user_id=user_id,
                agent_id=agent_id,
                app_name=app_name,
                conversation_data=conv_data
            )
            
            session.merge(conv_model)
            session.commit()
        finally:
            session.close()
    
    def load_conversation(self, conversation_id: str) -> Conversation:
        """Load conversation."""
        session = self.Session()
        try:
            model = session.query(ConversationModel).filter_by(
                id=conversation_id
            ).first()
            
            if model:
                return Conversation.from_dict(model.conversation_data)
            return None
        finally:
            session.close()

# Usage
storage = SQLAlchemyConversationStorage(
    db_url="postgresql://user:pass@localhost:5432/a2a_db"
)
```

## Integration with A2A Server

Store conversations in your A2A server:

```python
from python_a2a import A2AServer, Message, Conversation
from python_a2a import create_fastapi_app
import uvicorn

# Initialize storage
storage = PostgreSQLConversationStorage(
    db_url="postgresql://user:pass@localhost:5432/a2a_db"
)

async def handle_conversation(
    conversation: Conversation,
    user_id: str,
    agent_id: str
) -> Message:
    """Handle conversation and save to database."""
    
    # Process conversation
    last_message = conversation.messages[-1]
    response_text = f"Processed: {last_message.content[0].text}"
    
    # Add response to conversation
    conversation.add_message(Message(
        role=MessageRole.AGENT,
        content=[TextContent(text=response_text)]
    ))
    
    # Save to database
    conversation_id = conversation.metadata.get("id", "auto_generated_id")
    await storage.save_conversation(
        conversation_id=conversation_id,
        user_id=user_id,
        conversation=conversation,
        agent_id=agent_id
    )
    
    return conversation.messages[-1]

# Create server with storage
server = A2AServer(
    agent_card={"name": "stored_agent"},
    conversation_handler=handle_conversation
)

app = create_fastapi_app(server)
uvicorn.run(app, host="0.0.0.0", port=8000)
```

## Database Schema Comparison

### ADK DatabaseSessionService Schema
```sql
CREATE TABLE sessions (
    id VARCHAR PRIMARY KEY,
    app_name VARCHAR NOT NULL,
    user_id VARCHAR NOT NULL,
    session_id VARCHAR NOT NULL,
    state JSONB,
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);
```

### A2A Conversation Storage Schema
```sql
CREATE TABLE a2a_conversations (
    id VARCHAR PRIMARY KEY,
    user_id VARCHAR NOT NULL,
    agent_id VARCHAR,
    app_name VARCHAR,
    conversation_data JSONB NOT NULL,  -- Full conversation with messages
    metadata JSONB,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

## Key Differences

1. **ADK Sessions**: Store state + events separately
2. **A2A Conversations**: Store complete conversation (messages) as JSON

## Best Practices

1. **Index frequently queried fields**: `user_id`, `agent_id`, `app_name`
2. **Use JSONB in PostgreSQL**: For efficient JSON storage and querying
3. **Add metadata**: Store additional context (user preferences, session info)
4. **Implement cleanup**: Archive or delete old conversations
5. **Backup regularly**: Conversations contain important interaction history

## Next Steps

- Review [Core Concepts](01-Core-Concepts.md) for Conversation structure
- Check out [Server Implementation](02-Server-Implementation.md) for integration
- See examples in `A2A/examples/` directory
