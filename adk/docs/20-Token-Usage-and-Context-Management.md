# Google ADK: Token Usage and Context Management

**File Path**: `docs/20-Token-Usage-and-Context-Management.md`  
**Package**: `google.adk`

## Overview

This document provides a comprehensive guide to:
1. **Token Usage Tracking** - How to access input/output token counts from responses
2. **Context Length Management** - How to track and measure context length for sessions
3. **Model Context Limits** - Understanding model-specific context windows
4. **Context Compaction** - Detailed explanation of ADK's sliding window compaction mechanism

---

## Part 1: Token Usage in Responses

### Accessing Token Usage Metadata

ADK provides token usage information through the `usage_metadata` attribute on `Event` objects. Since `Event` extends `LlmResponse`, all events have access to usage metadata.

#### Usage Metadata Structure

```python
from google.genai import types

# Usage metadata contains:
usage_metadata: types.GenerateContentResponseUsageMetadata
  - prompt_token_count: int      # Input tokens
  - candidates_token_count: int   # Output tokens  
  - total_token_count: int        # Total tokens (input + output)
```

### Example 1: Accessing Token Usage from Events

```python
#!/usr/bin/env python3
"""Example: Access token usage from events."""

import asyncio
from google.adk import Agent
from google.adk.runners import InMemoryRunner
from google.genai import types

async def main():
    agent = Agent(
        name="token_tracking_agent",
        model="gemini-1.5-flash",
        instruction="You are a helpful assistant."
    )
    
    runner = InMemoryRunner(agent=agent)
    
    session = await runner.session_service.create_session(
        app_name="InMemoryRunner",
        user_id="user1",
        session_id="session1"
    )
    
    total_input_tokens = 0
    total_output_tokens = 0
    
    async for event in runner.run_async(
        user_id="user1",
        session_id="session1",
        new_message=types.UserContent(parts=[types.Part(text="Explain quantum computing in detail.")])
    ):
        # Check for usage metadata
        if event.usage_metadata:
            input_tokens = event.usage_metadata.prompt_token_count or 0
            output_tokens = event.usage_metadata.candidates_token_count or 0
            total_tokens = event.usage_metadata.total_token_count or 0
            
            print(f"\n[Token Usage]")
            print(f"  Input tokens:  {input_tokens}")
            print(f"  Output tokens: {output_tokens}")
            print(f"  Total tokens:  {total_tokens}")
            
            total_input_tokens += input_tokens
            total_output_tokens += output_tokens
        
        # Print content
        if event.content and event.content.parts:
            for part in event.content.parts:
                if part.text:
                    print(part.text, end="", flush=True)
    
    print(f"\n\n[Session Totals]")
    print(f"  Total input tokens:  {total_input_tokens}")
    print(f"  Total output tokens: {total_output_tokens}")
    print(f"  Grand total:         {total_input_tokens + total_output_tokens}")

if __name__ == "__main__":
    asyncio.run(main())
```

### Example 2: Tracking Token Usage Across Multiple Turns

```python
#!/usr/bin/env python3
"""Track token usage across multiple conversation turns."""

import asyncio
from google.adk import Agent
from google.adk.runners import InMemoryRunner
from google.genai import types

class TokenTracker:
    """Tracks token usage across a session."""
    
    def __init__(self):
        self.input_tokens = 0
        self.output_tokens = 0
        self.turn_count = 0
    
    def add_event(self, event):
        """Add token usage from an event."""
        if event.usage_metadata:
            self.input_tokens += event.usage_metadata.prompt_token_count or 0
            self.output_tokens += event.usage_metadata.candidates_token_count or 0
            self.turn_count += 1
    
    def get_summary(self):
        """Get usage summary."""
        return {
            "turns": self.turn_count,
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "total_tokens": self.input_tokens + self.output_tokens,
            "avg_input_per_turn": self.input_tokens / self.turn_count if self.turn_count > 0 else 0,
            "avg_output_per_turn": self.output_tokens / self.turn_count if self.turn_count > 0 else 0,
        }

async def main():
    agent = Agent(
        name="multi_turn_agent",
        model="gemini-1.5-flash",
        instruction="You are a helpful assistant."
    )
    
    runner = InMemoryRunner(agent=agent)
    tracker = TokenTracker()
    
    session = await runner.session_service.create_session(
        app_name="InMemoryRunner",
        user_id="user1",
        session_id="session1"
    )
    
    messages = [
        "What is Python?",
        "How does it differ from Java?",
        "Can you give me a code example?",
    ]
    
    for i, message in enumerate(messages, 1):
        print(f"\n{'='*60}")
        print(f"Turn {i}: {message}")
        print('='*60)
        
        async for event in runner.run_async(
            user_id="user1",
            session_id="session1",
            new_message=types.UserContent(parts=[types.Part(text=message)])
        ):
            tracker.add_event(event)
            
            if event.content and event.content.parts:
                for part in event.content.parts:
                    if part.text:
                        print(part.text, end="", flush=True)
        
        print()  # New line
    
    # Print summary
    summary = tracker.get_summary()
    print(f"\n{'='*60}")
    print("Token Usage Summary")
    print('='*60)
    print(f"Total turns:              {summary['turns']}")
    print(f"Total input tokens:       {summary['input_tokens']:,}")
    print(f"Total output tokens:      {summary['output_tokens']:,}")
    print(f"Total tokens:            {summary['total_tokens']:,}")
    print(f"Avg input per turn:       {summary['avg_input_per_turn']:.1f}")
    print(f"Avg output per turn:      {summary['avg_output_per_turn']:.1f}")

if __name__ == "__main__":
    asyncio.run(main())
```

### Example 3: Token Usage in Callbacks

```python
#!/usr/bin/env python3
"""Track token usage using callbacks."""

import asyncio
from google.adk import Agent
from google.adk.runners import InMemoryRunner
from google.adk.agents import CallbackContext
from google.genai import types

class TokenUsagePlugin:
    """Plugin to track token usage."""
    
    def __init__(self):
        self.session_tokens = {}  # session_id -> token counts
    
    async def on_event(self, ctx: CallbackContext, event):
        """Track tokens from each event."""
        if event.usage_metadata:
            session_id = ctx.session.id
            
            if session_id not in self.session_tokens:
                self.session_tokens[session_id] = {
                    "input": 0,
                    "output": 0,
                    "turns": 0
                }
            
            tokens = self.session_tokens[session_id]
            tokens["input"] += event.usage_metadata.prompt_token_count or 0
            tokens["output"] += event.usage_metadata.candidates_token_count or 0
            tokens["turns"] += 1
    
    def get_session_stats(self, session_id: str):
        """Get statistics for a session."""
        return self.session_tokens.get(session_id, {
            "input": 0,
            "output": 0,
            "turns": 0
        })

async def main():
    token_plugin = TokenUsagePlugin()
    
    agent = Agent(
        name="callback_agent",
        model="gemini-1.5-flash",
        instruction="You are a helpful assistant.",
        callbacks={
            "on_event": [token_plugin.on_event]
        }
    )
    
    runner = InMemoryRunner(agent=agent)
    
    session = await runner.session_service.create_session(
        app_name="InMemoryRunner",
        user_id="user1",
        session_id="session1"
    )
    
    async for event in runner.run_async(
        user_id="user1",
        session_id="session1",
        new_message=types.UserContent(parts=[types.Part(text="Tell me about AI.")])
    ):
        if event.content and event.content.parts:
            for part in event.content.parts:
                if part.text:
                    print(part.text, end="", flush=True)
    
    # Get stats
    stats = token_plugin.get_session_stats("session1")
    print(f"\n\n[Token Stats]")
    print(f"  Input tokens:  {stats['input']:,}")
    print(f"  Output tokens: {stats['output']:,}")
    print(f"  Total tokens:  {stats['input'] + stats['output']:,}")
    print(f"  Turns:         {stats['turns']}")

if __name__ == "__main__":
    asyncio.run(main())
```

### Important Notes on Token Usage

1. **Not All Events Have Usage Metadata**: Only events that result from LLM calls will have `usage_metadata`. Events like user messages, tool calls, or system events may not have this information.

2. **Streaming Responses**: For streaming responses, usage metadata may be available only on the final event or may be accumulated across multiple events.

3. **Multiple Agents**: In multi-agent scenarios, each agent's response will have its own usage metadata.

---

## Part 2: Context Length Tracking

### Understanding Context Length

**Context length** refers to the total number of tokens in the conversation history that is sent to the model. In ADK, context is built from `session.events` and converted to `types.Content` objects that are sent to the LLM.

### How Context is Built

The context sent to the model is constructed in `flows/llm_flows/contents.py`:

```python
# Simplified flow
session.events (list[Event])
  ↓
_get_contents(branch, events, agent_name)
  ↓
Filter events (rewind, compaction, branch filtering)
  ↓
Convert to types.Content objects
  ↓
llm_request.contents (sent to model)
```

### Example 1: Calculate Context Length from Session

```python
#!/usr/bin/env python3
"""Calculate context length from session events."""

import asyncio
from google.adk import Agent
from google.adk.runners import InMemoryRunner
from google.genai import types

def estimate_tokens(text: str) -> int:
    """Rough token estimation (1 token ≈ 4 characters for English)."""
    return len(text) // 4

def calculate_context_length(session) -> dict:
    """Calculate context length from session events."""
    total_chars = 0
    event_count = 0
    
    for event in session.events:
        if event.content and event.content.parts:
            for part in event.content.parts:
                if part.text:
                    total_chars += len(part.text)
                    event_count += 1
    
    estimated_tokens = estimate_tokens("".join([
        part.text
        for event in session.events
        if event.content
        for part in event.content.parts or []
        if part.text
    ]))
    
    return {
        "event_count": len(session.events),
        "events_with_content": event_count,
        "total_characters": total_chars,
        "estimated_tokens": estimated_tokens,
        "events": [
            {
                "id": event.id,
                "author": event.author,
                "invocation_id": event.invocation_id,
                "has_content": bool(event.content),
                "char_count": sum(
                    len(part.text or "")
                    for part in (event.content.parts or [])
                )
            }
            for event in session.events
        ]
    }

async def main():
    agent = Agent(
        name="context_tracking_agent",
        model="gemini-1.5-flash",
        instruction="You are a helpful assistant."
    )
    
    runner = InMemoryRunner(agent=agent)
    
    session = await runner.session_service.create_session(
        app_name="InMemoryRunner",
        user_id="user1",
        session_id="session1"
    )
    
    # Multiple turns
    messages = [
        "Hello!",
        "Tell me about Python.",
        "What are its key features?",
        "Give me an example.",
    ]
    
    for message in messages:
        async for event in runner.run_async(
            user_id="user1",
            session_id="session1",
            new_message=types.UserContent(parts=[types.Part(text=message)])
        ):
            if event.content and event.content.parts:
                for part in event.content.parts:
                    if part.text:
                        print(part.text, end="", flush=True)
        print("\n")
    
    # Calculate context length
    context_info = calculate_context_length(session)
    
    print(f"\n{'='*60}")
    print("Context Length Analysis")
    print('='*60)
    print(f"Total events:            {context_info['event_count']}")
    print(f"Events with content:     {context_info['events_with_content']}")
    print(f"Total characters:        {context_info['total_characters']:,}")
    print(f"Estimated tokens:        {context_info['estimated_tokens']:,}")
    print(f"\nEvent Breakdown:")
    for event_info in context_info['events']:
        print(f"  - {event_info['author']}: {event_info['char_count']} chars "
              f"(inv: {event_info['invocation_id'][:8]}...)")

if __name__ == "__main__":
    asyncio.run(main())
```

### Example 2: Track Context Length Over Time

```python
#!/usr/bin/env python3
"""Track context length growth over multiple turns."""

import asyncio
from google.adk import Agent
from google.adk.runners import InMemoryRunner
from google.genai import types

def get_context_size(session) -> int:
    """Get estimated context size in tokens."""
    text = "".join([
        part.text or ""
        for event in session.events
        if event.content
        for part in event.content.parts or []
    ])
    return len(text) // 4  # Rough estimate

async def main():
    agent = Agent(
        name="growth_tracking_agent",
        model="gemini-1.5-flash",
        instruction="You are a helpful assistant."
    )
    
    runner = InMemoryRunner(agent=agent)
    
    session = await runner.session_service.create_session(
        app_name="InMemoryRunner",
        user_id="user1",
        session_id="session1"
    )
    
    # Track context size after each turn
    context_sizes = []
    
    messages = [
        "Hi",
        "Tell me a story",
        "Continue the story",
        "What happened next?",
        "Keep going",
    ]
    
    for i, message in enumerate(messages, 1):
        # Get context size before this turn
        size_before = get_context_size(session)
        
        async for event in runner.run_async(
            user_id="user1",
            session_id="session1",
            new_message=types.UserContent(parts=[types.Part(text=message)])
        ):
            if event.content and event.content.parts:
                for part in event.content.parts:
                    if part.text:
                        print(part.text[:100], end="...\n" if len(part.text) > 100 else "\n")
        
        # Get context size after this turn
        # Need to reload session to get updated events
        session = await runner.session_service.get_session(
            app_name="InMemoryRunner",
            user_id="user1",
            session_id="session1"
        )
        size_after = get_context_size(session)
        
        context_sizes.append({
            "turn": i,
            "before": size_before,
            "after": size_after,
            "growth": size_after - size_before
        })
    
    # Print growth chart
    print(f"\n{'='*60}")
    print("Context Length Growth")
    print('='*60)
    print(f"{'Turn':<6} {'Before':<12} {'After':<12} {'Growth':<12}")
    print("-" * 60)
    for info in context_sizes:
        print(f"{info['turn']:<6} {info['before']:<12,} {info['after']:<12,} {info['growth']:<12,}")

if __name__ == "__main__":
    asyncio.run(main())
```

### Example 3: Get Actual Context Sent to Model

```python
#!/usr/bin/env python3
"""Get the actual context that would be sent to the model."""

import asyncio
from google.adk import Agent
from google.adk.runners import InMemoryRunner
from google.genai import types
from google.adk.flows.llm_flows.contents import _get_contents

async def main():
    agent = Agent(
        name="context_inspection_agent",
        model="gemini-1.5-flash",
        instruction="You are a helpful assistant."
    )
    
    runner = InMemoryRunner(agent=agent)
    
    session = await runner.session_service.create_session(
        app_name="InMemoryRunner",
        user_id="user1",
        session_id="session1"
    )
    
    # Build conversation
    messages = [
        "Hello!",
        "What is machine learning?",
        "Explain neural networks.",
    ]
    
    for message in messages:
        async for event in runner.run_async(
            user_id="user1",
            session_id="session1",
            new_message=types.UserContent(parts=[types.Part(text=message)])
        ):
            pass  # Just build conversation
    
    # Reload session to get all events
    session = await runner.session_service.get_session(
        app_name="InMemoryRunner",
        user_id="user1",
        session_id="session1"
    )
    
    # Get the actual contents that would be sent to model
    contents = _get_contents(
        branch=None,
        events=session.events,
        agent_name=agent.name
    )
    
    print(f"\n{'='*60}")
    print("Context Sent to Model")
    print('='*60)
    print(f"Number of Content objects: {len(contents)}\n")
    
    total_chars = 0
    for i, content in enumerate(contents, 1):
        text = "".join([
            part.text or ""
            for part in content.parts or []
        ])
        total_chars += len(text)
        print(f"Content {i} ({content.role}):")
        print(f"  Length: {len(text)} characters")
        print(f"  Preview: {text[:100]}...")
        print()
    
    estimated_tokens = total_chars // 4
    print(f"Total characters: {total_chars:,}")
    print(f"Estimated tokens: {estimated_tokens:,}")

if __name__ == "__main__":
    asyncio.run(main())
```

---

## Part 3: Model Context Limits

### Understanding Model Context Windows

Different models have different context window limits:

| Model | Context Window | Notes |
|-------|---------------|-------|
| `gemini-1.5-flash` | 1,000,000 tokens | Very large context |
| `gemini-1.5-pro` | 2,000,000 tokens | Largest context |
| `gemini-pro` | 32,768 tokens | Standard context |
| `gemini-1.0-pro` | 32,768 tokens | Standard context |

### Example: Check Context Against Model Limit

```python
#!/usr/bin/env python3
"""Check if context exceeds model limits."""

import asyncio
from google.adk import Agent
from google.adk.runners import InMemoryRunner
from google.genai import types

# Model context limits (in tokens)
MODEL_LIMITS = {
    "gemini-1.5-flash": 1_000_000,
    "gemini-1.5-pro": 2_000_000,
    "gemini-pro": 32_768,
    "gemini-1.0-pro": 32_768,
}

def estimate_tokens(text: str) -> int:
    """Rough token estimation."""
    return len(text) // 4

def get_model_limit(model_name: str) -> int:
    """Get context limit for a model."""
    # Extract base model name
    base_model = model_name.split("/")[-1] if "/" in model_name else model_name
    return MODEL_LIMITS.get(base_model, 32_768)  # Default to 32K

def check_context_usage(session, model_name: str) -> dict:
    """Check context usage against model limit."""
    # Get all text from events
    text = "".join([
        part.text or ""
        for event in session.events
        if event.content
        for part in event.content.parts or []
    ])
    
    estimated_tokens = estimate_tokens(text)
    model_limit = get_model_limit(model_name)
    usage_percent = (estimated_tokens / model_limit) * 100
    
    return {
        "estimated_tokens": estimated_tokens,
        "model_limit": model_limit,
        "usage_percent": usage_percent,
        "remaining_tokens": model_limit - estimated_tokens,
        "is_within_limit": estimated_tokens < model_limit,
        "warning_threshold": usage_percent > 80,
    }

async def main():
    model_name = "gemini-1.5-flash"
    agent = Agent(
        name="limit_check_agent",
        model=model_name,
        instruction="You are a helpful assistant."
    )
    
    runner = InMemoryRunner(agent=agent)
    
    session = await runner.session_service.create_session(
        app_name="InMemoryRunner",
        user_id="user1",
        session_id="session1"
    )
    
    # Build a long conversation
    for i in range(10):
        message = f"Tell me fact number {i+1} about artificial intelligence."
        async for event in runner.run_async(
            user_id="user1",
            session_id="session1",
            new_message=types.UserContent(parts=[types.Part(text=message)])
        ):
            pass
        
        # Reload session
        session = await runner.session_service.get_session(
            app_name="InMemoryRunner",
            user_id="user1",
            session_id="session1"
        )
        
        # Check usage
        usage = check_context_usage(session, model_name)
        
        print(f"\nTurn {i+1}:")
        print(f"  Estimated tokens: {usage['estimated_tokens']:,}")
        print(f"  Model limit:      {usage['model_limit']:,}")
        print(f"  Usage:            {usage['usage_percent']:.2f}%")
        print(f"  Remaining:        {usage['remaining_tokens']:,}")
        
        if usage['warning_threshold']:
            print(f"  ⚠️  WARNING: Approaching limit!")
        if not usage['is_within_limit']:
            print(f"  ❌ ERROR: Exceeded limit!")

if __name__ == "__main__":
    asyncio.run(main())
```

---

## Part 4: Context Compaction - Detailed Explanation

### What is Context Compaction?

**Context compaction** is ADK's mechanism to reduce the size of conversation history by summarizing older events while maintaining context. This helps manage long conversations that might exceed model context limits.

### How Compaction Works

ADK uses a **sliding window compaction** approach:

1. **Trigger**: Compaction is triggered after a certain number of new invocations (`compaction_interval`)
2. **Window Selection**: A sliding window of events is selected for compaction
3. **Overlap**: Previous compacted range is overlapped to maintain context continuity
4. **Summarization**: Selected events are summarized using an LLM
5. **Compacted Event**: A `CompactedEvent` is created and added to the session

### Compaction Configuration

```python
from google.adk import App, Agent
from google.adk.apps import EventsCompactionConfig

# Configure compaction
compaction_config = EventsCompactionConfig(
    compaction_interval=3,  # Compact after 3 new invocations
    overlap_size=1,          # Include 1 invocation from previous compaction
    summarizer=None          # Use default LLM summarizer
)

app = App(
    name="my_app",
    root_agent=agent,
    events_compaction_config=compaction_config
)
```

### Compaction Process Flow

```
Session Events: [E1, E2, E3, E4, E5, E6, E7, E8]
                 │
                 ├─ Invocations 1-3: No compaction
                 │
                 ├─ After Invocation 3: Compact [E1, E2, E3]
                 │  → Creates CompactedEvent(C1) summarizing E1-E3
                 │
                 ├─ Session: [E1, E2, E3, C1, E4, E5, E6]
                 │
                 ├─ After Invocation 6: Compact [E3, E4, E5, E6] (overlap E3)
                 │  → Creates CompactedEvent(C2) summarizing E3-E6
                 │
                 └─ Session: [E1, E2, E3, C1, E4, E5, E6, C2, E7, E8]
```

### Example 1: Basic Compaction Setup

```python
#!/usr/bin/env python3
"""Basic compaction example."""

import asyncio
from google.adk import App, Agent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.adk.apps import EventsCompactionConfig
from google.genai import types

async def main():
    # Create agent
    agent = Agent(
        name="compaction_agent",
        model="gemini-1.5-flash",
        instruction="You are a helpful assistant."
    )
    
    # Configure compaction
    compaction_config = EventsCompactionConfig(
        compaction_interval=2,  # Compact after 2 new invocations
        overlap_size=1           # Overlap 1 invocation
    )
    
    # Create app with compaction
    app = App(
        name="compaction_app",
        root_agent=agent,
        events_compaction_config=compaction_config
    )
    
    # Create runner
    runner = Runner(
        app=app,
        session_service=InMemorySessionService()
    )
    
    session = await runner.session_service.create_session(
        app_name="compaction_app",
        user_id="user1",
        session_id="session1"
    )
    
    # Multiple turns - compaction will trigger
    messages = [
        "Hello!",
        "Tell me about Python.",
        "What are its advantages?",
        "Give me an example.",
        "Explain more.",
    ]
    
    for i, message in enumerate(messages, 1):
        print(f"\n{'='*60}")
        print(f"Turn {i}: {message}")
        print('='*60)
        
        async for event in runner.run_async(
            user_id="user1",
            session_id="session1",
            new_message=types.UserContent(parts=[types.Part(text=message)])
        ):
            # Check if this is a compaction event
            if event.actions and event.actions.compaction:
                print(f"\n[COMPACTION EVENT]")
                print(f"  Start timestamp: {event.actions.compaction.start_timestamp}")
                print(f"  End timestamp: {event.actions.compaction.end_timestamp}")
                if event.actions.compaction.compacted_content:
                    print(f"  Summary: {event.actions.compacted_content.parts[0].text[:200]}...")
            elif event.content and event.content.parts:
                for part in event.content.parts:
                    if part.text:
                        print(part.text[:100], end="...\n" if len(part.text) > 100 else "\n")
        
        # Reload session to see compaction
        session = await runner.session_service.get_session(
            app_name="compaction_app",
            user_id="user1",
            session_id="session1"
        )
        
        # Count events
        regular_events = [e for e in session.events if not (e.actions and e.actions.compaction)]
        compaction_events = [e for e in session.events if e.actions and e.actions.compaction]
        
        print(f"\n[Session State]")
        print(f"  Regular events: {len(regular_events)}")
        print(f"  Compaction events: {len(compaction_events)}")
        print(f"  Total events: {len(session.events)}")

if __name__ == "__main__":
    asyncio.run(main())
```

### Example 2: Custom Summarizer

```python
#!/usr/bin/env python3
"""Custom compaction summarizer."""

import asyncio
from google.adk import App, Agent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.adk.apps import EventsCompactionConfig, LlmEventSummarizer
from google.genai import types

async def main():
    agent = Agent(
        name="custom_compaction_agent",
        model="gemini-1.5-flash",
        instruction="You are a helpful assistant."
    )
    
    # Custom prompt template
    custom_template = (
        "Summarize the following conversation history. "
        "Focus on key decisions, important facts, and user preferences. "
        "Be concise but comprehensive.\n\n"
        "{conversation_history}"
    )
    
    # Create custom summarizer
    custom_summarizer = LlmEventSummarizer(
        llm=agent.canonical_model,
        prompt_template=custom_template
    )
    
    # Configure compaction with custom summarizer
    compaction_config = EventsCompactionConfig(
        compaction_interval=3,
        overlap_size=1,
        summarizer=custom_summarizer
    )
    
    app = App(
        name="custom_compaction_app",
        root_agent=agent,
        events_compaction_config=compaction_config
    )
    
    runner = Runner(
        app=app,
        session_service=InMemorySessionService()
    )
    
    session = await runner.session_service.create_session(
        app_name="custom_compaction_app",
        user_id="user1",
        session_id="session1"
    )
    
    # Build conversation
    messages = [
        "I love Python programming.",
        "I work as a data scientist.",
        "I prefer using pandas for data analysis.",
        "Tell me about machine learning.",
    ]
    
    for message in messages:
        async for event in runner.run_async(
            user_id="user1",
            session_id="session1",
            new_message=types.UserContent(parts=[types.Part(text=message)])
        ):
            if event.actions and event.actions.compaction:
                print("\n[Compaction Summary]")
                if event.actions.compaction.compacted_content:
                    summary = event.actions.compaction.compacted_content.parts[0].text
                    print(summary)

if __name__ == "__main__":
    asyncio.run(main())
```

### Example 3: Monitor Compaction Impact

```python
#!/usr/bin/env python3
"""Monitor how compaction affects context size."""

import asyncio
from google.adk import App, Agent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.adk.apps import EventsCompactionConfig
from google.genai import types

def get_context_size(session) -> int:
    """Get estimated context size."""
    text = "".join([
        part.text or ""
        for event in session.events
        if event.content
        for part in event.content.parts or []
    ])
    return len(text) // 4

async def main():
    agent = Agent(
        name="monitor_agent",
        model="gemini-1.5-flash",
        instruction="You are a helpful assistant."
    )
    
    # Enable compaction
    compaction_config = EventsCompactionConfig(
        compaction_interval=2,
        overlap_size=1
    )
    
    app = App(
        name="monitor_app",
        root_agent=agent,
        events_compaction_config=compaction_config
    )
    
    runner = Runner(
        app=app,
        session_service=InMemorySessionService()
    )
    
    session = await runner.session_service.create_session(
        app_name="monitor_app",
        user_id="user1",
        session_id="session1"
    )
    
    messages = [f"Message {i+1}" for i in range(10)]
    
    print(f"{'Turn':<6} {'Events':<8} {'Compactions':<12} {'Context Size':<15} {'Reduction':<12}")
    print("-" * 60)
    
    for i, message in enumerate(messages, 1):
        size_before = get_context_size(session)
        
        async for event in runner.run_async(
            user_id="user1",
            session_id="session1",
            new_message=types.UserContent(parts=[types.Part(text=message)])
        ):
            pass
        
        # Reload session
        session = await runner.session_service.get_session(
            app_name="monitor_app",
            user_id="user1",
            session_id="session1"
        )
        
        size_after = get_context_size(session)
        compaction_count = sum(
            1 for e in session.events
            if e.actions and e.actions.compaction
        )
        regular_events = sum(
            1 for e in session.events
            if not (e.actions and e.actions.compaction)
        )
        
        reduction = size_before - size_after if size_after < size_before else 0
        
        print(f"{i:<6} {regular_events:<8} {compaction_count:<12} {size_after:<15,} {reduction:<12,}")

if __name__ == "__main__":
    asyncio.run(main())
```

### Compaction Parameters Explained

#### `compaction_interval`

- **Type**: `int`
- **Default**: None (compaction disabled)
- **Meaning**: Number of **new** user-initiated invocations that trigger compaction
- **Example**: `compaction_interval=3` means compact after every 3 new invocations

#### `overlap_size`

- **Type**: `int`
- **Default**: 0
- **Meaning**: Number of invocations from the previous compaction range to include in the new compaction
- **Purpose**: Maintains context continuity between compacted ranges
- **Example**: `overlap_size=1` includes 1 invocation from the previous range

#### `summarizer`

- **Type**: `BaseEventsSummarizer` (optional)
- **Default**: `LlmEventSummarizer` (created automatically if None)
- **Meaning**: The summarizer used to create compacted summaries
- **Customization**: Can provide custom prompt templates or different summarization strategies

### How Compaction Events Work

When compaction occurs, a `CompactedEvent` is created:

```python
CompactedEvent:
  - start_timestamp: float    # Timestamp of first event in range
  - end_timestamp: float      # Timestamp of last event in range
  - compacted_content: Content # LLM-generated summary
```

The compacted event is added to the session, but the original events remain. During context building:
- Original events may be hidden from context (depending on implementation)
- Compacted events provide summarized context
- Overlap ensures continuity

### Best Practices for Compaction

1. **Choose Appropriate Interval**: 
   - Too frequent: Wastes tokens on summarization
   - Too infrequent: May exceed context limits
   - **Recommendation**: Start with 3-5 invocations

2. **Use Overlap**:
   - Overlap maintains context continuity
   - **Recommendation**: Use `overlap_size=1` or `overlap_size=2`

3. **Monitor Context Size**:
   - Track context size before/after compaction
   - Adjust parameters based on your use case

4. **Custom Summarizers**:
   - Use custom prompts for domain-specific summarization
   - Focus on preserving important information

---

## Summary

### Token Usage
- ✅ Available via `event.usage_metadata`
- ✅ Contains `prompt_token_count`, `candidates_token_count`, `total_token_count`
- ✅ Track across multiple turns using callbacks or manual tracking

### Context Length
- ✅ Calculate from `session.events`
- ✅ Estimate tokens from text length
- ✅ Track growth over time
- ✅ Inspect actual context sent to model

### Model Limits
- ✅ Check against model-specific limits
- ✅ Monitor usage percentage
- ✅ Set warning thresholds

### Compaction
- ✅ Sliding window approach
- ✅ Configurable interval and overlap
- ✅ Custom summarizers supported
- ✅ Reduces context size while maintaining continuity

---

## Related Documentation

- [Runners Package](10-Runners-Package.md) - Event processing and compaction
- [Sessions Package](07-Sessions-Package.md) - Session management
- [Apps Package](05-Apps-Package.md) - App configuration including compaction
- [ADK Memory and Session Runtime Trace](ADK-Memory-and-Session-Runtime-Trace.md) - Implementation details
