# Python A2A Server Implementation Guide

**File Path**: `A2A/docs/02-Server-Implementation.md`

## Overview

This guide covers how to create and deploy A2A servers using Python A2A. An A2A server is an agent that can receive and process A2A protocol messages.

## Basic A2A Server

The simplest way to create an A2A server:

```python
from python_a2a import A2AServer, Message, TextContent, MessageRole

def handle_message(message: Message) -> Message:
    """Handle incoming messages."""
    user_text = ""
    for content in message.content:
        if isinstance(content, TextContent):
            user_text += content.text
    
    # Simple echo response
    response_text = f"You said: {user_text}"
    
    return Message(
        role=MessageRole.AGENT,
        content=[TextContent(text=response_text)]
    )

# Create server
server = A2AServer(
    agent_card={
        "name": "echo_agent",
        "description": "An agent that echoes your messages",
        "version": "1.0.0"
    },
    message_handler=handle_message
)
```

## Running a Server with FastAPI

To run an A2A server as a web service, use FastAPI:

```python
from python_a2a import A2AServer, create_fastapi_app
from python_a2a import Message, TextContent, MessageRole
import uvicorn

def handle_message(message: Message) -> Message:
    """Handle incoming messages."""
    user_text = ""
    for content in message.content:
        if isinstance(content, TextContent):
            user_text += content.text
    
    response_text = f"Echo: {user_text}"
    
    return Message(
        role=MessageRole.AGENT,
        content=[TextContent(text=response_text)]
    )

# Create server
server = A2AServer(
    agent_card={
        "name": "echo_server",
        "description": "Echo server agent",
        "version": "1.0.0"
    },
    message_handler=handle_message
)

# Create FastAPI app
app = create_fastapi_app(server)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

## Server with Agent Card

Define a detailed agent card:

```python
from python_a2a import A2AServer, AgentCard, AgentSkill

agent_card = AgentCard(
    name="math_agent",
    description="An agent specialized in mathematical problem solving",
    version="1.0.0",
    endpoint="http://localhost:8000",
    skills=[
        AgentSkill(
            name="arithmetic",
            description="Performs basic arithmetic operations"
        ),
        AgentSkill(
            name="algebra",
            description="Solves algebraic equations"
        )
    ]
)

server = A2AServer(
    agent_card=agent_card,
    message_handler=handle_message
)
```

## Handling Conversations

Handle full conversations instead of single messages:

```python
from python_a2a import A2AServer, Conversation, Message, TextContent, MessageRole

def handle_conversation(conversation: Conversation) -> Message:
    """Handle a conversation."""
    # Get the last user message
    last_message = conversation.messages[-1]
    user_text = ""
    
    for content in last_message.content:
        if isinstance(content, TextContent):
            user_text += content.text
    
    # Use conversation history for context
    context = f"Previous messages: {len(conversation.messages)}"
    response_text = f"{context}\nYou said: {user_text}"
    
    return Message(
        role=MessageRole.AGENT,
        content=[TextContent(text=response_text)]
    )

server = A2AServer(
    agent_card={"name": "conversation_agent"},
    conversation_handler=handle_conversation
)
```

## Server with Function Calling

Handle function calls from clients:

```python
from python_a2a import (
    A2AServer, Message, TextContent, MessageRole,
    FunctionCallContent, FunctionResponseContent
)

def calculate(a: float, b: float, operation: str) -> float:
    """Perform a calculation."""
    if operation == "add":
        return a + b
    elif operation == "subtract":
        return a - b
    elif operation == "multiply":
        return a * b
    elif operation == "divide":
        return a / b if b != 0 else 0
    return 0

def handle_message(message: Message) -> Message:
    """Handle messages, including function calls."""
    responses = []
    
    for content in message.content:
        if isinstance(content, FunctionCallContent):
            # Handle function call
            params = content.parameters
            result = calculate(
                params.get("a", 0),
                params.get("b", 0),
                params.get("operation", "add")
            )
            
            responses.append(
                FunctionResponseContent(
                    name=content.name,
                    response={"result": result}
                )
            )
        elif isinstance(content, TextContent):
            # Handle text
            responses.append(
                TextContent(text=f"Received: {content.text}")
            )
    
    return Message(
        role=MessageRole.AGENT,
        content=responses
    )

server = A2AServer(
    agent_card={
        "name": "calculator_agent",
        "description": "An agent that performs calculations"
    },
    message_handler=handle_message
)
```

## Streaming Responses

Support streaming responses:

```python
from python_a2a import A2AServer, Message, TextContent, MessageRole
from typing import AsyncGenerator

async def stream_response(message: Message) -> AsyncGenerator[str, None]:
    """Stream response tokens."""
    user_text = ""
    for content in message.content:
        if isinstance(content, TextContent):
            user_text += content.text
    
    response = f"Processing: {user_text}"
    for char in response:
        yield char
        await asyncio.sleep(0.1)  # Simulate processing

server = A2AServer(
    agent_card={"name": "streaming_agent"},
    message_handler=handle_message,
    stream_handler=stream_response
)
```

## LLM-Powered Servers

### OpenAI Server

```python
from python_a2a import OpenAIA2AServer
import os

server = OpenAIA2AServer(
    agent_card={
        "name": "openai_agent",
        "description": "Agent powered by OpenAI"
    },
    api_key=os.getenv("OPENAI_API_KEY"),
    model="gpt-4"
)
```

### Anthropic Server

```python
from python_a2a import AnthropicA2AServer
import os

server = AnthropicA2AServer(
    agent_card={
        "name": "claude_agent",
        "description": "Agent powered by Anthropic Claude"
    },
    api_key=os.getenv("ANTHROPIC_API_KEY"),
    model="claude-3-opus-20240229"
)
```

## Google A2A Compatibility

Enable Google A2A format compatibility:

```python
server = A2AServer(
    agent_card={...},
    google_a2a_compatible=True  # Enable Google A2A format
)
```

## Server Metadata

Add custom metadata to your server:

```python
def get_metadata():
    """Return server metadata."""
    return {
        "version": "1.0.0",
        "uptime": "2 hours",
        "requests_processed": 150
    }

server = A2AServer(
    agent_card={...},
    message_handler=handle_message,
    metadata_handler=get_metadata
)
```

## Error Handling

Handle errors gracefully:

```python
from python_a2a import A2AServer, Message, ErrorContent, MessageRole

def handle_message(message: Message) -> Message:
    """Handle messages with error handling."""
    try:
        # Process message
        user_text = ""
        for content in message.content:
            if isinstance(content, TextContent):
                user_text += content.text
        
        if not user_text:
            raise ValueError("Empty message")
        
        return Message(
            role=MessageRole.AGENT,
            content=[TextContent(text=f"Processed: {user_text}")]
        )
    except Exception as e:
        return Message(
            role=MessageRole.AGENT,
            content=[
                ErrorContent(
                    error=str(e),
                    code="PROCESSING_ERROR"
                )
            ]
        )
```

## Complete Example

See `A2A/examples/simple_server.py` for a complete working example.

## Next Steps

- Learn about [Client Implementation](03-Client-Implementation.md)
- Explore [Workflows](04-Workflows.md)
- Check out [Advanced Features](05-Advanced-Features.md)
