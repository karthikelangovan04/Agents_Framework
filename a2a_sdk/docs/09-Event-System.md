# A2A-SDK Event System Documentation

**File Path**: `docs-a2a-sdk/09-Event-System.md`  
**Package**: `a2a.server.events`

## Overview

The A2A SDK event system provides asynchronous event processing using queues and consumers. This enables decoupled, scalable event handling.

## Key Classes

### EventQueue

Queue for storing events.

**Location**: `a2a.server.events.event_queue`

**Key Methods**: 8 methods

**Usage**:
```python
from a2a.server.events.event_queue import EventQueue

event_queue = EventQueue()
```

### EventConsumer

Consumes events from queue.

**Location**: `a2a.server.events.event_consumer`

**Key Methods**: 4 methods

**Usage**:
```python
from a2a.server.events.event_consumer import EventConsumer

async def process_event(event):
    """Process event."""
    print(f"Processing: {event}")

consumer = EventConsumer(
    queue=event_queue,
    process_fn=process_event
)
```

### QueueManager

Manages multiple event queues.

**Location**: `a2a.server.events.queue_manager`

**Key Methods**: 5 methods

### InMemoryQueueManager

In-memory queue manager.

**Location**: `a2a.server.events.in_memory_queue_manager`

**Key Methods**: 6 methods

## Example 1: Basic Event Queue

```python
#!/usr/bin/env python3
"""Basic event queue example."""

import asyncio
from a2a.server.events.event_queue import EventQueue
from a2a.server.events.event_consumer import EventConsumer

async def process_event(event):
    """Process event."""
    print(f"Processing event: {event}")

async def main():
    # Create event queue
    event_queue = EventQueue()
    
    # Create consumer
    consumer = EventConsumer(
        queue=event_queue,
        process_fn=process_event
    )
    
    # Start consumer
    consumer_task = asyncio.create_task(consumer.start())
    
    # Add events
    await event_queue.put("event_1")
    await event_queue.put("event_2")
    await event_queue.put("event_3")
    
    # Wait for processing
    await asyncio.sleep(1)
    
    # Stop consumer
    await consumer.stop()
    consumer_task.cancel()

if __name__ == "__main__":
    asyncio.run(main())
```

## Example 2: Queue Manager

```python
#!/usr/bin/env python3
"""Queue manager example."""

import asyncio
from a2a.server.events.in_memory_queue_manager import InMemoryQueueManager

async def main():
    # Create queue manager
    queue_manager = InMemoryQueueManager()
    
    # Create queue
    queue = await queue_manager.get_or_create_queue("task_queue")
    
    # Add events
    await queue.put("event_1")
    await queue.put("event_2")
    
    # Get queue
    retrieved_queue = await queue_manager.get_queue("task_queue")
    print(f"Queue size: {await retrieved_queue.size()}")

if __name__ == "__main__":
    asyncio.run(main())
```

## Example 3: Server with Event System

```python
#!/usr/bin/env python3
"""Server with event system."""

import asyncio
from a2a.server.apps.jsonrpc.fastapi_app import A2AFastAPI
from a2a.server.request_handlers.jsonrpc_handler import JSONRPCHandler
from a2a.server.events.event_queue import EventQueue
from a2a.server.events.event_consumer import EventConsumer
from a2a.types import AgentCard
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

# Create handler with event queue
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

## Best Practices

1. **Use Event Queues for Async Processing**
   ```python
   # ✅ GOOD: Use event queue
   event_queue = EventQueue()
   consumer = EventConsumer(queue=event_queue, process_fn=process)
   ```

2. **Handle Event Errors**
   ```python
   # ✅ GOOD: Handle errors
   async def process_event(event):
       try:
           # Process event
           pass
       except Exception as e:
           print(f"Error processing event: {e}")
   ```

3. **Use Queue Manager for Multiple Queues**
   ```python
   # ✅ GOOD: Use queue manager
   queue_manager = InMemoryQueueManager()
   queue = await queue_manager.get_or_create_queue("queue_name")
   ```

## Comparison with ADK

| Feature | ADK | A2A SDK Events |
|--------|-----|---------------|
| **Event Model** | Session events | Queue-based |
| **Processing** | Synchronous | Asynchronous |
| **Queue Management** | Built-in | QueueManager |

## Related Documentation

- [Server Package](03-Server-Package.md) - Server implementation
- [Task Management](07-Task-Management.md) - Task orchestration

---

**Last Updated:** February 2, 2026  
**A2A-SDK Version:** 0.3.22
