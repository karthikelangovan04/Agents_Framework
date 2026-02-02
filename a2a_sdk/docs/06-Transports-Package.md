# A2A-SDK Transports Package Documentation

**File Path**: `docs-a2a-sdk/06-Transports-Package.md`  
**Package**: `a2a.client.transports`

## Overview

The `a2a.client.transports` package provides transport layer implementations for different protocols. A2A SDK supports multiple transport protocols, allowing you to choose the best one for your use case.

## Transport Abstraction

All transports implement the `ClientTransport` base class, providing a unified interface:

```python
from a2a.client.transports.base import ClientTransport

# All transports inherit from ClientTransport
class ClientTransport:
    async def send_request(self, ...):
        """Send request via transport."""
        pass
```

## Supported Transports

### 1. REST Transport

**Location**: `a2a.client.transports.rest`

**Protocol**: HTTP REST API

**Usage**:
```python
from a2a.client.transports.rest import RestTransport
from a2a.client import Client, ClientConfig

transport = RestTransport(
    base_url="http://localhost:8000",
    timeout=30.0
)

config = ClientConfig(transport=transport)
client = Client(config)
```

**Key Features**:
- Standard HTTP REST API
- JSON request/response
- Configurable timeout
- Retry support

**Configuration**:
```python
RestTransport(
    base_url="http://localhost:8000",  # Base URL
    timeout=30.0,                      # Request timeout
    headers={"Custom-Header": "value"}  # Custom headers
)
```

### 2. JSON-RPC Transport

**Location**: `a2a.client.transports.jsonrpc`

**Protocol**: JSON-RPC 2.0

**Usage**:
```python
from a2a.client.transports.jsonrpc import JsonRpcTransport
from a2a.client import Client, ClientConfig

transport = JsonRpcTransport(
    base_url="http://localhost:8000"
)

config = ClientConfig(transport=transport)
client = Client(config)
```

**Key Features**:
- JSON-RPC 2.0 protocol
- Method-based calls
- Batch request support
- Error handling

**Configuration**:
```python
JsonRpcTransport(
    base_url="http://localhost:8000",  # Base URL
    timeout=30.0                       # Request timeout
)
```

### 3. gRPC Transport (Optional)

**Location**: `a2a.client.transports.grpc`

**Protocol**: gRPC

**Requires**: `pip install "a2a-sdk[grpc]"`

**Usage**:
```python
from a2a.client.transports.grpc import GrpcTransport
from a2a.client import Client, ClientConfig

transport = GrpcTransport(
    endpoint="localhost:50051"
)

config = ClientConfig(transport=transport)
client = Client(config)
```

**Key Features**:
- High-performance gRPC
- Streaming support
- Binary protocol
- Type-safe

**Configuration**:
```python
GrpcTransport(
    endpoint="localhost:50051",  # gRPC endpoint
    timeout=30.0                 # Request timeout
)
```

## Example 1: REST Transport

```python
#!/usr/bin/env python3
"""REST transport example."""

import asyncio
from a2a.client import Client, ClientConfig
from a2a.client.transports.rest import RestTransport
from a2a.types import Message

async def main():
    # Create REST transport
    transport = RestTransport(
        base_url="http://localhost:8000",
        timeout=30.0
    )
    
    # Create client
    config = ClientConfig(transport=transport)
    client = Client(config)
    
    # Send message via REST
    message = Message(role="user", content=[{"text": "Hello"}])
    async for event in client.send_message(message):
        print(event)

if __name__ == "__main__":
    asyncio.run(main())
```

## Example 2: JSON-RPC Transport

```python
#!/usr/bin/env python3
"""JSON-RPC transport example."""

import asyncio
from a2a.client import Client, ClientConfig
from a2a.client.transports.jsonrpc import JsonRpcTransport
from a2a.types import Message

async def main():
    # Create JSON-RPC transport
    transport = JsonRpcTransport(
        base_url="http://localhost:8000"
    )
    
    # Create client
    config = ClientConfig(transport=transport)
    client = Client(config)
    
    # Send message via JSON-RPC
    message = Message(role="user", content=[{"text": "Hello"}])
    async for event in client.send_message(message):
        print(event)

if __name__ == "__main__":
    asyncio.run(main())
```

## Example 3: Switching Transports

```python
#!/usr/bin/env python3
"""Switching between transports."""

import asyncio
from a2a.client import Client, ClientConfig
from a2a.client.transports.rest import RestTransport
from a2a.client.transports.jsonrpc import JsonRpcTransport
from a2a.types import Message

async def main():
    # Option 1: REST transport
    rest_transport = RestTransport(base_url="http://localhost:8000")
    rest_client = Client(ClientConfig(transport=rest_transport))
    
    # Option 2: JSON-RPC transport (same client interface)
    jsonrpc_transport = JsonRpcTransport(base_url="http://localhost:8000")
    jsonrpc_client = Client(ClientConfig(transport=jsonrpc_transport))
    
    # Both clients have the same interface
    message = Message(role="user", content=[{"text": "Hello"}])
    
    # Use REST client
    async for event in rest_client.send_message(message):
        print(f"REST: {event}")
    
    # Use JSON-RPC client
    async for event in jsonrpc_client.send_message(message):
        print(f"JSON-RPC: {event}")

if __name__ == "__main__":
    asyncio.run(main())
```

## Transport Selection Guide

### When to Use REST

- ✅ Standard HTTP APIs
- ✅ Simple request/response
- ✅ Wide compatibility
- ✅ Easy debugging

### When to Use JSON-RPC

- ✅ Method-based calls
- ✅ Batch requests
- ✅ Structured protocol
- ✅ Error handling

### When to Use gRPC

- ✅ High performance
- ✅ Streaming
- ✅ Type safety
- ✅ Binary protocol

## Custom Transport

Create custom transports by extending `ClientTransport`:

```python
from a2a.client.transports.base import ClientTransport

class CustomTransport(ClientTransport):
    async def send_request(self, method, params, **kwargs):
        """Implement custom transport logic."""
        # Custom implementation
        pass
```

## Best Practices

1. **Choose Appropriate Transport**
   ```python
   # ✅ GOOD: Use REST for simple APIs
   transport = RestTransport(base_url="http://api.example.com")
   
   # ✅ GOOD: Use JSON-RPC for method-based calls
   transport = JsonRpcTransport(base_url="http://api.example.com")
   
   # ✅ GOOD: Use gRPC for high performance
   transport = GrpcTransport(endpoint="api.example.com:50051")
   ```

2. **Configure Timeouts**
   ```python
   # ✅ GOOD: Set appropriate timeout
   transport = RestTransport(
       base_url="http://localhost:8000",
       timeout=30.0  # 30 seconds
   )
   ```

3. **Handle Transport Errors**
   ```python
   from a2a.client.errors import A2AClientHTTPError
   
   try:
       async for event in client.send_message(message):
           # Process events
           pass
   except A2AClientHTTPError as e:
       # Handle HTTP errors
       print(f"HTTP error: {e.status_code}")
   ```

## Comparison with ADK

| Feature | ADK | A2A SDK Transports |
|--------|-----|-------------------|
| **Transport** | Built-in HTTP | Multiple (REST/JSON-RPC/gRPC) |
| **Abstraction** | None | `ClientTransport` base class |
| **Protocol Selection** | Fixed | Configurable |
| **Custom Transport** | Not supported | Supported (extend base) |

## Troubleshooting

### Issue: Connection refused

**Solution**: Check that server is running and URL is correct:
```python
transport = RestTransport(
    base_url="http://localhost:8000"  # Verify URL
)
```

### Issue: Timeout errors

**Solution**: Increase timeout:
```python
transport = RestTransport(
    base_url="http://localhost:8000",
    timeout=60.0  # Increase timeout
)
```

### Issue: gRPC import errors

**Solution**: Install gRPC extras:
```bash
pip install "a2a-sdk[grpc]"
```

## Related Documentation

- [Client Package](02-Client-Package.md) - Client usage
- [Server Package](03-Server-Package.md) - Server implementation
- [Package Structure](01-Package-Structure.md) - Package overview

---

**Last Updated:** February 2, 2026  
**A2A-SDK Version:** 0.3.22
