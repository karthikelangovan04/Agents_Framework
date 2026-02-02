# Google ADK: Memory Services Comparison

**File Path**: `docs/18-Memory-Services-Comparison.md`  
**Package**: `google.adk.memory`

## Overview

This document explains the key differences between `InMemoryMemoryService` and `VertexAiMemoryBankService`, how they work, when to use each, and how they relate to session management in Google ADK.

---

## Understanding Memory vs Sessions

Before diving into the differences, it's crucial to understand the distinction between **Memory Services** and **Session Services**:

### Session Services (Short-term, Episodic Memory)
- **Purpose**: Store conversation history and state **within a single session**
- **Scope**: One conversation session (identified by `session_id`)
- **Lifetime**: Exists for the duration of a conversation session
- **Storage**: Events (messages) and state (key-value pairs) for the current conversation
- **Use Case**: Maintaining context within a conversation

### Memory Services (Long-term, Semantic Memory)
- **Purpose**: Store and retrieve information **across multiple sessions**
- **Scope**: All sessions for a user (`user_id`) across an application (`app_name`)
- **Lifetime**: Persistent, survives across sessions
- **Storage**: Semantic memories extracted from completed sessions
- **Use Case**: Learning from past interactions, remembering user preferences, building long-term knowledge

---

## InMemoryMemoryService vs VertexAiMemoryBankService

### Quick Comparison Table

| Feature | InMemoryMemoryService | VertexAiMemoryBankService |
|---------|----------------------|---------------------------|
| **Storage Type** | In-memory Python dictionary | Google Cloud Vertex AI Memory Bank |
| **Persistence** | Lost on restart | Persistent across restarts |
| **Search Method** | Keyword matching (simple text search) | Semantic search (embeddings + vector search) |
| **Scalability** | Limited by RAM | Scales to millions of memories |
| **Performance** | Very fast (in-memory) | Fast (managed service) |
| **Use Case** | Development, testing, prototyping | Production applications |
| **Setup** | No setup required | Requires GCP project and Memory Bank |
| **Cost** | Free | Pay-per-use (Google Cloud pricing) |
| **Concurrency** | Single process only | Multi-process, distributed |

---

## InMemoryMemoryService

### How It Works

`InMemoryMemoryService` stores memories in a simple Python dictionary structure:

```python
# Internal storage structure (simplified)
_session_events = {
    "app_name/user_id": {
        "session_id_1": [event1, event2, ...],
        "session_id_2": [event3, event4, ...],
    }
}
```

### Key Characteristics

1. **Storage**: Python dictionary in RAM (`_session_events`)
2. **Search**: Simple keyword matching - extracts words from query and matches against stored event text
3. **Persistence**: Data is lost when the process terminates
4. **Thread Safety**: Not thread-safe (single process only)
5. **Performance**: Very fast for small datasets (< 10,000 memories)

### Implementation Details

```python
# Simplified implementation logic
async def add_session_to_memory(self, session: Session):
    """Store session events in memory."""
    user_key = f"{session.app_name}/{session.user_id}"
    if user_key not in self._session_events:
        self._session_events[user_key] = {}
    
    # Store only events with content
    self._session_events[user_key][session.id] = [
        event for event in session.events 
        if event.content and event.content.parts
    ]

async def search_memory(self, *, app_name, user_id, query) -> SearchMemoryResponse:
    """Search memories using keyword matching."""
    words_in_query = _extract_words_lower(query)
    memories = []
    
    user_key = f"{app_name}/{user_id}"
    if user_key not in self._session_events:
        return SearchMemoryResponse(memories=[])
    
    # Search through all stored events
    for session_id, events in self._session_events[user_key].items():
        for event in events:
            event_text = _extract_text_from_content(event.content)
            event_words = _extract_words_lower(event_text)
            
            # If any query word matches event text, include it
            if any(word in event_words for word in words_in_query):
                memories.append(MemoryEntry(
                    content=event.content,
                    author=event.author,
                    timestamp=event.timestamp,
                    custom_metadata={"session_id": session_id}
                ))
    
    return SearchMemoryResponse(memories=memories)
```

### Example Usage

```python
import asyncio
from google.adk import Agent
from google.adk.memory import InMemoryMemoryService
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

async def main():
    # Create services
    memory_service = InMemoryMemoryService()
    session_service = InMemorySessionService()
    
    # Create agent
    agent = Agent(
        name="memory_agent",
        model="gemini-1.5-flash",
        instruction="You are a helpful assistant that remembers past conversations."
    )
    
    # Create runner
    runner = Runner(
        app_name="memory_app",
        agent=agent,
        session_service=session_service,
        memory_service=memory_service
    )
    
    # First session - user tells agent their preferences
    session1 = await session_service.create_session(
        app_name="memory_app",
        user_id="alice",
        session_id="session_1"
    )
    
    # Have a conversation
    async for event in runner.run_async(
        user_id="alice",
        session_id=session1.id,
        new_message=types.UserContent(parts=[types.Part(text="I love Python programming")])
    ):
        if event.content:
            print(f"Agent: {event.content}")
    
    # Save session to memory
    await memory_service.add_session_to_memory(session1)
    
    # Second session - agent can recall past information
    session2 = await session_service.create_session(
        app_name="memory_app",
        user_id="alice",
        session_id="session_2"
    )
    
    # Search memory for user preferences
    search_result = await memory_service.search_memory(
        app_name="memory_app",
        user_id="alice",
        query="What programming language does the user like?"
    )
    
    print(f"\nFound {len(search_result.memories)} memories:")
    for memory in search_result.memories:
        print(f"  - {memory.content}")
    
    # Use memory in conversation
    memory_context = "\n".join([
        f"Previous conversation: {mem.content.parts[0].text if mem.content.parts else ''}"
        for mem in search_result.memories[:3]
    ])
    
    async for event in runner.run_async(
        user_id="alice",
        session_id=session2.id,
        new_message=types.UserContent(parts=[types.Part(
            text=f"Based on this context: {memory_context}\n\nWhat do I like?"
        )])
    ):
        if event.content:
            print(f"\nAgent: {event.content}")

asyncio.run(main())
```

### When to Use InMemoryMemoryService

✅ **Use when:**
- Developing and testing locally
- Prototyping new features
- Running unit tests
- Small-scale applications (< 1,000 users)
- Single-process applications
- No persistence requirements

❌ **Don't use when:**
- Production applications
- Multi-process deployments
- Need persistence across restarts
- Large-scale applications (> 10,000 memories)
- Need semantic search capabilities
- Distributed systems

---

## VertexAiMemoryBankService

### How It Works

`VertexAiMemoryBankService` uses Google Cloud Vertex AI Memory Bank, a managed service that:

1. **Stores memories** in Google Cloud Storage
2. **Creates embeddings** automatically for semantic search
3. **Uses vector search** to find semantically similar memories
4. **Scales automatically** to handle millions of memories

### Key Characteristics

1. **Storage**: Google Cloud Vertex AI Memory Bank (managed service)
2. **Search**: Semantic search using embeddings and vector similarity
3. **Persistence**: Permanent storage in Google Cloud
4. **Thread Safety**: Fully thread-safe and distributed
5. **Performance**: Optimized for large-scale semantic search
6. **Scalability**: Handles millions of memories efficiently

### Implementation Details

```python
# Simplified implementation logic
async def add_session_to_memory(self, session: Session):
    """Store session in Vertex AI Memory Bank."""
    # Convert session events to memory entries
    memory_entries = []
    for event in session.events:
        if event.content and event.content.parts:
            memory_entries.append({
                "content": event.content,
                "author": event.author,
                "timestamp": event.timestamp.isoformat(),
                "custom_metadata": {
                    "session_id": session.id,
                    "app_name": session.app_name,
                    "user_id": session.user_id
                }
            })
    
    # Upload to Vertex AI Memory Bank
    # The service automatically:
    # 1. Creates embeddings for each memory
    # 2. Stores in Memory Bank
    # 3. Indexes for semantic search
    await self._client.upload_memories(
        memory_bank_id=self.memory_bank_id,
        memories=memory_entries
    )

async def search_memory(self, *, app_name, user_id, query) -> SearchMemoryResponse:
    """Search memories using semantic similarity."""
    # Vertex AI Memory Bank:
    # 1. Creates embedding for the query
    # 2. Performs vector similarity search
    # 3. Returns semantically similar memories
    # 4. Filters by app_name and user_id (if configured)
    
    results = await self._client.search_memories(
        memory_bank_id=self.memory_bank_id,
        query=query,
        filter={
            "app_name": app_name,
            "user_id": user_id
        },
        limit=10
    )
    
    # Convert to MemoryEntry objects
    memories = [
        MemoryEntry(
            content=result.content,
            author=result.author,
            timestamp=result.timestamp,
            custom_metadata=result.custom_metadata
        )
        for result in results
    ]
    
    return SearchMemoryResponse(memories=memories)
```

### Example Usage

```python
import asyncio
from google.adk import Agent
from google.adk.memory import VertexAiMemoryBankService
from google.adk.runners import Runner
from google.adk.sessions import VertexAiSessionService
from google.genai import types

async def main():
    # Create Vertex AI Memory Bank service
    # Requires: GCP project, Memory Bank ID, and authentication
    memory_service = VertexAiMemoryBankService(
        project_id="your-gcp-project-id",
        location="us-central1",
        memory_bank_id="your-memory-bank-id"
    )
    
    # Create Vertex AI Session service
    session_service = VertexAiSessionService(
        project_id="your-gcp-project-id",
        location="us-central1"
    )
    
    # Create agent
    agent = Agent(
        name="persistent_memory_agent",
        model="gemini-1.5-flash",
        instruction="You are a helpful assistant with persistent memory."
    )
    
    # Create runner
    runner = Runner(
        app_name="production_app",
        agent=agent,
        session_service=session_service,
        memory_service=memory_service
    )
    
    # First session - user shares information
    session1 = await session_service.create_session(
        app_name="production_app",
        user_id="alice",
        session_id="session_2024_01_15"
    )
    
    # Conversation
    async for event in runner.run_async(
        user_id="alice",
        session_id=session1.id,
        new_message=types.UserContent(parts=[types.Part(
            text="I'm a software engineer working on machine learning projects. "
                 "I prefer using Python and TensorFlow for my work."
        )])
    ):
        if event.content:
            print(f"Agent: {event.content}")
    
    # Save to long-term memory
    await memory_service.add_session_to_memory(session1)
    print("\nSession saved to Memory Bank")
    
    # Weeks later - second session
    session2 = await session_service.create_session(
        app_name="production_app",
        user_id="alice",
        session_id="session_2024_02_01"
    )
    
    # Semantic search - finds memories even with different wording
    search_result = await memory_service.search_memory(
        app_name="production_app",
        user_id="alice",
        query="What does the user do for work?"
    )
    
    print(f"\nFound {len(search_result.memories)} relevant memories:")
    for memory in search_result.memories:
        print(f"  - {memory.content.parts[0].text if memory.content.parts else ''}")
    
    # Agent can use this context
    async for event in runner.run_async(
        user_id="alice",
        session_id=session2.id,
        new_message=types.UserContent(parts=[types.Part(
            text="What do you know about my work?"
        )])
    ):
        if event.content:
            print(f"\nAgent: {event.content}")

asyncio.run(main())
```

### Setting Up Vertex AI Memory Bank

Before using `VertexAiMemoryBankService`, you need to:

1. **Create a GCP Project** (if you don't have one)
2. **Enable Vertex AI API**
3. **Create a Memory Bank**:

```python
from google.cloud import aiplatform

# Initialize Vertex AI
aiplatform.init(project="your-project-id", location="us-central1")

# Create Memory Bank
memory_bank = aiplatform.MemoryBank.create(
    display_name="my-memory-bank",
    description="Memory bank for my application"
)

print(f"Memory Bank ID: {memory_bank.name}")
```

4. **Authenticate**: Set up Application Default Credentials (ADC)

```bash
# Option 1: Use gcloud
gcloud auth application-default login

# Option 2: Set environment variable
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/service-account-key.json"
```

### When to Use VertexAiMemoryBankService

✅ **Use when:**
- Production applications
- Need persistence across restarts
- Multi-process or distributed deployments
- Large-scale applications (> 10,000 memories)
- Need semantic search (understanding meaning, not just keywords)
- Want managed, scalable infrastructure
- Need to search across millions of memories

❌ **Don't use when:**
- Local development (use `InMemoryMemoryService` instead)
- Quick prototyping
- Unit testing
- No GCP access or budget constraints
- Simple keyword matching is sufficient

---

## How Memory Services Work with Sessions

### The Relationship

Memory services and session services work together but serve different purposes:

```
┌─────────────────────────────────────────────────────────────┐
│                    Agent Conversation                        │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
        ┌───────────────────────────────────┐
        │   Session Service (Short-term)    │
        │   - Stores conversation events     │
        │   - Maintains session state       │
        │   - Episodic memory               │
        └───────────────────────────────────┘
                            │
                            │ (when session completes)
                            ▼
        ┌───────────────────────────────────┐
        │   Memory Service (Long-term)       │
        │   - Stores semantic memories       │
        │   - Cross-session knowledge       │
        │   - Semantic search                │
        └───────────────────────────────────┘
```

### Complete Example: Memory + Sessions

```python
import asyncio
from google.adk import Agent
from google.adk.memory import InMemoryMemoryService
from google.adk.sessions import InMemorySessionService
from google.adk.runners import Runner
from google.genai import types

async def demonstrate_memory_and_sessions():
    """
    Demonstrates how Memory Services and Session Services work together.
    """
    
    # Initialize services
    memory_service = InMemoryMemoryService()
    session_service = InMemorySessionService()
    
    # Create agent
    agent = Agent(
        name="smart_assistant",
        model="gemini-1.5-flash",
        instruction="""You are a helpful assistant that remembers past conversations.
        Use the memory search tool to recall information from previous sessions."""
    )
    
    runner = Runner(
        app_name="demo_app",
        agent=agent,
        session_service=session_service,
        memory_service=memory_service
    )
    
    # ============================================
    # SESSION 1: User shares preferences
    # ============================================
    print("=" * 60)
    print("SESSION 1: User shares preferences")
    print("=" * 60)
    
    session1 = await session_service.create_session(
        app_name="demo_app",
        user_id="alice",
        session_id="session_1"
    )
    
    # User tells agent their preferences
    messages_session1 = [
        "I love Italian food, especially pasta and pizza.",
        "My favorite programming language is Python.",
        "I work as a data scientist."
    ]
    
    for msg in messages_session1:
        print(f"\nUser: {msg}")
        async for event in runner.run_async(
            user_id="alice",
            session_id=session1.id,
            new_message=types.UserContent(parts=[types.Part(text=msg)])
        ):
            if event.content and event.content.parts:
                for part in event.content.parts:
                    if part.text:
                        print(f"Agent: {part.text}")
    
    # Save session to long-term memory
    await memory_service.add_session_to_memory(session1)
    print("\n✓ Session 1 saved to memory")
    
    # ============================================
    # SESSION 2: Agent recalls information
    # ============================================
    print("\n" + "=" * 60)
    print("SESSION 2: Agent recalls past information")
    print("=" * 60)
    
    # New session (simulating a different day/conversation)
    session2 = await session_service.create_session(
        app_name="demo_app",
        user_id="alice",
        session_id="session_2"
    )
    
    # Search memory for user preferences
    print("\nSearching memory for user preferences...")
    search_result = await memory_service.search_memory(
        app_name="demo_app",
        user_id="alice",
        query="What does the user like to eat?"
    )
    
    print(f"Found {len(search_result.memories)} relevant memories:")
    for i, memory in enumerate(search_result.memories[:3], 1):
        text = memory.content.parts[0].text if memory.content.parts else ""
        print(f"  {i}. {text[:100]}...")
    
    # User asks about their preferences
    print("\nUser: What do I like?")
    async for event in runner.run_async(
        user_id="alice",
        session_id=session2.id,
        new_message=types.UserContent(parts=[types.Part(
            text="What do I like? Can you recall from our past conversations?"
        )])
    ):
        if event.content and event.content.parts:
            for part in event.content.parts:
                if part.text:
                    print(f"Agent: {part.text}")
    
    # ============================================
    # SESSION 3: Different user, no memory
    # ============================================
    print("\n" + "=" * 60)
    print("SESSION 3: Different user (no shared memory)")
    print("=" * 60)
    
    session3 = await session_service.create_session(
        app_name="demo_app",
        user_id="bob",  # Different user
        session_id="session_3"
    )
    
    # Search memory for Bob (should be empty)
    search_result_bob = await memory_service.search_memory(
        app_name="demo_app",
        user_id="bob",
        query="What does the user like?"
    )
    
    print(f"\nFound {len(search_result_bob.memories)} memories for Bob")
    print("(Bob has no previous conversations)")
    
    # Bob asks the same question
    print("\nBob: What do I like?")
    async for event in runner.run_async(
        user_id="bob",
        session_id=session3.id,
        new_message=types.UserContent(parts=[types.Part(
            text="What do I like?"
        )])
    ):
        if event.content and event.content.parts:
            for part in event.content.parts:
                if part.text:
                    print(f"Agent: {part.text}")

if __name__ == "__main__":
    asyncio.run(demonstrate_memory_and_sessions())
```

### Key Differences in Practice

| Aspect | Session Service | Memory Service |
|--------|----------------|----------------|
| **When data is stored** | Continuously during conversation | Explicitly via `add_session_to_memory()` |
| **When data is retrieved** | Automatically at session start | On-demand via `search_memory()` |
| **Data scope** | Single session | All sessions for a user |
| **Search capability** | Sequential access to events | Semantic/keyword search |
| **Use in conversation** | Automatically included in context | Must be explicitly searched and included |

---

## Search Comparison: Keyword vs Semantic

### InMemoryMemoryService: Keyword Matching

```python
# Query: "What does the user like?"
# Search: Looks for words "what", "does", "user", "like"

# Stored memory: "I love Italian food, especially pasta"
# Match: ✅ (contains "like" conceptually, but keyword match might miss it)

# Stored memory: "My favorite is pizza"
# Match: ❌ (no keyword overlap with query words)

# Stored memory: "I like programming"
# Match: ✅ (contains "like")
```

**Limitation**: Only finds exact word matches, misses semantic relationships.

### VertexAiMemoryBankService: Semantic Search

```python
# Query: "What does the user like?"
# Search: Creates embedding, finds semantically similar memories

# Stored memory: "I love Italian food, especially pasta"
# Match: ✅ (semantically similar - "love" ≈ "like")

# Stored memory: "My favorite is pizza"
# Match: ✅ (semantically similar - "favorite" ≈ "like")

# Stored memory: "I enjoy cooking"
# Match: ✅ (semantically similar - "enjoy" ≈ "like")

# Stored memory: "I dislike vegetables"
# Match: ✅ (semantically related, but opposite sentiment)
```

**Advantage**: Understands meaning, not just keywords. Finds related concepts.

---

## Performance Comparison

### InMemoryMemoryService

```python
# Performance characteristics
- Storage: O(1) - Dictionary lookup
- Search: O(n * m) where n = memories, m = words per memory
- Memory usage: ~1KB per memory entry
- Scalability: Limited by RAM

# Example: 10,000 memories
- Search time: ~50-100ms
- Memory usage: ~10MB
- Works well for: < 100,000 memories
```

### VertexAiMemoryBankService

```python
# Performance characteristics
- Storage: O(1) - Managed service
- Search: O(log n) - Vector index search
- Memory usage: Managed by Google Cloud
- Scalability: Millions of memories

# Example: 1,000,000 memories
- Search time: ~100-200ms
- Memory usage: Managed (not your concern)
- Works well for: Any scale
```

---

## Migration Guide

### From InMemoryMemoryService to VertexAiMemoryBankService

```python
# Before (Development)
from google.adk.memory import InMemoryMemoryService

memory_service = InMemoryMemoryService()

# After (Production)
from google.adk.memory import VertexAiMemoryBankService

memory_service = VertexAiMemoryBankService(
    project_id="your-project-id",
    location="us-central1",
    memory_bank_id="your-memory-bank-id"
)

# The API is identical - no code changes needed!
# Just swap the service implementation
```

### Migrating Existing Memories

If you have memories stored in `InMemoryMemoryService` and want to migrate:

```python
import asyncio
from google.adk.memory import InMemoryMemoryService, VertexAiMemoryBankService
from google.adk.sessions import InMemorySessionService

async def migrate_memories():
    """Migrate memories from InMemory to Vertex AI."""
    
    # Source: InMemory
    source_memory = InMemoryMemoryService()
    source_session = InMemorySessionService()
    
    # Target: Vertex AI
    target_memory = VertexAiMemoryBankService(
        project_id="your-project-id",
        location="us-central1",
        memory_bank_id="your-memory-bank-id"
    )
    
    # Get all sessions from source
    # (This is a simplified example - actual implementation would
    #  need to iterate through all stored sessions)
    
    # For each session, add to target memory
    # sessions = get_all_sessions_from_source()
    # for session in sessions:
    #     await target_memory.add_session_to_memory(session)
    
    print("Migration complete!")

asyncio.run(migrate_memories())
```

---

## Best Practices

### 1. Use the Right Service for the Right Purpose

```python
# Development/Testing
memory_service = InMemoryMemoryService()

# Production
memory_service = VertexAiMemoryBankService(
    project_id="prod-project",
    location="us-central1",
    memory_bank_id="prod-memory-bank"
)
```

### 2. Save Sessions to Memory Selectively

```python
# Don't save every session - only meaningful ones
async def after_agent_callback(ctx):
    """Save session to memory only if it contains valuable information."""
    session = ctx.session
    
    # Check if session has meaningful content
    has_valuable_info = any(
        event.content and len(event.content.parts) > 0
        for event in session.events
    )
    
    if has_valuable_info:
        await ctx.memory_service.add_session_to_memory(session)
```

### 3. Use Memory Search Strategically

```python
# Search memory before important conversations
async def start_conversation(user_id: str, query: str):
    # Search for relevant past memories
    memories = await memory_service.search_memory(
        app_name="my_app",
        user_id=user_id,
        query=query
    )
    
    # Include top memories in context
    context = "\n".join([
        f"Previous conversation: {mem.content.parts[0].text}"
        for mem in memories[:3]
    ])
    
    # Use context in conversation
    # ...
```

### 4. Handle Memory Service Errors Gracefully

```python
try:
    await memory_service.add_session_to_memory(session)
except Exception as e:
    # Log error but don't fail the conversation
    logger.error(f"Failed to save to memory: {e}")
    # Continue with conversation
```

---

## Troubleshooting

### InMemoryMemoryService Issues

**Problem**: Memories lost after restart
- **Cause**: In-memory storage doesn't persist
- **Solution**: Use `VertexAiMemoryBankService` for persistence

**Problem**: Slow search with many memories
- **Cause**: Linear search through all memories
- **Solution**: Consider `VertexAiMemoryBankService` for better performance

**Problem**: Memory not found in search
- **Cause**: Keyword matching requires exact word overlap
- **Solution**: Use more general keywords or switch to semantic search

### VertexAiMemoryBankService Issues

**Problem**: Authentication errors
- **Cause**: Missing or invalid GCP credentials
- **Solution**: Set up Application Default Credentials:
  ```bash
  gcloud auth application-default login
  ```

**Problem**: Memory Bank not found
- **Cause**: Incorrect `memory_bank_id` or project
- **Solution**: Verify Memory Bank exists and ID is correct

**Problem**: Search returns no results
- **Cause**: No memories stored yet or query doesn't match
- **Solution**: Ensure `add_session_to_memory()` was called, try different query

---

## Summary

| Service | Best For | Key Advantage |
|---------|----------|---------------|
| **InMemoryMemoryService** | Development, testing, small apps | Simple, fast, no setup |
| **VertexAiMemoryBankService** | Production, large-scale apps | Semantic search, scalability, persistence |

**Remember**: 
- **Sessions** = Short-term conversation context
- **Memory** = Long-term cross-session knowledge
- Use both together for complete agent memory capabilities

---

## Related Documentation

- [Sessions Package](07-Sessions-Package.md) - Session management
- [Memory Package](08-Memory-Package.md) - Memory service overview
- [ADK Memory and Session Runtime Trace](ADK-Memory-and-Session-Runtime-Trace.md) - Implementation details
- [State Management](11-State-Management.md) - Session state handling
