# Python A2A Advanced Features

**File Path**: `A2A/docs/05-Advanced-Features.md`

## Overview

This guide covers advanced features of Python A2A, including MCP integration, LangChain integration, agent discovery, and more.

## MCP (Model Context Protocol) Integration

Python A2A includes built-in support for the Model Context Protocol (MCP).

### FastMCP Integration

```python
from python_a2a import FastMCP, create_fastapi_app
from python_a2a.mcp import MCPResponse

# Create FastMCP server
mcp = FastMCP("my_agent")

@mcp.tool()
def calculate(a: float, b: float, operation: str) -> float:
    """Perform a calculation."""
    if operation == "add":
        return a + b
    elif operation == "subtract":
        return a - b
    # ... more operations
    return 0

# Create FastAPI app
app = create_fastapi_app(mcp)
```

### MCP Client

```python
from python_a2a import MCPClient

# Connect to MCP server
client = MCPClient(
    server_url="http://localhost:8000"
)

# Call tools
result = await client.call_tool("calculate", {"a": 5, "b": 3, "operation": "add"})
```

## LangChain Integration

Convert between LangChain and A2A components:

### Convert LangChain Agent to A2A Server

```python
from python_a2a import to_a2a_server
from langchain.agents import create_openai_functions_agent

# Create LangChain agent
langchain_agent = create_openai_functions_agent(...)

# Convert to A2A server
a2a_server = to_a2a_server(langchain_agent)
```

### Convert A2A Server to LangChain Agent

```python
from python_a2a import to_langchain_agent, A2AServer

# Create A2A server
a2a_server = A2AServer(...)

# Convert to LangChain agent
langchain_agent = to_langchain_agent(a2a_server)
```

### Convert LangChain Tools

```python
from python_a2a import to_langchain_tool
from python_a2a import A2AServer

a2a_server = A2AServer(...)
langchain_tool = to_langchain_tool(a2a_server)
```

## Agent Discovery

Discover agents on a network:

### Discovery Client

```python
from python_a2a import DiscoveryClient

# Create discovery client
discovery = DiscoveryClient(
    registry_url="http://localhost:8080"
)

# Discover agents
agents = await discovery.discover_agents()

# Find agents by skill
math_agents = await discovery.find_agents_by_skill("mathematics")
```

### Agent Registry

Run an agent registry server:

```python
from python_a2a import AgentRegistry, run_registry

# Create registry
registry = AgentRegistry()

# Register agents
registry.register_agent(
    name="math_agent",
    endpoint="http://localhost:8000",
    skills=["mathematics"]
)

# Run registry server
run_registry(registry, host="0.0.0.0", port=8080)
```

## Agent Network

Create a network of agents:

```python
from python_a2a import AgentNetwork, A2AClient

# Create network
network = AgentNetwork()

# Add agents
network.add_agent("math", A2AClient(endpoint_url="http://localhost:8000"))
network.add_agent("code", A2AClient(endpoint_url="http://localhost:8001"))

# Route message to best agent
response = await network.route_message(
    message=Message(...),
    skill="mathematics"
)
```

## Streaming

### Server-Side Streaming

```python
from python_a2a import A2AServer
from typing import AsyncGenerator

async def stream_handler(message: Message) -> AsyncGenerator[str, None]:
    """Stream response tokens."""
    response = "Processing your request..."
    for token in response.split():
        yield token + " "
        await asyncio.sleep(0.1)

server = A2AServer(
    agent_card={...},
    stream_handler=stream_handler
)
```

### Client-Side Streaming

```python
from python_a2a import StreamingClient

client = StreamingClient(endpoint_url="http://localhost:8000")

async for chunk in client.stream_message(message):
    print(chunk, end="", flush=True)
```

## Custom Content Types

Create custom content types:

```python
from python_a2a import Message, ContentType

class ImageContent:
    def __init__(self, image_url: str):
        self.image_url = image_url
        self.type = ContentType.IMAGE

message = Message(
    role=MessageRole.USER,
    content=[
        TextContent(text="What's in this image?"),
        ImageContent(image_url="https://example.com/image.jpg")
    ]
)
```

## Error Handling

### Custom Error Responses

```python
from python_a2a import Message, ErrorContent, MessageRole

def handle_message(message: Message) -> Message:
    try:
        # Process message
        ...
    except ValueError as e:
        return Message(
            role=MessageRole.AGENT,
            content=[
                ErrorContent(
                    error=str(e),
                    code="VALIDATION_ERROR",
                    details={"field": "input"}
                )
            ]
        )
```

## Metadata

Add metadata to messages:

```python
from python_a2a import Message, Metadata

message = Message(
    role=MessageRole.USER,
    content=[TextContent(text="Hello")],
    metadata=Metadata(
        user_id="123",
        session_id="abc",
        timestamp="2024-01-01T00:00:00Z"
    )
)
```

## Task Management

Handle long-running tasks:

```python
from python_a2a import Task, TaskStatus

# Create task
task = Task(
    name="process_data",
    status=TaskStatus.PENDING
)

# Update task
task.status = TaskStatus.RUNNING
task.progress = 50

# Complete task
task.status = TaskStatus.COMPLETED
task.result = {"processed": 1000}
```

## Next Steps

- Review [Core Concepts](01-Core-Concepts.md)
- Check out [Examples](../examples/)
- Read the [Index](INDEX.md) for all documentation
