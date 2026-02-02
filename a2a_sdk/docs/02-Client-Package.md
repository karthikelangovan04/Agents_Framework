# A2A-SDK Client Package Documentation

**File Path**: `docs-a2a-sdk/02-Client-Package.md`  
**Package**: `a2a.client`

## Overview

The `a2a.client` package provides the client implementation for the A2A (Agent-to-Agent) protocol. It enables you to create clients that can communicate with A2A agent servers, send messages, manage tasks, and handle responses.

## Key Classes

### Client

The main client class for A2A protocol communication.

**Location**: `a2a.client.client`

**Constructor**:
```python
from a2a.client import Client, ClientConfig
from a2a.client.transports.rest import RestTransport

config = ClientConfig(
    transport=RestTransport(base_url="http://localhost:8000")
)
client = Client(config)
```

**Key Methods**:
- `send_message()` - Send a message to an agent (11 methods total)
- `get_agent_card()` - Retrieve agent card
- `get_task()` - Get task status
- `cancel_task()` - Cancel a task
- `subscribe_to_task()` - Subscribe to task updates

### BaseClient

Abstract base class for all client implementations.

**Location**: `a2a.client.base_client`

**Key Methods**: 12 methods including transport management, authentication handling, request/response processing

### ClientConfig

Configuration for A2A clients.

**Location**: `a2a.client.client`

**Key Properties**:
- `transport` - Transport protocol (JSON-RPC, REST, gRPC)
- `timeout` - Request timeout
- `retry_config` - Retry configuration

### ClientTaskManager

Manages task lifecycle and state tracking.

**Location**: `a2a.client.client_task_manager`

**Key Methods**:
- `process_event()` - Process task events
- `get_current_task()` - Get current task
- `reset()` - Reset task manager

### ClientCallContext

Context object for client-side calls.

**Location**: `a2a.client.middleware`

**Key Properties**:
- `state` - Call-specific state dictionary
- `session_id` - Session identifier
- `request_metadata` - Request metadata
- `extensions` - Active extensions

## Example 1: Basic Client

Create a simple client that sends messages to an A2A agent:

```python
#!/usr/bin/env python3
"""Basic A2A client example."""

import asyncio
from a2a.client import Client, ClientConfig
from a2a.client.transports.rest import RestTransport
from a2a.types import Message

async def main():
    # Create client configuration
    config = ClientConfig(
        transport=RestTransport(
            base_url="http://localhost:8000"
        )
    )
    
    # Create client
    client = Client(config)
    
    # Create a message
    message = Message(
        role="user",
        content=[{"text": "Hello, A2A agent!"}]
    )
    
    # Send message
    async for event in client.send_message(message):
        if isinstance(event, Message):
            print(f"Response: {event.content}")
        elif isinstance(event, tuple):
            task, update = event
            print(f"Task {task.id}: {task.status}")

if __name__ == "__main__":
    asyncio.run(main())
```

## Example 2: Client with Context

Use ClientCallContext to maintain conversation context:

```python
#!/usr/bin/env python3
"""Client with context management."""

import asyncio
from a2a.client import Client, ClientConfig
from a2a.client.transports.rest import RestTransport
from a2a.client.middleware import ClientCallContext
from a2a.types import Message

async def main():
    # Create client
    config = ClientConfig(
        transport=RestTransport(base_url="http://localhost:8000")
    )
    client = Client(config)
    
    # Create context with session ID
    context = ClientCallContext(
        session_id="session_123",
        state={"user_id": "user_456", "message_count": 0}
    )
    
    # First message
    message1 = Message(role="user", content=[{"text": "My name is Alice"}])
    async for event in client.send_message(message1, context=context):
        if isinstance(event, Message):
            print(f"Agent: {event.content}")
    
    # Update context
    context.state["message_count"] += 1
    
    # Second message (context maintained)
    message2 = Message(role="user", content=[{"text": "What's my name?"}])
    async for event in client.send_message(message2, context=context):
        if isinstance(event, Message):
            print(f"Agent: {event.content}")

if __name__ == "__main__":
    asyncio.run(main())
```

## Example 3: Client with Task Management

Use ClientTaskManager to track tasks:

```python
#!/usr/bin/env python3
"""Client with task management."""

import asyncio
from a2a.client import Client, ClientConfig
from a2a.client.transports.rest import RestTransport
from a2a.client.client_task_manager import ClientTaskManager
from a2a.types import Message

async def main():
    # Create client
    config = ClientConfig(
        transport=RestTransport(base_url="http://localhost:8000")
    )
    client = Client(config)
    
    # Create task manager
    task_manager = ClientTaskManager()
    
    # Send message
    message = Message(role="user", content=[{"text": "Calculate 25 * 17"}])
    
    async for event in client.send_message(message):
        # Process event with task manager
        task_manager.process_event(event)
        
        if isinstance(event, tuple):
            task, update = event
            print(f"Task ID: {task.id}")
            print(f"Status: {task.status}")
            
            # Get current task from manager
            current_task = task_manager.get_current_task()
            if current_task:
                print(f"Current task: {current_task.id}")

if __name__ == "__main__":
    asyncio.run(main())
```

## Example 4: Client with Authentication

Use authentication with credentials:

```python
#!/usr/bin/env python3
"""Client with authentication."""

import asyncio
from a2a.client import Client, ClientConfig
from a2a.client.transports.rest import RestTransport
from a2a.client.auth.credentials import CredentialService, InMemoryContextCredentialStore
from a2a.types import Message

async def main():
    # Create credential store
    credential_store = InMemoryContextCredentialStore()
    
    # Store credentials
    credential_store.store_credential(
        session_id="session_123",
        security_scheme_name="api_key",
        credential="your-api-key-here"
    )
    
    # Create credential service
    credential_service = CredentialService(credential_store)
    
    # Create client with authentication
    config = ClientConfig(
        transport=RestTransport(base_url="http://localhost:8000"),
        credential_service=credential_service
    )
    client = Client(config)
    
    # Send authenticated message
    message = Message(role="user", content=[{"text": "Hello"}])
    async for event in client.send_message(message):
        print(event)

if __name__ == "__main__":
    asyncio.run(main())
```

## Example 5: Client with JSON-RPC Transport

Use JSON-RPC transport instead of REST:

```python
#!/usr/bin/env python3
"""Client with JSON-RPC transport."""

import asyncio
from a2a.client import Client, ClientConfig
from a2a.client.transports.jsonrpc import JsonRpcTransport
from a2a.types import Message

async def main():
    # Create JSON-RPC transport
    transport = JsonRpcTransport(
        base_url="http://localhost:8000"
    )
    
    # Create client
    config = ClientConfig(transport=transport)
    client = Client(config)
    
    # Send message via JSON-RPC
    message = Message(role="user", content=[{"text": "Hello"}])
    async for event in client.send_message(message):
        print(event)

if __name__ == "__main__":
    asyncio.run(main())
```

## Transport Protocols

### REST Transport

**Location**: `a2a.client.transports.rest`

**Usage**:
```python
from a2a.client.transports.rest import RestTransport

transport = RestTransport(
    base_url="http://localhost:8000",
    timeout=30.0
)
```

### JSON-RPC Transport

**Location**: `a2a.client.transports.jsonrpc`

**Usage**:
```python
from a2a.client.transports.jsonrpc import JsonRpcTransport

transport = JsonRpcTransport(
    base_url="http://localhost:8000"
)
```

### gRPC Transport (Optional)

**Location**: `a2a.client.transports.grpc`

**Requires**: `pip install "a2a-sdk[grpc]"`

**Usage**:
```python
from a2a.client.transports.grpc import GrpcTransport

transport = GrpcTransport(
    endpoint="localhost:50051"
)
```

## Error Handling

A2A client provides comprehensive error classes:

```python
from a2a.client.errors import (
    A2AClientError,
    A2AClientHTTPError,
    A2AClientInvalidArgsError,
    A2AClientInvalidStateError,
    A2AClientJSONError
)

try:
    async for event in client.send_message(message):
        # Process events
        pass
except A2AClientHTTPError as e:
    print(f"HTTP error: {e.status_code} - {e.message}")
except A2AClientError as e:
    print(f"Client error: {e}")
```

## Best Practices

1. **Use Context for Conversation Tracking**
   ```python
   # ✅ GOOD: Use consistent session_id
   context = ClientCallContext(session_id="session_123")
   
   # ❌ BAD: New context for each call
   context = ClientCallContext()  # No session linking
   ```

2. **Use TaskManager for Task Tracking**
   ```python
   # ✅ GOOD: Track tasks
   task_manager = ClientTaskManager()
   task_manager.process_event(event)
   
   # ❌ BAD: Manual task tracking
   # Easy to lose track of tasks
   ```

3. **Handle Streaming Responses**
   ```python
   # ✅ GOOD: Handle both streaming and non-streaming
   async for event in client.send_message(message):
       if isinstance(event, Message):
           # Final message
           pass
       elif isinstance(event, tuple):
           # Task update
           task, update = event
           pass
   ```

4. **Configure Timeouts**
   ```python
   # ✅ GOOD: Set appropriate timeout
   transport = RestTransport(
       base_url="http://localhost:8000",
       timeout=30.0  # 30 seconds
   )
   ```

## Comparison with ADK

| Feature | ADK | A2A SDK Client |
|--------|-----|----------------|
| **Client Type** | `RemoteA2aAgent` | `Client` |
| **Transport** | Built-in HTTP | Abstracted (REST/JSON-RPC/gRPC) |
| **Context** | Session-based | `ClientCallContext` |
| **Task Management** | Built into Runner | `ClientTaskManager` |
| **Authentication** | Built-in | `CredentialService` |

## Troubleshooting

### Issue: Connection refused

**Solution**: Ensure the A2A server is running and accessible at the configured URL.

### Issue: Timeout errors

**Solution**: Increase timeout or check network connectivity:
```python
transport = RestTransport(
    base_url="http://localhost:8000",
    timeout=60.0  # Increase timeout
)
```

### Issue: Authentication errors

**Solution**: Ensure credentials are properly configured:
```python
credential_store.store_credential(
    session_id="session_123",
    security_scheme_name="api_key",
    credential="your-key"
)
```

## Related Documentation

- [Transports Package](06-Transports-Package.md) - Transport protocols
- [Authentication Package](08-Authentication.md) - Authentication details
- [Task Management](07-Task-Management.md) - Task orchestration
- [Context and Memory](04-Context-and-Memory.md) - Context management

---

**Last Updated:** February 2, 2026  
**A2A-SDK Version:** 0.3.22
