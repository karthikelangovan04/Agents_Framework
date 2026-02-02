# A2A-SDK Context and Memory Management

**File Path**: `docs-a2a-sdk/04-Context-and-Memory.md`  
**Package**: `a2a-sdk`  
**Related Docs**: 
- [ADK Memory and Session Runtime Trace](../docs/ADK-Memory-and-Session-Runtime-Trace.md)
- [A2A Multi-Agent Sessions and State](../docs/13-A2A-Multi-Agent-Sessions-and-State.md)
- [ADK State Management](../docs/11-State-Management.md)

## Overview

This document explains how **context** and **memory** work in A2A-SDK, comparing it with Google ADK's approach. You'll learn:

1. How A2A SDK manages short-term context
2. How A2A SDK handles long-term memory
3. How context flows in multi-agent orchestrator systems
4. Comparison with ADK's session/memory system
5. Best practices for context retention

---

## Part 1: Understanding Context in A2A SDK

### What is Context in A2A SDK?

**Context** in A2A SDK represents the runtime state and information available during agent interactions. Unlike ADK's session-based approach, A2A SDK uses **context objects** that are passed through the call chain.

### Key Context Types

#### 1. **ClientCallContext** (`a2a.client.middleware.ClientCallContext`)

**Purpose**: Manages context on the client side during A2A protocol calls.

**Location**: `a2a/client/middleware.py`

**Key Features**:
- Stores call-specific state
- Manages session IDs
- Handles request metadata
- Provides extension context
- Inherits from `A2ABaseModel` (Pydantic)

**Structure**:
```python
class ClientCallContext(A2ABaseModel):
    """Context for client-side A2A calls."""
    # State dictionary for storing call-specific data
    state: dict[str, Any] = {}
    # Session ID for tracking conversations
    session_id: Optional[str] = None
    # Request metadata
    request_metadata: dict[str, Any] = {}
    # Extension context
    extensions: list[str] = []
```

**Usage**:
```python
from a2a.client.middleware import ClientCallContext

# Create context for a call
context = ClientCallContext(
    session_id="session_123",
    state={"user_id": "user_456"},
    request_metadata={"source": "web"}
)

# Use context in client calls
async for event in client.send_message(
    message=message,
    context=context
):
    # Process events
    pass
```

#### 2. **ServerCallContext** (`a2a.server.context.ServerCallContext`)

**Purpose**: Manages context on the server side during request processing.

**Location**: `a2a/server/context.py`

**Key Features**:
- Server-side call state
- Request metadata
- User information
- Extension context
- Inherits from `A2ABaseModel`

**Structure**:
```python
class ServerCallContext(A2ABaseModel):
    """Context for server-side A2A calls."""
    # State dictionary
    state: dict[str, Any] = {}
    # User information
    user: Optional[User] = None
    # Request metadata
    request_metadata: dict[str, Any] = {}
    # Extension context
    extensions: list[str] = []
```

**Usage**:
```python
from a2a.server.context import ServerCallContext
from a2a.auth.user import User

# Create server context
context = ServerCallContext(
    user=User(user_id="user_123"),
    state={"agent_id": "agent_456"},
    request_metadata={"ip": "192.168.1.1"}
)

# Use in request handler
response = await handler.handle_request(
    request=request,
    context=context
)
```

#### 3. **RequestContext** (`a2a.server.agent_execution.context.RequestContext`)

**Purpose**: Context specifically for agent execution on the server.

**Location**: `a2a/server/agent_execution/context.py`

**Key Features**:
- Agent execution state
- User input tracking
- Extension management
- Related task tracking

**Methods**:
- `get_user_input()` - Get user input from context
- `add_activated_extension()` - Track activated extensions
- `attach_related_task()` - Link related tasks

**Usage**:
```python
from a2a.server.agent_execution.context import RequestContext

# RequestContext is created by RequestContextBuilder
context = await context_builder.build(request)

# Access user input
user_input = context.get_user_input()

# Track extensions
context.add_activated_extension("extension_name")

# Attach related task
context.attach_related_task(task_id)
```

---

## Part 2: Short-Term Context Retention

### How A2A SDK Retains Short-Term Context

**Short-term context** in A2A SDK refers to context that exists during a single request-response cycle or task execution.

#### Client-Side Short-Term Context

**Flow**:
```
User Request
    ↓
ClientCallContext Created
    ↓
Context Passed Through Transport
    ↓
Context Available in All Client Methods
    ↓
Context State Persisted in ClientTaskManager
```

**Example: Maintaining Context Across Multiple Calls**

```python
from a2a.client import Client, ClientConfig
from a2a.client.transports.rest import RestTransport
from a2a.client.middleware import ClientCallContext
from a2a.client.client_task_manager import ClientTaskManager

# Create client
config = ClientConfig(transport=RestTransport(...))
client = Client(config)

# Create task manager (maintains context)
task_manager = ClientTaskManager()

# Create context with session ID
context = ClientCallContext(
    session_id="session_123",
    state={"conversation_id": "conv_456"}
)

# First call - context is passed
async for event in client.send_message(
    message=Message(...),
    context=context
):
    # Task manager tracks context
    task_manager.process_event(event)
    if isinstance(event, tuple) and isinstance(event[0], Task):
        # Context is maintained in task
        task = event[0]
        print(f"Task ID: {task.id}")
        print(f"Context state: {context.state}")

# Second call - same context (maintains conversation)
context.state["message_count"] = context.state.get("message_count", 0) + 1

async for event in client.send_message(
    message=Message(...),
    context=context  # Same context = maintains conversation
):
    task_manager.process_event(event)
```

**Key Points**:
1. **ClientCallContext** is created per conversation/session
2. **State dictionary** persists across multiple calls with the same context
3. **ClientTaskManager** tracks task state and maintains context
4. **Session ID** links multiple calls together

#### Server-Side Short-Term Context

**Flow**:
```
Incoming Request
    ↓
ServerCallContext Created
    ↓
RequestContext Built (for agent execution)
    ↓
Context Passed to RequestHandler
    ↓
Context Available During Agent Execution
    ↓
Context State Updated During Processing
```

**Example: Server-Side Context Management**

```python
from a2a.server.request_handlers.jsonrpc_handler import JSONRPCHandler
from a2a.server.context import ServerCallContext
from a2a.server.agent_execution.context import RequestContext

class CustomHandler(JSONRPCHandler):
    async def handle_request(self, request, context: ServerCallContext):
        # Context is available throughout request processing
        user_id = context.user.user_id if context.user else None
        
        # Build request context for agent execution
        request_context = await self.context_builder.build(
            request,
            server_context=context
        )
        
        # Context state can be updated
        request_context.state["request_count"] = \
            request_context.state.get("request_count", 0) + 1
        
        # Execute agent with context
        response = await self.agent_executor.execute(
            request_context
        )
        
        return response
```

**Key Points**:
1. **ServerCallContext** is created per request
2. **RequestContext** is built for agent execution
3. **State updates** persist during request processing
4. **Context flows** through handler → executor → agent

---

## Part 3: Long-Term Memory and Persistence

### How A2A SDK Handles Long-Term Memory

**Long-term memory** in A2A SDK refers to persistent storage of conversations, tasks, and context across multiple sessions.

#### Conversation Storage

Unlike ADK's `Session` with `events` and `state`, A2A SDK uses **Task-based persistence**:

**ADK Approach**:
```python
# ADK: Session with events and state
session = await session_service.get_session(...)
session.events.append(new_event)
session.state.update(new_state)
await session_service.append_event(session, new_event)
```

**A2A SDK Approach**:
```python
# A2A SDK: Task-based with conversation in messages
task = await client.send_message(message, context=context)
# Task contains conversation history
# Task can be persisted to database
```

#### Task-Based Context Persistence

**Task Structure**:
```python
from a2a.types import Task

# Task contains:
task.id                    # Unique task ID
task.status                # Task status
task.messages              # Conversation messages (long-term)
task.artifacts             # Generated artifacts
task.metadata              # Task metadata
```

**Example: Persisting Tasks for Long-Term Memory**

```python
from a2a.client import Client
from a2a.client.middleware import ClientCallContext
from a2a.types import Task
import json

class TaskStorage:
    """Store tasks for long-term memory."""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self._init_db()
    
    def save_task(self, task: Task, context: ClientCallContext):
        """Save task with context for long-term memory."""
        task_data = {
            "task_id": task.id,
            "session_id": context.session_id,
            "task": task.model_dump(),  # Pydantic serialization
            "context_state": context.state,
            "messages": [msg.model_dump() for msg in task.messages] if task.messages else []
        }
        # Save to database/file
        # ...
    
    def load_task(self, task_id: str) -> tuple[Task, dict]:
        """Load task and context state."""
        # Load from database/file
        # Reconstruct Task and context state
        # ...

# Usage
storage = TaskStorage("tasks.db")

# Send message (creates task)
context = ClientCallContext(session_id="session_123")
async for event in client.send_message(message, context=context):
    if isinstance(event, tuple) and isinstance(event[0], Task):
        task = event[0]
        # Save for long-term memory
        storage.save_task(task, context)

# Later: Load conversation history
task, context_state = storage.load_task("task_456")
# Task contains all messages = conversation history
```

#### Comparison: ADK vs A2A SDK Long-Term Memory

| Aspect | ADK | A2A SDK |
|--------|-----|---------|
| **Storage Unit** | Session (with events + state) | Task (with messages + artifacts) |
| **Conversation History** | `session.events` (list of Event) | `task.messages` (list of Message) |
| **State Persistence** | `session.state` (dict) | `context.state` (dict) + `task.metadata` |
| **Retrieval** | `session_service.get_session()` | `client.get_task()` or custom storage |
| **Long-term Memory** | `MemoryService.search_memory()` | Task persistence + message history |
| **Semantic Search** | Vertex AI Memory Bank | Not built-in (can be added) |

---

## Part 4: Context Flow in Multi-Agent Orchestrator Systems

### How Context Flows in A2A Multi-Agent Systems

**Architecture**:
```
User
  ↓
Orchestrator Client (A2A SDK Client)
  ├── Maintains: ClientCallContext (short-term)
  ├── Persists: Tasks (long-term)
  └── Tracks: Conversation via session_id
  ↓
Remote Agent Server (A2A SDK Server)
  ├── Receives: Request with context
  ├── Creates: ServerCallContext
  └── Processes: RequestContext
  ↓
Response
  ↓
Orchestrator Client
  └── Updates: Task with new messages
```

### Example: Orchestrator with Context Retention

```python
from a2a.client import Client, ClientConfig
from a2a.client.transports.rest import RestTransport
from a2a.client.middleware import ClientCallContext
from a2a.client.client_task_manager import ClientTaskManager
from a2a.types import Message

class Orchestrator:
    """Orchestrator that maintains context across multiple agents."""
    
    def __init__(self):
        self.client = Client(ClientConfig(
            transport=RestTransport(base_url="http://agent-server:8000")
        ))
        self.task_manager = ClientTaskManager()
        # Long-term storage
        self.conversation_storage = {}
    
    async def process_user_message(
        self,
        user_message: str,
        user_id: str,
        session_id: str
    ):
        """Process user message with context retention."""
        
        # Get or create context for this session
        if session_id not in self.conversation_storage:
            context = ClientCallContext(
                session_id=session_id,
                state={
                    "user_id": user_id,
                    "message_count": 0,
                    "conversation_history": []
                }
            )
            self.conversation_storage[session_id] = {
                "context": context,
                "tasks": []
            }
        else:
            context = self.conversation_storage[session_id]["context"]
        
        # Update context state
        context.state["message_count"] += 1
        
        # Create message
        message = Message(
            role="user",
            content=[{"text": user_message}]
        )
        
        # Send message (maintains context)
        task = None
        async for event in self.client.send_message(
            message=message,
            context=context
        ):
            if isinstance(event, tuple) and isinstance(event[0], Task):
                task = event[0]
                # Track task
                self.task_manager.process_event(event)
                # Store for long-term memory
                self.conversation_storage[session_id]["tasks"].append(task)
        
        # Update conversation history in context
        if task and task.messages:
            context.state["conversation_history"].extend([
                msg.model_dump() for msg in task.messages
            ])
        
        return task
    
    async def get_conversation_history(self, session_id: str):
        """Retrieve full conversation history (long-term memory)."""
        if session_id not in self.conversation_storage:
            return []
        
        # Collect all messages from all tasks
        all_messages = []
        for task in self.conversation_storage[session_id]["tasks"]:
            if task.messages:
                all_messages.extend(task.messages)
        
        return all_messages

# Usage
orchestrator = Orchestrator()

# First message
task1 = await orchestrator.process_user_message(
    "Hello, I'm Alice",
    user_id="user_123",
    session_id="session_456"
)

# Second message (context maintained)
task2 = await orchestrator.process_user_message(
    "What's my name?",
    user_id="user_123",
    session_id="session_456"  # Same session = context retained
)

# Retrieve full conversation (long-term memory)
history = await orchestrator.get_conversation_history("session_456")
print(f"Total messages: {len(history)}")
```

### Context Filtering (Like ADK)

**Important**: A2A SDK doesn't automatically filter context like ADK does. You need to implement filtering:

```python
class ContextAwareOrchestrator:
    """Orchestrator that filters context before sending to agents."""
    
    def filter_context_for_agent(
        self,
        full_context: ClientCallContext,
        agent_name: str
    ) -> ClientCallContext:
        """Filter context to only relevant information."""
        
        # Get conversation history
        history = full_context.state.get("conversation_history", [])
        
        # Filter based on agent type
        if agent_name == "math_agent":
            # Only include math-related messages
            filtered = [
                msg for msg in history
                if self._is_math_related(msg)
            ]
        elif agent_name == "database_agent":
            # Only include database-related messages
            filtered = [
                msg for msg in history
                if self._is_database_related(msg)
            ]
        else:
            # Default: last 3 messages
            filtered = history[-3:]
        
        # Create filtered context
        filtered_context = ClientCallContext(
            session_id=full_context.session_id,
            state={
                **full_context.state,
                "conversation_history": filtered  # Filtered history
            }
        )
        
        return filtered_context
    
    async def call_agent_with_filtered_context(
        self,
        agent_name: str,
        message: Message,
        full_context: ClientCallContext
    ):
        """Call agent with only relevant context."""
        
        # Filter context
        filtered_context = self.filter_context_for_agent(
            full_context,
            agent_name
        )
        
        # Call agent with filtered context
        async for event in self.client.send_message(
            message=message,
            context=filtered_context
        ):
            yield event
```

---

## Part 5: Comparison with ADK Framework

### Side-by-Side Comparison

| Feature | ADK Framework | A2A SDK |
|---------|---------------|---------|
| **Short-term Context** | `InvocationContext.session` (Session object) | `ClientCallContext` / `ServerCallContext` |
| **Context Structure** | `session.events` + `session.state` | `context.state` dict + task messages |
| **Long-term Memory** | `MemoryService.search_memory()` | Task persistence + message history |
| **Session Management** | `SessionService` (DatabaseSessionService) | Custom storage (Task-based) |
| **Context Retrieval** | `session_service.get_session()` | `client.get_task()` or custom storage |
| **State Scoping** | app/user/session/temp prefixes | Flat state dict (can add prefixes) |
| **Event History** | `session.events` (list of Event) | `task.messages` (list of Message) |
| **Context Filtering** | Automatic (LLM-based) | Manual (developer implements) |
| **Multi-agent Context** | Shared session or filtered context | Task-based with context passing |

### Key Differences

#### 1. **Context Model**

**ADK**:
- Uses **Session** as the primary context container
- Session has `events` (conversation history) and `state` (key-value store)
- Hierarchical state with prefixes (`app:`, `user:`, session-level, `temp:`)

**A2A SDK**:
- Uses **Context objects** (ClientCallContext, ServerCallContext)
- Context has `state` dict (flat structure)
- Task contains `messages` (conversation history)
- No built-in hierarchical state (can be implemented)

#### 2. **Memory Retrieval**

**ADK**:
```python
# Long-term memory search
memories = await memory_service.search_memory(
    app_name="my_app",
    user_id="user_123",
    query="user preferences"
)
# Returns: SearchMemoryResponse with MemoryEntry objects
```

**A2A SDK**:
```python
# Long-term memory = task history
tasks = await storage.get_tasks_by_session("session_123")
conversation = []
for task in tasks:
    conversation.extend(task.messages)
# No built-in semantic search (can add with embeddings)
```

#### 3. **Context Persistence**

**ADK**:
- Automatic persistence via `SessionService.append_event()`
- State deltas automatically persisted
- Events stored in database

**A2A SDK**:
- Manual persistence (save tasks to storage)
- Context state must be manually persisted
- No automatic event storage (tasks contain messages)

---

## Part 6: Best Practices

### 1. **Use Session IDs for Context Linking**

```python
# ✅ GOOD: Use consistent session_id
context = ClientCallContext(session_id="session_123")

# ❌ BAD: New context for each call
context = ClientCallContext()  # No session_id = no context linking
```

### 2. **Store Context State in Task Metadata**

```python
# ✅ GOOD: Store context in task metadata
task.metadata = {
    "session_id": context.session_id,
    "user_id": context.state.get("user_id"),
    "message_count": context.state.get("message_count", 0)
}
```

### 3. **Implement Context Filtering**

```python
# ✅ GOOD: Filter context before sending to agents
filtered_context = filter_context_for_agent(full_context, agent_name)

# ❌ BAD: Send full context to all agents
# Wastes tokens and can confuse agents
```

### 4. **Persist Tasks for Long-Term Memory**

```python
# ✅ GOOD: Save tasks to database
await storage.save_task(task, context)

# ❌ BAD: Rely only on in-memory context
# Context lost on restart
```

### 5. **Use TaskManager for Context Tracking**

```python
# ✅ GOOD: Use ClientTaskManager
task_manager = ClientTaskManager()
task_manager.process_event(event)  # Tracks context

# ❌ BAD: Manual context tracking
# Easy to lose context
```

---

## Summary

### Key Takeaways

1. **Short-term Context**:
   - A2A SDK uses `ClientCallContext` and `ServerCallContext`
   - Context state persists during request/response cycle
   - Session ID links multiple calls together

2. **Long-term Memory**:
   - A2A SDK uses **Task-based persistence**
   - Tasks contain message history (conversation)
   - No built-in semantic search (unlike ADK's MemoryService)

3. **Context Flow**:
   - Orchestrator maintains context via `ClientCallContext`
   - Context passed to remote agents via protocol
   - Tasks track conversation history

4. **Comparison with ADK**:
   - ADK: Session-based with automatic persistence
   - A2A SDK: Context-based with manual persistence
   - ADK: Built-in semantic memory search
   - A2A SDK: Task-based message history

5. **Best Practices**:
   - Use consistent session IDs
   - Filter context before sending to agents
   - Persist tasks for long-term memory
   - Use TaskManager for context tracking

---

**Related Documentation**:
- [Client Package](02-Client-Package.md) - Client implementation details
- [Server Package](03-Server-Package.md) - Server implementation details
- [Task Management](07-Task-Management.md) - Task orchestration
- [ADK Memory and Session Runtime Trace](../docs/ADK-Memory-and-Session-Runtime-Trace.md) - ADK's approach

---

**Last Updated:** February 2, 2026  
**A2A-SDK Version:** 0.3.22
