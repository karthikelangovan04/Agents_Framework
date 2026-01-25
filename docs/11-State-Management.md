# Google ADK State Management Documentation

**File Path**: `docs/11-State-Management.md`  
**Package**: `google.adk.sessions.state`

## Overview

State management in Google ADK allows you to maintain and share data across different scopes: application-level, user-level, and session-level. The `State` class provides a unified interface for managing state with automatic delta tracking and prefix-based scoping.

## Key Concepts

### State Scopes

State in Google ADK is organized into three hierarchical scopes:

1. **Application-Level State** (`app:` prefix)
   - Shared across all users and sessions in an application
   - Persists across all sessions
   - Use for: global configuration, application settings, shared resources

2. **User-Level State** (`user:` prefix)
   - Specific to a user across all their sessions
   - Persists across sessions for the same user
   - Use for: user preferences, user profile data, user-specific settings

3. **Session-Level State** (no prefix)
   - Specific to a single session
   - Only exists during the session lifecycle
   - Use for: conversation context, temporary data, session-specific variables

4. **Temporary State** (`temp:` prefix)
   - Not persisted, only exists during event processing
   - Automatically discarded after event processing
   - Use for: intermediate calculations, temporary variables

### State Prefixes

```python
from google.adk.sessions.state import State

State.APP_PREFIX   # "app:"
State.USER_PREFIX  # "user:"
State.TEMP_PREFIX  # "temp:"
```

## Understanding Delta State

### What is Delta State?

**Delta state** represents **pending changes** that haven't been committed to persistent storage yet. The `State` class maintains two separate dictionaries:

1. **`value`** - The current committed state (what's been saved)
2. **`delta`** - Pending changes (what's been modified but not yet saved)

### How Delta Works

Think of it like this:
- **`value`** = What's in the database/file (committed state)
- **`delta`** = What you've changed in memory (pending changes)

When you read from state:
- If a key exists in `delta`, it returns the delta value (the latest change)
- Otherwise, it returns the value from `value` (the committed state)

When you write to state:
- Both `value` and `delta` are updated (for now - this may change in future versions)

### Why Use Delta?

Delta state provides several benefits:

1. **Efficient Updates**: Track only what changed, not the entire state
2. **Atomic Operations**: Batch multiple changes before committing
3. **Rollback Capability**: Can discard delta if needed before committing
4. **Performance**: Only persist changes, not the entire state each time

### Example: Delta in Action

```python
from google.adk.sessions.state import State

# Initial state (committed)
value = {"name": "Alice", "age": 25}
delta = {}  # No pending changes

state = State(value=value, delta=delta)

# Read from state - returns committed value
print(state["name"])  # "Alice" (from value)

# Make a change - updates both value and delta
state["age"] = 26

# Now delta has the change
print(state._delta)  # {"age": 26}
print(state["age"])  # 26 (from delta, takes precedence)

# Delta takes precedence when reading
state["name"] = "Bob"  # Update name
print(state["name"])   # "Bob" (from delta, not "Alice" from value)

# Check if there are pending changes
print(state.has_delta())  # True

# Get combined view
combined = state.to_dict()  # {"name": "Bob", "age": 26}
```

### Delta in Event Processing

When events are processed, state changes are tracked in `state_delta`:

```python
# Event with state_delta
event.actions.state_delta = {
    "message_count": 5,
    "user:last_active": "2024-01-01"
}

# This delta is extracted and applied:
# - App-level: keys with "app:" prefix
# - User-level: keys with "user:" prefix  
# - Session-level: keys without prefix
# - Temporary: keys with "temp:" prefix (discarded after processing)
```

## Real-World Scenarios

### Scenario 1: E-Commerce Shopping Cart

**Situation**: A user is shopping online, adding items to their cart.

```python
import asyncio
from google.adk.sessions import InMemorySessionService
from google.adk.sessions.state import State
from google.adk import Agent
from google.adk.runners import Runner
from google.genai import types

async def main():
    session_service = InMemorySessionService()
    agent = Agent(
        name="shopping_assistant",
        model="gemini-1.5-flash",
        instruction="You are a shopping assistant. Help users with their cart."
    )
    
    runner = Runner(
        app_name="ecommerce_app",
        agent=agent,
        session_service=session_service
    )
    
    # Initial session - user starts shopping
    session = await session_service.create_session(
        app_name="ecommerce_app",
        user_id="user123",
        session_id="shopping_session_001",
        state={
            "cart_items": [],           # Session-level: cart is per session
            "cart_total": 0.0,          # Session-level: total for this session
            State.USER_PREFIX + "loyalty_points": 1000,  # User-level: persists across sessions
            State.APP_PREFIX + "tax_rate": 0.08           # App-level: same for all users
        }
    )
    
    print("=== Initial State ===")
    print(f"Cart items: {session.state['cart_items']}")
    print(f"Cart total: ${session.state['cart_total']}")
    print(f"Loyalty points: {session.state[State.USER_PREFIX + 'loyalty_points']}")
    print(f"Tax rate: {session.state[State.APP_PREFIX + 'tax_rate']}")
    
    # User adds item - state_delta updates session state
    async for event in runner.run_async(
        user_id="user123",
        session_id="shopping_session_001",
        new_message=types.UserContent(parts=[types.Part(text="Add iPhone 15 to cart")]),
        state_delta={
            "cart_items": ["iPhone 15"],  # Delta: new cart items
            "cart_total": 999.99,          # Delta: updated total
            State.USER_PREFIX + "last_purchase_category": "electronics"  # Delta: user preference
        }
    ):
        if event.content:
            print(event.content)
    
    # Retrieve session - delta has been applied
    updated_session = await session_service.get_session(
        app_name="ecommerce_app",
        user_id="user123",
        session_id="shopping_session_001"
    )
    
    print("\n=== After Adding Item ===")
    print(f"Cart items: {updated_session.state['cart_items']}")  # ["iPhone 15"]
    print(f"Cart total: ${updated_session.state['cart_total']}")  # 999.99
    print(f"Last category: {updated_session.state[State.USER_PREFIX + 'last_purchase_category']}")
    
    # User adds another item - another delta update
    async for event in runner.run_async(
        user_id="user123",
        session_id="shopping_session_001",
        new_message=types.UserContent(parts=[types.Part(text="Add AirPods Pro too")]),
        state_delta={
            "cart_items": ["iPhone 15", "AirPods Pro"],  # Delta: updated cart
            "cart_total": 1299.98                          # Delta: new total
        }
    ):
        pass
    
    final_session = await session_service.get_session(
        app_name="ecommerce_app",
        user_id="user123",
        session_id="shopping_session_001"
    )
    
    print("\n=== After Adding Second Item ===")
    print(f"Cart items: {final_session.state['cart_items']}")  # ["iPhone 15", "AirPods Pro"]
    print(f"Cart total: ${final_session.state['cart_total']}")  # 1299.98
    
    # User starts new session - cart is empty, but loyalty points persist
    new_session = await session_service.create_session(
        app_name="ecommerce_app",
        user_id="user123",  # Same user
        session_id="shopping_session_002"  # New session
    )
    
    print("\n=== New Session (Same User) ===")
    print(f"Cart items: {new_session.state.get('cart_items', [])}")  # [] - empty (session-level)
    print(f"Loyalty points: {new_session.state[State.USER_PREFIX + 'loyalty_points']}")  # 1000 - persists!
    print(f"Last category: {new_session.state.get(State.USER_PREFIX + 'last_purchase_category')}")  # Persists!

asyncio.run(main())
```

**What Happens**:
- **Session-level state** (`cart_items`, `cart_total`): Resets in each new session
- **User-level state** (`loyalty_points`, `last_purchase_category`): Persists across all sessions for the same user
- **App-level state** (`tax_rate`): Same for all users and sessions
- **Delta updates**: Each `state_delta` incrementally updates the state

### Scenario 2: Customer Support Chat

**Situation**: A customer support agent handling multiple conversations.

```python
import asyncio
from google.adk.sessions import InMemorySessionService
from google.adk.sessions.state import State
from google.adk import Agent
from google.adk.runners import Runner
from google.genai import types

async def main():
    session_service = InMemorySessionService()
    agent = Agent(
        name="support_agent",
        model="gemini-1.5-flash",
        instruction="You are a helpful customer support agent."
    )
    
    runner = Runner(
        app_name="support_app",
        agent=agent,
        session_service=session_service
    )
    
    # Customer starts support chat
    session = await session_service.create_session(
        app_name="support_app",
        user_id="customer_456",
        session_id="support_chat_001",
        state={
            "conversation_topic": None,           # Session-level: topic for this chat
            "message_count": 0,                   # Session-level: messages in this chat
            "escalation_level": "tier1",         # Session-level: support tier
            State.USER_PREFIX + "total_tickets": 3,      # User-level: all-time tickets
            State.USER_PREFIX + "satisfaction_score": 4.5, # User-level: average rating
            State.APP_PREFIX + "business_hours": "9am-5pm EST"  # App-level: same for all
        }
    )
    
    # Customer sends first message
    async for event in runner.run_async(
        user_id="customer_456",
        session_id="support_chat_001",
        new_message=types.UserContent(parts=[types.Part(text="I need help with my order")]),
        state_delta={
            "conversation_topic": "order_issue",  # Delta: set topic
            "message_count": 1,                   # Delta: increment count
            State.TEMP_PREFIX + "processing_time": 0.5  # Temp: discarded after processing
        }
    ):
        if event.content:
            print(event.content)
    
    # Customer sends follow-up
    async for event in runner.run_async(
        user_id="customer_456",
        session_id="support_chat_001",
        new_message=types.UserContent(parts=[types.Part(text="Order #12345")]),
        state_delta={
            "message_count": 2,                   # Delta: increment
            "order_id": "12345",                  # Delta: store order ID
            State.USER_PREFIX + "last_contact_date": "2024-01-15"  # Delta: user-level update
        }
    ):
        pass
    
    # Issue resolved - escalate satisfaction
    async for event in runner.run_async(
        user_id="customer_456",
        session_id="support_chat_001",
        new_message=types.UserContent(parts=[types.Part(text="Thank you! Issue resolved")]),
        state_delta={
            "message_count": 3,
            "escalation_level": "resolved",       # Delta: update status
            State.USER_PREFIX + "total_tickets": 4,      # Delta: increment user-level
            State.USER_PREFIX + "satisfaction_score": 4.7  # Delta: update average
        }
    ):
        pass
    
    final_session = await session_service.get_session(
        app_name="support_app",
        user_id="customer_456",
        session_id="support_chat_001"
    )
    
    print("=== Support Chat Summary ===")
    print(f"Topic: {final_session.state['conversation_topic']}")
    print(f"Messages: {final_session.state['message_count']}")
    print(f"Status: {final_session.state['escalation_level']}")
    print(f"Order ID: {final_session.state.get('order_id')}")
    print(f"User total tickets: {final_session.state[State.USER_PREFIX + 'total_tickets']}")
    print(f"User satisfaction: {final_session.state[State.USER_PREFIX + 'satisfaction_score']}")
    
    # New chat session - session state resets, user state persists
    new_chat = await session_service.create_session(
        app_name="support_app",
        user_id="customer_456",  # Same customer
        session_id="support_chat_002"  # New chat
    )
    
    print("\n=== New Chat Session ===")
    print(f"Messages: {new_chat.state.get('message_count', 0)}")  # 0 - reset
    print(f"Topic: {new_chat.state.get('conversation_topic')}")   # None - reset
    print(f"User total tickets: {new_chat.state[State.USER_PREFIX + 'total_tickets']}")  # 4 - persists!

asyncio.run(main())
```

**What Happens**:
- **Session-level** (`conversation_topic`, `message_count`): Tracks current conversation only
- **User-level** (`total_tickets`, `satisfaction_score`): Builds customer history across all chats
- **App-level** (`business_hours`): Shared configuration
- **Temporary** (`processing_time`): Used during processing, then discarded

### Scenario 3: Multi-User Game with Leaderboards

**Situation**: A game where players compete, with app-wide leaderboards.

```python
import asyncio
from google.adk.sessions import InMemorySessionService
from google.adk.sessions.state import State
from google.adk import Agent
from google.adk.runners import Runner
from google.genai import types

async def main():
    session_service = InMemorySessionService()
    agent = Agent(
        name="game_assistant",
        model="gemini-1.5-flash",
        instruction="You are a game assistant helping players."
    )
    
    runner = Runner(
        app_name="game_app",
        agent=agent,
        session_service=session_service
    )
    
    # Player starts a game session
    session = await session_service.create_session(
        app_name="game_app",
        user_id="player_alice",
        session_id="game_session_001",
        state={
            "current_level": 1,                    # Session-level: level in this game
            "score": 0,                            # Session-level: score for this session
            "lives": 3,                            # Session-level: lives in this game
            State.USER_PREFIX + "total_wins": 10,         # User-level: all-time wins
            State.USER_PREFIX + "high_score": 5000,        # User-level: personal best
            State.USER_PREFIX + "preferred_difficulty": "medium",  # User-level: preference
            State.APP_PREFIX + "max_level": 100,           # App-level: game configuration
            State.APP_PREFIX + "leaderboard_enabled": True  # App-level: feature flag
        }
    )
    
    # Player progresses through levels
    async for event in runner.run_async(
        user_id="player_alice",
        session_id="game_session_001",
        new_message=types.UserContent(parts=[types.Part(text="Complete level 1")]),
        state_delta={
            "current_level": 2,                    # Delta: advance level
            "score": 1000,                          # Delta: add points
            State.TEMP_PREFIX + "level_completion_time": 120  # Temp: discarded
        }
    ):
        pass
    
    # Player completes more levels
    async for event in runner.run_async(
        user_id="player_alice",
        session_id="game_session_001",
        new_message=types.UserContent(parts=[types.Part(text="Complete level 2")]),
        state_delta={
            "current_level": 3,
            "score": 2500,                          # Delta: cumulative score
            "lives": 2                             # Delta: lost a life
        }
    ):
        pass
    
    # Player wins the game
    async for event in runner.run_async(
        user_id="player_alice",
        session_id="game_session_001",
        new_message=types.UserContent(parts=[types.Part(text="Win the game")]),
        state_delta={
            "current_level": 4,
            "score": 5000,                          # Delta: final score
            State.USER_PREFIX + "total_wins": 11,    # Delta: increment user wins
            State.USER_PREFIX + "high_score": 5000   # Delta: update if new record
        }
    ):
        pass
    
    final_session = await session_service.get_session(
        app_name="game_app",
        user_id="player_alice",
        session_id="game_session_001"
    )
    
    print("=== Game Session Summary ===")
    print(f"Final level: {final_session.state['current_level']}")
    print(f"Final score: {final_session.state['score']}")
    print(f"Remaining lives: {final_session.state['lives']}")
    print(f"Total wins: {final_session.state[State.USER_PREFIX + 'total_wins']}")
    print(f"High score: {final_session.state[State.USER_PREFIX + 'high_score']}")
    
    # Player starts new game - session resets, user stats persist
    new_game = await session_service.create_session(
        app_name="game_app",
        user_id="player_alice",
        session_id="game_session_002"
    )
    
    print("\n=== New Game Session ===")
    print(f"Starting level: {new_game.state.get('current_level', 1)}")  # 1 - reset
    print(f"Starting score: {new_game.state.get('score', 0)}")          # 0 - reset
    print(f"Total wins: {new_game.state[State.USER_PREFIX + 'total_wins']}")  # 11 - persists!
    print(f"High score: {new_game.state[State.USER_PREFIX + 'high_score']}")   # 5000 - persists!
    print(f"Max level: {new_game.state[State.APP_PREFIX + 'max_level']}")        # 100 - app-wide

asyncio.run(main())
```

**What Happens**:
- **Session-level** (`current_level`, `score`, `lives`): Game state for current session only
- **User-level** (`total_wins`, `high_score`): Player statistics across all games
- **App-level** (`max_level`, `leaderboard_enabled`): Game configuration for all players
- **Delta updates**: Each game action updates state incrementally

### Scenario 4: Delta State Flow Visualization

Here's how delta state flows through the system:

```python
# Step 1: Initial State (Committed)
value = {"count": 10, "name": "Alice"}
delta = {}  # Empty - no pending changes

state = State(value=value, delta=delta)
print(state["count"])  # 10 (from value)

# Step 2: Make Changes (Delta accumulates)
state["count"] = 15    # Delta: {"count": 15}
state["name"] = "Bob"  # Delta: {"count": 15, "name": "Bob"}

print(state["count"])  # 15 (from delta - takes precedence!)
print(state["name"])   # "Bob" (from delta - takes precedence!)

# Step 3: Check Pending Changes
print(state.has_delta())  # True
print(state._delta)      # {"count": 15, "name": "Bob"}

# Step 4: Event Processing
# When event is processed, state_delta is extracted:
state_delta = {
    "count": 15,
    "name": "Bob"
}

# Step 5: Commit (happens automatically when event is appended)
# Delta is merged into value, then delta is cleared
# value = {"count": 15, "name": "Bob"}
# delta = {}  # Cleared after commit

# Step 6: New Changes (new delta cycle)
state["count"] = 20  # New delta: {"count": 20}
print(state["count"])  # 20 (from new delta)
```

### Key Takeaways from Scenarios

1. **Session-level state** = Temporary, per-conversation data
   - Shopping cart items
   - Current conversation topic
   - Game session progress

2. **User-level state** = Persistent user data
   - Loyalty points
   - Total tickets
   - High scores
   - Preferences

3. **App-level state** = Global configuration
   - Tax rates
   - Business hours
   - Game settings
   - Feature flags

4. **Delta state** = Efficient change tracking
   - Only track what changed
   - Batch multiple updates
   - Commit atomically
   - Rollback if needed

These scenarios show how delta state enables efficient, scoped state management in real applications.

## How State Retrieval Works in Real-Time

### Automatic State Merging

**Yes, the system automatically retrieves and merges state from persistent storage!**

When you retrieve a session, the session service automatically:

1. **Loads session-level state** from the session storage
2. **Loads user-level state** from persistent storage (PostgreSQL, etc.) for that user
3. **Loads app-level state** from persistent storage for that application
4. **Merges all three** into a single unified state object

This happens **automatically** - you don't need to manually fetch user or app state.

### Real-Time Flow with PostgreSQL

Here's what happens behind the scenes when you use `DatabaseSessionService`:

```python
import asyncio
from google.adk.sessions import DatabaseSessionService
from google.adk.sessions.state import State
from google.adk import Agent
from google.adk.runners import Runner
from google.genai import types

async def main():
    # Using PostgreSQL for persistent storage
    session_service = DatabaseSessionService(
        db_url="postgresql+asyncpg://user:pass@localhost:5432/game_db"
    )
    
    agent = Agent(name="game_agent", model="gemini-1.5-flash")
    runner = Runner(
        app_name="game_app",
        agent=agent,
        session_service=session_service
    )
    
    # Step 1: Retrieve existing session
    # Behind the scenes, this automatically:
    # 1. Queries sessions table for session-level state
    # 2. Queries user_states table for user-level state (WHERE user_id = "player_alice")
    # 3. Queries app_states table for app-level state (WHERE app_name = "game_app")
    # 4. Merges all three into session.state
    session = await session_service.get_session(
        app_name="game_app",
        user_id="player_alice",
        session_id="game_session_001"
    )
    
    # Step 2: Access merged state
    # All state is automatically available, regardless of where it's stored
    print(session.state["current_level"])  # Session-level (from sessions table)
    print(session.state[State.USER_PREFIX + "total_wins"])  # User-level (from user_states table)
    print(session.state[State.APP_PREFIX + "max_level"])  # App-level (from app_states table)
    
    # Step 3: Make changes
    async for event in runner.run_async(
        user_id="player_alice",
        session_id="game_session_001",
        new_message=types.UserContent(parts=[types.Part(text="Complete level 5")]),
        state_delta={
            "current_level": 6,  # Session-level update
            State.USER_PREFIX + "total_wins": 12  # User-level update
        }
    ):
        pass
    
    # Step 4: State is automatically persisted
    # Behind the scenes:
    # - Session-level changes → saved to sessions table
    # - User-level changes → saved to user_states table
    # - App-level changes → saved to app_states table
    
    await session_service.close()

asyncio.run(main())
```

### Database Schema for State Storage

When using `DatabaseSessionService`, state is stored in separate tables:

```sql
-- Session-level state (per session)
CREATE TABLE sessions (
    id VARCHAR PRIMARY KEY,
    app_name VARCHAR,
    user_id VARCHAR,
    state JSONB,  -- Session-level state stored here
    ...
);

-- User-level state (per user, across all sessions)
CREATE TABLE user_states (
    app_name VARCHAR,
    user_id VARCHAR,
    key VARCHAR,
    value JSONB,  -- User-level state stored here
    PRIMARY KEY (app_name, user_id, key)
);

-- App-level state (per application, shared by all users)
CREATE TABLE app_states (
    app_name VARCHAR,
    key VARCHAR,
    value JSONB,  -- App-level state stored here
    PRIMARY KEY (app_name, key)
);
```

### What "App-Level" Means

**App-level state is application-wide configuration**, not per-agent or per-tournament. It's defined by the `app_name` parameter you pass to `Runner`:

```python
# Same app_name = same app-level state
runner1 = Runner(app_name="game_app", agent=agent1, ...)  # Uses "game_app" app-level state
runner2 = Runner(app_name="game_app", agent=agent2, ...)  # Same app-level state
runner3 = Runner(app_name="tournament_app", agent=agent3, ...)  # Different app-level state

# All sessions with app_name="game_app" share the same app-level state
# All sessions with app_name="tournament_app" share different app-level state
```

**Examples of App-Level State**:
- `app:max_level` - Maximum level in the game (same for all players)
- `app:leaderboard_enabled` - Feature flag (same for all players)
- `app:tax_rate` - Tax rate for e-commerce (same for all users)
- `app:business_hours` - Support hours (same for all customers)

**It's NOT**:
- ❌ Per-agent state (agents don't have their own app-level state)
- ❌ Per-tournament state (unless you use different `app_name` for tournaments)
- ❌ Per-user state (that's user-level)

### Detailed Game Scenario Explanation

Let's break down the Multi-User Game scenario with real database operations:

```python
import asyncio
from google.adk.sessions import DatabaseSessionService
from google.adk.sessions.state import State
from google.adk import Agent
from google.adk.runners import Runner
from google.genai import types

async def main():
    # PostgreSQL backend - all state persists here
    session_service = DatabaseSessionService(
        db_url="postgresql+asyncpg://user:pass@localhost:5432/game_db"
    )
    
    agent = Agent(name="game_agent", model="gemini-1.5-flash")
    runner = Runner(
        app_name="game_app",  # This defines the app-level scope
        agent=agent,
        session_service=session_service
    )
    
    # === SCENARIO: Player Alice starts a new game ===
    
    # When creating a session, the system automatically:
    # 1. Creates session record in 'sessions' table
    # 2. Queries 'user_states' table for player_alice's data
    #    SELECT * FROM user_states WHERE app_name='game_app' AND user_id='player_alice'
    #    → Returns: total_wins=10, high_score=5000, preferred_difficulty='medium'
    # 3. Queries 'app_states' table for game_app's config
    #    SELECT * FROM app_states WHERE app_name='game_app'
    #    → Returns: max_level=100, leaderboard_enabled=true
    # 4. Merges all into session.state
    
    session = await session_service.create_session(
        app_name="game_app",
        user_id="player_alice",
        session_id="game_session_001",
        state={
            "current_level": 1,  # Session-level: new game starts at level 1
            "score": 0,            # Session-level: score resets
            "lives": 3             # Session-level: lives reset
            # User-level and app-level are automatically loaded from database!
        }
    )
    
    # Access merged state (automatically includes user + app state)
    print("=== Session Created ===")
    print(f"Current level: {session.state['current_level']}")  # 1 (session-level)
    print(f"Score: {session.state['score']}")  # 0 (session-level)
    print(f"Total wins: {session.state[State.USER_PREFIX + 'total_wins']}")  # 10 (user-level, from DB)
    print(f"High score: {session.state[State.USER_PREFIX + 'high_score']}")  # 5000 (user-level, from DB)
    print(f"Max level: {session.state[State.APP_PREFIX + 'max_level']}")  # 100 (app-level, from DB)
    
    # === Player progresses ===
    async for event in runner.run_async(
        user_id="player_alice",
        session_id="game_session_001",
        new_message=types.UserContent(parts=[types.Part(text="Complete level 1")]),
        state_delta={
            "current_level": 2,  # Session-level: updates sessions table
            "score": 1000         # Session-level: updates sessions table
        }
    ):
        pass
    
    # === Player wins game ===
    async for event in runner.run_async(
        user_id="player_alice",
        session_id="game_session_001",
        new_message=types.UserContent(parts=[types.Part(text="Win the game")]),
        state_delta={
            "current_level": 4,
            "score": 5000,
            State.USER_PREFIX + "total_wins": 11,  # User-level: updates user_states table
            State.USER_PREFIX + "high_score": 5000  # User-level: updates user_states table
        }
    ):
        pass
    
    # === Player starts NEW game session ===
    # When retrieving, system automatically:
    # 1. Queries sessions table → new session, so session-level state is empty
    # 2. Queries user_states table → returns updated total_wins=11, high_score=5000
    # 3. Queries app_states table → returns max_level=100, leaderboard_enabled=true
    # 4. Merges all
    
    new_session = await session_service.create_session(
        app_name="game_app",
        user_id="player_alice",  # Same user
        session_id="game_session_002"  # New session
    )
    
    print("\n=== New Game Session ===")
    print(f"Current level: {new_session.state.get('current_level', 1)}")  # 1 (new session, resets)
    print(f"Score: {new_session.state.get('score', 0)}")  # 0 (new session, resets)
    print(f"Total wins: {new_session.state[State.USER_PREFIX + 'total_wins']}")  # 11 (persists from DB!)
    print(f"High score: {new_session.state[State.USER_PREFIX + 'high_score']}")  # 5000 (persists from DB!)
    print(f"Max level: {new_session.state[State.APP_PREFIX + 'max_level']}")  # 100 (app-wide, from DB!)
    
    # === Different player (Bob) starts game ===
    # System automatically:
    # 1. Queries user_states for player_bob → different user data
    # 2. Queries app_states for game_app → SAME app-level state (shared!)
    
    bob_session = await session_service.create_session(
        app_name="game_app",  # Same app
        user_id="player_bob",  # Different user
        session_id="game_session_003"
    )
    
    print("\n=== Different Player (Bob) ===")
    print(f"Bob's total wins: {bob_session.state.get(State.USER_PREFIX + 'total_wins', 0)}")  # Bob's data
    print(f"Bob's high score: {bob_session.state.get(State.USER_PREFIX + 'high_score', 0)}")  # Bob's data
    print(f"Max level: {bob_session.state[State.APP_PREFIX + 'max_level']}")  # 100 (SAME - app-wide!)
    
    await session_service.close()

asyncio.run(main())
```

### Key Points

1. **Automatic Retrieval**: User-level and app-level state are automatically loaded from PostgreSQL when you retrieve a session
2. **Automatic Merging**: All three state levels are merged into `session.state` automatically
3. **App-Level Scope**: Defined by `app_name` - all sessions with the same `app_name` share app-level state
4. **User-Level Scope**: Defined by `user_id` - all sessions for the same `user_id` share user-level state
5. **Session-Level Scope**: Defined by `session_id` - unique to each session
6. **Persistent Storage**: User-level and app-level state persist in PostgreSQL across sessions
7. **Real-Time**: State is automatically retrieved and merged every time you get a session

### Tournament Scenario

If you want tournament-specific state, use a different `app_name`:

```python
# Regular game
regular_runner = Runner(app_name="game_app", ...)
regular_session = await session_service.create_session(
    app_name="game_app",
    user_id="player_alice",
    session_id="regular_game_001"
)

# Tournament game (different app_name = different app-level state)
tournament_runner = Runner(app_name="tournament_app", ...)
tournament_session = await session_service.create_session(
    app_name="tournament_app",  # Different app = different app-level state
    user_id="player_alice",     # Same user = same user-level state
    session_id="tournament_001"
)

# Both sessions share:
# - Same user-level state (player_alice's stats)
# - Different app-level state (game_app vs tournament_app config)
# - Different session-level state (different games)
```

## State Class

### Overview

The `State` class maintains both the current state value and pending delta changes. This allows for efficient state updates and tracking of changes before they are committed.

### Constructor

```python
from google.adk.sessions.state import State

state = State(
    value: dict[str, Any],  # Current state value
    delta: dict[str, Any]   # Pending delta changes
)
```

### Methods

#### `__getitem__(key: str) -> Any`

Gets a value from state. Returns delta value if present, otherwise returns current value.

```python
state = State(value={"name": "Alice"}, delta={})
name = state["name"]  # Returns "Alice"

# Delta takes precedence
state = State(value={"name": "Alice"}, delta={"name": "Bob"})
name = state["name"]  # Returns "Bob"
```

#### `__setitem__(key: str, value: Any)`

Sets a value in state. Updates both current value and delta.

```python
state = State(value={}, delta={})
state["name"] = "Alice"
# Both state._value and state._delta are updated
```

#### `__contains__(key: str) -> bool`

Checks if a key exists in state (either in value or delta).

```python
state = State(value={"name": "Alice"}, delta={})
"name" in state  # True
"age" in state   # False
```

#### `get(key: str, default: Any = None) -> Any`

Gets a value with a default if key doesn't exist.

```python
state = State(value={"name": "Alice"}, delta={})
name = state.get("name", "Unknown")  # "Alice"
age = state.get("age", 0)            # 0 (default)
```

#### `setdefault(key: str, default: Any = None) -> Any`

Gets a value, or sets it to default if key doesn't exist.

```python
state = State(value={}, delta={})
name = state.setdefault("name", "Alice")  # Sets and returns "Alice"
age = state.setdefault("age", 0)         # Sets and returns 0
```

#### `update(delta: dict[str, Any])`

Updates state with multiple key-value pairs.

```python
state = State(value={}, delta={})
state.update({"name": "Alice", "age": 30})
# Updates both value and delta
```

#### `has_delta() -> bool`

Checks if there are pending delta changes.

```python
state = State(value={}, delta={})
state.has_delta()  # False

state["name"] = "Alice"
state.has_delta()  # True
```

#### `to_dict() -> dict[str, Any]`

Returns a dictionary combining current value and delta.

```python
state = State(value={"name": "Alice"}, delta={"age": 30})
state_dict = state.to_dict()
# Returns {"name": "Alice", "age": 30}
```

## State Scoping Examples

### Example 1: Application-Level State

Store application-wide configuration:

```python
import asyncio
from google.adk.sessions import InMemorySessionService
from google.adk.sessions.state import State

async def main():
    session_service = InMemorySessionService()
    
    # Create session with app-level state
    session = await session_service.create_session(
        app_name="my_app",
        user_id="user1",
        session_id="session1",
        state={
            State.APP_PREFIX + "version": "1.0.0",
            State.APP_PREFIX + "theme": "dark"
        }
    )
    
    # Access app-level state
    print(session.state[State.APP_PREFIX + "version"])  # "1.0.0"
    print(session.state[State.APP_PREFIX + "theme"])    # "dark"
    
    # App-level state is shared across all sessions
    session2 = await session_service.create_session(
        app_name="my_app",
        user_id="user2",
        session_id="session2"
    )
    
    # Same app-level state available
    print(session2.state[State.APP_PREFIX + "version"])  # "1.0.0"

asyncio.run(main())
```

### Example 2: User-Level State

Store user-specific preferences:

```python
import asyncio
from google.adk.sessions import InMemorySessionService
from google.adk.sessions.state import State

async def main():
    session_service = InMemorySessionService()
    
    # Create session with user-level state
    session = await session_service.create_session(
        app_name="my_app",
        user_id="alice",
        session_id="session1",
        state={
            State.USER_PREFIX + "language": "en",
            State.USER_PREFIX + "timezone": "UTC"
        }
    )
    
    # Access user-level state
    print(session.state[State.USER_PREFIX + "language"])  # "en"
    
    # User-level state persists across sessions for the same user
    session2 = await session_service.create_session(
        app_name="my_app",
        user_id="alice",  # Same user
        session_id="session2"
    )
    
    # Same user-level state available
    print(session2.state[State.USER_PREFIX + "language"])  # "en"

asyncio.run(main())
```

### Example 3: Session-Level State

Store session-specific context:

```python
import asyncio
from google.adk.sessions import InMemorySessionService

async def main():
    session_service = InMemorySessionService()
    
    # Create session with session-level state
    session = await session_service.create_session(
        app_name="my_app",
        user_id="user1",
        session_id="session1",
        state={
            "conversation_topic": "weather",
            "message_count": 0
        }
    )
    
    # Access session-level state (no prefix needed)
    print(session.state["conversation_topic"])  # "weather"
    print(session.state["message_count"])        # 0
    
    # Update session state
    session.state["message_count"] = 1

asyncio.run(main())
```

### Example 4: Temporary State

Use temporary state for intermediate calculations:

```python
import asyncio
from google.adk.sessions import InMemorySessionService
from google.adk.sessions.state import State
from google.adk import Agent
from google.adk.runners import Runner
from google.genai import types

async def main():
    session_service = InMemorySessionService()
    agent = Agent(
        name="calc_agent",
        model="gemini-1.5-flash",
        instruction="You are a calculator assistant."
    )
    
    runner = Runner(
        app_name="calc_app",
        agent=agent,
        session_service=session_service
    )
    
    session = await session_service.create_session(
        app_name="calc_app",
        user_id="user1",
        session_id="session1"
    )
    
    # Temporary state is used during event processing
    # It's automatically discarded after processing
    # You can use it in event.actions.state_delta:
    # {
    #     State.TEMP_PREFIX + "intermediate_result": 42
    # }

asyncio.run(main())
```

## State Delta Updates

State can be updated through events using `state_delta` in event actions. The session service automatically extracts and applies state deltas based on their prefixes.

### Example: Updating State via Events

```python
import asyncio
from google.adk.sessions import InMemorySessionService
from google.adk.sessions.state import State
from google.adk import Agent
from google.adk.runners import Runner
from google.genai import types

async def main():
    session_service = InMemorySessionService()
    agent = Agent(
        name="state_agent",
        model="gemini-1.5-flash",
        instruction="You are a helpful assistant."
    )
    
    runner = Runner(
        app_name="state_app",
        agent=agent,
        session_service=session_service
    )
    
    session = await session_service.create_session(
        app_name="state_app",
        user_id="user1",
        session_id="session1"
    )
    
    # State can be updated via run_async with state_delta parameter
    async for event in runner.run_async(
        user_id="user1",
        session_id="session1",
        new_message=types.UserContent(parts=[types.Part(text="Hello")]),
        state_delta={
            State.USER_PREFIX + "last_interaction": "2024-01-01",
            "session_count": 1
        }
    ):
        if event.content:
            print(event.content)
    
    # Retrieve updated session
    updated_session = await session_service.get_session(
        app_name="state_app",
        user_id="user1",
        session_id="session1"
    )
    
    if updated_session:
        print(updated_session.state[State.USER_PREFIX + "last_interaction"])
        print(updated_session.state["session_count"])

asyncio.run(main())
```

## State Extraction Utility

The `extract_state_delta` function separates state into app, user, and session deltas:

```python
from google.adk.sessions._session_util import extract_state_delta
from google.adk.sessions.state import State

state = {
    State.APP_PREFIX + "version": "1.0.0",
    State.USER_PREFIX + "language": "en",
    "session_id": "session1"
}

deltas = extract_state_delta(state)
# Returns:
# {
#     "app": {"version": "1.0.0"},
#     "user": {"language": "en"},
#     "session": {"session_id": "session1"}
# }
```

## Best Practices

### 1. Use Appropriate State Scopes

- **App-level**: Configuration that applies to all users
- **User-level**: Preferences and data specific to a user
- **Session-level**: Conversation context and temporary data
- **Temp-level**: Intermediate calculations (not persisted)

### 2. State Key Naming

Use descriptive, namespaced keys:

```python
# Good
State.APP_PREFIX + "api_version"
State.USER_PREFIX + "preferred_language"
"conversation_context"

# Avoid
"data"
"value"
"temp"
```

### 3. State Size Management

Keep state small and focused:

- Store references to external data, not the data itself
- Use compression for large data
- Clean up old state periodically
- Avoid storing sensitive data in state

### 4. State Persistence

- App-level and user-level state persist across sessions
- Session-level state only exists during the session
- Temporary state is discarded after event processing
- State is automatically persisted when events are appended

### 5. State Updates

- Use `state_delta` in events for incremental updates
- State changes are automatically tracked
- Delta changes take precedence over current values
- State is merged when sessions are retrieved

## Common Patterns

### Pattern 1: Initialize State on Session Creation

```python
session = await session_service.create_session(
    app_name="my_app",
    user_id="user1",
    session_id="session1",
    state={
        State.APP_PREFIX + "app_version": "1.0.0",
        State.USER_PREFIX + "user_preference": "default",
        "session_start_time": time.time()
    }
)
```

### Pattern 2: Update State During Execution

```python
# Update state via state_delta in run_async
async for event in runner.run_async(
    user_id="user1",
    session_id="session1",
    new_message=types.UserContent(parts=[types.Part(text="Hello")]),
    state_delta={
        "message_count": session.state.get("message_count", 0) + 1
    }
):
    # Process events
    pass
```

### Pattern 3: Access State Across Scopes

```python
# Get app-level state
app_version = session.state.get(State.APP_PREFIX + "version")

# Get user-level state
user_lang = session.state.get(State.USER_PREFIX + "language")

# Get session-level state
session_topic = session.state.get("conversation_topic")
```

## Troubleshooting

### Issue: State not persisting

**Problem**: State changes are lost between sessions.

**Solution**:
- Ensure you're using the correct prefix for the scope you want
- App-level and user-level state persist automatically
- Session-level state only exists during the session
- Check that events are being appended (state is persisted with events)

### Issue: State conflicts between scopes

**Problem**: State values are overwriting each other.

**Solution**:
- Use appropriate prefixes to avoid key conflicts
- App-level: `State.APP_PREFIX + "key"`
- User-level: `State.USER_PREFIX + "key"`
- Session-level: no prefix needed
- Temporary: `State.TEMP_PREFIX + "key"`

### Issue: State too large

**Problem**: State is consuming too much memory or storage.

**Solution**:
- Store references instead of full data
- Use external storage for large data
- Implement state cleanup
- Limit state size per scope

### Issue: Delta not applied

**Problem**: State delta changes aren't being reflected.

**Solution**:
- Ensure state_delta is passed correctly in run_async
- Check that events are being appended to the session
- Verify state prefixes are correct
- Temporary state (temp:) is automatically discarded

## Related Documentation

- [Sessions Package](07-Sessions-Package.md) - How sessions manage state
- [Runners Package](10-Runners-Package.md) - How runners use state_delta
- [Events Package](09-Other-Packages.md#events-package) - Event structure and state_delta

## API Reference

### State Class

```python
class State:
    APP_PREFIX: str = "app:"
    USER_PREFIX: str = "user:"
    TEMP_PREFIX: str = "temp:"
    
    def __init__(self, value: dict[str, Any], delta: dict[str, Any])
    def __getitem__(self, key: str) -> Any
    def __setitem__(self, key: str, value: Any)
    def __contains__(self, key: str) -> bool
    def get(self, key: str, default: Any = None) -> Any
    def setdefault(self, key: str, default: Any = None) -> Any
    def update(self, delta: dict[str, Any])
    def has_delta(self) -> bool
    def to_dict(self) -> dict[str, Any]
```

### Utility Functions

```python
def extract_state_delta(state: dict[str, Any]) -> dict[str, dict[str, Any]]:
    """Extracts app, user, and session state deltas from a state dictionary."""
    # Returns: {"app": {...}, "user": {...}, "session": {...}}
```
