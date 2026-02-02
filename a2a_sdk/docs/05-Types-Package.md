# A2A-SDK Types Package Documentation

**File Path**: `docs-a2a-sdk/05-Types-Package.md`  
**Package**: `a2a.types`

## Overview

The `a2a.types` package contains all type definitions for the A2A protocol. These are protobuf-generated types that provide type-safe models for messages, tasks, agent cards, requests, and responses.

## Statistics

- **Total Types**: 96 classes
- **Base Class**: All types inherit from `A2ABaseModel`
- **Methods**: Each type provides 27 methods (inherited from base model)

## Key Types

### Message

Represents a message in an A2A conversation.

**Usage**:
```python
from a2a.types import Message

message = Message(
    role="user",
    content=[{"text": "Hello, agent!"}]
)
```

**Key Properties**:
- `role` - Message role (user, agent, system)
- `content` - Message content (list of content parts)
- `metadata` - Additional metadata

### Task

Represents a task in the A2A system.

**Usage**:
```python
from a2a.types import Task

task = Task(
    id="task_123",
    status="running",
    messages=[message1, message2]
)
```

**Key Properties**:
- `id` - Task identifier
- `status` - Task status
- `messages` - Conversation messages
- `artifacts` - Generated artifacts
- `metadata` - Task metadata

### AgentCard

Describes an agent's capabilities and metadata.

**Usage**:
```python
from a2a.types import AgentCard

card = AgentCard(
    name="my_agent",
    description="A helpful agent",
    capabilities={"function_calling": True}
)
```

**Key Properties**:
- `name` - Agent name
- `description` - Agent description
- `capabilities` - Agent capabilities
- `endpoints` - Agent endpoints

### A2ARequest

Base request type for A2A protocol.

**Usage**:
```python
from a2a.types import A2ARequest

request = A2ARequest(
    # Request properties
)
```

### SendMessageRequest

Request to send a message.

**Usage**:
```python
from a2a.types import SendMessageRequest

request = SendMessageRequest(
    message=Message(...),
    configuration=MessageSendConfiguration(...)
)
```

### SendMessageResponse

Response from sending a message.

**Usage**:
```python
from a2a.types import SendMessageResponse

response = SendMessageResponse(
    # Response properties
)
```

## Complete Type List

The `a2a.types` module contains 96 protobuf-generated types. Here are the main categories:

### Message Types
- `Message`
- `JSONRPCMessage`
- `MessageSendConfiguration`
- `MessageSendParams`

### Task Types
- `Task`
- `TaskIdParams`
- `TaskQueryParams`
- `TaskStatusUpdateEvent`
- `TaskArtifactUpdateEvent`

### Request/Response Types
- `A2ARequest`
- `A2AError`
- `SendMessageRequest`
- `SendMessageResponse`
- `SendMessageSuccessResponse`
- `SendStreamingMessageRequest`
- `SendStreamingMessageResponse`

### Agent Types
- `AgentCard`
- `AgentCapabilities`

### Security Types
- `APIKeySecurityScheme`
- `SecurityScheme`

### Configuration Types
- `TaskPushNotificationConfig`
- `GetTaskPushNotificationConfigParams`

## Example: Working with Types

```python
from a2a.types import (
    Message,
    Task,
    AgentCard,
    SendMessageRequest,
    MessageSendConfiguration
)

# Create agent card
agent_card = AgentCard(
    name="calculator",
    description="A calculator agent",
    capabilities={"function_calling": True}
)

# Create message
message = Message(
    role="user",
    content=[{"text": "Calculate 25 * 17"}]
)

# Create message send configuration
config = MessageSendConfiguration(
    # Configuration options
)

# Create send message request
request = SendMessageRequest(
    message=message,
    configuration=config
)

# Use types in client
from a2a.client import Client
client = Client(...)
async for response in client.send_message(message):
    if isinstance(response, Task):
        print(f"Task ID: {response.id}")
        print(f"Status: {response.status}")
```

## Type Serialization

All types inherit from `A2ABaseModel` (Pydantic), providing:

### JSON Serialization

```python
# Convert to JSON string
json_str = message.model_dump_json()

# Convert to dictionary
message_dict = message.model_dump()

# Create from JSON
message = Message.model_validate_json(json_str)

# Create from dictionary
message = Message.model_validate(message_dict)
```

### Type Validation

```python
# Automatic validation
try:
    message = Message(
        role="invalid_role",  # Will raise ValidationError
        content=[]
    )
except ValidationError as e:
    print(f"Validation error: {e}")
```

## Best Practices

1. **Use Type Hints**
   ```python
   # ✅ GOOD: Use type hints
   def process_message(message: Message) -> Message:
       # Process message
       return response
   ```

2. **Validate Input**
   ```python
   # ✅ GOOD: Validate before use
   try:
       message = Message.model_validate(data)
   except ValidationError:
       # Handle error
       pass
   ```

3. **Use Model Methods**
   ```python
   # ✅ GOOD: Use Pydantic methods
   json_str = message.model_dump_json()
   message_copy = message.model_copy()
   ```

## Comparison with ADK

| Feature | ADK | A2A SDK Types |
|--------|-----|---------------|
| **Type System** | Runtime types | Protobuf-generated |
| **Base Class** | Custom | `A2ABaseModel` (Pydantic) |
| **Serialization** | Custom | Pydantic (automatic) |
| **Validation** | Manual | Automatic (Pydantic) |
| **Type Count** | ~50 types | 96 types |

## Related Documentation

- [Client Package](02-Client-Package.md) - Using types in clients
- [Server Package](03-Server-Package.md) - Using types in servers
- [Package Structure](01-Package-Structure.md) - Package overview

---

**Last Updated:** February 2, 2026  
**A2A-SDK Version:** 0.3.22
