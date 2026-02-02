# Google ADK: Vertex AI RAG Memory Service

**File Path**: `docs/19-VertexAI-RAG-Memory-Service.md`  
**Package**: `google.adk.memory.VertexAiRagMemoryService`

## Overview

`VertexAiRagMemoryService` is a memory service implementation that uses **Google Cloud Vertex AI RAG (Retrieval-Augmented Generation)** for storing and retrieving long-term memories across sessions. Unlike `VertexAiMemoryBankService` which uses Memory Bank, this service uses Vertex AI RAG corpora for semantic search and retrieval.

### What is RAG?

**RAG (Retrieval-Augmented Generation)** is a technique that:
1. **Stores** documents/data in a searchable corpus
2. **Creates embeddings** automatically for semantic understanding
3. **Retrieves** relevant context based on semantic similarity
4. **Augments** LLM prompts with retrieved context

### Key Characteristics

- ✅ **Semantic Search**: Uses vector embeddings for meaning-based retrieval
- ✅ **Scalable**: Handles large volumes of memories efficiently
- ✅ **Persistent**: Stores memories in Google Cloud Vertex AI RAG corpus
- ✅ **Automatic Embeddings**: Vertex AI handles embedding creation automatically
- ✅ **Filtered Results**: Filters by `app_name` and `user_id` automatically
- ✅ **Event Merging**: Intelligently merges overlapping events from same session

---

## Comparison with Other Memory Services

| Feature | InMemoryMemoryService | VertexAiMemoryBankService | VertexAiRagMemoryService |
|---------|----------------------|---------------------------|--------------------------|
| **Storage** | In-memory dict | Vertex AI Memory Bank | Vertex AI RAG Corpus |
| **Search Method** | Keyword matching | Semantic (Memory Bank) | Semantic (RAG) |
| **Persistence** | ❌ Lost on restart | ✅ Persistent | ✅ Persistent |
| **Setup Complexity** | None | Medium (Memory Bank) | Medium (RAG Corpus) |
| **Use Case** | Development/testing | Production (Memory Bank) | Production (RAG) |
| **Data Format** | Events as-is | Structured facts | JSON events in corpus |
| **Filtering** | Manual | Built-in by scope | Built-in by display_name |

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Agent Session                              │
│              (Session with events)                            │
└──────────────────────────┬───────────────────────────────────┘
                           │
                           │ add_session_to_memory()
                           ▼
┌─────────────────────────────────────────────────────────────┐
│         VertexAiRagMemoryService                             │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ 1. Extract events with content                        │  │
│  │ 2. Convert to JSON format                              │  │
│  │ 3. Write to temporary file                             │  │
│  │ 4. Upload to RAG corpus                                 │  │
│  │    (display_name: app_name.user_id.session_id)         │  │
│  └──────────────────────────────────────────────────────┘  │
└──────────────────────────┬───────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│         Vertex AI RAG Corpus                                 │
│  - Stores uploaded files                                     │
│  - Creates embeddings automatically                          │
│  - Indexes for semantic search                               │
└──────────────────────────┬───────────────────────────────────┘
                           │
                           │ search_memory(query)
                           ▼
┌─────────────────────────────────────────────────────────────┐
│         Semantic Search & Retrieval                          │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ 1. Query → embedding                                   │  │
│  │ 2. Vector similarity search                            │  │
│  │ 3. Filter by app_name.user_id prefix                   │  │
│  │ 4. Parse JSON events                                   │  │
│  │ 5. Merge overlapping events                            │  │
│  │ 6. Return MemoryEntry list                             │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

---

## API Reference

### Constructor

```python
VertexAiRagMemoryService(
    rag_corpus: Optional[str] = None,
    similarity_top_k: Optional[int] = None,
    vector_distance_threshold: float = 10,
)
```

#### Parameters

- **`rag_corpus`** (Optional[str]): 
  - The name of the Vertex AI RAG corpus to use
  - Format: `projects/{project}/locations/{location}/ragCorpora/{rag_corpus_id}`
  - Or just: `{rag_corpus_id}` (will be resolved automatically)
  - **Required** for `add_session_to_memory()` and `search_memory()`

- **`similarity_top_k`** (Optional[int]):
  - Number of top contexts to retrieve during search
  - Default: None (uses RAG service default)
  - Higher values = more results but potentially less relevant

- **`vector_distance_threshold`** (float):
  - Only returns contexts with vector distance smaller than threshold
  - Default: `10`
  - Lower values = stricter similarity requirement
  - Higher values = more lenient matching

### Methods

#### `add_session_to_memory(session: Session)`

Adds a session's events to the RAG corpus.

**Process:**
1. Extracts events with content from the session
2. Converts each event to JSON format with `author`, `timestamp`, and `text`
3. Writes to a temporary file
4. Uploads file to RAG corpus with `display_name = f"{app_name}.{user_id}.{session_id}"`
5. Cleans up temporary file

**Example:**
```python
await memory_service.add_session_to_memory(session)
```

#### `search_memory(*, app_name: str, user_id: str, query: str) -> SearchMemoryResponse`

Searches for memories matching the query using semantic similarity.

**Process:**
1. Performs RAG retrieval query with the provided query text
2. Filters results by `app_name.user_id.` prefix in `source_display_name`
3. Parses JSON events from retrieved contexts
4. Merges overlapping events from the same session
5. Returns `SearchMemoryResponse` with `MemoryEntry` objects

**Returns:** `SearchMemoryResponse` containing:
- `memories`: List of `MemoryEntry` objects matching the query

**Example:**
```python
result = await memory_service.search_memory(
    app_name="my_app",
    user_id="alice",
    query="What did the user say about Python?"
)
```

---

## Setup and Prerequisites

### 1. Install Required Packages

```bash
# Install Google ADK (includes Vertex AI support)
pip install google-adk

# Ensure Vertex AI SDK is installed
pip install google-cloud-aiplatform
```

### 2. Set Up Google Cloud Project

```bash
# Authenticate with Google Cloud
gcloud auth application-default login

# Set your project
gcloud config set project YOUR_PROJECT_ID
```

### 3. Create a RAG Corpus

You need to create a RAG corpus in Vertex AI before using the service:

```python
from google.cloud import aiplatform
from vertexai.preview import rag

# Initialize Vertex AI
aiplatform.init(project="your-project-id", location="us-central1")

# Create a RAG corpus
corpus = rag.create_corpus(
    display_name="my-memory-corpus",
    description="Corpus for storing agent memories"
)

print(f"Corpus created: {corpus.name}")
# Output: projects/123456/locations/us-central1/ragCorpora/789012
```

**Alternative: Using gcloud CLI**

```bash
# Create corpus
gcloud ai rag-corpora create \
  --display-name="my-memory-corpus" \
  --region=us-central1

# Get corpus ID from output
```

### 4. Initialize the Service

```python
from google.adk.memory import VertexAiRagMemoryService

# Option 1: Full resource path
memory_service = VertexAiRagMemoryService(
    rag_corpus="projects/123456/locations/us-central1/ragCorpora/789012",
    similarity_top_k=5,
    vector_distance_threshold=8.0
)

# Option 2: Just corpus ID (if default project/location set)
memory_service = VertexAiRagMemoryService(
    rag_corpus="789012",
    similarity_top_k=5
)
```

---

## Complete Examples

### Example 1: Basic Usage

```python
#!/usr/bin/env python3
"""Basic example of VertexAiRagMemoryService."""

import asyncio
from google.adk import Agent
from google.adk.memory import VertexAiRagMemoryService
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

async def main():
    # Initialize RAG memory service
    memory_service = VertexAiRagMemoryService(
        rag_corpus="projects/your-project/locations/us-central1/ragCorpora/your-corpus-id",
        similarity_top_k=5,
        vector_distance_threshold=10.0
    )
    
    # Initialize session service
    session_service = InMemorySessionService()
    
    # Create agent
    agent = Agent(
        name="rag_memory_agent",
        model="gemini-1.5-flash",
        instruction="You are a helpful assistant with RAG-based memory."
    )
    
    # Create runner
    runner = Runner(
        app_name="rag_app",
        agent=agent,
        session_service=session_service,
        memory_service=memory_service
    )
    
    # Create and use session
    session = await session_service.create_session(
        app_name="rag_app",
        user_id="alice",
        session_id="session_1"
    )
    
    # Have a conversation
    print("User: I love Python programming and machine learning")
    async for event in runner.run_async(
        user_id="alice",
        session_id=session.id,
        new_message=types.UserContent(parts=[types.Part(
            text="I love Python programming and machine learning"
        )])
    ):
        if event.content and event.content.parts:
            for part in event.content.parts:
                if part.text:
                    print(f"Agent: {part.text}")
    
    # Save session to RAG memory
    await memory_service.add_session_to_memory(session)
    print("\n✓ Session saved to RAG corpus")
    
    # Later: Search memory
    print("\nSearching memory...")
    search_result = await memory_service.search_memory(
        app_name="rag_app",
        user_id="alice",
        query="What programming language does the user like?"
    )
    
    print(f"Found {len(search_result.memories)} memories:")
    for memory in search_result.memories:
        text = memory.content.parts[0].text if memory.content.parts else ""
        print(f"  - {text}")

if __name__ == "__main__":
    asyncio.run(main())
```

### Example 2: Multi-Session Memory

```python
#!/usr/bin/env python3
"""Example showing memory across multiple sessions."""

import asyncio
from google.adk import Agent
from google.adk.memory import VertexAiRagMemoryService
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

async def main():
    memory_service = VertexAiRagMemoryService(
        rag_corpus="projects/your-project/locations/us-central1/ragCorpora/your-corpus-id",
        similarity_top_k=10
    )
    
    session_service = InMemorySessionService()
    
    agent = Agent(
        name="multi_session_agent",
        model="gemini-1.5-flash",
        instruction="You are an assistant that remembers past conversations."
    )
    
    runner = Runner(
        app_name="multi_app",
        agent=agent,
        session_service=session_service,
        memory_service=memory_service
    )
    
    # ============================================
    # SESSION 1: User shares preferences
    # ============================================
    print("=" * 60)
    print("SESSION 1: User shares information")
    print("=" * 60)
    
    session1 = await session_service.create_session(
        app_name="multi_app",
        user_id="bob",
        session_id="session_2024_01_15"
    )
    
    messages = [
        "I'm a software engineer.",
        "I specialize in Python and Go.",
        "I work on distributed systems.",
        "I prefer using Docker for containerization."
    ]
    
    for msg in messages:
        print(f"\nUser: {msg}")
        async for event in runner.run_async(
            user_id="bob",
            session_id=session1.id,
            new_message=types.UserContent(parts=[types.Part(text=msg)])
        ):
            if event.content and event.content.parts:
                for part in event.content.parts:
                    if part.text:
                        print(f"Agent: {part.text}")
    
    # Save to memory
    await memory_service.add_session_to_memory(session1)
    print("\n✓ Session 1 saved")
    
    # ============================================
    # SESSION 2: Different day, agent recalls
    # ============================================
    print("\n" + "=" * 60)
    print("SESSION 2: Agent recalls past information")
    print("=" * 60)
    
    session2 = await session_service.create_session(
        app_name="multi_app",
        user_id="bob",
        session_id="session_2024_01_20"
    )
    
    # Search memory
    search_result = await memory_service.search_memory(
        app_name="multi_app",
        user_id="bob",
        query="What technologies does the user work with?"
    )
    
    print(f"\nFound {len(search_result.memories)} relevant memories:")
    for i, memory in enumerate(search_result.memories[:5], 1):
        text = memory.content.parts[0].text if memory.content.parts else ""
        print(f"  {i}. {text[:100]}...")
    
    # Use memory in conversation
    memory_context = "\n".join([
        f"- {mem.content.parts[0].text}"
        for mem in search_result.memories[:3]
        if mem.content.parts
    ])
    
    print("\nUser: What do you know about my work?")
    async for event in runner.run_async(
        user_id="bob",
        session_id=session2.id,
        new_message=types.UserContent(parts=[types.Part(
            text=f"Based on this context:\n{memory_context}\n\nWhat do you know about my work?"
        )])
    ):
        if event.content and event.content.parts:
            for part in event.content.parts:
                if part.text:
                    print(f"Agent: {part.text}")

if __name__ == "__main__":
    asyncio.run(main())
```

### Example 3: Using with Callbacks

```python
#!/usr/bin/env python3
"""Example using RAG memory with callbacks."""

import asyncio
from google.adk import Agent
from google.adk.memory import VertexAiRagMemoryService
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.adk.agents import CallbackContext
from google.genai import types

async def after_agent_callback(ctx: CallbackContext):
    """Save session to memory after agent responds."""
    if ctx.memory_service:
        # Only save if conversation was meaningful
        if len(ctx.session.events) > 2:  # At least user + agent messages
            await ctx.memory_service.add_session_to_memory(ctx.session)
            print("\n[Callback] Session saved to RAG memory")

async def main():
    memory_service = VertexAiRagMemoryService(
        rag_corpus="projects/your-project/locations/us-central1/ragCorpora/your-corpus-id"
    )
    
    session_service = InMemorySessionService()
    
    agent = Agent(
        name="callback_agent",
        model="gemini-1.5-flash",
        instruction="You are a helpful assistant.",
        callbacks={
            "after_agent": [after_agent_callback]
        }
    )
    
    runner = Runner(
        app_name="callback_app",
        agent=agent,
        session_service=session_service,
        memory_service=memory_service
    )
    
    session = await session_service.create_session(
        app_name="callback_app",
        user_id="charlie",
        session_id="session_1"
    )
    
    # Conversation - automatically saved by callback
    async for event in runner.run_async(
        user_id="charlie",
        session_id=session.id,
        new_message=types.UserContent(parts=[types.Part(
            text="My favorite color is blue and I love jazz music"
        )])
    ):
        if event.content and event.content.parts:
            for part in event.content.parts:
                if part.text:
                    print(f"Agent: {part.text}")

if __name__ == "__main__":
    asyncio.run(main())
```

### Example 4: Advanced Search with Filtering

```python
#!/usr/bin/env python3
"""Advanced search examples with different thresholds."""

import asyncio
from google.adk.memory import VertexAiRagMemoryService

async def main():
    # Strict similarity (only very similar results)
    strict_service = VertexAiRagMemoryService(
        rag_corpus="projects/your-project/locations/us-central1/ragCorpora/your-corpus-id",
        similarity_top_k=3,
        vector_distance_threshold=5.0  # Strict threshold
    )
    
    # Lenient similarity (more results)
    lenient_service = VertexAiRagMemoryService(
        rag_corpus="projects/your-project/locations/us-central1/ragCorpora/your-corpus-id",
        similarity_top_k=10,
        vector_distance_threshold=15.0  # Lenient threshold
    )
    
    # Search with strict service
    strict_results = await strict_service.search_memory(
        app_name="my_app",
        user_id="alice",
        query="Python programming"
    )
    print(f"Strict search: {len(strict_results.memories)} results")
    
    # Search with lenient service
    lenient_results = await lenient_service.search_memory(
        app_name="my_app",
        user_id="alice",
        query="Python programming"
    )
    print(f"Lenient search: {len(lenient_results.memories)} results")

if __name__ == "__main__":
    asyncio.run(main())
```

### Example 5: Error Handling

```python
#!/usr/bin/env python3
"""Example with proper error handling."""

import asyncio
import logging
from google.adk import Agent
from google.adk.memory import VertexAiRagMemoryService
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

logging.basicConfig(level=logging.INFO)

async def main():
    try:
        memory_service = VertexAiRagMemoryService(
            rag_corpus="projects/your-project/locations/us-central1/ragCorpora/your-corpus-id"
        )
    except Exception as e:
        print(f"Failed to initialize RAG memory service: {e}")
        return
    
    session_service = InMemorySessionService()
    
    agent = Agent(
        name="error_handling_agent",
        model="gemini-1.5-flash",
        instruction="You are a helpful assistant."
    )
    
    runner = Runner(
        app_name="error_app",
        agent=agent,
        session_service=session_service,
        memory_service=memory_service
    )
    
    session = await session_service.create_session(
        app_name="error_app",
        user_id="dave",
        session_id="session_1"
    )
    
    # Try to save to memory
    try:
        await memory_service.add_session_to_memory(session)
        print("✓ Session saved successfully")
    except ValueError as e:
        print(f"ValueError: {e}")
        print("Make sure rag_corpus is set correctly")
    except Exception as e:
        print(f"Unexpected error: {e}")
        logging.exception("Error saving to memory")
    
    # Try to search memory
    try:
        result = await memory_service.search_memory(
            app_name="error_app",
            user_id="dave",
            query="test query"
        )
        print(f"Search successful: {len(result.memories)} results")
    except Exception as e:
        print(f"Search failed: {e}")
        logging.exception("Error searching memory")

if __name__ == "__main__":
    asyncio.run(main())
```

---

## Related Services and Packages

### 1. VertexAiRagRetrieval Tool

`VertexAiRagRetrieval` is a **tool** (not a memory service) that allows agents to retrieve information from RAG corpora during conversation.

**Key Differences:**

| Aspect | VertexAiRagMemoryService | VertexAiRagRetrieval |
|--------|-------------------------|---------------------|
| **Type** | Memory Service | Tool |
| **Purpose** | Long-term memory storage | On-demand retrieval |
| **Usage** | `memory_service` in Runner | Tool added to agent |
| **Storage** | Stores session events | Reads from corpus |
| **When Used** | Explicit `add_session_to_memory()` | Called by agent during conversation |

**Example: Using VertexAiRagRetrieval Tool**

```python
from google.adk import Agent
from google.adk.tools.retrieval import VertexAiRagRetrieval
from google.adk.runners import Runner

# Create RAG retrieval tool
rag_tool = VertexAiRagRetrieval(
    name="search_knowledge_base",
    description="Search the knowledge base for relevant information",
    rag_corpora=["projects/your-project/locations/us-central1/ragCorpora/your-corpus-id"],
    similarity_top_k=5
)

# Create agent with tool
agent = Agent(
    name="rag_tool_agent",
    model="gemini-1.5-flash",
    instruction="You are an assistant with access to a knowledge base.",
    tools=[rag_tool]
)

# Agent can now use the tool during conversation
runner = Runner(agent=agent)
```

### 2. VertexAiMemoryBankService

Another memory service option. See [Memory Services Comparison](18-Memory-Services-Comparison.md) for differences.

### 3. BaseMemoryService

Abstract base class that all memory services inherit from. Defines the interface:
- `add_session_to_memory(session)`
- `search_memory(app_name, user_id, query) -> SearchMemoryResponse`

---

## How It Works Internally

### Storage Process (`add_session_to_memory`)

```python
# Simplified internal process
async def add_session_to_memory(self, session: Session):
    # 1. Extract events with content
    events_with_content = [
        event for event in session.events
        if event.content and event.content.parts
    ]
    
    # 2. Convert to JSON format
    json_lines = []
    for event in events_with_content:
        text_parts = [part.text for part in event.content.parts if part.text]
        json_lines.append(json.dumps({
            "author": event.author,
            "timestamp": event.timestamp,
            "text": ".".join(text_parts)
        }))
    
    # 3. Write to temporary file
    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt") as temp_file:
        temp_file.write("\n".join(json_lines))
        temp_file_path = temp_file.name
    
    # 4. Upload to RAG corpus
    rag.upload_file(
        corpus_name=rag_corpus,
        path=temp_file_path,
        display_name=f"{session.app_name}.{session.user_id}.{session.id}"
    )
```

### Search Process (`search_memory`)

```python
# Simplified internal process
async def search_memory(self, *, app_name, user_id, query):
    # 1. Perform RAG retrieval query
    response = rag.retrieval_query(
        text=query,
        rag_resources=[...],
        similarity_top_k=self.similarity_top_k,
        vector_distance_threshold=self.vector_distance_threshold
    )
    
    # 2. Filter by app_name.user_id prefix
    memory_results = []
    for context in response.contexts.contexts:
        if not context.source_display_name.startswith(f"{app_name}.{user_id}."):
            continue
        
        # 3. Parse JSON events
        session_id = context.source_display_name.split(".")[-1]
        events = []
        for line in context.text.split("\n"):
            event_data = json.loads(line)
            events.append(Event(
                author=event_data["author"],
                timestamp=event_data["timestamp"],
                content=Content(parts=[Part(text=event_data["text"])])
            ))
        
        # 4. Merge overlapping events
        merged_events = _merge_event_lists([events])
        
        # 5. Create MemoryEntry objects
        for event in merged_events:
            memory_results.append(MemoryEntry(
                content=event.content,
                author=event.author,
                timestamp=event.timestamp
            ))
    
    return SearchMemoryResponse(memories=memory_results)
```

---

## Best Practices

### 1. Corpus Management

```python
# Create separate corpora for different purposes
memory_corpus = "projects/.../ragCorpora/user-memories"
knowledge_corpus = "projects/.../ragCorpora/knowledge-base"

# Use appropriate corpus for each use case
user_memory_service = VertexAiRagMemoryService(rag_corpus=memory_corpus)
knowledge_service = VertexAiRagMemoryService(rag_corpus=knowledge_corpus)
```

### 2. Threshold Tuning

```python
# Start with defaults, then tune based on results
memory_service = VertexAiRagMemoryService(
    rag_corpus=corpus_id,
    similarity_top_k=5,  # Start with 5, increase if needed
    vector_distance_threshold=10.0  # Start with 10, adjust based on precision/recall
)

# If too many irrelevant results: lower threshold
# If missing relevant results: raise threshold
```

### 3. Selective Memory Storage

```python
async def should_save_session(session: Session) -> bool:
    """Determine if session should be saved to memory."""
    # Only save meaningful conversations
    if len(session.events) < 2:
        return False
    
    # Check if conversation has substantial content
    total_text_length = sum(
        len(part.text or "")
        for event in session.events
        if event.content
        for part in event.content.parts or []
    )
    
    return total_text_length > 100  # Minimum threshold

# Use in callback
async def after_agent_callback(ctx: CallbackContext):
    if await should_save_session(ctx.session):
        await ctx.memory_service.add_session_to_memory(ctx.session)
```

### 4. Query Optimization

```python
# Good queries (specific, semantic)
query1 = "What programming languages does the user know?"
query2 = "User's preferences for development tools"

# Bad queries (too vague or keyword-focused)
query3 = "Python"  # Too vague
query4 = "user like"  # Not semantic enough
```

### 5. Error Handling

```python
async def safe_add_to_memory(memory_service, session):
    """Safely add session to memory with error handling."""
    try:
        await memory_service.add_session_to_memory(session)
        return True
    except ValueError as e:
        logger.error(f"Configuration error: {e}")
        return False
    except Exception as e:
        logger.exception(f"Unexpected error saving to memory: {e}")
        return False
```

### 6. Memory Cleanup

```python
# Periodically clean up old memories
# Note: This requires direct RAG corpus management
from vertexai.preview import rag

async def cleanup_old_memories(corpus_name: str, days_old: int = 30):
    """Remove memories older than specified days."""
    # List files in corpus
    # Filter by date
    # Delete old files
    # (Implementation depends on RAG API)
    pass
```

---

## Troubleshooting

### Issue: ImportError for VertexAiRagMemoryService

**Error:**
```python
ImportError: cannot import name 'VertexAiRagMemoryService'
```

**Solution:**
```bash
# Install Vertex AI SDK
pip install google-cloud-aiplatform

# Verify installation
python -c "from google.adk.memory import VertexAiRagMemoryService; print('OK')"
```

### Issue: RAG corpus not found

**Error:**
```python
ValueError: Rag resources must be set.
```

**Solution:**
```python
# Make sure rag_corpus is provided
memory_service = VertexAiRagMemoryService(
    rag_corpus="projects/your-project/locations/us-central1/ragCorpora/your-corpus-id"
)
```

### Issue: No results from search

**Possible Causes:**
1. No memories stored yet
2. Threshold too strict
3. Query doesn't match stored content

**Solution:**
```python
# Check if memories exist
result = await memory_service.search_memory(
    app_name="my_app",
    user_id="alice",
    query="test"
)
print(f"Results: {len(result.memories)}")

# Try more lenient threshold
lenient_service = VertexAiRagMemoryService(
    rag_corpus=corpus_id,
    vector_distance_threshold=20.0  # More lenient
)
```

### Issue: Authentication errors

**Error:**
```python
google.auth.exceptions.DefaultCredentialsError: Could not automatically determine credentials
```

**Solution:**
```bash
# Set up Application Default Credentials
gcloud auth application-default login

# Or set environment variable
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/service-account-key.json"
```

### Issue: Results from wrong user

**Cause:** Filtering by `app_name.user_id` prefix might not be working correctly.

**Solution:**
```python
# Verify display_name format matches
# Should be: "{app_name}.{user_id}.{session_id}"

# Check search results
result = await memory_service.search_memory(
    app_name="my_app",
    user_id="alice",
    query="test"
)

for memory in result.memories:
    print(f"Metadata: {memory.custom_metadata}")
```

---

## Performance Considerations

### Storage Performance

- **Upload time**: Depends on file size and number of events
- **Typical**: ~100-500ms for sessions with 10-50 events
- **Optimization**: Batch multiple sessions if possible

### Search Performance

- **Query time**: ~100-300ms for semantic search
- **Factors**: 
  - Corpus size
  - `similarity_top_k` value
  - Network latency
- **Optimization**: Use appropriate `similarity_top_k` (don't request more than needed)

### Scalability

- **Corpus size**: Can handle millions of documents
- **Concurrent requests**: Vertex AI handles scaling automatically
- **Cost**: Pay-per-use based on storage and queries

---

## Comparison: RAG vs Memory Bank

| Aspect | VertexAiRagMemoryService | VertexAiMemoryBankService |
|--------|-------------------------|--------------------------|
| **Storage Format** | Files in RAG corpus | Structured facts in Memory Bank |
| **Data Model** | JSON events | Fact-based memories |
| **Search** | Semantic (vector) | Semantic (Memory Bank) |
| **Use Case** | Document-like memories | Fact extraction |
| **Setup** | RAG corpus | Memory Bank + Agent Engine |
| **Filtering** | Display name prefix | Built-in scope filtering |
| **Event Preservation** | Full event structure | Extracted facts |

**When to use RAG:**
- Need to preserve full conversation context
- Document-like memory storage
- Already using RAG for other purposes

**When to use Memory Bank:**
- Need fact extraction
- Want structured memory format
- Using Agent Engine already

---

## Summary

`VertexAiRagMemoryService` provides:

✅ **Semantic search** using Vertex AI RAG  
✅ **Persistent storage** in Google Cloud  
✅ **Automatic filtering** by app/user  
✅ **Event preservation** in original format  
✅ **Scalable** to millions of memories  

**Key Takeaways:**
- Requires RAG corpus setup
- Uses semantic search (not keyword)
- Filters automatically by `app_name.user_id`
- Stores events as JSON in corpus files
- Best for production applications needing semantic memory

---

## Related Documentation

- [Memory Services Comparison](18-Memory-Services-Comparison.md) - Compare all memory services
- [Memory Package](08-Memory-Package.md) - Overview of memory services
- [Sessions Package](07-Sessions-Package.md) - Session management
- [Tools Package](02-Tools-Package.md) - Including VertexAiRagRetrieval tool
- [ADK Memory and Session Runtime Trace](ADK-Memory-and-Session-Runtime-Trace.md) - Implementation details

---

## Additional Resources

- [Vertex AI RAG Documentation](https://cloud.google.com/vertex-ai/generative-ai/docs/rag/overview)
- [RAG Best Practices](https://cloud.google.com/vertex-ai/generative-ai/docs/rag/best-practices)
- [Vertex AI Python SDK](https://cloud.google.com/python/docs/reference/aiplatform/latest)
