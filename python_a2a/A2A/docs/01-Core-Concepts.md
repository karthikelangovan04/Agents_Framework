# Python A2A Core Concepts

**File Path**: `A2A/docs/01-Core-Concepts.md`

## Overview

The Agent-to-Agent (A2A) protocol is an open standard that enables AI agents to communicate and collaborate across different systems, frameworks, and vendors. This document covers the core concepts you need to understand to work with Python A2A.

## Key Concepts

### 1. Agent Card

An **Agent Card** is a JSON document that describes an agent's capabilities, endpoints, and metadata. It serves as a "business card" for agents, allowing them to discover and interact with each other.

```python
from python_a2a import AgentCard

agent_card = AgentCard(
    name="math_agent",
    description="An agent specialized in mathematical problem solving",
    version="1.0.0",
    endpoint="http://localhost:8000",
    skills=["mathematics", "problem_solving"]
)
```

### 2. Message

A **Message** is the fundamental unit of communication in A2A. Messages contain:
- **Role**: The sender's role (user, agent, system)
- **Content**: The actual message content (text, function calls, etc.)
- **Metadata**: Additional information about the message

```python
from python_a2a import Message, TextContent, MessageRole

message = Message(
    role=MessageRole.USER,
    content=[
        TextContent(text="What is 2 + 2?")
    ]
)
```

### 3. Conversation

A **Conversation** is a sequence of messages that form a dialogue between agents or between a user and an agent.

```python
from python_a2a import Conversation, Message, TextContent, MessageRole

conversation = Conversation(
    messages=[
        Message(
            role=MessageRole.USER,
            content=[TextContent(text="Hello!")]
        ),
        Message(
            role=MessageRole.AGENT,
            content=[TextContent(text="Hi! How can I help you?")]
        )
    ]
)
```

### 4. A2A Server

An **A2A Server** is an agent that can receive and process A2A messages. It implements the server-side of the A2A protocol.

```python
from python_a2a import A2AServer

server = A2AServer(
    agent_card={
        "name": "my_agent",
        "description": "My A2A agent"
    },
    message_handler=lambda message: handle_message(message)
)
```

### 5. A2A Client

An **A2A Client** is used to communicate with A2A servers. It handles the client-side of the A2A protocol.

```python
from python_a2a import A2AClient

client = A2AClient(
    endpoint_url="http://localhost:8000"
)
```

## Content Types

A2A supports multiple content types:

### Text Content
```python
from python_a2a import TextContent

text_content = TextContent(text="Hello, world!")
```

### Function Call Content
```python
from python_a2a import FunctionCallContent, FunctionParameter

function_call = FunctionCallContent(
    name="calculate",
    parameters={
        "a": 5,
        "b": 3,
        "operation": "add"
    }
)
```

### Function Response Content
```python
from python_a2a import FunctionResponseContent

function_response = FunctionResponseContent(
    name="calculate",
    response={"result": 8}
)
```

### Error Content
```python
from python_a2a import ErrorContent

error_content = ErrorContent(
    error="Invalid input",
    code="INVALID_INPUT"
)
```

## Message Roles

Messages can have different roles:

- **USER**: Messages from users
- **AGENT**: Messages from agents
- **SYSTEM**: System messages

```python
from python_a2a import MessageRole

# User message
user_msg = Message(role=MessageRole.USER, content=[...])

# Agent message
agent_msg = Message(role=MessageRole.AGENT, content=[...])

# System message
system_msg = Message(role=MessageRole.SYSTEM, content=[...])
```

## Agent Skills

**Agent Skills** describe what an agent can do. They help with agent discovery and routing.

```python
from python_a2a import AgentSkill

skill = AgentSkill(
    name="mathematics",
    description="Can solve mathematical problems",
    parameters={
        "difficulty": "easy|medium|hard"
    }
)
```

## Protocol Flow

The typical A2A interaction flow:

1. **Discovery**: Client discovers available agents (via Agent Cards)
2. **Connection**: Client connects to an agent server
3. **Message Exchange**: Client sends messages, server responds
4. **Function Calls**: Agents can call functions/tools
5. **Streaming**: Support for streaming responses

## Google A2A Compatibility

Python A2A supports Google's A2A format for compatibility:

```python
server = A2AServer(
    agent_card={...},
    google_a2a_compatible=True  # Enable Google A2A format
)
```

## Next Steps

- Learn how to [build A2A servers](02-Server-Implementation.md)
- Learn how to [create A2A clients](03-Client-Implementation.md)
- Explore [workflow orchestration](04-Workflows.md)
- Check out [real-world examples](../examples/)
