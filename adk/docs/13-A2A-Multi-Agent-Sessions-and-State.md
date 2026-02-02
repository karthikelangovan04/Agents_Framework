# A2A Multi-Agent Sessions and State Management

**File Path**: `docs/13-A2A-Multi-Agent-Sessions-and-State.md`  
**Related Docs**: 
- [State Management](11-State-Management.md)
- [Sessions Package](07-Sessions-Package.md)
- [A2A Package](04-A2A-Package.md)

## Overview

This document explains how **state** and **sessions** work in Google ADK, particularly in **multi-agent A2A (Agent-to-Agent) systems**. You'll learn:

1. What "state" means in Google ADK
2. How `DatabaseSessionService` works with PostgreSQL
3. How sessions and context flow in A2A multi-agent systems
4. Whether sessions are unique per agent or shared
5. Real-world examples with PostgreSQL

---

## Part 1: Understanding State in Google ADK

### What is State?

**State** in Google ADK is persistent data that agents can read and write during conversations. It's organized into **hierarchical scopes** that determine where and how long data persists.

### State Scopes

State is organized into four scopes:

1. **Application-Level State** (`app:` prefix)
   - **Scope**: Shared across ALL users and sessions in an application
   - **Persistence**: Persists forever (until explicitly deleted)
   - **Use Cases**: Global configuration, feature flags, app-wide settings
   - **Example**: `app:tax_rate`, `app:max_level`, `app:api_version`

2. **User-Level State** (`user:` prefix)
   - **Scope**: Specific to ONE user across ALL their sessions
   - **Persistence**: Persists across all sessions for the same user
   - **Use Cases**: User preferences, user profile, user statistics
   - **Example**: `user:preferred_language`, `user:total_wins`, `user:loyalty_points`

3. **Session-Level State** (no prefix)
   - **Scope**: Specific to ONE session only
   - **Persistence**: Only exists during the session lifecycle
   - **Use Cases**: Conversation context, temporary variables, session-specific data
   - **Example**: `conversation_topic`, `message_count`, `cart_items`

4. **Temporary State** (`temp:` prefix)
   - **Scope**: Only during event processing
   - **Persistence**: Automatically discarded after event processing
   - **Use Cases**: Intermediate calculations, temporary variables
   - **Example**: `temp:intermediate_result`, `temp:processing_time`

### State Prefixes

```python
from google.adk.sessions.state import State

State.APP_PREFIX   # "app:"
State.USER_PREFIX  # "user:"
State.TEMP_PREFIX  # "temp:"
# Session-level: no prefix needed
```

### Example: State in Action

```python
from google.adk.sessions.state import State

# App-level: shared by all users
state[State.APP_PREFIX + "tax_rate"] = 0.08

# User-level: specific to this user
state[State.USER_PREFIX + "loyalty_points"] = 1000

# Session-level: only for this conversation
state["cart_items"] = ["iPhone 15", "AirPods"]

# Temporary: discarded after processing
state[State.TEMP_PREFIX + "calculation"] = 42
```

---

## Part 2: DatabaseSessionService with PostgreSQL

### What is DatabaseSessionService?

`DatabaseSessionService` is a session service that stores sessions, events, and state in a **SQLAlchemy-compatible database** (PostgreSQL, MySQL, SQLite, etc.). It provides persistent storage for production applications.

### Database Schema

When using `DatabaseSessionService`, the following tables are automatically created:

```sql
-- Session-level state and metadata
CREATE TABLE sessions (
    id VARCHAR PRIMARY KEY,
    app_name VARCHAR NOT NULL,
    user_id VARCHAR NOT NULL,
    session_id VARCHAR NOT NULL,
    state JSONB,  -- Session-level state stored here
    created_at TIMESTAMP,
    updated_at TIMESTAMP,
    UNIQUE(app_name, user_id, session_id)
);

-- All conversation events
CREATE TABLE events (
    id VARCHAR PRIMARY KEY,
    app_name VARCHAR NOT NULL,
    user_id VARCHAR NOT NULL,
    session_id VARCHAR NOT NULL,
    author VARCHAR,  -- 'user', 'agent', or agent name
    timestamp TIMESTAMP,
    content JSONB,  -- Event content (messages, tool calls, etc.)
    FOREIGN KEY (session_id) REFERENCES sessions(id)
);

-- User-level state (persists across sessions)
CREATE TABLE user_states (
    app_name VARCHAR NOT NULL,
    user_id VARCHAR NOT NULL,
    key VARCHAR NOT NULL,
    value JSONB,  -- User-level state value
    PRIMARY KEY (app_name, user_id, key)
);

-- App-level state (shared by all users)
CREATE TABLE app_states (
    app_name VARCHAR NOT NULL,
    key VARCHAR NOT NULL,
    value JSONB,  -- App-level state value
    PRIMARY KEY (app_name, key)
);
```

### How State is Automatically Merged

When you retrieve a session, `DatabaseSessionService` **automatically**:

1. **Loads session-level state** from `sessions` table
2. **Loads user-level state** from `user_states` table (for that user)
3. **Loads app-level state** from `app_states` table (for that app)
4. **Merges all three** into a single unified `session.state` object

You don't need to manually fetch user or app state - it's automatic!

### Example: DatabaseSessionService with PostgreSQL

```python
import asyncio
from google.adk.sessions import DatabaseSessionService
from google.adk.sessions.state import State
from google.adk import Agent
from google.adk.runners import Runner
from google.genai import types

async def main():
    # Create PostgreSQL session service
    session_service = DatabaseSessionService(
        db_url="postgresql+asyncpg://user:password@localhost:5432/adk_db"
    )
    
    agent = Agent(
        name="postgres_agent",
        model="gemini-1.5-flash",
        instruction="You are a helpful assistant."
    )
    
    runner = Runner(
        app_name="my_app",
        agent=agent,
        session_service=session_service
    )
    
    # Create session - state is automatically loaded from DB
    session = await session_service.create_session(
        app_name="my_app",
        user_id="user123",
        session_id="session001",
        state={
            # Session-level state
            "conversation_topic": None,
            "message_count": 0,
            # User-level state (automatically loaded from user_states table)
            # App-level state (automatically loaded from app_states table)
        }
    )
    
    # Access merged state
    print(session.state["conversation_topic"])  # Session-level
    print(session.state.get(State.USER_PREFIX + "preferred_language"))  # User-level (from DB)
    print(session.state.get(State.APP_PREFIX + "api_version"))  # App-level (from DB)
    
    # Update state via state_delta
    async for event in runner.run_async(
        user_id="user123",
        session_id="session001",
        new_message=types.UserContent(parts=[types.Part(text="Hello")]),
        state_delta={
            "message_count": 1,  # Session-level update
            State.USER_PREFIX + "last_active": "2024-01-15"  # User-level update
        }
    ):
        if event.content:
            print(event.content)
    
    # State is automatically persisted to database
    await session_service.close()

asyncio.run(main())
```

### Real PostgreSQL Example: Postgres Agent

Based on the test file `test_session_context.py`, here's how a real PostgreSQL agent works:

```python
import asyncio
import os
from google.adk.sessions import DatabaseSessionService
from google.adk.runners import Runner
from google.genai.types import Content, Part
from .agent import root_agent

# PostgreSQL connection
DB_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://adk_user:adk_password@localhost:5433/adk_db"
)

async def main():
    # Initialize services
    session_service = DatabaseSessionService(db_url=DB_URL)
    
    runner = Runner(
        agent=root_agent,
        app_name="postgres_agent_app",
        session_service=session_service,
    )
    
    user_id = "user_001"
    session_id = "test_session_001"
    
    # Step 1: Create session
    session = await session_service.create_session(
        app_name="postgres_agent_app",
        user_id=user_id,
        session_id=session_id,
    )
    print(f"Session created: {session.id}")
    print(f"Initial state: {session.state}")
    
    # Step 2: First interaction
    user_message_1 = Content(
        parts=[Part(text="Hi! My name is Alice and I love reading science fiction novels.")],
        role="user",
    )
    
    async for event in runner.run_async(
        user_id=user_id,
        session_id=session_id,
        new_message=user_message_1,
    ):
        if event.is_final_response() and event.content:
            print(f"Agent: {event.content.parts[0].text}")
    
    # Step 3: Second interaction (agent remembers context)
    user_message_2 = Content(
        parts=[Part(text="What's my favorite genre?")],
        role="user",
    )
    
    async for event in runner.run_async(
        user_id=user_id,
        session_id=session_id,
        new_message=user_message_2,
    ):
        if event.is_final_response() and event.content:
            print(f"Agent: {event.content.parts[0].text}")
            # Agent should remember: "science fiction"
    
    # Step 4: Retrieve session and verify
    retrieved_session = await session_service.get_session(
        app_name="postgres_agent_app",
        user_id=user_id,
        session_id=session_id,
    )
    
    print(f"Total events: {len(retrieved_session.events)}")
    print(f"Session state: {retrieved_session.state}")
    
    await session_service.close()

asyncio.run(main())
```

**What Happens Behind the Scenes**:

1. **Session Creation**: Creates record in `sessions` table
2. **State Loading**: Automatically queries `user_states` and `app_states` tables
3. **Event Storage**: Each interaction stores events in `events` table
4. **State Updates**: `state_delta` updates are persisted to appropriate tables
5. **Context Retrieval**: When retrieving session, all events and state are loaded

---

## Part 3: Sessions and Context in A2A Multi-Agent Systems

### Key Question: Are Sessions Unique Per Agent?

**Answer**: **It depends on the architecture**, but typically:

- **Orchestrator Agent**: Maintains the **primary session** with the user
- **Remote Agents**: May have their **own sessions** on their servers, OR they may receive context from the orchestrator

### How A2A Works

In an A2A multi-agent system:

1. **User** → **Orchestrator Agent** (has session with user)
2. **Orchestrator Agent** → **Remote Agent** (via HTTP/A2A protocol)
3. **Remote Agent** processes request and returns response
4. **Orchestrator Agent** receives response and continues conversation

### Session Flow in A2A

```
┌─────────────┐
│   User      │
└──────┬──────┘
       │
       │ user_id="user123", session_id="session001"
       ▼
┌─────────────────────────┐
│ Orchestrator Agent      │
│ (Local/Client)          │
│                         │
│ Session Service:        │
│ - app_name="my_app"     │
│ - user_id="user123"     │
│ - session_id="session001"│
│                         │
│ State:                  │
│ - conversation_history  │
│ - user preferences      │
│ - session context       │
└──────┬──────────────────┘
       │
       │ A2A Protocol (HTTP)
       │ Passes: user_id, session_id, context
       ▼
┌─────────────────────────┐
│ Remote Agent Server     │
│ (Remote/Server)         │
│                         │
│ Option A:               │
│ - Uses orchestrator's   │
│   session_id            │
│ - Receives context      │
│                         │
│ Option B:               │
│ - Creates own session  │
│ - Receives context      │
│ - Returns result        │
└──────┬──────────────────┘
       │
       │ Response
       ▼
┌─────────────────────────┐
│ Orchestrator Agent      │
│ (Updates session)       │
└──────┬──────────────────┘
       │
       │ Final response
       ▼
┌─────────────┐
│   User      │
└─────────────┘
```

### Example 1: A2A with Session Context Passing

**Orchestrator (Client Side)**:

```python
import asyncio
from google.adk import Agent
from google.adk.a2a import RemoteA2aAgent
from google.adk.sessions import DatabaseSessionService
from google.adk.runners import Runner
from google.genai import types

async def main():
    # Orchestrator's session service (PostgreSQL)
    orchestrator_session_service = DatabaseSessionService(
        db_url="postgresql+asyncpg://user:pass@localhost:5432/orchestrator_db"
    )
    
    # Create remote agent reference
    remote_math = RemoteA2aAgent(
        name="remote_math",
        agent_card_url="http://localhost:8000/agent_card.json"
    )
    
    # Create orchestrator agent
    orchestrator = Agent(
        name="orchestrator",
        model="gemini-1.5-flash",
        instruction="""You are a coordinator agent.
        Route math questions to remote_math agent.
        Maintain conversation context.""",
        sub_agents=[remote_math]
    )
    
    # Create runner with session service
    runner = Runner(
        app_name="multi_agent_app",
        agent=orchestrator,
        session_service=orchestrator_session_service
    )
    
    user_id = "user123"
    session_id = "session001"
    
    # Create session on orchestrator side
    session = await orchestrator_session_service.create_session(
        app_name="multi_agent_app",
        user_id=user_id,
        session_id=session_id,
        state={
            "conversation_history": [],
            "last_agent_used": None
        }
    )
    
    # User asks math question
    async for event in runner.run_async(
        user_id=user_id,
        session_id=session_id,
        new_message=types.UserContent(
            parts=[types.Part(text="What is 15 * 23?")]
        ),
        state_delta={
            "last_agent_used": "remote_math"
        }
    ):
        if event.content:
            print(event.content)
    
    # Orchestrator's session maintains context
    updated_session = await orchestrator_session_service.get_session(
        app_name="multi_agent_app",
        user_id=user_id,
        session_id=session_id
    )
    
    print(f"Conversation history: {updated_session.state.get('conversation_history')}")
    print(f"Last agent used: {updated_session.state.get('last_agent_used')}")
    
    await orchestrator_session_service.close()

asyncio.run(main())
```

**Remote Agent Server Side**:

```python
from google.adk import Agent
from google.adk.apps import App
from google.adk.sessions import DatabaseSessionService
import uvicorn

# Remote agent's session service (can be same or different DB)
remote_session_service = DatabaseSessionService(
    db_url="postgresql+asyncpg://user:pass@localhost:5432/remote_agent_db"
)

# Create specialized remote agent
math_agent = Agent(
    name="remote_math_agent",
    description="A remote agent specialized in mathematics",
    model="gemini-1.5-flash",
    instruction="You are a math expert. Solve mathematical problems step by step."
)

# Create app with agent and session service
app = App(
    agent=math_agent,
    session_service=remote_session_service  # Optional: remote agent can have its own sessions
)

if __name__ == "__main__":
    print("Starting remote math agent server on http://localhost:8000")
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

### How Context is Passed

When the orchestrator calls a remote agent via A2A:

1. **A2A Protocol** automatically includes:
   - `user_id` from the orchestrator's session
   - `session_id` from the orchestrator's session (or a derived one)
   - Conversation context (recent messages)
   - Relevant state (if configured)

2. **Remote Agent** receives:
   - The user's message/question
   - Context from orchestrator's session
   - Any relevant state

3. **Remote Agent** processes and returns:
   - Response to the question
   - Any state updates (if applicable)

4. **Orchestrator** receives response and:
   - Updates its own session with the interaction
   - Stores the remote agent's response
   - Maintains conversation history

---

## ⚠️ Important: Token Cost and Context Relevance

### The Problem

You're absolutely right to be concerned! In a multi-agent system:

1. **Token Cost Issue**: If the orchestrator sends full conversation context to every sub-agent, you're paying for duplicate tokens:
   - Orchestrator processes full context: **X tokens**
   - Remote Agent 1 receives full context: **X tokens** (duplicate!)
   - Remote Agent 2 receives full context: **X tokens** (duplicate!)
   - **Total: 3X tokens** instead of just X tokens

2. **Context Relevance Issue**: 
   - Math agent doesn't need database query context
   - Database agent doesn't need math calculation context
   - Sending irrelevant context wastes tokens and can confuse agents

### How A2A Actually Works

**Good News**: The A2A protocol and Google ADK are designed to minimize this:

1. **Orchestrator decides what to send**: The orchestrator agent (powered by Gemini) intelligently extracts only **relevant context** when calling sub-agents
2. **Sub-agents are stateless by default**: Remote agents typically receive only the **current request**, not the full conversation history
3. **Context is filtered**: The orchestrator's LLM filters context based on what's relevant to each sub-agent

### Best Practices for Minimizing Token Costs

#### Strategy 1: Let Orchestrator Filter Context (Recommended)

The orchestrator agent should extract only relevant information:

```python
orchestrator = Agent(
    name="orchestrator",
    model="gemini-1.5-flash",
    instruction="""You are a coordinator agent.
    
    When routing to sub-agents:
    - Extract ONLY the information relevant to that agent
    - Do NOT send full conversation history
    - Do NOT send context from other agents
    
    Examples:
    - For math questions → Send only: the math question, any relevant numbers
    - For database questions → Send only: the database query request, relevant table names
    - For code questions → Send only: the coding request, relevant code snippets
    
    Keep context minimal and focused."""
)
```

#### Strategy 2: Use Stateless Remote Agents

Configure remote agents to be stateless (no session service):

```python
# Remote agent WITHOUT session service = stateless
# Only receives current request, not full history
app = App(
    agent=math_agent,
    # No session_service = stateless, minimal context
)
```

#### Strategy 3: Implement Context Filtering

Manually filter context before calling remote agents:

```python
async def call_remote_agent_with_filtered_context(
    remote_agent: RemoteA2aAgent,
    user_message: str,
    session: Session,
    context_filter: callable
):
    """Call remote agent with only relevant context."""
    
    # Filter events to only relevant ones
    relevant_events = [
        event for event in session.events
        if context_filter(event)
    ]
    
    # Create minimal context
    filtered_context = {
        "current_message": user_message,
        "relevant_history": relevant_events[-3:],  # Only last 3 relevant events
    }
    
    # Call remote agent with filtered context
    # (Implementation depends on A2A protocol details)
    return await remote_agent.process(filtered_context)
```

#### Strategy 4: Use State Instead of Full Context

Store relevant information in state, then pass only state keys:

```python
# Instead of sending full conversation:
# ❌ BAD: Sends 1000 tokens of conversation history

# ✅ GOOD: Store summary in state, send only state reference
session.state["math_context"] = {
    "last_math_question": "What is 25 * 17?",
    "last_math_answer": "425",
    "math_topic": "multiplication"
}

# When calling math agent, send only:
filtered_context = {
    "current_question": user_message,
    "math_state": session.state.get("math_context", {})
}
# Only ~50 tokens instead of 1000!
```

### Example: Cost-Optimized Multi-Agent System

```python
import asyncio
from google.adk import Agent
from google.adk.a2a import RemoteA2aAgent
from google.adk.sessions import DatabaseSessionService
from google.adk.runners import Runner
from google.genai import types

async def main():
    session_service = DatabaseSessionService(
        db_url="postgresql+asyncpg://user:pass@localhost:5432/multi_agent_db"
    )
    
    # Remote agents (stateless - no session service)
    remote_math = RemoteA2aAgent(
        name="remote_math",
        agent_card_url="http://localhost:8000/agent_card.json"
    )
    
    remote_db = RemoteA2aAgent(
        name="remote_db",
        agent_card_url="http://localhost:8001/agent_card.json"
    )
    
    # Orchestrator with context-filtering instructions
    orchestrator = Agent(
        name="orchestrator",
        model="gemini-1.5-flash",
        instruction="""You are a cost-efficient coordinator agent.
        
        CRITICAL RULES FOR TOKEN OPTIMIZATION:
        1. When calling remote_math:
           - Send ONLY: the current math question
           - Send ONLY: relevant numbers from current conversation
           - DO NOT send: database queries, code snippets, or other agent contexts
           
        2. When calling remote_db:
           - Send ONLY: the current database question
           - Send ONLY: relevant table/query information
           - DO NOT send: math calculations or other agent contexts
           
        3. Maintain conversation context in YOUR session only
        4. Extract and pass minimal context to sub-agents
        5. Each sub-agent should receive only what it needs
        
        This minimizes token costs and keeps responses relevant.""",
        sub_agents=[remote_math, remote_db]
    )
    
    runner = Runner(
        app_name="cost_optimized_app",
        agent=orchestrator,
        session_service=session_service
    )
    
    user_id = "user123"
    session_id = "session001"
    
    # Create session
    session = await session_service.create_session(
        app_name="cost_optimized_app",
        user_id=user_id,
        session_id=session_id,
        state={
            # Store agent-specific context separately
            "math_context": {},  # Only math-related info
            "db_context": {},    # Only database-related info
            "general_context": {}  # General conversation
        }
    )
    
    # User asks math question
    async for event in runner.run_async(
        user_id=user_id,
        session_id=session_id,
        new_message=types.UserContent(
            parts=[types.Part(text="What is 25 * 17?")]
        ),
        state_delta={
            "math_context": {
                "last_question": "What is 25 * 17?",
                "topic": "multiplication"
            }
        }
    ):
        if event.content:
            print(event.content)
    
    # User asks database question
    # Orchestrator should NOT send math context to DB agent!
    async for event in runner.run_async(
        user_id=user_id,
        session_id=session_id,
        new_message=types.UserContent(
            parts=[types.Part(text="Show me all users in the database")]
        ),
        state_delta={
            "db_context": {
                "last_query": "Show me all users",
                "table": "users"
            }
        }
    ):
        if event.content:
            print(event.content)
    
    await session_service.close()

asyncio.run(main())
```

### Token Cost Comparison

**❌ Without Optimization** (sending full context to all agents):
```
User: "What is 25 * 17?"
  → Orchestrator processes: 500 tokens (full history)
  → Remote Math receives: 500 tokens (full history) 
  → Remote DB receives: 500 tokens (full history) ❌ Not even called!
Total: 1500 tokens (wasteful!)
```

**✅ With Optimization** (filtered context):
```
User: "What is 25 * 17?"
  → Orchestrator processes: 500 tokens (full history)
  → Remote Math receives: 50 tokens (only math question) ✅
  → Remote DB: Not called ✅
Total: 550 tokens (efficient!)
```

**Savings: 950 tokens (63% reduction!)**

### Key Takeaways

1. **Orchestrator filters context**: The LLM in the orchestrator intelligently extracts only relevant context
2. **Sub-agents are stateless**: Remote agents typically don't receive full conversation history
3. **Use state for summaries**: Store agent-specific context in state, pass only summaries
4. **Instruct orchestrator clearly**: Tell the orchestrator to minimize context when routing
5. **Monitor token usage**: Track tokens to verify optimization is working

### Verification: Check What's Actually Sent

To verify context filtering is working:

```python
# Add logging to see what context is sent
import logging

logging.basicConfig(level=logging.DEBUG)

# When orchestrator calls remote agent, check logs:
# - What context is included?
# - Is it filtered or full history?
# - Are irrelevant agent contexts excluded?
```

---

## Part 3.5: Context Filtering Best Practices

### Example 2: Multi-Agent System with PostgreSQL

Here's a complete example showing how sessions work in a multi-agent A2A system:

```python
import asyncio
from google.adk import Agent
from google.adk.a2a import RemoteA2aAgent
from google.adk.sessions import DatabaseSessionService
from google.adk.sessions.state import State
from google.adk.runners import Runner
from google.genai import types

async def main():
    # Shared PostgreSQL database for all agents
    db_url = "postgresql+asyncpg://user:password@localhost:5432/multi_agent_db"
    
    # Orchestrator's session service
    orchestrator_session_service = DatabaseSessionService(db_url=db_url)
    
    # Create remote agent references
    remote_math = RemoteA2aAgent(
        name="remote_math",
        agent_card_url="http://localhost:8000/agent_card.json"
    )
    
    remote_db = RemoteA2aAgent(
        name="remote_db",
        agent_card_url="http://localhost:8001/agent_card.json"
    )
    
    # Create orchestrator agent
    orchestrator = Agent(
        name="orchestrator",
        model="gemini-1.5-flash",
        instruction="""You are a coordinator agent.
        - Math questions → remote_math
        - Database questions → remote_db
        - General questions → answer directly
        Maintain conversation context.""",
        sub_agents=[remote_math, remote_db]
    )
    
    runner = Runner(
        app_name="multi_agent_app",
        agent=orchestrator,
        session_service=orchestrator_session_service
    )
    
    user_id = "user123"
    session_id = "multi_agent_session_001"
    
    # Create session with initial state
    session = await orchestrator_session_service.create_session(
        app_name="multi_agent_app",
        user_id=user_id,
        session_id=session_id,
        state={
            # Session-level state
            "conversation_topic": None,
            "agents_used": [],
            "message_count": 0,
            # User-level state (will be loaded from DB automatically)
            # App-level state (will be loaded from DB automatically)
        }
    )
    
    print(f"=== Session Created ===")
    print(f"Session ID: {session.id}")
    print(f"Initial state: {session.state}")
    
    # Interaction 1: Math question
    print(f"\n=== Interaction 1: Math Question ===")
    async for event in runner.run_async(
        user_id=user_id,
        session_id=session_id,
        new_message=types.UserContent(
            parts=[types.Part(text="What is 25 * 17?")]
        ),
        state_delta={
            "conversation_topic": "mathematics",
            "agents_used": ["remote_math"],
            "message_count": 1
        }
    ):
        if event.content and event.content.parts:
            for part in event.content.parts:
                if part.text:
                    print(f"Agent: {part.text}")
    
    # Interaction 2: Follow-up (orchestrator maintains context)
    print(f"\n=== Interaction 2: Follow-up ===")
    async for event in runner.run_async(
        user_id=user_id,
        session_id=session_id,
        new_message=types.UserContent(
            parts=[types.Part(text="What about 30 * 20?")]
        ),
        state_delta={
            "message_count": 2
        }
    ):
        if event.content and event.content.parts:
            for part in event.content.parts:
                if part.text:
                    print(f"Agent: {part.text}")
    
    # Retrieve session and verify state
    print(f"\n=== Session State Verification ===")
    updated_session = await orchestrator_session_service.get_session(
        app_name="multi_agent_app",
        user_id=user_id,
        session_id=session_id
    )
    
    print(f"Total events: {len(updated_session.events)}")
    print(f"Conversation topic: {updated_session.state.get('conversation_topic')}")
    print(f"Agents used: {updated_session.state.get('agents_used')}")
    print(f"Message count: {updated_session.state.get('message_count')}")
    
    # Verify in database
    print(f"\n=== Database Verification ===")
    print(f"Check PostgreSQL database:")
    print(f"  SELECT * FROM sessions WHERE session_id = '{session_id}';")
    print(f"  SELECT * FROM events WHERE session_id = '{session_id}' ORDER BY timestamp;")
    print(f"  SELECT * FROM user_states WHERE user_id = '{user_id}';")
    
    await orchestrator_session_service.close()

asyncio.run(main())
```

### Key Points About Sessions in A2A

1. **Orchestrator Maintains Primary Session**
   - The orchestrator agent has the main session with the user
   - This session stores the full conversation history
   - State is managed at the orchestrator level

2. **Remote Agents Receive Context**
   - When orchestrator calls a remote agent, context is passed via A2A protocol
   - Remote agents can:
     - Use the orchestrator's session_id (recommended for continuity)
     - Create their own temporary sessions
     - Process without sessions (stateless)

3. **State Scoping Still Applies**
   - App-level state: Shared across all agents in the same app
   - User-level state: Shared across all agents for the same user
   - Session-level state: Specific to the orchestrator's session

4. **Database Storage**
   - If using `DatabaseSessionService`, all state is stored in PostgreSQL
   - Each agent server can use the same database or different databases
   - Using the same database allows sharing app-level and user-level state

---

## Part 4: Complete Multi-Agent Example with PostgreSQL

### Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    PostgreSQL Database                      │
│                                                             │
│  Tables:                                                    │
│  - sessions (orchestrator sessions)                       │
│  - events (all conversation events)                         │
│  - user_states (user-level state)                          │
│  - app_states (app-level state)                            │
└─────────────────────────────────────────────────────────────┘
         ▲                           ▲
         │                           │
    ┌────┴────┐                 ┌────┴────┐
    │         │                 │         │
┌───┴───┐ ┌───┴───┐         ┌───┴───┐ ┌───┴───┐
│Orch.  │ │Remote │         │Remote │ │Remote │
│Agent  │ │Math   │         │DB     │ │Code   │
│       │ │Agent  │         │Agent  │ │Agent  │
│Port   │ │Port   │         │Port   │ │Port   │
│3000   │ │8000   │         │8001   │ │8002   │
└───┬───┘ └───────┘         └───────┘ └───────┘
    │
    │ User interacts here
    ▼
┌─────────┐
│  User   │
└─────────┘
```

### Step 1: Remote Agent Servers

**Remote Math Agent Server** (`remote_math_server.py`):

```python
#!/usr/bin/env python3
"""Remote math agent server for A2A communication."""

from google.adk import Agent
from google.adk.apps import App
from google.adk.sessions import DatabaseSessionService
import uvicorn
import os

# Use same database for state sharing (optional)
db_url = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://user:password@localhost:5432/multi_agent_db"
)

# Remote agent can have its own session service
# Or it can be stateless and just process requests
remote_session_service = DatabaseSessionService(db_url=db_url)

# Create specialized math agent
math_agent = Agent(
    name="remote_math_agent",
    description="A remote agent specialized in mathematical problem solving",
    model="gemini-1.5-flash",
    instruction="""You are a math expert.
    Solve mathematical problems step by step.
    Show your work clearly.
    Be concise and accurate."""
)

# Create app with agent and optional session service
app = App(
    agent=math_agent,
    session_service=remote_session_service  # Optional: enables session support
)

if __name__ == "__main__":
    print("Starting remote math agent server on http://localhost:8000")
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

**Remote Database Agent Server** (`remote_db_server.py`):

```python
#!/usr/bin/env python3
"""Remote database agent server for A2A communication."""

from google.adk import Agent
from google.adk.apps import App
from google.adk.sessions import DatabaseSessionService
import uvicorn
import os

db_url = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://user:password@localhost:5432/multi_agent_db"
)

remote_session_service = DatabaseSessionService(db_url=db_url)

# Create specialized database agent
db_agent = Agent(
    name="remote_db_agent",
    description="A remote agent specialized in database queries",
    model="gemini-1.5-flash",
    instruction="""You are a database expert.
    Help users with database queries and operations.
    Be precise and explain your reasoning."""
)

app = App(
    agent=db_agent,
    session_service=remote_session_service
)

if __name__ == "__main__":
    print("Starting remote database agent server on http://localhost:8001")
    uvicorn.run(app, host="0.0.0.0", port=8001)
```

### Step 2: Orchestrator Client

**Orchestrator Client** (`orchestrator_client.py`):

```python
#!/usr/bin/env python3
"""Orchestrator client that coordinates multiple remote agents."""

import asyncio
from google.adk import Agent
from google.adk.a2a import RemoteA2aAgent
from google.adk.sessions import DatabaseSessionService
from google.adk.sessions.state import State
from google.adk.runners import Runner
from google.genai import types
import os

# Shared database for all agents
db_url = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://user:password@localhost:5432/multi_agent_db"
)

async def main():
    # Orchestrator's session service
    orchestrator_session_service = DatabaseSessionService(db_url=db_url)
    
    # Create remote agent references
    remote_math = RemoteA2aAgent(
        name="remote_math",
        agent_card_url="http://localhost:8000/agent_card.json"
    )
    
    remote_db = RemoteA2aAgent(
        name="remote_db",
        agent_card_url="http://localhost:8001/agent_card.json"
    )
    
    # Create orchestrator agent
    orchestrator = Agent(
        name="orchestrator",
        model="gemini-1.5-flash",
        instruction="""You are a coordinator agent that routes questions to specialized agents.
        
        Routing rules:
        - Math questions (calculations, equations, numbers) → remote_math
        - Database questions (SQL, queries, data) → remote_db
        - General questions → answer directly if you can
        
        Always maintain conversation context and remember previous interactions."""
    )
    
    # Add sub-agents
    orchestrator.sub_agents = [remote_math, remote_db]
    
    # Create runner with session service
    runner = Runner(
        app_name="multi_agent_app",
        agent=orchestrator,
        session_service=orchestrator_session_service
    )
    
    user_id = "user123"
    session_id = "multi_agent_session_001"
    
    # Create session with initial state
    session = await orchestrator_session_service.create_session(
        app_name="multi_agent_app",
        user_id=user_id,
        session_id=session_id,
        state={
            # Session-level state
            "conversation_topic": None,
            "agents_used": [],
            "message_count": 0,
            "user_name": None,
            # User-level and app-level state loaded automatically from DB
        }
    )
    
    print("=" * 80)
    print("Multi-Agent Orchestrator with PostgreSQL Sessions")
    print("=" * 80)
    print(f"\nSession ID: {session.id}")
    print(f"User ID: {user_id}")
    print(f"Database: {db_url.split('@')[-1] if '@' in db_url else db_url}")
    print("\nType 'quit' to exit.\n")
    
    while True:
        user_input = input("You: ")
        if user_input.lower() == 'quit':
            break
        
        print("\nAgent: ", end="", flush=True)
        
        # Update state based on interaction
        state_delta = {
            "message_count": session.state.get("message_count", 0) + 1
        }
        
        async for event in runner.run_async(
            user_id=user_id,
            session_id=session_id,
            new_message=types.UserContent(parts=[types.Part(text=user_input)]),
            state_delta=state_delta
        ):
            if event.content and event.content.parts:
                for part in event.content.parts:
                    if part.text:
                        print(part.text, end="", flush=True)
        
        print("\n")
        
        # Retrieve updated session
        session = await orchestrator_session_service.get_session(
            app_name="multi_agent_app",
            user_id=user_id,
            session_id=session_id
        )
    
    # Final session summary
    print("\n" + "=" * 80)
    print("Session Summary")
    print("=" * 80)
    final_session = await orchestrator_session_service.get_session(
        app_name="multi_agent_app",
        user_id=user_id,
        session_id=session_id
    )
    
    print(f"Total events: {len(final_session.events)}")
    print(f"Message count: {final_session.state.get('message_count')}")
    print(f"Agents used: {final_session.state.get('agents_used')}")
    print(f"Conversation topic: {final_session.state.get('conversation_topic')}")
    
    print(f"\nDatabase queries to verify:")
    print(f"  SELECT * FROM sessions WHERE session_id = '{session_id}';")
    print(f"  SELECT COUNT(*) FROM events WHERE session_id = '{session_id}';")
    print(f"  SELECT * FROM user_states WHERE user_id = '{user_id}';")
    
    await orchestrator_session_service.close()
    print("\n✅ Session closed. Goodbye!")

if __name__ == "__main__":
    asyncio.run(main())
```

### Step 3: Running the System

1. **Start Remote Agent Servers**:

```bash
# Terminal 1: Math Agent
python remote_math_server.py

# Terminal 2: Database Agent
python remote_db_server.py
```

2. **Start Orchestrator Client**:

```bash
# Terminal 3: Orchestrator
python orchestrator_client.py
```

3. **Interact with the System**:

```
You: What is 25 * 17?
Agent: [Orchestrator routes to remote_math] The result is 425.

You: What about 30 * 20?
Agent: [Orchestrator remembers context, routes to remote_math] The result is 600.

You: Show me all users in the database
Agent: [Orchestrator routes to remote_db] [Database query results]
```

### How Sessions Flow

1. **User sends message** → Orchestrator receives it
2. **Orchestrator creates/retrieves session** → Loads state from PostgreSQL
3. **Orchestrator routes to remote agent** → Passes context via A2A
4. **Remote agent processes** → May use its own session or be stateless
5. **Remote agent returns response** → Orchestrator receives it
6. **Orchestrator updates session** → Saves to PostgreSQL
7. **Orchestrator responds to user** → Maintains conversation context

### Database Verification

After running interactions, verify in PostgreSQL:

```sql
-- Check orchestrator session
SELECT * FROM sessions 
WHERE app_name = 'multi_agent_app' 
  AND user_id = 'user123' 
  AND session_id = 'multi_agent_session_001';

-- Check all events
SELECT 
    id,
    author,
    timestamp,
    content->'parts'->0->>'text' AS message_text
FROM events
WHERE app_name = 'multi_agent_app'
  AND user_id = 'user123'
  AND session_id = 'multi_agent_session_001'
ORDER BY timestamp ASC;

-- Check user-level state
SELECT * FROM user_states
WHERE app_name = 'multi_agent_app'
  AND user_id = 'user123';

-- Check app-level state
SELECT * FROM app_states
WHERE app_name = 'multi_agent_app';
```

---

## Summary

### Key Takeaways

1. **State in Google ADK**:
   - Organized into app-level, user-level, session-level, and temporary scopes
   - Automatically merged when retrieving sessions
   - Persisted in PostgreSQL when using `DatabaseSessionService`

2. **DatabaseSessionService**:
   - Stores sessions, events, and state in PostgreSQL
   - Automatically loads and merges state from multiple tables
   - Provides persistent storage for production applications

3. **Sessions in A2A Multi-Agent Systems**:
   - **Orchestrator maintains primary session** with the user
   - **Remote agents receive filtered context** via A2A protocol (not full history)
   - **Sessions can be shared** (same database) or separate
   - **State scoping applies** across all agents in the system

4. **Context Flow**:
   - User → Orchestrator (session maintained, full context)
   - Orchestrator → Remote Agent (**filtered context only**, not full history)
   - Remote Agent → Orchestrator (response returned)
   - Orchestrator → User (final response, session updated)

5. **⚠️ Token Cost Optimization** (CRITICAL):
   - **Orchestrator filters context** before sending to sub-agents
   - **Sub-agents receive only relevant information**, not full conversation
   - **Use state for summaries** instead of sending full history
   - **Instruct orchestrator** to minimize context when routing
   - **Monitor token usage** to verify optimization
   - **Avoid sending irrelevant context** (e.g., math context to DB agent)

6. **Best Practices**:
   - Use `DatabaseSessionService` with PostgreSQL for production
   - Share database across agents for unified state management
   - Let orchestrator maintain primary session
   - Use state prefixes correctly (app:, user:, temp:)
   - **Filter context per agent** to minimize token costs
   - **Keep remote agents stateless** when possible
   - Verify state in database after interactions

---

## Related Documentation

- [State Management](11-State-Management.md) - Detailed state management guide
- [Sessions Package](07-Sessions-Package.md) - Session service documentation
- [A2A Package](04-A2A-Package.md) - Agent-to-Agent communication
- [Runners Package](10-Runners-Package.md) - How runners use sessions

---

## Appendix: PostgreSQL Setup

### Install Dependencies

```bash
pip install google-adk
pip install sqlalchemy>=2.0
pip install asyncpg  # For PostgreSQL
```

### Create Database

```sql
CREATE DATABASE multi_agent_db;
CREATE USER adk_user WITH PASSWORD 'adk_password';
GRANT ALL PRIVILEGES ON DATABASE multi_agent_db TO adk_user;
```

### Connection String

```python
db_url = "postgresql+asyncpg://adk_user:adk_password@localhost:5432/multi_agent_db"
```

### Tables Created Automatically

`DatabaseSessionService` automatically creates:
- `sessions` - Session metadata and session-level state
- `events` - All conversation events
- `user_states` - User-level state
- `app_states` - App-level state
- `metadata` - Schema version information

No manual table creation needed!
