# Google ADK Memory Package Documentation

**File Path**: `docs/08-Memory-Package.md`  
**Package**: `google.adk.memory`

## Overview

The `google.adk.memory` package provides memory services for agents, allowing them to store and retrieve information across sessions. Memory services enable agents to learn from past interactions and maintain long-term knowledge.

## Key Classes

### BaseMemoryService

Abstract base class for memory services.

### InMemoryMemoryService

In-memory memory service (for development).

### VertexAiMemoryBankService

Vertex AI Memory Bank service (for production).

### VertexAiRagMemoryService

Vertex AI RAG (Retrieval-Augmented Generation) memory service.

## Example 1: Basic Memory Usage

Create an agent with memory:

```python
from google.adk import Agent
from google.adk.memory import InMemoryMemoryService
from google.adk.runners import Runner

# Create memory service
memory_service = InMemoryMemoryService()

# Create agent
agent = Agent(
    name="memory_agent",
    description="An agent with memory",
    model="gemini-1.5-flash",
    instruction="You are a helpful assistant with memory."
)

# Create runner with memory
runner = Runner(
    agent=agent,
    memory_service=memory_service
)

async def main():
    # Store information
    memory_service.store(
        key="user_preference",
        value="likes dark mode",
        metadata={"user_id": "alice"}
    )
    
    # Retrieve information
    result = memory_service.retrieve(
        key="user_preference",
        metadata={"user_id": "alice"}
    )
    
    # Use agent with memory
    async for event in runner.run("What do I like?", memory_service=memory_service):
        if hasattr(event, 'content'):
            print(event.content)

asyncio.run(main())
```

**Runnable Session:**

Save as `examples/memory_agent.py`:

```python
#!/usr/bin/env python3
"""Agent with memory capabilities."""

import asyncio
from google.adk import Agent
from google.adk.memory import InMemoryMemoryService
from google.adk.runners import Runner

async def main():
    # Create memory service
    memory_service = InMemoryMemoryService()
    
    # Create agent
    agent = Agent(
        name="memory_agent",
        description="An agent that can remember information",
        model="gemini-1.5-flash",
        instruction="""You are a helpful assistant with memory.
        When users tell you something, remember it.
        When asked, recall what you remember."""
    )
    
    # Create runner
    runner = Runner(agent=agent)
    
    print("Memory Agent: Hello! I can remember things you tell me.")
    print("Try: 'Remember that I like pizza' then 'What do I like?'")
    print("Type 'quit' to exit.\n")
    
    while True:
        user_input = input("You: ")
        if user_input.lower() == 'quit':
            break
        
        # Store user input in memory if it's a "remember" command
        if user_input.lower().startswith("remember"):
            memory_service.store(
                key="user_memory",
                value=user_input,
                metadata={"type": "user_preference"}
            )
        
        print("\nAgent: ", end="", flush=True)
        async for event in runner.run(user_input):
            if hasattr(event, 'content') and event.content:
                print(event.content, end="", flush=True)
        print("\n")

if __name__ == "__main__":
    asyncio.run(main())
```

## Example 2: Vertex AI Memory Bank

Use Vertex AI Memory Bank for persistent memory:

```python
from google.adk.memory import VertexAiMemoryBankService
from google.adk import Agent
from google.adk.runners import Runner

# Create Vertex AI memory service
memory_service = VertexAiMemoryBankService(
    project_id="your-project-id",
    location="us-central1",
    memory_bank_id="your-memory-bank-id"
)

# Create agent
agent = Agent(
    name="persistent_memory_agent",
    model="gemini-1.5-flash",
    instruction="You are a helpful assistant with persistent memory."
)

# Use with agent
runner = Runner(agent=agent, memory_service=memory_service)
```

## Example 3: RAG Memory Service

Use RAG (Retrieval-Augmented Generation) for semantic memory:

```python
from google.adk.memory import VertexAiRagMemoryService
from google.adk import Agent

# Create RAG memory service
rag_memory = VertexAiRagMemoryService(
    project_id="your-project-id",
    location="us-central1",
    data_store_id="your-data-store-id"
)

# Create agent with RAG memory
agent = Agent(
    name="rag_agent",
    model="gemini-1.5-flash",
    instruction="You are an assistant with RAG capabilities.",
    memory_service=rag_memory
)
```

## Example 4: Memory Search

Search memory by similarity:

```python
from google.adk.memory import InMemoryMemoryService

memory_service = InMemoryMemoryService()

# Store multiple memories
memory_service.store(key="memory1", value="User likes Python")
memory_service.store(key="memory2", value="User prefers Linux")
memory_service.store(key="memory3", value="User works as a developer")

# Search by similarity
results = memory_service.search(
    query="What programming language does the user like?",
    limit=3
)

for result in results:
    print(f"Found: {result.value} (score: {result.score})")
```

## Best Practices

1. **Memory Keys**: Use descriptive, consistent keys
2. **Metadata**: Add metadata for better organization
3. **Cleanup**: Periodically clean up old memories
4. **Privacy**: Don't store sensitive information
5. **Indexing**: Use RAG for semantic search

## Troubleshooting

### Issue: Memory not persisting
- Check memory service configuration
- Verify Vertex AI credentials if using Vertex AI services
- Check memory service is passed to runner

### Issue: Memory search not working
- Verify RAG/data store is configured
- Check query format
- Ensure memories are properly stored

## Related Documentation

- [Sessions Package](07-Sessions-Package.md)
- [Agents Package](01-Agents-Package.md)
