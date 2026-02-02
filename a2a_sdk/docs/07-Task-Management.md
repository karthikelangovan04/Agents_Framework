# A2A-SDK Task Management Documentation

**File Path**: `docs-a2a-sdk/07-Task-Management.md`  
**Package**: `a2a.server.tasks`, `a2a.client.client_task_manager`

## Overview

Task management in A2A SDK provides orchestration and lifecycle management for long-running agent interactions. Tasks track conversation state, artifacts, and status updates.

## Key Classes

### TaskManager

Orchestrates task lifecycle on the server side.

**Location**: `a2a.server.tasks.task_manager`

**Key Methods**: 6 methods

**Usage**:
```python
from a2a.server.tasks.task_manager import TaskManager
from a2a.server.tasks.inmemory_task_store import InMemoryTaskStore

task_store = InMemoryTaskStore()
task_manager = TaskManager(task_store=task_store)
```

### TaskStore

Interface for task storage.

**Location**: `a2a.server.tasks.task_store`

**Key Methods**: 3 methods

**Implementations**:
- `InMemoryTaskStore` - In-memory storage
- `DatabaseTaskStore` - Database storage (requires `[sql]`)

### ClientTaskManager

Manages tasks on the client side.

**Location**: `a2a.client.client_task_manager`

**Key Methods**: 6 methods

**Usage**:
```python
from a2a.client.client_task_manager import ClientTaskManager

task_manager = ClientTaskManager()
```

## Example 1: Basic Task Management

```python
#!/usr/bin/env python3
"""Basic task management example."""

from a2a.server.tasks.task_manager import TaskManager
from a2a.server.tasks.inmemory_task_store import InMemoryTaskStore
from a2a.types import Task, Message

# Create task store
task_store = InMemoryTaskStore()

# Create task manager
task_manager = TaskManager(task_store=task_store)

# Create task
task = Task(
    id="task_123",
    status="running",
    messages=[Message(role="user", content=[{"text": "Hello"}])]
)

# Save task
await task_store.save_task(task)

# Get task
retrieved_task = await task_store.get_task("task_123")
print(f"Task status: {retrieved_task.status}")
```

## Example 2: Task Updates

```python
#!/usr/bin/env python3
"""Task update example."""

from a2a.server.tasks.task_manager import TaskManager
from a2a.server.tasks.task_updater import TaskUpdater
from a2a.server.tasks.inmemory_task_store import InMemoryTaskStore
from a2a.types import Task, TaskStatusUpdateEvent

# Create task manager
task_store = InMemoryTaskStore()
task_manager = TaskManager(task_store=task_store)
task_updater = TaskUpdater(task_store=task_store)

# Create initial task
task = Task(id="task_123", status="running")
await task_store.save_task(task)

# Update task status
status_update = TaskStatusUpdateEvent(
    task_id="task_123",
    status="completed"
)

updated_task = await task_updater.update_task_status(status_update)
print(f"Updated status: {updated_task.status}")
```

## Example 3: Result Aggregation

```python
#!/usr/bin/env python3
"""Result aggregation example."""

from a2a.server.tasks.result_aggregator import ResultAggregator
from a2a.types import Task, TaskArtifactUpdateEvent

# Create result aggregator
aggregator = ResultAggregator()

# Create task with artifacts
task = Task(
    id="task_123",
    artifacts=[{"type": "text", "content": "Result 1"}]
)

# Add artifact update
artifact_update = TaskArtifactUpdateEvent(
    task_id="task_123",
    artifact={"type": "text", "content": "Result 2"}
)

# Aggregate results
aggregated_task = aggregator.aggregate_artifact(task, artifact_update)
print(f"Total artifacts: {len(aggregated_task.artifacts)}")
```

## Example 4: Client-Side Task Management

```python
#!/usr/bin/env python3
"""Client-side task management."""

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
    message = Message(role="user", content=[{"text": "Hello"}])
    async for event in client.send_message(message):
        # Process event
        task_manager.process_event(event)
        
        if isinstance(event, tuple):
            task, update = event
            print(f"Task ID: {task.id}")
            print(f"Status: {task.status}")
            
            # Get current task
            current_task = task_manager.get_current_task()
            if current_task:
                print(f"Current task: {current_task.id}")

if __name__ == "__main__":
    asyncio.run(main())
```

## Task Stores

### InMemoryTaskStore

In-memory storage for development/testing.

**Location**: `a2a.server.tasks.inmemory_task_store`

**Usage**:
```python
from a2a.server.tasks.inmemory_task_store import InMemoryTaskStore

task_store = InMemoryTaskStore()
```

### DatabaseTaskStore

Database-backed storage for production.

**Location**: `a2a.server.tasks.database_task_store`

**Requires**: `pip install "a2a-sdk[postgresql]"` (or mysql, sqlite, sql)

**Usage**:
```python
from a2a.server.tasks.database_task_store import DatabaseTaskStore

task_store = DatabaseTaskStore(
    connection_string="postgresql://user:pass@localhost/db"
)
```

## Push Notifications

### PushNotificationSender

Sends push notifications for task updates.

**Location**: `a2a.server.tasks.push_notification_sender`

**Usage**:
```python
from a2a.server.tasks.push_notification_sender import PushNotificationSender

class CustomPushSender(PushNotificationSender):
    async def send_notification(self, config, event):
        # Send notification
        pass
```

### PushNotificationConfigStore

Stores push notification configurations.

**Location**: `a2a.server.tasks.push_notification_config_store`

**Implementations**:
- `InMemoryPushNotificationConfigStore`
- `DatabasePushNotificationConfigStore`

## Best Practices

1. **Use TaskManager for Orchestration**
   ```python
   # ✅ GOOD: Use TaskManager
   task_manager = TaskManager(task_store=task_store)
   ```

2. **Choose Appropriate Task Store**
   ```python
   # ✅ GOOD: In-memory for development
   task_store = InMemoryTaskStore()
   
   # ✅ GOOD: Database for production
   task_store = DatabaseTaskStore(...)
   ```

3. **Track Task State**
   ```python
   # ✅ GOOD: Track task state
   task_manager.process_event(event)
   current_task = task_manager.get_current_task()
   ```

## Comparison with ADK

| Feature | ADK | A2A SDK Tasks |
|--------|-----|---------------|
| **Task Model** | Session-based | Task-based |
| **Storage** | SessionService | TaskStore |
| **State Tracking** | Session.state | Task.metadata |
| **Updates** | Event-based | TaskUpdater |

## Related Documentation

- [Server Package](03-Server-Package.md) - Server implementation
- [Client Package](02-Client-Package.md) - Client usage
- [Context and Memory](04-Context-and-Memory.md) - Context management

---

**Last Updated:** February 2, 2026  
**A2A-SDK Version:** 0.3.22
