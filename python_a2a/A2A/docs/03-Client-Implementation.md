# Python A2A Client Implementation Guide

**File Path**: `A2A/docs/03-Client-Implementation.md`

## Overview

This guide covers how to create A2A clients to communicate with A2A servers. A client connects to servers, sends messages, and receives responses.

## Basic A2A Client

The simplest way to create an A2A client:

```python
from python_a2a import A2AClient, Message, TextContent, MessageRole
import asyncio

async def main():
    # Create client
    client = A2AClient(
        endpoint_url="http://localhost:8000"
    )
    
    # Create a message
    message = Message(
        role=MessageRole.USER,
        content=[TextContent(text="Hello!")]
    )
    
    # Send message and get response
    response = await client.send_message(message)
    
    # Process response
    for content in response.content:
        if isinstance(content, TextContent):
            print(content.text)

asyncio.run(main())
```

## Client Configuration

Configure client with custom headers and timeout:

```python
client = A2AClient(
    endpoint_url="http://localhost:8000",
    headers={
        "Authorization": "Bearer your-token",
        "X-Custom-Header": "value"
    },
    timeout=60  # 60 seconds
)
```

## Agent Card Discovery

Discover agent capabilities using Agent Card:

```python
from python_a2a import A2AClient

client = A2AClient(endpoint_url="http://localhost:8000")

# Get agent card
agent_card = await client.get_agent_card()
print(f"Agent: {agent_card.name}")
print(f"Description: {agent_card.description}")
print(f"Skills: {agent_card.skills}")
```

## Sending Messages

### Simple Text Message

```python
from python_a2a import A2AClient, Message, TextContent, MessageRole

client = A2AClient(endpoint_url="http://localhost:8000")

message = Message(
    role=MessageRole.USER,
    content=[TextContent(text="What is 2 + 2?")]
)

response = await client.send_message(message)
```

### Multiple Content Types

```python
from python_a2a import (
    A2AClient, Message, TextContent, MessageRole,
    FunctionCallContent
)

client = A2AClient(endpoint_url="http://localhost:8000")

message = Message(
    role=MessageRole.USER,
    content=[
        TextContent(text="Calculate 5 + 3"),
        FunctionCallContent(
            name="calculate",
            parameters={"a": 5, "b": 3, "operation": "add"}
        )
    ]
)

response = await client.send_message(message)
```

## Streaming Responses

Receive streaming responses:

```python
from python_a2a import A2AClient, Message, TextContent, MessageRole

client = A2AClient(endpoint_url="http://localhost:8000")

message = Message(
    role=MessageRole.USER,
    content=[TextContent(text="Tell me a story")]
)

print("Response: ", end="", flush=True)
async for chunk in client.stream_message(message):
    print(chunk, end="", flush=True)
print()  # New line at end
```

## Handling Conversations

Send messages in a conversation context:

```python
from python_a2a import A2AClient, Conversation, Message, TextContent, MessageRole

client = A2AClient(endpoint_url="http://localhost:8000")

# Create conversation
conversation = Conversation(
    messages=[
        Message(
            role=MessageRole.USER,
            content=[TextContent(text="Hello")]
        ),
        Message(
            role=MessageRole.AGENT,
            content=[TextContent(text="Hi! How can I help?")]
        )
    ]
)

# Add new message
conversation.messages.append(
    Message(
        role=MessageRole.USER,
        content=[TextContent(text="What's the weather?")]
    )
)

# Send conversation
response = await client.send_conversation(conversation)
```

## Function Calling

Call functions on the server:

```python
from python_a2a import (
    A2AClient, Message, TextContent, MessageRole,
    FunctionCallContent, FunctionResponseContent
)

client = A2AClient(endpoint_url="http://localhost:8000")

# Create function call message
message = Message(
    role=MessageRole.USER,
    content=[
        FunctionCallContent(
            name="calculate",
            parameters={
                "a": 10,
                "b": 5,
                "operation": "multiply"
            }
        )
    ]
)

response = await client.send_message(message)

# Process function response
for content in response.content:
    if isinstance(content, FunctionResponseContent):
        print(f"Result: {content.response}")
```

## Error Handling

Handle errors gracefully:

```python
from python_a2a import A2AClient, A2AConnectionError, A2ARequestError
from python_a2a import Message, TextContent, MessageRole

client = A2AClient(endpoint_url="http://localhost:8000")

try:
    message = Message(
        role=MessageRole.USER,
        content=[TextContent(text="Hello")]
    )
    response = await client.send_message(message)
except A2AConnectionError as e:
    print(f"Connection error: {e}")
except A2ARequestError as e:
    print(f"Request error: {e}")
except Exception as e:
    print(f"Unexpected error: {e}")
```

## LLM-Powered Clients

### OpenAI Client

```python
from python_a2a import OpenAIA2AClient
import os

client = OpenAIA2AClient(
    api_key=os.getenv("OPENAI_API_KEY"),
    model="gpt-4"
)

message = Message(
    role=MessageRole.USER,
    content=[TextContent(text="Hello!")]
)

response = await client.send_message(message)
```

### Anthropic Client

```python
from python_a2a import AnthropicA2AClient
import os

client = AnthropicA2AClient(
    api_key=os.getenv("ANTHROPIC_API_KEY"),
    model="claude-3-opus-20240229"
)

message = Message(
    role=MessageRole.USER,
    content=[TextContent(text="Hello!")]
)

response = await client.send_message(message)
```

## Complete Example

See `A2A/examples/simple_client.py` for a complete working example.

## Next Steps

- Learn about [Server Implementation](02-Server-Implementation.md)
- Explore [Workflows](04-Workflows.md)
- Check out [Advanced Features](05-Advanced-Features.md)
