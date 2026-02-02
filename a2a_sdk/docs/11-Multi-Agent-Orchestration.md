# A2A-SDK Multi-Agent Orchestration Documentation

**File Path**: `docs-a2a-sdk/11-Multi-Agent-Orchestration.md`  
**Related Docs**: 
- [Context and Memory](04-Context-and-Memory.md)
- [Client Package](02-Client-Package.md)
- [Server Package](03-Server-Package.md)

## Overview

This document explains how to build multi-agent systems with A2A SDK, including orchestrator patterns, context passing, task coordination, and state management across agents.

## Key Concepts

### Orchestrator Pattern

An orchestrator agent coordinates multiple specialized agents, routing requests and aggregating responses.

### Context Passing

Context flows from orchestrator to remote agents, maintaining conversation state.

### Task Coordination

Tasks coordinate work across multiple agents, tracking progress and results.

## Example 1: Basic Orchestrator

```python
#!/usr/bin/env python3
"""Basic orchestrator example."""

import asyncio
from a2a.client import Client, ClientConfig
from a2a.client.transports.rest import RestTransport
from a2a.client.middleware import ClientCallContext
from a2a.client.client_task_manager import ClientTaskManager
from a2a.types import Message

class Orchestrator:
    """Orchestrator that coordinates multiple agents."""
    
    def __init__(self):
        # Math agent client
        self.math_client = Client(ClientConfig(
            transport=RestTransport(base_url="http://math-agent:8000")
        ))
        
        # Database agent client
        self.db_client = Client(ClientConfig(
            transport=RestTransport(base_url="http://db-agent:8000")
        ))
        
        self.task_manager = ClientTaskManager()
    
    async def process_request(
        self,
        user_message: str,
        session_id: str
    ):
        """Process user request and route to appropriate agent."""
        
        # Create context
        context = ClientCallContext(
            session_id=session_id,
            state={"user_message": user_message}
        )
        
        # Determine which agent to use
        if "calculate" in user_message.lower() or "math" in user_message.lower():
            # Route to math agent
            message = Message(role="user", content=[{"text": user_message}])
            async for event in self.math_client.send_message(message, context=context):
                yield event
        elif "query" in user_message.lower() or "database" in user_message.lower():
            # Route to database agent
            message = Message(role="user", content=[{"text": user_message}])
            async for event in self.db_client.send_message(message, context=context):
                yield event
        else:
            # Default response
            yield Message(role="agent", content=[{"text": "I can help with math or database queries."}])

# Usage
async def main():
    orchestrator = Orchestrator()
    
    async for response in orchestrator.process_request(
        "Calculate 25 * 17",
        session_id="session_123"
    ):
        print(response)

if __name__ == "__main__":
    asyncio.run(main())
```

## Example 2: Context Filtering

```python
#!/usr/bin/env python3
"""Orchestrator with context filtering."""

from a2a.client.middleware import ClientCallContext
from a2a.types import Message

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
                "conversation_history": filtered
            }
        )
        
        return filtered_context
    
    def _is_math_related(self, message):
        """Check if message is math-related."""
        text = message.get("text", "").lower()
        math_keywords = ["calculate", "math", "add", "subtract", "multiply", "divide"]
        return any(keyword in text for keyword in math_keywords)
    
    def _is_database_related(self, message):
        """Check if message is database-related."""
        text = message.get("text", "").lower()
        db_keywords = ["query", "database", "select", "insert", "update"]
        return any(keyword in text for keyword in db_keywords)
```

## Example 3: Task Coordination

```python
#!/usr/bin/env python3
"""Task coordination across agents."""

import asyncio
from a2a.client import Client, ClientConfig
from a2a.client.transports.rest import RestTransport
from a2a.client.client_task_manager import ClientTaskManager
from a2a.types import Message

class TaskCoordinator:
    """Coordinates tasks across multiple agents."""
    
    def __init__(self):
        self.clients = {
            "math": Client(ClientConfig(
                transport=RestTransport(base_url="http://math-agent:8000")
            )),
            "db": Client(ClientConfig(
                transport=RestTransport(base_url="http://db-agent:8000")
            ))
        }
        self.task_manager = ClientTaskManager()
    
    async def coordinate_task(self, user_request: str, session_id: str):
        """Coordinate task across multiple agents."""
        
        tasks = []
        
        # Step 1: Math calculation
        math_message = Message(role="user", content=[{"text": user_request}])
        math_context = ClientCallContext(session_id=session_id)
        
        async for event in self.clients["math"].send_message(math_message, context=math_context):
            if isinstance(event, tuple):
                task, update = event
                tasks.append(("math", task))
                self.task_manager.process_event(event)
        
        # Step 2: Database query (using math result)
        db_message = Message(
            role="user",
            content=[{"text": f"Store result: {tasks[0][1]}"}]
        )
        
        async for event in self.clients["db"].send_message(db_message, context=math_context):
            if isinstance(event, tuple):
                task, update = event
                tasks.append(("db", task))
                self.task_manager.process_event(event)
        
        return tasks
```

## Best Practices

1. **Filter Context Before Sending**
   ```python
   # ✅ GOOD: Filter context
   filtered_context = filter_context_for_agent(full_context, agent_name)
   
   # ❌ BAD: Send full context
   # Wastes tokens and can confuse agents
   ```

2. **Use TaskManager for Coordination**
   ```python
   # ✅ GOOD: Track tasks
   task_manager = ClientTaskManager()
   task_manager.process_event(event)
   ```

3. **Maintain Session Context**
   ```python
   # ✅ GOOD: Use consistent session_id
   context = ClientCallContext(session_id="session_123")
   ```

## Comparison with ADK

| Feature | ADK | A2A SDK Orchestration |
|--------|-----|---------------------|
| **Orchestrator** | `Agent` with `sub_agents` | `Client` with multiple clients |
| **Context Filtering** | Automatic (LLM-based) | Manual (developer implements) |
| **Task Coordination** | Built into Runner | `ClientTaskManager` |
| **State Management** | Session-based | Context-based + Task-based |

## Related Documentation

- [Context and Memory](04-Context-and-Memory.md) - Context management
- [Client Package](02-Client-Package.md) - Client usage
- [Task Management](07-Task-Management.md) - Task orchestration

---

**Last Updated:** February 2, 2026  
**A2A-SDK Version:** 0.3.22
