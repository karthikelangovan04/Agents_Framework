# State Updates in ADK: Web UI and Programmatic Guide

**File Path**: `docs/23-State-Updates-in-ADK-Web-and-Programmatically.md`  
**Related Docs**: 
- [State Management](11-State-Management.md)
- [Sessions Package](07-Sessions-Package.md)
- [ADK Web Interface](14-ADK-Web-Interface-Analysis.md)
- [Callbacks Documentation](https://google.github.io/adk-docs/callbacks/)

## Overview

This document provides a comprehensive guide to updating session state in Google ADK, covering both the ADK Web UI and programmatic approaches. State management is a core feature that allows agents to maintain context, preferences, and data across interactions.

---

## Table of Contents

1. [Understanding State in ADK](#understanding-state-in-adk)
2. [When to Update State](#when-to-update-state)
3. [State Scopes and Prefixes](#state-scopes-and-prefixes)
4. [Updating State in ADK Web UI](#updating-state-in-adk-web-ui)
5. [Updating State Programmatically](#updating-state-programmatically)
6. [Updating State via Callbacks](#updating-state-via-callbacks)
7. [Real-World Examples](#real-world-examples)
8. [Best Practices](#best-practices)

---

## Understanding State in ADK

### What is State?

**State** in Google ADK is persistent data that agents can read and write during conversations. It's organized into hierarchical scopes that determine where and how long data persists:

- **Session-level state**: Temporary data specific to a single conversation session
- **User-level state**: Persistent data specific to a user across all their sessions
- **Application-level state**: Global configuration shared across all users and sessions
- **Temporary state**: Non-persisted data used during event processing

### Why Update State?

State updates enable agents to:

1. **Maintain Context**: Remember information from previous interactions in the same session
2. **Track User Preferences**: Store user-specific settings that persist across sessions
3. **Manage Application Configuration**: Store global settings that affect all users
4. **Implement Business Logic**: Track counters, flags, and workflow state
5. **Enable Personalization**: Remember user history, preferences, and behavior patterns

---

## When to Update State

### Common Scenarios

#### 1. **Session-Level State Updates**

Update session-level state when you need to track:
- **Conversation context**: Current topic, conversation flow, temporary variables
- **Session-specific counters**: Message count, interaction count, step number
- **Temporary data**: Shopping cart items, form data, current task state
- **Session metadata**: Start time, last activity, session flags

**Example Scenarios**:
- User adds items to shopping cart → Update `cart_items` and `cart_total`
- User progresses through a multi-step process → Update `current_step`
- Agent tracks conversation topic → Update `conversation_topic`

#### 2. **User-Level State Updates**

Update user-level state when you need to persist:
- **User preferences**: Language, theme, notification settings
- **User profile data**: Name, email, preferences, settings
- **User statistics**: Total interactions, high scores, achievements
- **User history**: Last login, last interaction date, activity patterns

**Example Scenarios**:
- User changes language preference → Update `user:preferred_language`
- User completes a purchase → Update `user:total_purchases` and `user:loyalty_points`
- User sets notification preferences → Update `user:notification_settings`

#### 3. **Application-Level State Updates**

Update app-level state when you need global configuration:
- **Feature flags**: Enable/disable features for all users
- **Configuration**: API versions, tax rates, business rules
- **Global counters**: Total users, system-wide statistics
- **Application settings**: Maintenance mode, rate limits

**Example Scenarios**:
- Admin enables a new feature → Update `app:feature_enabled`
- System updates tax rate → Update `app:tax_rate`
- Application version changes → Update `app:version`

#### 4. **State Updates via Callbacks**

Update state in callbacks when you need to:
- **Track agent behavior**: Log model calls, tool usage, decision points
- **Implement guardrails**: Block certain operations, enforce policies
- **Add metadata**: Track invocation details, performance metrics
- **Modify behavior**: Change agent behavior based on state

**Example Scenarios**:
- Track number of LLM calls → Update `llm_call_count` in `before_model_callback`
- Log tool usage → Update `tools_used` list in `after_tool_callback`
- Implement rate limiting → Update `request_count` in `before_agent_callback`

---

## State Scopes and Prefixes

### State Prefixes

ADK uses prefixes to distinguish between state scopes:

```python
from google.adk.sessions.state import State

# Application-level state (shared across all users)
State.APP_PREFIX   # "app:"

# User-level state (persists across sessions for same user)
State.USER_PREFIX  # "user:"

# Temporary state (discarded after event processing)
State.TEMP_PREFIX  # "temp:"

# Session-level state (no prefix needed)
# Just use the key directly: "conversation_topic"
```

### State Scope Examples

```python
# Session-level (no prefix)
state["message_count"] = 5
state["conversation_topic"] = "weather"
state["cart_items"] = ["item1", "item2"]

# User-level (user: prefix)
state[State.USER_PREFIX + "preferred_language"] = "en"
state[State.USER_PREFIX + "total_purchases"] = 10
state[State.USER_PREFIX + "last_login"] = "2024-01-15"

# Application-level (app: prefix)
state[State.APP_PREFIX + "version"] = "1.0.0"
state[State.APP_PREFIX + "tax_rate"] = 0.08
state[State.APP_PREFIX + "feature_enabled"] = True

# Temporary state (temp: prefix - not persisted)
state[State.TEMP_PREFIX + "intermediate_result"] = 42
```

---

## Updating State in ADK Web UI

### Accessing State Update in Dev UI

The ADK Web UI (Dev UI) provides a built-in interface for viewing and editing session state:

1. **Start ADK Web**:
   ```bash
   adk web [AGENTS_DIR]
   ```

2. **Navigate to Session**:
   - Open the Dev UI at `http://localhost:8000/dev-ui/`
   - Select a session from the session list
   - Start or continue a conversation

3. **Access State Editor**:
   - Click the **three dots (⋮) menu** button in the session interface
   - Select **"Update State"** or **"Edit State"** option
   - A state editor panel will open showing the current state (often displayed as `{}` if empty)

### Using the State Editor

The state editor in ADK Web UI allows you to:

1. **View Current State**: See all state keys and values for the current session
2. **Edit State Values**: Modify existing state values directly
3. **Add New State**: Add new state keys and values
4. **Delete State**: Remove state keys (set to `null` or delete key)

**State Editor Interface**:
- **JSON Editor**: State is displayed and edited as JSON
- **Real-time Updates**: Changes are reflected immediately
- **State Scopes**: You can see and edit session-level, user-level, and app-level state
- **Validation**: JSON syntax is validated before saving

### State Update API Endpoint

Behind the scenes, the ADK Web UI uses the REST API endpoint:

```
PATCH /apps/{app_name}/users/{user_id}/sessions/{session_id}
```

**Request Body** (`UpdateSessionRequest`):
```json
{
  "state_delta": {
    "message_count": 5,
    "user:preferred_language": "en",
    "app:version": "1.0.0"
  }
}
```

**Example using curl**:
```bash
curl -X PATCH "http://localhost:8000/apps/my_app/users/user123/sessions/session456" \
  -H "Content-Type: application/json" \
  -d '{
    "state_delta": {
      "conversation_topic": "weather",
      "message_count": 3
    }
  }'
```

### When State Shows as `{}`

If the state editor shows `{}` (empty object), it means:

1. **No state has been set yet**: The session was created without initial state
2. **State is empty**: All state keys have been cleared or never initialized
3. **State hasn't been loaded**: The session exists but state hasn't been populated

**To initialize state**:
- Add state keys manually in the editor
- Send a message that triggers state updates
- Use programmatic state updates (see below)

---

## Updating State Programmatically

### Method 1: Using `state_delta` in `run_async`

The most common way to update state is through the `state_delta` parameter in `runner.run_async()`:

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
        model="gemini-2.0-flash",
        instruction="You are a helpful assistant."
    )
    
    runner = Runner(
        app_name="state_app",
        agent=agent,
        session_service=session_service
    )
    
    # Create session
    session = await session_service.create_session(
        app_name="state_app",
        user_id="user123",
        session_id="session456"
    )
    
    # Update state via state_delta in run_async
    async for event in runner.run_async(
        user_id="user123",
        session_id="session456",
        new_message=types.UserContent(parts=[types.Part(text="Hello")]),
        state_delta={
            # Session-level updates
            "message_count": 1,
            "conversation_topic": "greeting",
            
            # User-level updates
            State.USER_PREFIX + "last_interaction": "2024-01-15",
            State.USER_PREFIX + "total_messages": 1,
            
            # App-level updates
            State.APP_PREFIX + "total_interactions": 1000
        }
    ):
        if event.content:
            print(event.content)
    
    # Retrieve updated session
    updated_session = await session_service.get_session(
        app_name="state_app",
        user_id="user123",
        session_id="session456"
    )
    
    print(f"Message count: {updated_session.state['message_count']}")
    print(f"Last interaction: {updated_session.state[State.USER_PREFIX + 'last_interaction']}")

asyncio.run(main())
```

### Method 2: Direct State Manipulation

You can directly modify session state, but changes are only persisted when events are appended:

```python
import asyncio
from google.adk.sessions import InMemorySessionService
from google.adk.sessions.state import State

async def main():
    session_service = InMemorySessionService()
    
    # Get existing session
    session = await session_service.get_session(
        app_name="my_app",
        user_id="user123",
        session_id="session456"
    )
    
    if session:
        # Direct state manipulation
        session.state["message_count"] = 5
        session.state["conversation_topic"] = "weather"
        session.state[State.USER_PREFIX + "preferred_language"] = "en"
        
        # To persist, append an event with state_delta
        from google.adk.events import Event
        await session_service.append_event(
            app_name="my_app",
            user_id="user123",
            session_id="session456",
            event=Event(
                invocation_id="inv_001",
                author="system",
                actions={"state_delta": session.state.delta}
            )
        )

asyncio.run(main())
```

### Method 3: Using Session Service Update (PATCH endpoint)

If you're building a custom API or using the REST API directly:

```python
import httpx
import asyncio

async def update_session_state():
    async with httpx.AsyncClient() as client:
        response = await client.patch(
            "http://localhost:8000/apps/my_app/users/user123/sessions/session456",
            json={
                "state_delta": {
                    "message_count": 5,
                    "conversation_topic": "weather",
                    "user:preferred_language": "en"
                }
            }
        )
        print(response.json())

asyncio.run(update_session_state())
```

### Method 4: Creating Session with Initial State

You can set initial state when creating a session:

```python
import asyncio
from google.adk.sessions import InMemorySessionService
from google.adk.sessions.state import State

async def main():
    session_service = InMemorySessionService()
    
    # Create session with initial state
    session = await session_service.create_session(
        app_name="my_app",
        user_id="user123",
        session_id="session456",
        state={
            # Session-level
            "message_count": 0,
            "conversation_topic": None,
            
            # User-level
            State.USER_PREFIX + "preferred_language": "en",
            State.USER_PREFIX + "total_sessions": 1,
            
            # App-level
            State.APP_PREFIX + "version": "1.0.0"
        }
    )
    
    print(f"Initial state: {session.state.to_dict()}")

asyncio.run(main())
```

---

## Updating State via Callbacks

Callbacks provide hooks to update state at specific points in agent execution. As mentioned in the [official callbacks documentation](https://google.github.io/adk-docs/callbacks/), you can "Manage State: Read or dynamically update the agent's session state during execution."

### Accessing State in Callbacks

The `CallbackContext` object provides access to the current session and its state:

```python
from google.adk.agents import LlmAgent
from google.adk.agents.callback_context import CallbackContext
from google.adk.models import LlmResponse, LlmRequest
from google.adk.sessions.state import State
from typing import Optional

def before_model_callback(
    callback_context: CallbackContext,
    llm_request: LlmRequest
) -> Optional[LlmResponse]:
    """Update state before model call."""
    
    # Access session state
    session = callback_context.session
    state = session.state
    
    # Read current state
    message_count = state.get("message_count", 0)
    
    # Update state (will be persisted when event is appended)
    state["message_count"] = message_count + 1
    state["last_model_call"] = "before_model"
    state[State.USER_PREFIX + "total_model_calls"] = (
        state.get(State.USER_PREFIX + "total_model_calls", 0) + 1
    )
    
    # Return None to proceed with model call
    return None

# Register callback
agent = LlmAgent(
    name="StateTrackingAgent",
    model="gemini-2.0-flash",
    instruction="You are a helpful assistant.",
    before_model_callback=before_model_callback
)
```

### Example: Tracking Tool Usage

```python
from google.adk.agents import LlmAgent
from google.adk.agents.callback_context import CallbackContext, ToolContext
from google.adk.sessions.state import State
from typing import Optional, Dict, Any

def after_tool_callback(
    callback_context: CallbackContext,
    tool_context: ToolContext,
    tool_result: Dict[str, Any]
) -> Optional[Dict[str, Any]]:
    """Track tool usage in state."""
    
    session = callback_context.session
    state = session.state
    
    # Get current tools used list
    tools_used = state.get("tools_used", [])
    
    # Add current tool to list
    tool_name = tool_context.tool_name
    if tool_name not in tools_used:
        tools_used.append(tool_name)
        state["tools_used"] = tools_used
    
    # Update user-level statistics
    user_tool_count = state.get(State.USER_PREFIX + "total_tool_calls", 0)
    state[State.USER_PREFIX + "total_tool_calls"] = user_tool_count + 1
    
    # Return None to use original tool result
    return None

agent = LlmAgent(
    name="ToolTrackingAgent",
    model="gemini-2.0-flash",
    instruction="You are a helpful assistant.",
    after_tool_callback=after_tool_callback
)
```

### Example: Implementing Guardrails with State

```python
from google.adk.agents import LlmAgent
from google.adk.agents.callback_context import CallbackContext
from google.adk.models import LlmResponse, LlmRequest
from google.adk.sessions.state import State
from typing import Optional

def before_model_guardrail(
    callback_context: CallbackContext,
    llm_request: LlmRequest
) -> Optional[LlmResponse]:
    """Implement rate limiting using state."""
    
    session = callback_context.session
    state = session.state
    
    # Get user-level request count
    user_id = callback_context.user_id
    request_count_key = State.USER_PREFIX + f"request_count_{user_id}"
    request_count = state.get(request_count_key, 0)
    
    # Check rate limit (e.g., 100 requests per day)
    if request_count >= 100:
        return LlmResponse(
            content=types.Content(
                role="model",
                parts=[types.Part(
                    text="Rate limit exceeded. Please try again tomorrow."
                )]
            )
        )
    
    # Increment request count
    state[request_count_key] = request_count + 1
    
    # Also track in session-level state
    session_request_count = state.get("session_request_count", 0)
    state["session_request_count"] = session_request_count + 1
    
    # Allow model call to proceed
    return None

agent = LlmAgent(
    name="RateLimitedAgent",
    model="gemini-2.0-flash",
    instruction="You are a helpful assistant.",
    before_model_callback=before_model_guardrail
)
```

### Example: State-Based Personalization

```python
from google.adk.agents import LlmAgent
from google.adk.agents.callback_context import CallbackContext
from google.adk.models import LlmResponse, LlmRequest
from google.adk.sessions.state import State
from google.genai import types
from typing import Optional

def before_model_personalize(
    callback_context: CallbackContext,
    llm_request: LlmRequest
) -> Optional[LlmResponse]:
    """Personalize responses based on user state."""
    
    session = callback_context.session
    state = session.state
    
    # Get user preferences from state
    preferred_language = state.get(State.USER_PREFIX + "preferred_language", "en")
    user_name = state.get(State.USER_PREFIX + "name", "User")
    conversation_style = state.get(State.USER_PREFIX + "conversation_style", "formal")
    
    # Modify system instruction based on user preferences
    if llm_request.config.system_instruction:
        original_instruction = llm_request.config.system_instruction.parts[0].text if llm_request.config.system_instruction.parts else ""
        
        personalized_instruction = f"""
        {original_instruction}
        
        User preferences:
        - Name: {user_name}
        - Language: {preferred_language}
        - Style: {conversation_style}
        
        Adapt your responses accordingly.
        """
        
        llm_request.config.system_instruction.parts[0].text = personalized_instruction
    
    # Track personalization usage
    state["personalization_applied"] = True
    
    return None

agent = LlmAgent(
    name="PersonalizedAgent",
    model="gemini-2.0-flash",
    instruction="You are a helpful assistant.",
    before_model_callback=before_model_personalize
)
```

---

## Real-World Examples

### Example 1: E-Commerce Shopping Cart

```python
import asyncio
from google.adk.sessions import InMemorySessionService
from google.adk.sessions.state import State
from google.adk import Agent
from google.adk.runners import Runner
from google.genai import types

async def shopping_cart_example():
    session_service = InMemorySessionService()
    agent = Agent(
        name="shopping_assistant",
        model="gemini-2.0-flash",
        instruction="You are a shopping assistant."
    )
    
    runner = Runner(
        app_name="ecommerce_app",
        agent=agent,
        session_service=session_service
    )
    
    # Create session with initial state
    session = await session_service.create_session(
        app_name="ecommerce_app",
        user_id="user123",
        session_id="shopping_session_001",
        state={
            "cart_items": [],
            "cart_total": 0.0,
            State.USER_PREFIX + "loyalty_points": 1000,
            State.APP_PREFIX + "tax_rate": 0.08
        }
    )
    
    # User adds item to cart
    async for event in runner.run_async(
        user_id="user123",
        session_id="shopping_session_001",
        new_message=types.UserContent(parts=[types.Part(text="Add iPhone 15 to cart")]),
        state_delta={
            "cart_items": ["iPhone 15"],
            "cart_total": 999.99,
            State.USER_PREFIX + "last_purchase_category": "electronics"
        }
    ):
        if event.content:
            print(event.content)
    
    # Retrieve updated session
    updated_session = await session_service.get_session(
        app_name="ecommerce_app",
        user_id="user123",
        session_id="shopping_session_001"
    )
    
    print(f"Cart items: {updated_session.state['cart_items']}")
    print(f"Cart total: ${updated_session.state['cart_total']}")
    print(f"Loyalty points: {updated_session.state[State.USER_PREFIX + 'loyalty_points']}")

asyncio.run(shopping_cart_example())
```

### Example 2: Customer Support with State Tracking

```python
import asyncio
from google.adk.sessions import InMemorySessionService
from google.adk.sessions.state import State
from google.adk import Agent
from google.adk.runners import Runner
from google.genai import types

async def support_chat_example():
    session_service = InMemorySessionService()
    agent = Agent(
        name="support_agent",
        model="gemini-2.0-flash",
        instruction="You are a customer support agent."
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
            "conversation_topic": None,
            "message_count": 0,
            "escalation_level": "tier1",
            State.USER_PREFIX + "total_tickets": 3,
            State.USER_PREFIX + "satisfaction_score": 4.5
        }
    )
    
    # Customer sends message
    async for event in runner.run_async(
        user_id="customer_456",
        session_id="support_chat_001",
        new_message=types.UserContent(parts=[types.Part(text="I need help with my order")]),
        state_delta={
            "conversation_topic": "order_issue",
            "message_count": 1
        }
    ):
        if event.content:
            print(event.content)
    
    # Issue resolved
    async for event in runner.run_async(
        user_id="customer_456",
        session_id="support_chat_001",
        new_message=types.UserContent(parts=[types.Part(text="Thank you! Issue resolved")]),
        state_delta={
            "message_count": 2,
            "escalation_level": "resolved",
            State.USER_PREFIX + "total_tickets": 4,
            State.USER_PREFIX + "satisfaction_score": 4.7
        }
    ):
        pass
    
    # Retrieve final session state
    final_session = await session_service.get_session(
        app_name="support_app",
        user_id="customer_456",
        session_id="support_chat_001"
    )
    
    print(f"Topic: {final_session.state['conversation_topic']}")
    print(f"Messages: {final_session.state['message_count']}")
    print(f"Total tickets: {final_session.state[State.USER_PREFIX + 'total_tickets']}")

asyncio.run(support_chat_example())
```

### Example 3: Game with Leaderboards

```python
import asyncio
from google.adk.sessions import InMemorySessionService
from google.adk.sessions.state import State
from google.adk import Agent
from google.adk.runners import Runner
from google.genai import types

async def game_example():
    session_service = InMemorySessionService()
    agent = Agent(
        name="game_assistant",
        model="gemini-2.0-flash",
        instruction="You are a game assistant."
    )
    
    runner = Runner(
        app_name="game_app",
        agent=agent,
        session_service=session_service
    )
    
    # Player starts game
    session = await session_service.create_session(
        app_name="game_app",
        user_id="player_alice",
        session_id="game_session_001",
        state={
            "current_level": 1,
            "score": 0,
            "lives": 3,
            State.USER_PREFIX + "total_wins": 10,
            State.USER_PREFIX + "high_score": 5000,
            State.APP_PREFIX + "max_level": 100
        }
    )
    
    # Player progresses
    async for event in runner.run_async(
        user_id="player_alice",
        session_id="game_session_001",
        new_message=types.UserContent(parts=[types.Part(text="Complete level 1")]),
        state_delta={
            "current_level": 2,
            "score": 1000
        }
    ):
        pass
    
    # Player wins
    async for event in runner.run_async(
        user_id="player_alice",
        session_id="game_session_001",
        new_message=types.UserContent(parts=[types.Part(text="Win the game")]),
        state_delta={
            "current_level": 4,
            "score": 5000,
            State.USER_PREFIX + "total_wins": 11,
            State.USER_PREFIX + "high_score": 5000
        }
    ):
        pass
    
    # Retrieve updated session
    final_session = await session_service.get_session(
        app_name="game_app",
        user_id="player_alice",
        session_id="game_session_001"
    )
    
    print(f"Final level: {final_session.state['current_level']}")
    print(f"Final score: {final_session.state['score']}")
    print(f"Total wins: {final_session.state[State.USER_PREFIX + 'total_wins']}")

asyncio.run(game_example())
```

---

## Best Practices

### 1. Use Appropriate State Scopes

- **Session-level**: Temporary data, conversation context, session-specific variables
- **User-level**: Persistent user data, preferences, statistics
- **App-level**: Global configuration, feature flags, shared settings
- **Temporary**: Intermediate calculations (automatically discarded)

### 2. State Key Naming

Use descriptive, namespaced keys:

```python
# Good
State.APP_PREFIX + "api_version"
State.USER_PREFIX + "preferred_language"
"conversation_topic"
"message_count"

# Avoid
"data"
"value"
"temp"
"x"
```

### 3. State Size Management

Keep state small and focused:

- Store references to external data, not the data itself
- Use compression for large data
- Clean up old state periodically
- Avoid storing sensitive data in state

### 4. State Persistence

- **App-level and user-level state**: Persist across sessions automatically
- **Session-level state**: Only exists during the session lifecycle
- **Temporary state**: Discarded after event processing
- **State is persisted**: Automatically when events are appended

### 5. State Updates

- Use `state_delta` in `run_async` for incremental updates
- State changes are automatically tracked
- Delta changes take precedence over current values
- State is merged when sessions are retrieved

### 6. Error Handling

Always handle cases where state might not exist:

```python
# Good: Use .get() with defaults
message_count = state.get("message_count", 0)
preferred_language = state.get(State.USER_PREFIX + "preferred_language", "en")

# Avoid: Direct access without checking
message_count = state["message_count"]  # KeyError if not exists
```

### 7. State Validation

Validate state updates before applying:

```python
def validate_state_update(state_delta: dict) -> bool:
    """Validate state updates before applying."""
    # Check required keys
    if "message_count" in state_delta:
        if not isinstance(state_delta["message_count"], int):
            return False
    
    # Check value ranges
    if "score" in state_delta:
        if state_delta["score"] < 0:
            return False
    
    return True
```

### 8. State Updates in Callbacks

When updating state in callbacks:

- Access state via `callback_context.session.state`
- State changes are persisted when events are appended
- Use appropriate prefixes for state scopes
- Don't modify state in a way that breaks agent execution

---

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
async for event in runner.run_async(
    user_id="user1",
    session_id="session1",
    new_message=types.UserContent(parts=[types.Part(text="Hello")]),
    state_delta={
        "message_count": session.state.get("message_count", 0) + 1
    }
):
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

### Pattern 4: Update State in Callbacks

```python
def before_model_callback(
    callback_context: CallbackContext,
    llm_request: LlmRequest
) -> Optional[LlmResponse]:
    session = callback_context.session
    state = session.state
    
    # Update state
    state["model_call_count"] = state.get("model_call_count", 0) + 1
    
    return None
```

---

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
- Ensure `state_delta` is passed correctly in `run_async`
- Check that events are being appended to the session
- Verify state prefixes are correct
- Temporary state (`temp:`) is automatically discarded

### Issue: State shows as `{}` in Web UI

**Problem**: State editor shows empty object.

**Solution**:
- Initialize state when creating session
- Send a message that triggers state updates
- Use programmatic state updates
- Check that session exists and is loaded correctly

---

## Related Documentation

- [State Management](11-State-Management.md) - Comprehensive state management guide
- [Sessions Package](07-Sessions-Package.md) - How sessions manage state
- [Runners Package](10-Runners-Package.md) - How runners use state_delta
- [ADK Web Interface](14-ADK-Web-Interface-Analysis.md) - Web UI details
- [Callbacks Documentation](https://google.github.io/adk-docs/callbacks/) - Official callbacks guide
- [Events Package](09-Other-Packages.md#events-package) - Event structure and state_delta

---

## Summary

State updates in ADK can be performed:

1. **In ADK Web UI**: Use the three-dots menu → "Update State" option
2. **Programmatically**: Via `state_delta` in `run_async()`, direct state manipulation, or REST API
3. **Via Callbacks**: Access and modify state in callback functions using `CallbackContext`

State is organized into scopes (session, user, app, temp) using prefixes, and updates are automatically persisted when events are appended. Choose the appropriate scope and method based on your use case.

---

**Last Updated**: 2025-02-05  
**Related**: [State Management](11-State-Management.md), [Callbacks](https://google.github.io/adk-docs/callbacks/)
