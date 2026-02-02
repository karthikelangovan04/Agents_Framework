# Google ADK Runners Package Documentation

**File Path**: `docs/10-Runners-Package.md`  
**Package**: `google.adk.runners`

## Overview

The `google.adk.runners` package provides the **execution engine** for Google ADK agents. While the `Agent` class defines what an agent is and how it behaves, the `Runner` class is responsible for **actually executing** the agent, managing its lifecycle, handling sessions, processing events, and coordinating with various services.

**Key Insight**: Creating an `Agent` instance (like in lines 95-100 of `01-Agents-Package.md`) is just **instantiation** - it defines the agent but doesn't run it. The `Runner` is what **executes** the agent and makes it functional.

## Package Structure

The runners package contains:

- **Runner**: The main execution engine for agents
- **InMemoryRunner**: A convenience class for testing and development with in-memory services

## Key Concepts

### Agent vs Runner

**Agent (`Agent` class)**:
- Defines the agent's behavior, model, instructions, tools, and capabilities
- Is a **configuration/blueprint** - it describes what the agent can do
- Cannot execute on its own

**Runner (`Runner` class)**:
- **Executes** the agent
- Manages the execution environment (sessions, memory, artifacts)
- Handles event streaming and processing
- Coordinates with services (session, memory, artifact, credential)
- Manages plugin callbacks and lifecycle

**Analogy**: Think of `Agent` as a recipe (what to cook) and `Runner` as the chef (who actually cooks it).

## Runner Class

### Purpose

The `Runner` class is the **orchestrator** that:

1. **Executes Agents**: Runs agents and manages their execution lifecycle
2. **Manages Sessions**: Handles conversation sessions, state, and history
3. **Processes Events**: Generates, filters, and streams events from agent execution
4. **Coordinates Services**: Integrates with artifact storage, session management, memory, and credential services
5. **Handles Plugins**: Executes plugin callbacks (before_run, on_event, after_run)
6. **Manages Resumability**: Supports resuming interrupted invocations
7. **Streams Responses**: Provides async event streaming for real-time interactions
8. **Handles Live Mode**: Supports live/streaming audio/video interactions

### Constructor Parameters

```python
Runner(
    app: Optional[App] = None,                    # App instance (recommended)
    app_name: Optional[str] = None,                # Application name
    agent: Optional[BaseAgent] = None,            # Root agent to run
    plugins: Optional[List[BasePlugin]] = None,  # Plugins (deprecated, use app)
    artifact_service: Optional[BaseArtifactService] = None,  # Artifact storage
    session_service: BaseSessionService,           # Session management (required)
    memory_service: Optional[BaseMemoryService] = None,  # Memory storage
    credential_service: Optional[BaseCredentialService] = None,  # Credentials
    plugin_close_timeout: float = 5.0,            # Plugin cleanup timeout
)
```

**Important**: You must provide either:
- An `app` instance (recommended), OR
- Both `app_name` and `agent`

### Key Attributes

```python
app_name: str                          # Application name
agent: BaseAgent                       # Root agent to execute
artifact_service: BaseArtifactService  # Artifact storage service
session_service: BaseSessionService     # Session management service
memory_service: BaseMemoryService      # Memory storage service
credential_service: BaseCredentialService  # Credential service
plugin_manager: PluginManager          # Plugin manager
context_cache_config: ContextCacheConfig  # Context caching config
resumability_config: ResumabilityConfig   # Resumability config
```

## Core Methods

### 1. `run()` - Synchronous Execution

**Purpose**: Synchronous wrapper for local testing and convenience.

```python
def run(
    self,
    *,
    user_id: str,
    session_id: str,
    new_message: types.Content,
    run_config: Optional[RunConfig] = None,
) -> Generator[Event, None, None]
```

**Note**: This is a convenience method that wraps `run_async()` in a thread. For production, use `run_async()`.

**Example**:
```python
runner = Runner(agent=agent, session_service=session_service)

# Synchronous execution
for event in runner.run(
    user_id="user123",
    session_id="session456",
    new_message=types.UserContent(parts=[types.Part(text="Hello!")])
):
    if event.content:
        print(event.content)
```

### 2. `run_async()` - Asynchronous Execution (Primary Method)

**Purpose**: Main entry point for running agents asynchronously. This is the **recommended method** for production use.

```python
async def run_async(
    self,
    *,
    user_id: str,
    session_id: str,
    invocation_id: Optional[str] = None,
    new_message: Optional[types.Content] = None,
    state_delta: Optional[dict[str, Any]] = None,
    run_config: Optional[RunConfig] = None,
) -> AsyncGenerator[Event, None]
```

**Parameters**:
- `user_id`: User identifier for the session
- `session_id`: Session identifier (must exist or be created)
- `invocation_id`: Optional invocation ID to resume a previous invocation
- `new_message`: New user message to process
- `state_delta`: Optional state changes to apply
- `run_config`: Configuration for this run

**Returns**: Async generator yielding `Event` objects

**What It Does**:

1. **Retrieves Session**: Gets or validates the session
2. **Creates Invocation Context**: Sets up context for the agent execution
3. **Handles New Message**: Processes and appends user message to session
4. **Finds Agent to Run**: Determines which agent should handle the message
5. **Executes Agent**: Runs the agent's `run_async()` method
6. **Processes Events**: 
   - Appends events to session
   - Applies plugin callbacks
   - Yields events to caller
7. **Runs Compaction**: If enabled, compacts events after invocation
8. **Handles Resumability**: Supports resuming interrupted invocations

**Example**:
```python
async def main():
    runner = Runner(
        agent=agent,
        session_service=InMemorySessionService()
    )
    
    # Create or get session
    session = await runner.session_service.create_session(
        app_name="my_app",
        user_id="user123",
        session_id="session456"
    )
    
    # Run agent
    async for event in runner.run_async(
        user_id="user123",
        session_id="session456",
        new_message=types.UserContent(parts=[types.Part(text="What is AI?")])
    ):
        if event.content and event.content.parts:
            for part in event.content.parts:
                if part.text:
                    print(part.text, end="", flush=True)
    print()  # New line after response

asyncio.run(main())
```

### 3. `run_live()` - Live/Streaming Execution

**Purpose**: Runs agent in live mode for audio/video streaming interactions (experimental).

```python
async def run_live(
    self,
    *,
    user_id: Optional[str] = None,
    session_id: Optional[str] = None,
    live_request_queue: LiveRequestQueue,
    run_config: Optional[RunConfig] = None,
    session: Optional[Session] = None,
) -> AsyncGenerator[Event, None]
```

**Use Cases**:
- Real-time audio conversations
- Video interactions
- Streaming responses
- Multi-modal live interactions

**Note**: This is an experimental feature and API may change.

### 4. `run_debug()` - Debug Helper

**Purpose**: Convenience method for quick testing and experimentation.

```python
async def run_debug(
    self,
    user_messages: str | list[str],
    *,
    user_id: str = 'debug_user_id',
    session_id: str = 'debug_session_id',
    run_config: RunConfig | None = None,
    quiet: bool = False,
    verbose: bool = False,
) -> list[Event]
```

**Features**:
- Automatically creates sessions
- Handles message formatting
- Prints output to console
- Returns all events for inspection

**Example**:
```python
runner = InMemoryRunner(agent=agent)

# Quick debug
events = await runner.run_debug("What is 2+2?")

# Multiple messages
events = await runner.run_debug([
    "Hello!",
    "What's my name?",
    "What did we discuss?"
])
```

**Important**: This is for debugging only. Use `run_async()` for production.

### 5. `rewind_async()` - Session Rewind

**Purpose**: Rewinds a session to before a specific invocation.

```python
async def rewind_async(
    self,
    *,
    user_id: str,
    session_id: str,
    rewind_before_invocation_id: str,
) -> None
```

**Use Cases**:
- Undoing agent actions
- Reverting state changes
- Restoring artifacts to previous versions

## Execution Flow

When you call `runner.run_async()`, here's what happens:

```
1. Session Retrieval
   ↓
2. Invocation Context Creation
   ↓
3. Plugin: before_run callbacks
   ↓
4. Message Processing & Appending
   ↓
5. Agent Selection (find_agent_to_run)
   ↓
6. Agent Execution (agent.run_async)
   ├── LLM Call
   ├── Tool Execution
   ├── Sub-agent Transfer
   └── Event Generation
   ↓
7. Event Processing
   ├── Append to Session
   ├── Plugin: on_event callbacks
   └── Yield to Caller
   ↓
8. Plugin: after_run callbacks
   ↓
9. Event Compaction (if enabled)
   ↓
10. Complete
```

## InMemoryRunner Class

### Purpose

A convenience class that provides in-memory implementations of all services, perfect for:
- Testing and development
- Quick prototyping
- Learning and experimentation
- Unit testing

### Constructor

```python
InMemoryRunner(
    agent: Optional[BaseAgent] = None,
    *,
    app_name: Optional[str] = None,
    plugins: Optional[list[BasePlugin]] = None,
    app: Optional[App] = None,
    plugin_close_timeout: float = 5.0,
)
```

**Key Features**:
- Automatically uses `InMemoryArtifactService`
- Automatically uses `InMemorySessionService`
- Automatically uses `InMemoryMemoryService`
- No external dependencies
- Perfect for local development

**Example**:
```python
from google.adk import Agent
from google.adk.runners import InMemoryRunner

# Create agent
agent = Agent(
    name="test_agent",
    model="gemini-1.5-flash",
    instruction="You are a helpful assistant."
)

# Create runner (no services needed!)
runner = InMemoryRunner(agent=agent)

# Use immediately
async def main():
    async for event in runner.run_async(
        user_id="user1",
        session_id="session1",
        new_message=types.UserContent(parts=[types.Part(text="Hello!")])
    ):
        if event.content:
            print(event.content)

asyncio.run(main())
```

## Example 1: Basic Runner Usage

Complete example showing agent instantiation vs execution:

```python
#!/usr/bin/env python3
"""Basic runner usage example."""

import asyncio
from google.adk import Agent
from google.adk.runners import InMemoryRunner
from google.genai import types

async def main():
    # Step 1: Create Agent (just instantiation - doesn't run)
    agent = Agent(
        name="simple_agent",
        description="A simple helpful assistant",
        model="gemini-1.5-flash",
        instruction="You are a helpful assistant. Answer questions clearly and concisely."
    )
    
    # Step 2: Create Runner (execution engine)
    runner = InMemoryRunner(agent=agent)
    
    # Step 3: Create session
    session = await runner.session_service.create_session(
        app_name="InMemoryRunner",
        user_id="user123",
        session_id="session456"
    )
    
    print("Agent created and runner ready!")
    print("Type 'quit' to exit.\n")
    
    while True:
        user_input = input("You: ")
        if user_input.lower() == 'quit':
            break
        
        print("\nAgent: ", end="", flush=True)
        
        # Step 4: Actually RUN the agent (this is where execution happens)
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

if __name__ == "__main__":
    asyncio.run(main())
```

**Key Points**:
- Line 10-15: Agent instantiation (just configuration)
- Line 18: Runner creation (execution engine)
- Line 21-25: Session creation
- Line 35-42: **Actual execution** - this is where the agent runs

## Example 2: Runner with Services

Using Runner with custom services:

```python
#!/usr/bin/env python3
"""Runner with custom services example."""

import asyncio
from google.adk import Agent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.adk.memory import InMemoryMemoryService
from google.adk.artifacts import InMemoryArtifactService
from google.genai import types

async def main():
    # Create agent
    agent = Agent(
        name="service_agent",
        model="gemini-1.5-flash",
        instruction="You are a helpful assistant with memory."
    )
    
    # Create services
    session_service = InMemorySessionService()
    memory_service = InMemoryMemoryService()
    artifact_service = InMemoryArtifactService()
    
    # Create runner with services
    runner = Runner(
        app_name="my_app",
        agent=agent,
        session_service=session_service,
        memory_service=memory_service,
        artifact_service=artifact_service
    )
    
    # Create session
    session = await session_service.create_session(
        app_name="my_app",
        user_id="user1",
        session_id="session1"
    )
    
    # Run agent
    async for event in runner.run_async(
        user_id="user1",
        session_id="session1",
        new_message=types.UserContent(parts=[types.Part(text="Hello!")])
    ):
        if event.content:
            print(event.content)

if __name__ == "__main__":
    asyncio.run(main())
```

## Example 3: Runner with Resumability

Resuming interrupted invocations:

```python
#!/usr/bin/env python3
"""Runner with resumability example."""

import asyncio
from google.adk import Agent
from google.adk.runners import InMemoryRunner
from google.adk.apps import App, ResumabilityConfig
from google.genai import types

async def main():
    # Create agent
    agent = Agent(
        name="resumable_agent",
        model="gemini-1.5-flash",
        instruction="You are a helpful assistant."
    )
    
    # Create app with resumability
    app = App(
        name="resumable_app",
        root_agent=agent,
        resumability_config=ResumabilityConfig(is_resumable=True)
    )
    
    # Create runner from app
    runner = InMemoryRunner(app=app)
    
    # Create session
    session = await runner.session_service.create_session(
        app_name="resumable_app",
        user_id="user1",
        session_id="session1"
    )
    
    # First invocation
    invocation_id = None
    async for event in runner.run_async(
        user_id="user1",
        session_id="session1",
        new_message=types.UserContent(parts=[types.Part(text="Count to 10")])
    ):
        if event.invocation_id:
            invocation_id = event.invocation_id
        print(f"Event: {event.id}")
        # Simulate interruption
        if event.id == "event_5":  # Interrupt after 5 events
            break
    
    print(f"\nInterrupted at invocation: {invocation_id}")
    
    # Resume the invocation
    print("\nResuming...")
    async for event in runner.run_async(
        user_id="user1",
        session_id="session1",
        invocation_id=invocation_id
    ):
        print(f"Event: {event.id}")

if __name__ == "__main__":
    asyncio.run(main())
```

## Example 4: Event Processing

Processing different event types:

```python
#!/usr/bin/env python3
"""Event processing example."""

import asyncio
from google.adk import Agent
from google.adk.runners import InMemoryRunner
from google.genai import types

async def main():
    agent = Agent(
        name="event_agent",
        model="gemini-1.5-flash",
        instruction="You are a helpful assistant."
    )
    
    runner = InMemoryRunner(agent=agent)
    
    session = await runner.session_service.create_session(
        app_name="InMemoryRunner",
        user_id="user1",
        session_id="session1"
    )
    
    async for event in runner.run_async(
        user_id="user1",
        session_id="session1",
        new_message=types.UserContent(parts=[types.Part(text="Hello!")])
    ):
        # Process different event types
        if event.content:
            print(f"[CONTENT] {event.content}")
        
        if event.get_function_calls():
            print(f"[TOOL CALL] {event.get_function_calls()}")
        
        if event.get_function_responses():
            print(f"[TOOL RESPONSE] {event.get_function_responses()}")
        
        if event.actions:
            print(f"[ACTIONS] {event.actions}")
        
        if hasattr(event, 'usage_metadata') and event.usage_metadata:
            print(f"[USAGE] {event.usage_metadata}")

if __name__ == "__main__":
    asyncio.run(main())
```

## Key Responsibilities of Runner

### 1. Session Management

- Retrieves or creates sessions
- Appends events to sessions
- Manages session state
- Handles session lifecycle

### 2. Event Processing

- Generates events from agent execution
- Filters events (e.g., live audio events)
- Appends events to session
- Streams events to callers
- Handles event ordering (e.g., transcription buffering)

### 3. Service Coordination

- Integrates with artifact service (file storage)
- Integrates with session service (conversation history)
- Integrates with memory service (long-term memory)
- Integrates with credential service (authentication)

### 4. Plugin Management

- Executes `before_run` callbacks
- Executes `on_event` callbacks
- Executes `after_run` callbacks
- Manages plugin lifecycle

### 5. Agent Routing

- Determines which agent should handle a message
- Handles agent transfers
- Manages sub-agent execution
- Finds agents in the agent tree

### 6. Resumability

- Supports resuming interrupted invocations
- Manages invocation context
- Handles state restoration
- Manages artifact versioning

### 7. Event Compaction

- Compacts events after invocation (if enabled)
- Reduces session size
- Maintains conversation context

### 8. Live Mode Support

- Handles live/streaming interactions
- Manages audio/video streams
- Buffers events for proper ordering
- Handles transcription synchronization

## Runner vs Agent: When to Use What

### Use Agent For:
- Defining agent behavior and capabilities
- Configuring models, instructions, tools
- Setting up agent hierarchy (sub-agents)
- Creating agent blueprints

### Use Runner For:
- Actually executing agents
- Managing execution environment
- Handling sessions and state
- Processing events
- Integrating with services
- Production deployments

## Best Practices

1. **Use `run_async()` for Production**: The synchronous `run()` method is just a convenience wrapper. Use `run_async()` for production code.

2. **Use `InMemoryRunner` for Development**: Perfect for testing, prototyping, and learning. No setup required.

3. **Use `Runner` with Services for Production**: Configure proper services (session, memory, artifact) for production deployments.

4. **Handle Events Properly**: Process events asynchronously and handle different event types appropriately.

5. **Manage Sessions**: Create sessions before running, and reuse session IDs for conversation continuity.

6. **Use App for Configuration**: Pass an `App` instance to Runner for better configuration management.

7. **Close Runner Properly**: Use async context manager or call `close()` to clean up resources.

```python
# Good: Using async context manager
async with InMemoryRunner(agent=agent) as runner:
    async for event in runner.run_async(...):
        process(event)

# Also good: Manual cleanup
runner = InMemoryRunner(agent=agent)
try:
    async for event in runner.run_async(...):
        process(event)
finally:
    await runner.close()
```

## Common Patterns

### Pattern 1: Simple Conversation Loop

```python
runner = InMemoryRunner(agent=agent)
session_id = "conversation_1"

while True:
    user_input = input("You: ")
    if user_input == "quit":
        break
    
    async for event in runner.run_async(
        user_id="user1",
        session_id=session_id,
        new_message=types.UserContent(parts=[types.Part(text=user_input)])
    ):
        if event.content:
            print(event.content)
```

### Pattern 2: Batch Processing

```python
messages = ["Hello", "How are you?", "What can you do?"]

for message in messages:
    async for event in runner.run_async(
        user_id="user1",
        session_id="batch_session",
        new_message=types.UserContent(parts=[types.Part(text=message)])
    ):
        process(event)
```

### Pattern 3: Event Collection

```python
events = []
async for event in runner.run_async(...):
    events.append(event)
    process(event)

# Analyze all events later
analyze_events(events)
```

## Troubleshooting

### Issue: "Session not found"

**Cause**: Session doesn't exist or app_name mismatch.

**Solution**:
```python
# Create session first
session = await runner.session_service.create_session(
    app_name=runner.app_name,  # Use runner's app_name
    user_id="user1",
    session_id="session1"
)
```

### Issue: Agent not executing

**Cause**: Only created agent, didn't use runner.

**Solution**: Use runner to execute:
```python
# Wrong: Just creating agent doesn't run it
agent = Agent(...)

# Right: Use runner to execute
runner = InMemoryRunner(agent=agent)
async for event in runner.run_async(...):
    process(event)
```

### Issue: Events not appearing

**Cause**: Not processing events correctly.

**Solution**: Check event types and content:
```python
async for event in runner.run_async(...):
    if event.content:
        print(event.content)
    if event.get_function_calls():
        print("Tool called:", event.get_function_calls())
```

### Issue: Session state not persisting

**Cause**: Using InMemoryRunner (in-memory only).

**Solution**: Use persistent session service:
```python
from google.adk.sessions import VertexAISessionService

runner = Runner(
    agent=agent,
    session_service=VertexAISessionService(...)  # Persistent
)
```

## Related Documentation

- [Agents Package](01-Agents-Package.md) - Creating agents
- [Sessions Package](07-Sessions-Package.md) - Session management
- [Memory Package](08-Memory-Package.md) - Memory services
- [Apps Package](05-Apps-Package.md) - App configuration
- [Events Package](09-Other-Packages.md#events-package) - Event types

## Summary

**Key Takeaways**:

1. **Agent = Configuration**: The `Agent` class defines what an agent can do
2. **Runner = Execution**: The `Runner` class actually executes the agent
3. **Instantiation ≠ Execution**: Creating an agent doesn't run it - you need a runner
4. **Use `run_async()`**: This is the primary method for running agents
5. **Use `InMemoryRunner` for Development**: Perfect for testing and prototyping
6. **Use `Runner` with Services for Production**: Configure proper services for production

The Runner is the **bridge** between agent definition and agent execution. It's what makes agents functional and usable in real applications.

---

**Last Updated**: 2025-01-27  
**Google ADK Version**: 1.22.1
