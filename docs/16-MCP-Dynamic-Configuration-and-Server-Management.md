# MCP Dynamic Configuration and Server Management

**File Path**: `docs/16-MCP-Dynamic-Configuration-and-Server-Management.md`  
**Package**: `google.adk.tools.mcp_tool`  
**Related Documentation**: 
- [MCP Tools Dynamic Loading](15-MCP-Tools-Dynamic-Loading.md) - General MCP tools documentation
- [Tools Package](02-Tools-Package.md) - General tools documentation

## Overview

This document explains how to implement a Claude/Cursor-like dynamic MCP configuration system in Google ADK. It covers:

1. **Dynamic Configuration System**: JSON-based configuration similar to Claude Desktop
2. **Local Server Auto-Start**: How stdio servers are automatically started
3. **Remote Server Connection**: How to connect to hosted MCP servers
4. **MCP Marketplace Integration**: Connecting to servers from the MCP ecosystem

## Table of Contents

1. [Understanding MCP Server Types](#understanding-mcp-server-types)
2. [How Local Stdio Servers Are Started](#how-local-stdio-servers-are-started)
3. [How Remote Servers Work](#how-remote-servers-work)
4. [Dynamic Configuration System](#dynamic-configuration-system)
5. [MCP Marketplace Integration](#mcp-marketplace-integration)
6. [Complete Examples](#complete-examples)

---

## Understanding MCP Server Types

### Three Types of MCP Servers

Google ADK supports three connection types for MCP servers:

#### 1. **Stdio Servers** (Local Process)

- **Type**: Local process that runs on the same machine
- **Transport**: Standard input/output (stdio)
- **Startup**: Automatically started by Google ADK when needed
- **Use Case**: Tools that run locally (filesystem, local databases, etc.)

```python
# Example: Filesystem MCP server
StdioConnectionParams(
    server_params=StdioServerParameters(
        command="npx",
        args=["-y", "@modelcontextprotocol/server-filesystem", "/path/to/folder"]
    )
)
```

#### 2. **SSE Servers** (Remote via Server-Sent Events)

- **Type**: Remote HTTP server with SSE transport
- **Transport**: HTTP with Server-Sent Events
- **Startup**: Must be running before connection
- **Use Case**: Hosted services, cloud APIs

```python
# Example: Remote SSE server
SseConnectionParams(
    url="http://localhost:8000/mcp",
    headers={"Authorization": "Bearer token"}
)
```

#### 3. **Streamable HTTP Servers** (Remote via HTTP)

- **Type**: Remote HTTP server with streamable HTTP transport
- **Transport**: HTTP with bidirectional streaming
- **Startup**: Must be running before connection
- **Use Case**: Modern hosted services, API gateways

```python
# Example: Remote HTTP server
StreamableHTTPConnectionParams(
    url="https://api.example.com/mcp",
    headers={"Authorization": "Bearer token"}
)
```

---

## How Local Stdio Servers Are Started

### The Auto-Start Mechanism

**Key Point**: Google ADK (via the MCP SDK) automatically starts local stdio server processes. You don't need to manually start them.

### Step-by-Step Process

#### 1. Configuration Time (No Process Started)

When you create a `McpToolset` with `StdioConnectionParams`, **no process is started yet**:

```python
# At this point, NO process is running
toolset = McpToolset(
    connection_params=StdioConnectionParams(
        server_params=StdioServerParameters(
            command="npx",
            args=["-y", "@modelcontextprotocol/server-filesystem", "/tmp"]
        )
    )
)
```

#### 2. Lazy Initialization (Process Starts on First Use)

The process is started automatically when:

**Option A**: `get_tools()` is called
```python
# This triggers process startup
tools = await toolset.get_tools()
# Process is now running: npx -y @modelcontextprotocol/server-filesystem /tmp
```

**Option B**: A tool is invoked
```python
# Process starts automatically when tool is called
result = await agent.run_async("List files in /tmp")
# Process started in background
```

#### 3. Internal Process Management

The MCP SDK's `stdio_client` handles process management:

```python
# Simplified internal flow (from mcp.client.stdio)
async def stdio_client(server_params):
    # 1. Start the process
    process = await asyncio.create_subprocess_exec(
        server_params.command,
        *server_params.args,
        stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        env=server_params.env
    )
    
    # 2. Create communication streams
    read_stream = process.stdout
    write_stream = process.stdin
    
    # 3. Return streams for MCP protocol
    return (read_stream, write_stream)
```

### Process Lifecycle

```
┌─────────────────────────────────────────────────────────┐
│ 1. Toolset Created (No Process)                        │
│    McpToolset(StdioConnectionParams(...))               │
└─────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────┐
│ 2. First Tool Request                                    │
│    await toolset.get_tools()                             │
│    OR                                                     │
│    await agent.run_async("use tool")                     │
└─────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────┐
│ 3. MCPSessionManager.create_session()                   │
│    - Calls stdio_client()                                │
│    - Starts subprocess with command/args                 │
│    - Creates stdin/stdout streams                       │
└─────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────┐
│ 4. Process Running                                       │
│    Process: npx -y @modelcontextprotocol/server-...     │
│    - Communicates via stdin/stdout                       │
│    - Session pooled for reuse                            │
└─────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────┐
│ 5. Cleanup (When toolset.close() called)               │
│    - Process terminated                                   │
│    - Streams closed                                       │
│    - Resources released                                  │
└─────────────────────────────────────────────────────────┘
```

### Important Notes

1. **No Manual Process Management**: You never need to manually start/stop processes
2. **Automatic Cleanup**: Processes are terminated when `toolset.close()` is called
3. **Process Pooling**: For stdio servers, one process is typically shared per toolset
4. **Error Handling**: If the process fails to start, a `ConnectionError` is raised

### Example: Watching Process Start

```python
import asyncio
import psutil  # For process monitoring
from google.adk.tools.mcp_tool import McpToolset, StdioConnectionParams
from mcp import StdioServerParameters

async def demonstrate_auto_start():
    """Demonstrate that stdio servers start automatically."""
    
    # Check: No process running yet
    npx_processes = [p for p in psutil.process_iter(['name']) 
                     if 'npx' in p.info['name'].lower()]
    print(f"Before toolset creation: {len(npx_processes)} npx processes")
    
    # Create toolset (still no process)
    toolset = McpToolset(
        connection_params=StdioConnectionParams(
            server_params=StdioServerParameters(
                command="npx",
                args=["-y", "@modelcontextprotocol/server-filesystem", "/tmp"]
            )
        )
    )
    
    # Check: Still no process
    npx_processes = [p for p in psutil.process_iter(['name']) 
                     if 'npx' in p.info['name'].lower()]
    print(f"After toolset creation: {len(npx_processes)} npx processes")
    
    # Now trigger process start
    tools = await toolset.get_tools()
    
    # Check: Process is now running!
    npx_processes = [p for p in psutil.process_iter(['name']) 
                     if 'npx' in p.info['name'].lower()]
    print(f"After get_tools(): {len(npx_processes)} npx processes")
    print(f"Tools available: {len(tools)}")
    
    # Cleanup
    await toolset.close()
    
    # Check: Process terminated
    npx_processes = [p for p in psutil.process_iter(['name']) 
                     if 'npx' in p.info['name'].lower()]
    print(f"After close(): {len(npx_processes)} npx processes")

asyncio.run(demonstrate_auto_start())
```

---

## How Remote Servers Work

### Remote Server Requirements

**Critical**: Remote SSE and HTTP servers **must already be running** before you can connect to them. Google ADK does not start remote servers.

### Connection Flow

```
┌─────────────────────────────────────────────────────────┐
│ 1. Remote Server Already Running                        │
│    - SSE server at http://example.com/mcp               │
│    - HTTP server at https://api.example.com/mcp         │
└─────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────┐
│ 2. Create Toolset with Remote Connection               │
│    McpToolset(SseConnectionParams(url=...))            │
│    OR                                                    │
│    McpToolset(StreamableHTTPConnectionParams(url=...))  │
└─────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────┐
│ 3. Connection Established (When get_tools() called)   │
│    - HTTP connection to remote server                    │
│    - SSE/HTTP transport protocol handshake              │
│    - Authentication headers sent                        │
└─────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────┐
│ 4. Tools Retrieved                                      │
│    - List tools request sent                            │
│    - Tools received from remote server                  │
│    - Wrapped as ADK tools                              │
└─────────────────────────────────────────────────────────┘
```

### SSE Server Connection

```python
from google.adk.tools.mcp_tool import McpToolset, SseConnectionParams

# Remote SSE server must be running at this URL
toolset = McpToolset(
    connection_params=SseConnectionParams(
        url="http://localhost:8000/mcp",  # Server must be running!
        headers={
            "Authorization": "Bearer token123",
            "X-API-Version": "1.0"
        },
        timeout=10.0,
        sse_read_timeout=300.0
    )
)

# Connection happens here (if server is not running, this will fail)
tools = await toolset.get_tools()
```

### HTTP Server Connection

```python
from google.adk.tools.mcp_tool import McpToolset, StreamableHTTPConnectionParams

# Remote HTTP server must be running at this URL
toolset = McpToolset(
    connection_params=StreamableHTTPConnectionParams(
        url="https://api.example.com/mcp",  # Server must be running!
        headers={
            "Authorization": "Bearer remote_token",
            "Content-Type": "application/json"
        },
        timeout=15.0,
        sse_read_timeout=300.0
    )
)

# Connection happens here
tools = await toolset.get_tools()
```

### Error Handling for Remote Servers

```python
async def connect_to_remote_server(url: str, headers: dict):
    """Connect to remote server with error handling."""
    try:
        toolset = McpToolset(
            connection_params=SseConnectionParams(
                url=url,
                headers=headers
            )
        )
        
        # This will fail if server is not running
        tools = await toolset.get_tools()
        print(f"Successfully connected! {len(tools)} tools available")
        return toolset
        
    except ConnectionError as e:
        print(f"Failed to connect: {e}")
        print("Make sure the remote server is running!")
        return None
    except Exception as e:
        print(f"Unexpected error: {e}")
        return None
```

---

## Dynamic Configuration System

### Overview

The dynamic configuration system allows you to manage MCP servers via a JSON configuration file, similar to how Claude Desktop works.

### Configuration File Format

**Location**: `~/.adk/mcp_servers.json` (or custom path)

```json
{
  "mcpServers": {
    "server_name": {
      "type": "stdio|sse|http",
      "enabled": true,
      "command": "npx",
      "args": ["-y", "package-name"],
      "env": {"KEY": "value"},
      "url": "http://example.com/mcp",
      "headers": {"Authorization": "Bearer token"},
      "timeout": 5.0,
      "tool_filter": ["tool1", "tool2"],
      "tool_name_prefix": "prefix_"
    }
  }
}
```

### Using DynamicMCPConfigManager

See `examples/mcp_dynamic_config.py` for the complete implementation.

#### Basic Usage

```python
from examples.mcp_dynamic_config import DynamicMCPConfigManager, MCPServerConfig

# Initialize manager (loads from ~/.adk/mcp_servers.json)
manager = DynamicMCPConfigManager()

# Add a local stdio server
filesystem_config = MCPServerConfig(
    name="filesystem",
    type="stdio",
    command="npx",
    args=["-y", "@modelcontextprotocol/server-filesystem", "/tmp"]
)
manager.add_server(filesystem_config)

# Add a remote SSE server
remote_config = MCPServerConfig(
    name="remote_api",
    type="sse",
    url="http://localhost:8000/mcp",
    headers={"Authorization": "Bearer token"}
)
manager.add_server(remote_config)

# Create toolsets (stdio server will auto-start, remote must be running)
filesystem_toolset = await manager.create_toolset("filesystem")
remote_toolset = await manager.create_toolset("remote_api")

# Use in agent
agent = LlmAgent(
    model="gemini-2.0-flash",
    tools=[filesystem_toolset, remote_toolset]
)
```

### Key Features

1. **JSON-Based Configuration**: Edit config file without code changes
2. **Runtime Management**: Add/remove servers at runtime
3. **Auto-Start Local Servers**: Stdio servers start automatically
4. **Remote Server Support**: Connect to remote SSE/HTTP servers
5. **Tool Filtering**: Filter tools per server
6. **Enable/Disable**: Toggle servers without removing config

---

## MCP Marketplace Integration

### What is the MCP Marketplace?

While there isn't a single centralized marketplace, the MCP ecosystem includes:

1. **GitHub Repository**: [modelcontextprotocol/servers](https://github.com/modelcontextprotocol/servers) - 77k+ stars, open-source servers
2. **Platform Hosted**: Various platforms host MCP servers (AWS, Vercel, etc.)
3. **Community Servers**: Community-contributed servers

### Finding MCP Servers

#### 1. Official MCP Servers Repository

Browse available servers:
- Filesystem operations
- Google Maps
- GitHub integration
- Slack integration
- Database connectors
- And many more...

#### 2. Platform-Hosted Servers

- **AWS Marketplace**: MCP server with AI-powered tools
- **Vercel**: Hosted MCP servers
- **Custom Deployments**: Organizations host their own servers

### Connecting to Marketplace Servers

#### Example: GitHub MCP Server

```python
from examples.mcp_dynamic_config import DynamicMCPConfigManager, MCPServerConfig

manager = DynamicMCPConfigManager()

# GitHub MCP server (if hosted)
github_config = MCPServerConfig(
    name="github",
    type="sse",
    url="https://mcp-github.example.com/sse",
    headers={"Authorization": f"Bearer {github_token}"}
)
manager.add_server(github_config)

toolset = await manager.create_toolset("github")
```

#### Example: AWS Marketplace MCP Server

```python
# AWS Marketplace MCP Server
aws_config = MCPServerConfig(
    name="aws_marketplace",
    type="sse",
    url="https://mcp-server.aws-marketplace.com/sse",
    headers={
        "Authorization": f"Bearer {aws_token}",
        "X-API-Version": "2024-01-01"
    },
    timeout=15.0
)
manager.add_server(aws_config)
```

### Discovery Pattern

```python
async def discover_and_connect_marketplace_servers():
    """Discover and connect to marketplace MCP servers."""
    
    # In a real implementation, this would query:
    # - MCP registry API
    # - GitHub repository
    # - Service discovery endpoint
    
    discovered_servers = [
        {
            "name": "marketplace_server_1",
            "type": "sse",
            "url": "https://server1.example.com/mcp",
            "description": "File operations",
            "auth_required": True
        },
        {
            "name": "marketplace_server_2",
            "type": "http",
            "url": "https://server2.example.com/api/mcp",
            "description": "API integration",
            "auth_required": False
        }
    ]
    
    manager = DynamicMCPConfigManager()
    
    for server_info in discovered_servers:
        headers = {}
        if server_info.get("auth_required"):
            # Get token from user/keychain
            headers["Authorization"] = f"Bearer {get_token(server_info['name'])}"
        
        config = MCPServerConfig(
            name=server_info["name"],
            type=server_info["type"],
            url=server_info["url"],
            headers=headers if headers else None
        )
        
        manager.add_server(config)
        
        # Test connection
        try:
            toolset = await manager.create_toolset(config.name)
            if toolset:
                tools = await toolset.get_tools()
                print(f"✓ {config.name}: {len(tools)} tools")
        except Exception as e:
            print(f"✗ {config.name}: Connection failed - {e}")
    
    return manager
```

---

## Complete Examples

### Example 1: Local Stdio Server (Auto-Start)

```python
import asyncio
from google.adk.agents import LlmAgent
from google.adk.tools.mcp_tool import McpToolset, StdioConnectionParams
from mcp import StdioServerParameters

async def local_stdio_example():
    """Example: Local stdio server that auto-starts."""
    
    # Create toolset (no process started yet)
    toolset = McpToolset(
        connection_params=StdioConnectionParams(
            server_params=StdioServerParameters(
                command="npx",
                args=["-y", "@modelcontextprotocol/server-filesystem", "/tmp"]
            )
        )
    )
    
    # Process starts automatically here
    tools = await toolset.get_tools()
    print(f"Tools available: {[t.name for t in tools]}")
    
    # Create agent
    agent = LlmAgent(
        model="gemini-2.0-flash",
        name="local_agent",
        tools=[toolset]
    )
    
    # Use agent (process is running)
    response = await agent.run_async("List files in /tmp")
    print(response)
    
    # Cleanup (process terminated)
    await toolset.close()

asyncio.run(local_stdio_example())
```

### Example 2: Remote SSE Server

```python
import asyncio
from google.adk.agents import LlmAgent
from google.adk.tools.mcp_tool import McpToolset, SseConnectionParams

async def remote_sse_example():
    """Example: Remote SSE server (must be running)."""
    
    # Server must be running at this URL
    toolset = McpToolset(
        connection_params=SseConnectionParams(
            url="http://localhost:8000/mcp",
            headers={"Authorization": "Bearer token123"},
            timeout=10.0
        )
    )
    
    # Connection happens here (fails if server not running)
    try:
        tools = await toolset.get_tools()
        print(f"Connected! Tools: {[t.name for t in tools]}")
        
        agent = LlmAgent(
            model="gemini-2.0-flash",
            name="remote_agent",
            tools=[toolset]
        )
        
        response = await agent.run_async("Use remote tool")
        print(response)
        
    except ConnectionError as e:
        print(f"Failed to connect: {e}")
        print("Make sure the remote server is running!")

asyncio.run(remote_sse_example())
```

### Example 3: Dynamic Configuration

```python
import asyncio
from examples.mcp_dynamic_config import DynamicMCPConfigManager, MCPServerConfig
from google.adk.agents import LlmAgent

async def dynamic_config_example():
    """Example: Using dynamic configuration system."""
    
    manager = DynamicMCPConfigManager()
    
    # Add servers from config file or programmatically
    configs = [
        MCPServerConfig(
            name="filesystem",
            type="stdio",
            command="npx",
            args=["-y", "@modelcontextprotocol/server-filesystem", "/tmp"]
        ),
        MCPServerConfig(
            name="remote_api",
            type="sse",
            url="http://localhost:8000/mcp",
            headers={"Authorization": "Bearer token"}
        )
    ]
    
    for config in configs:
        manager.add_server(config)
    
    # Get all toolsets
    toolsets = await manager.get_all_toolsets()
    
    # Create agent
    agent = LlmAgent(
        model="gemini-2.0-flash",
        name="dynamic_agent",
        tools=toolsets
    )
    
    print(f"Agent created with {len(toolsets)} toolsets")
    
    # Cleanup
    await manager.close_all()

asyncio.run(dynamic_config_example())
```

### Example 4: Marketplace Integration

See `examples/mcp_remote_server_example.py` for complete marketplace integration examples.

---

## Summary

### Key Takeaways

1. **Local Stdio Servers**: Automatically started by Google ADK when `get_tools()` is called or a tool is invoked
2. **Remote Servers**: Must be running before connection; Google ADK only connects, doesn't start them
3. **Dynamic Configuration**: JSON-based system similar to Claude Desktop for managing servers
4. **Marketplace**: Connect to servers from the MCP ecosystem via SSE/HTTP

### Comparison: Claude/Cursor vs Google ADK

| Feature | Claude/Cursor | Google ADK |
|---------|---------------|------------|
| **Config Format** | JSON file | JSON file (via DynamicMCPConfigManager) |
| **Local Server Start** | Auto-start on launch | Auto-start on first use (lazy) |
| **Remote Server** | Connect to running server | Connect to running server |
| **Runtime Management** | Via UI | Via code/API |
| **Process Management** | Handled by client | Handled by MCP SDK |

### Best Practices

1. **Local Servers**: Let Google ADK handle process management automatically
2. **Remote Servers**: Verify servers are running before connecting
3. **Configuration**: Use `DynamicMCPConfigManager` for dynamic server management
4. **Error Handling**: Always handle `ConnectionError` for remote servers
5. **Cleanup**: Call `toolset.close()` or `manager.close_all()` when done

---

## Related Documentation

- [MCP Tools Dynamic Loading](15-MCP-Tools-Dynamic-Loading.md) - General MCP tools documentation
- [Tools Package](02-Tools-Package.md) - General tools documentation
- [Examples](../examples/mcp_dynamic_config.py) - Dynamic configuration implementation
- [Examples](../examples/mcp_remote_server_example.py) - Remote server examples

---

## References

- [MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk)
- [MCP Servers Repository](https://github.com/modelcontextprotocol/servers)
- [MCP Specification](https://modelcontextprotocol.io/)
- [Claude Desktop MCP Setup](https://support.claude.com/en/articles/10949351-getting-started-with-local-mcp-servers-on-claude-desktop)

---

**Last Updated:** 2025-01-26  
**Google ADK Version:** 1.22.1
