# A2A-SDK Server Package Documentation

**File Path**: `docs-a2a-sdk/03-Server-Package.md`  
**Package**: `a2a.server`

## Overview

The `a2a.server` package provides the server implementation for building A2A agent servers. It includes request handlers, agent execution, framework integrations, task management, and event systems.

## Key Classes

### RequestHandler

Base class for all request handlers.

**Location**: `a2a.server.request_handlers.request_handler`

**Key Methods**: 9 methods including request processing, response generation, error handling

### JSONRPCHandler

Handler for JSON-RPC protocol requests.

**Location**: `a2a.server.request_handlers.jsonrpc_handler`

**Key Methods**: 11 methods

**Usage**:
```python
from a2a.server.request_handlers.jsonrpc_handler import JSONRPCHandler
from a2a.types import AgentCard

handler = JSONRPCHandler(
    agent_card=AgentCard(name="my_agent"),
    # Add your agent logic
)
```

### RESTHandler

Handler for REST protocol requests.

**Location**: `a2a.server.request_handlers.rest_handler`

**Key Methods**: 10 methods

### AgentExecutor

Executes agent logic for incoming requests.

**Location**: `a2a.server.agent_execution.agent_executor`

**Key Methods**: 2 methods

### RequestContext

Context for agent execution.

**Location**: `a2a.server.agent_execution.context`

**Key Methods**:
- `get_user_input()` - Get user input
- `add_activated_extension()` - Track extensions
- `attach_related_task()` - Link tasks

### TaskManager

Manages task lifecycle and orchestration.

**Location**: `a2a.server.tasks.task_manager`

**Key Methods**: 6 methods

### ServerCallContext

Server-side call context.

**Location**: `a2a.server.context`

**Key Properties**:
- `state` - Server state dictionary
- `user` - User information
- `request_metadata` - Request metadata

## Example 1: Basic Server

Create a simple A2A server using FastAPI:

```python
#!/usr/bin/env python3
"""Basic A2A server example."""

from a2a.server.apps.jsonrpc.fastapi_app import A2AFastAPI
from a2a.server.request_handlers.jsonrpc_handler import JSONRPCHandler
from a2a.types import AgentCard, Message
import uvicorn

# Create agent card
agent_card = AgentCard(
    name="simple_agent",
    description="A simple A2A agent"
)

# Create request handler
async def handle_message(request: Message, context) -> Message:
    """Handle incoming message."""
    user_text = request.content[0].get("text", "") if request.content else ""
    
    # Simple echo response
    response = Message(
        role="agent",
        content=[{"text": f"You said: {user_text}"}]
    )
    return response

handler = JSONRPCHandler(
    agent_card=agent_card,
    message_handler=handle_message
)

# Create FastAPI app
app = A2AFastAPI(handler=handler)

if __name__ == "__main__":
    print("Starting A2A server on http://localhost:8000")
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

## Example 2: Server with Agent Execution

Use AgentExecutor for more complex agent logic:

```python
#!/usr/bin/env python3
"""Server with agent execution."""

from a2a.server.apps.jsonrpc.fastapi_app import A2AFastAPI
from a2a.server.request_handlers.jsonrpc_handler import JSONRPCHandler
from a2a.server.agent_execution.agent_executor import AgentExecutor
from a2a.server.agent_execution.simple_request_context_builder import SimpleRequestContextBuilder
from a2a.types import AgentCard
import uvicorn

# Create agent card
agent_card = AgentCard(
    name="calculator_agent",
    description="A calculator agent",
    capabilities={"function_calling": True}
)

# Create request context builder
context_builder = SimpleRequestContextBuilder()

# Create agent executor
async def execute_agent(context):
    """Execute agent logic."""
    user_input = context.get_user_input()
    
    # Simple calculator logic
    try:
        result = eval(user_input)  # In production, use safe evaluation
        return {"text": f"Result: {result}"}
    except:
        return {"text": "Invalid expression"}

agent_executor = AgentExecutor(
    execute_fn=execute_agent
)

# Create handler
handler = JSONRPCHandler(
    agent_card=agent_card,
    context_builder=context_builder,
    agent_executor=agent_executor
)

# Create app
app = A2AFastAPI(handler=handler)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

## Example 3: Server with Task Management

Use TaskManager for task orchestration:

```python
#!/usr/bin/env python3
"""Server with task management."""

from a2a.server.apps.jsonrpc.fastapi_app import A2AFastAPI
from a2a.server.request_handlers.jsonrpc_handler import JSONRPCHandler
from a2a.server.tasks.task_manager import TaskManager
from a2a.server.tasks.inmemory_task_store import InMemoryTaskStore
from a2a.types import AgentCard
import uvicorn

# Create task store
task_store = InMemoryTaskStore()

# Create task manager
task_manager = TaskManager(task_store=task_store)

# Create handler with task manager
agent_card = AgentCard(name="task_agent")
handler = JSONRPCHandler(
    agent_card=agent_card,
    task_manager=task_manager
)

# Create app
app = A2AFastAPI(handler=handler)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

## Example 4: REST Server

Create a REST-based server:

```python
#!/usr/bin/env python3
"""REST-based A2A server."""

from a2a.server.apps.rest.fastapi_app import A2ARESTFastAPIApplication
from a2a.server.request_handlers.rest_handler import RESTHandler
from a2a.types import AgentCard
import uvicorn

# Create agent card
agent_card = AgentCard(
    name="rest_agent",
    description="REST-based agent"
)

# Create REST handler
handler = RESTHandler(agent_card=agent_card)

# Create REST app
app = A2ARESTFastAPIApplication(handler=handler)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

## Example 5: Server with Event System

Use event queues for asynchronous processing:

```python
#!/usr/bin/env python3
"""Server with event system."""

from a2a.server.apps.jsonrpc.fastapi_app import A2AFastAPI
from a2a.server.request_handlers.jsonrpc_handler import JSONRPCHandler
from a2a.server.events.event_queue import EventQueue
from a2a.server.events.event_consumer import EventConsumer
from a2a.types import AgentCard
import asyncio
import uvicorn

# Create event queue
event_queue = EventQueue()

# Create event consumer
async def process_event(event):
    """Process events asynchronously."""
    print(f"Processing event: {event}")

consumer = EventConsumer(
    queue=event_queue,
    process_fn=process_event
)

# Start consumer
asyncio.create_task(consumer.start())

# Create handler
agent_card = AgentCard(name="event_agent")
handler = JSONRPCHandler(
    agent_card=agent_card,
    event_queue=event_queue
)

# Create app
app = A2AFastAPI(handler=handler)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

## Framework Integrations

### FastAPI (JSON-RPC)

**Location**: `a2a.server.apps.jsonrpc.fastapi_app`

```python
from a2a.server.apps.jsonrpc.fastapi_app import A2AFastAPI

app = A2AFastAPI(handler=handler)
uvicorn.run(app, host="0.0.0.0", port=8000)
```

### Starlette (JSON-RPC)

**Location**: `a2a.server.apps.jsonrpc.starlette_app`

```python
from a2a.server.apps.jsonrpc.starlette_app import A2AStarletteApplication

app = A2AStarletteApplication(handler=handler)
```

### FastAPI (REST)

**Location**: `a2a.server.apps.rest.fastapi_app`

```python
from a2a.server.apps.rest.fastapi_app import A2ARESTFastAPIApplication

app = A2ARESTFastAPIApplication(handler=handler)
uvicorn.run(app, host="0.0.0.0", port=8000)
```

## Request Handlers

### DefaultRequestHandler

Default implementation with common functionality.

**Location**: `a2a.server.request_handlers.default_request_handler`

**Key Methods**: 10 methods

### Custom Handler

Create custom handlers by extending RequestHandler:

```python
from a2a.server.request_handlers.request_handler import RequestHandler

class CustomHandler(RequestHandler):
    async def handle_request(self, request, context):
        # Custom logic
        return response
```

## Task Management

### InMemoryTaskStore

In-memory task storage (for development).

**Location**: `a2a.server.tasks.inmemory_task_store`

### DatabaseTaskStore

Database-backed task storage (requires `[sql]` extra).

**Location**: `a2a.server.tasks.database_task_store`

**Usage**:
```python
from a2a.server.tasks.database_task_store import DatabaseTaskStore

# Requires: pip install "a2a-sdk[postgresql]"
task_store = DatabaseTaskStore(
    connection_string="postgresql://user:pass@localhost/db"
)
```

## Best Practices

1. **Use Appropriate Handler Type**
   ```python
   # ✅ GOOD: Use JSON-RPC for A2A protocol
   handler = JSONRPCHandler(agent_card=card)
   
   # ✅ GOOD: Use REST for HTTP APIs
   handler = RESTHandler(agent_card=card)
   ```

2. **Handle Errors Gracefully**
   ```python
   async def handle_message(request, context):
       try:
           # Process request
           return response
       except Exception as e:
           # Return error response
           return error_message
   ```

3. **Use TaskManager for Long-Running Tasks**
   ```python
   # ✅ GOOD: Use TaskManager
   task_manager = TaskManager(task_store=task_store)
   handler = JSONRPCHandler(
       agent_card=card,
       task_manager=task_manager
   )
   ```

4. **Configure Proper Context Builders**
   ```python
   # ✅ GOOD: Use context builder
   context_builder = SimpleRequestContextBuilder()
   handler = JSONRPCHandler(
       agent_card=card,
       context_builder=context_builder
   )
   ```

## Comparison with ADK

| Feature | ADK | A2A SDK Server |
|--------|-----|----------------|
| **Server Type** | `App` (unified) | `RequestHandler` (protocol-specific) |
| **Framework** | Built-in FastAPI | Multiple (FastAPI, Starlette) |
| **Protocol** | A2A (built-in) | JSON-RPC, REST, gRPC |
| **Agent Execution** | Built into Runner | `AgentExecutor` |
| **Task Management** | Built into Runner | `TaskManager` |

## Troubleshooting

### Issue: Handler not responding

**Solution**: Check that handler is properly configured and agent card is valid.

### Issue: Task storage errors

**Solution**: Ensure task store is properly initialized:
```python
task_store = InMemoryTaskStore()  # For development
# or
task_store = DatabaseTaskStore(...)  # For production
```

### Issue: Context errors

**Solution**: Ensure context builder is configured:
```python
context_builder = SimpleRequestContextBuilder()
handler = JSONRPCHandler(
    agent_card=card,
    context_builder=context_builder
)
```

## Related Documentation

- [Client Package](02-Client-Package.md) - Client implementation
- [Task Management](07-Task-Management.md) - Task orchestration
- [Event System](09-Event-System.md) - Event queues
- [Context and Memory](04-Context-and-Memory.md) - Context management

---

**Last Updated:** February 2, 2026  
**A2A-SDK Version:** 0.3.22
