# MCP Dynamic Configuration Examples

This directory contains working examples for implementing Claude/Cursor-like dynamic MCP configuration in Google ADK.

## Files

- **`mcp_dynamic_config.py`**: Complete implementation of `DynamicMCPConfigManager` - a system for managing MCP servers via JSON configuration files
- **`mcp_config.json`**: Example configuration file (similar to Claude Desktop's config)
- **`mcp_remote_server_example.py`**: Examples for connecting to remote MCP servers from marketplace

## Quick Start

### 1. Basic Usage

```python
from mcp_dynamic_config import DynamicMCPConfigManager, MCPServerConfig
from google.adk.agents import LlmAgent

# Initialize manager (loads from ~/.adk/mcp_servers.json)
manager = DynamicMCPConfigManager()

# Add a local stdio server (auto-starts when used)
filesystem_config = MCPServerConfig(
    name="filesystem",
    type="stdio",
    command="npx",
    args=["-y", "@modelcontextprotocol/server-filesystem", "/tmp"]
)
manager.add_server(filesystem_config)

# Create toolset (process starts automatically on first use)
toolset = await manager.create_toolset("filesystem")

# Use in agent
agent = LlmAgent(
    model="gemini-2.0-flash",
    tools=[toolset]
)
```

### 2. Configuration File

Edit `~/.adk/mcp_servers.json`:

```json
{
  "mcpServers": {
    "filesystem": {
      "type": "stdio",
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-filesystem", "/tmp"]
    },
    "remote_api": {
      "type": "sse",
      "url": "http://localhost:8000/mcp",
      "headers": {"Authorization": "Bearer token"}
    }
  }
}
```

## Key Features

### ✅ Local Server Auto-Start

Local stdio servers are **automatically started** by Google ADK when:
- `get_tools()` is called on the toolset
- A tool from the toolset is invoked

**You don't need to manually start processes!**

### ✅ Remote Server Connection

Remote SSE/HTTP servers **must be running** before connection. Google ADK connects to them but doesn't start them.

### ✅ Dynamic Configuration

- Add/remove servers at runtime
- Enable/disable servers without removing config
- Filter tools per server
- Manage via JSON file or programmatically

## How It Works

### Local Stdio Servers

```
1. Create toolset → No process started
2. Call get_tools() → Process auto-starts
3. Use tools → Process running
4. Close toolset → Process terminated
```

### Remote Servers

```
1. Server must be running
2. Create toolset with URL
3. Call get_tools() → Connection established
4. Use tools → HTTP/SSE communication
```

## Documentation

For detailed explanations, see:
- [MCP Dynamic Configuration and Server Management](../docs/16-MCP-Dynamic-Configuration-and-Server-Management.md) - Complete guide
- [MCP Tools Dynamic Loading](../docs/15-MCP-Tools-Dynamic-Loading.md) - General MCP tools documentation

## Validation

**Yes, Pattern 4 (Dynamic Toolset Factory) is exactly what Claude/Cursor do!**

They use:
- JSON configuration files
- Auto-start of local stdio servers
- Connection to remote servers
- Runtime server management

The `DynamicMCPConfigManager` implements this same pattern for Google ADK.
