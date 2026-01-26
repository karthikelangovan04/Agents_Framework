# MCP Tools Dynamic Loading in Google ADK

**File Path**: `docs/15-MCP-Tools-Dynamic-Loading.md`  
**Package**: `google.adk.tools.mcp_tool`  
**Related Documentation**: 
- [Tools Package](02-Tools-Package.md) - General tools documentation
- [Agents Package](01-Agents-Package.md) - How agents use tools
- [Sessions Package](07-Sessions-Package.md) - Session management

## Overview

This document explains how Google ADK handles MCP (Model Context Protocol) tools, particularly focusing on dynamic loading mechanisms. It compares Google ADK's approach with how other applications (like Claude Desktop and ChatGPT) handle dynamic MCP tool configuration, and provides guidance on implementing dynamic MCP tools in your applications.

## Table of Contents

1. [Understanding MCP Tools](#understanding-mcp-tools)
2. [Google ADK's MCP Tool Architecture](#google-adks-mcp-tool-architecture)
3. [Dynamic Loading Mechanism](#dynamic-loading-mechanism)
4. [Comparison with Other Applications](#comparison-with-other-applications)
5. [Implementing Dynamic MCP Tools](#implementing-dynamic-mcp-tools)
6. [Best Practices](#best-practices)
7. [Advanced Patterns](#advanced-patterns)

---

## Understanding MCP Tools

### What is MCP?

The Model Context Protocol (MCP) is a standardized protocol that allows AI applications to connect to external tools and data sources. MCP servers expose tools that agents can use to interact with external systems.

### MCP Tool Flow

```
┌─────────────┐         ┌──────────────┐         ┌─────────────┐
│   Agent    │────────▶│  MCP Client  │────────▶│ MCP Server  │
│  (Google   │         │  (ADK Tool)  │         │  (External) │
│    ADK)    │◀────────│              │◀────────│             │
└─────────────┘         └──────────────┘         └─────────────┘
```

1. **Agent** requests tools from the toolset
2. **MCP Client** (McpToolset) connects to MCP Server
3. **MCP Server** exposes available tools
4. **MCP Client** wraps tools as ADK tools
5. **Agent** can now use these tools

---

## Google ADK's MCP Tool Architecture

### Core Components

Google ADK's MCP tool implementation consists of three main components:

#### 1. `McpToolset` - Tool Collection Manager

The `McpToolset` class manages the connection to an MCP server and provides tools to agents:

```python
from google.adk.agents import LlmAgent
from google.adk.tools.mcp_tool import McpToolset, StdioConnectionParams
from mcp import StdioServerParameters

# Create MCP toolset with stdio connection
filesystem_toolset = McpToolset(
    connection_params=StdioConnectionParams(
        server_params=StdioServerParameters(
            command="npx",
            args=["-y", "@modelcontextprotocol/server-filesystem", "/path/to/folder"]
        )
    )
)

# Create agent with MCP tools
agent = LlmAgent(
    model="gemini-2.0-flash",
    name="file_agent",
    tools=[filesystem_toolset]
)
```

**Key Features:**
- Manages MCP server connection
- Retrieves tools from MCP server dynamically
- Handles connection pooling and session management
- Supports multiple connection types (Stdio, SSE, Streamable HTTP)

#### 2. `McpTool` - Individual Tool Wrapper

Each tool from the MCP server is wrapped as an `McpTool`:

```python
# Internal implementation (simplified)
class McpTool(BaseAuthenticatedTool):
    def __init__(self, mcp_tool, mcp_session_manager, ...):
        # Wraps MCP tool with ADK interface
        self._mcp_tool = mcp_tool
        self._mcp_session_manager = mcp_session_manager
    
    async def run_async(self, *, args, tool_context):
        # Calls MCP server tool via session
        session = await self._mcp_session_manager.create_session()
        response = await session.call_tool(self._mcp_tool.name, arguments=args)
        return response
```

#### 3. `MCPSessionManager` - Connection Management

The `MCPSessionManager` handles:
- **Connection pooling**: Reuses sessions based on authentication headers
- **Session lifecycle**: Creates, maintains, and cleans up sessions
- **Retry logic**: Automatically retries on connection errors
- **Multiple protocols**: Supports Stdio, SSE, and Streamable HTTP

```python
# Session pooling based on headers
session_key = self._generate_session_key(merged_headers)
if session_key in self._sessions:
    session, exit_stack = self._sessions[session_key]
    if not self._is_session_disconnected(session):
        return session  # Reuse existing session
```

---

## Dynamic Loading Mechanism

### How Dynamic Loading Works

Google ADK implements **lazy loading** of MCP tools. Tools are not loaded at agent initialization; instead, they are fetched when needed:

#### Step 1: Agent Initialization (No Tools Loaded Yet)

```python
# At this point, no MCP connection is established
agent = LlmAgent(
    model="gemini-2.0-flash",
    name="my_agent",
    tools=[mcp_toolset]  # Toolset is just a reference
)
```

#### Step 2: Tool Discovery (When Agent Runs)

When the agent needs to use tools, it calls `get_tools()`:

```python
# Inside agent execution (simplified)
async def _get_available_tools(self, context):
    tools = []
    for toolset in self.tools:
        # This is where MCP connection happens!
        toolset_tools = await toolset.get_tools(readonly_context=context)
        tools.extend(toolset_tools)
    return tools
```

#### Step 3: MCP Connection and Tool Retrieval

```python
# Inside McpToolset.get_tools() (from implementation)
async def get_tools(self, readonly_context=None):
    # 1. Create/get MCP session
    session = await self._mcp_session_manager.create_session(headers=headers)
    
    # 2. Fetch tools from MCP server
    tools_response = await session.list_tools()
    
    # 3. Wrap each MCP tool as ADK tool
    tools = []
    for tool in tools_response.tools:
        mcp_tool = MCPTool(
            mcp_tool=tool,
            mcp_session_manager=self._mcp_session_manager,
            ...
        )
        if self._is_tool_selected(mcp_tool, readonly_context):
            tools.append(mcp_tool)
    
    return tools
```

### Key Characteristics

1. **Lazy Loading**: Tools are fetched only when `get_tools()` is called
2. **Context-Aware**: Tools can be filtered based on `readonly_context`
3. **Session Pooling**: Sessions are reused based on authentication headers
4. **Dynamic Discovery**: Each call to `get_tools()` queries the MCP server for current tools

### Tool Filtering

Tools can be filtered at multiple levels:

#### 1. Static Filtering (At Initialization)

```python
# Filter specific tools by name
toolset = McpToolset(
    connection_params=...,
    tool_filter=['read_file', 'write_file']  # Only these tools
)
```

#### 2. Dynamic Filtering (At Runtime)

```python
# Custom predicate function
def should_include_tool(tool: BaseTool, context: ReadonlyContext) -> bool:
    # Filter based on context (e.g., user permissions, session state)
    if context and hasattr(context, 'user_role'):
        if context.user_role == 'readonly':
            return tool.name.startswith('read_')
    return True

toolset = McpToolset(
    connection_params=...,
    tool_filter=should_include_tool
)
```

#### 3. Context-Based Filtering

```python
# Tools are filtered when get_tools() is called with context
async def get_tools(self, readonly_context=None):
    # readonly_context can contain:
    # - User information
    # - Session state
    # - Request metadata
    # - Custom filtering logic
    
    tools = await self._fetch_from_mcp_server()
    return [t for t in tools if self._is_tool_selected(t, readonly_context)]
```

---

## Comparison with Other Applications

### Claude Desktop / ChatGPT Approach

**Architecture:**
- **Frontend-driven**: Users configure MCP tools in the UI per chat session
- **Session-scoped**: Tools are added/removed dynamically during conversation
- **Discovery tools**: Special MCP tools (like `mcp-find`, `mcp-add`) allow dynamic server discovery
- **Gateway pattern**: Uses an MCP Gateway/Toolkit that manages multiple servers

**Example Flow:**
```
User → Frontend UI → Select MCP Server → Add to Chat → Backend Connects
```

**Key Differences:**

| Aspect | Claude/ChatGPT | Google ADK |
|--------|----------------|------------|
| **Configuration** | Frontend UI per session | Backend code at initialization |
| **Discovery** | Dynamic via `mcp-find` tool | Static configuration |
| **Scope** | Per-chat session | Per-agent/application |
| **Flexibility** | Users can add tools on-the-fly | Developers configure upfront |
| **Deployment** | No code changes needed | Requires code deployment |

### Google ADK Approach

**Architecture:**
- **Backend-driven**: MCP tools are configured in Python code
- **Application-scoped**: Tools are available to the entire agent/application
- **Lazy loading**: Tools are discovered when `get_tools()` is called
- **Session pooling**: Efficient connection reuse

**Example Flow:**
```
Developer → Code Configuration → Agent Initialization → Lazy Tool Loading
```

### Why the Difference?

1. **Deployment Model**: 
   - Claude/ChatGPT: SaaS with user-facing UI
   - Google ADK: Self-hosted applications with developer control

2. **Use Case**:
   - Claude/ChatGPT: End-users need flexibility to add tools
   - Google ADK: Developers want predictable, versioned tool configurations

3. **Security**:
   - Claude/ChatGPT: Users control their own tool access
   - Google ADK: Developers control tool access for all users

---

## Implementing Dynamic MCP Tools

### Pattern 1: Runtime Toolset Creation

Create toolsets dynamically based on user input or configuration:

```python
from google.adk.agents import LlmAgent
from google.adk.tools.mcp_tool import McpToolset, StdioConnectionParams
from mcp import StdioServerParameters

async def create_agent_with_dynamic_tools(user_config: dict):
    """Create agent with tools based on user configuration."""
    
    toolsets = []
    
    # Add filesystem toolset if user has access
    if user_config.get('filesystem_enabled'):
        filesystem_toolset = McpToolset(
            connection_params=StdioConnectionParams(
                server_params=StdioServerParameters(
                    command="npx",
                    args=["-y", "@modelcontextprotocol/server-filesystem", 
                          user_config['filesystem_path']]
                )
            )
        )
        toolsets.append(filesystem_toolset)
    
    # Add Google Maps toolset if API key provided
    if user_config.get('maps_api_key'):
        maps_toolset = McpToolset(
            connection_params=StdioConnectionParams(
                server_params=StdioServerParameters(
                    command="npx",
                    args=["-y", "@modelcontextprotocol/server-google-maps"],
                    env={"GOOGLE_MAPS_API_KEY": user_config['maps_api_key']}
                )
            )
        )
        toolsets.append(maps_toolset)
    
    # Create agent with dynamic toolsets
    agent = LlmAgent(
        model="gemini-2.0-flash",
        name="dynamic_agent",
        tools=toolsets
    )
    
    return agent
```

### Pattern 2: Context-Based Tool Filtering

Filter tools based on runtime context:

```python
from google.adk.tools.base_toolset import ToolPredicate
from google.adk.agents.readonly_context import ReadonlyContext

class RoleBasedToolFilter(ToolPredicate):
    """Filter tools based on user role."""
    
    def __init__(self, user_role: str):
        self.user_role = user_role
    
    def __call__(self, tool: BaseTool, context: ReadonlyContext = None) -> bool:
        # Admin users get all tools
        if self.user_role == 'admin':
            return True
        
        # Read-only users only get read tools
        if self.user_role == 'readonly':
            return tool.name.startswith('read_') or tool.name.startswith('list_')
        
        # Regular users get most tools except admin tools
        if self.user_role == 'user':
            return not tool.name.startswith('admin_')
        
        return False

# Use the filter
toolset = McpToolset(
    connection_params=...,
    tool_filter=RoleBasedToolFilter(user_role='readonly')
)
```

### Pattern 3: Session-Scoped Tools

Create toolsets per session using session state:

```python
from google.adk.sessions import SessionService
from google.adk.runners import Runner

class SessionScopedToolManager:
    """Manages toolsets per session."""
    
    def __init__(self, session_service: SessionService):
        self.session_service = session_service
        self._session_toolsets = {}  # session_id -> list of toolsets
    
    async def add_toolset_to_session(self, session_id: str, toolset: McpToolset):
        """Add a toolset to a specific session."""
        if session_id not in self._session_toolsets:
            self._session_toolsets[session_id] = []
        self._session_toolsets[session_id].append(toolset)
    
    async def get_toolsets_for_session(self, session_id: str) -> list[McpToolset]:
        """Get all toolsets for a session."""
        return self._session_toolsets.get(session_id, [])
    
    async def remove_toolset_from_session(self, session_id: str, toolset_name: str):
        """Remove a toolset from a session."""
        if session_id in self._session_toolsets:
            self._session_toolsets[session_id] = [
                ts for ts in self._session_toolsets[session_id]
                if ts.name != toolset_name
            ]

# Usage
tool_manager = SessionScopedToolManager(session_service)

# In your agent wrapper
async def create_agent_for_session(session_id: str):
    # Get base toolsets
    base_toolsets = [filesystem_toolset, maps_toolset]
    
    # Get session-specific toolsets
    session_toolsets = await tool_manager.get_toolsets_for_session(session_id)
    
    # Combine all toolsets
    all_toolsets = base_toolsets + session_toolsets
    
    # Create agent with combined toolsets
    agent = LlmAgent(
        model="gemini-2.0-flash",
        name=f"session_{session_id}_agent",
        tools=all_toolsets
    )
    
    return agent
```

### Pattern 4: Dynamic Toolset Factory

**This is the pattern used by Claude Desktop and Cursor!** They use a JSON configuration file to define MCP servers, and the client automatically starts local servers and connects to remote ones.

Create a factory that builds toolsets from configuration:

```python
from typing import Dict, List
from google.adk.tools.mcp_tool import McpToolset, StdioConnectionParams, SseConnectionParams
from mcp import StdioServerParameters

class MCPToolsetFactory:
    """Factory for creating MCP toolsets from configuration."""
    
    @staticmethod
    def create_from_config(config: Dict) -> List[McpToolset]:
        """Create toolsets from configuration dictionary."""
        toolsets = []
        
        for server_config in config.get('mcp_servers', []):
            server_type = server_config.get('type')
            
            if server_type == 'stdio':
                toolset = MCPToolsetFactory._create_stdio_toolset(server_config)
            elif server_type == 'sse':
                toolset = MCPToolsetFactory._create_sse_toolset(server_config)
            elif server_type == 'http':
                toolset = MCPToolsetFactory._create_http_toolset(server_config)
            else:
                raise ValueError(f"Unknown server type: {server_type}")
            
            toolsets.append(toolset)
        
        return toolsets
    
    @staticmethod
    def _create_stdio_toolset(config: Dict) -> McpToolset:
        """Create stdio-based toolset."""
        return McpToolset(
            connection_params=StdioConnectionParams(
                server_params=StdioServerParameters(
                    command=config['command'],
                    args=config.get('args', []),
                    env=config.get('env', {})
                ),
                timeout=config.get('timeout', 5.0)
            ),
            tool_filter=config.get('tool_filter'),
            tool_name_prefix=config.get('tool_name_prefix')
        )
    
    @staticmethod
    def _create_sse_toolset(config: Dict) -> McpToolset:
        """Create SSE-based toolset."""
        return McpToolset(
            connection_params=SseConnectionParams(
                url=config['url'],
                headers=config.get('headers'),
                timeout=config.get('timeout', 5.0),
                sse_read_timeout=config.get('sse_read_timeout', 300.0)
            ),
            tool_filter=config.get('tool_filter'),
            tool_name_prefix=config.get('tool_name_prefix')
        )
    
    @staticmethod
    def _create_http_toolset(config: Dict) -> McpToolset:
        """Create HTTP-based toolset."""
        from google.adk.tools.mcp_tool import StreamableHTTPConnectionParams
        return McpToolset(
            connection_params=StreamableHTTPConnectionParams(
                url=config['url'],
                headers=config.get('headers'),
                timeout=config.get('timeout', 5.0),
                sse_read_timeout=config.get('sse_read_timeout', 300.0)
            ),
            tool_filter=config.get('tool_filter'),
            tool_name_prefix=config.get('tool_name_prefix')
        )

# Usage
config = {
    'mcp_servers': [
        {
            'type': 'stdio',
            'command': 'npx',
            'args': ['-y', '@modelcontextprotocol/server-filesystem', '/path/to/files'],
            'tool_filter': ['read_file', 'write_file']
        },
        {
            'type': 'sse',
            'url': 'http://localhost:8000/mcp',
            'headers': {'Authorization': 'Bearer token123'}
        }
    ]
}

toolsets = MCPToolsetFactory.create_from_config(config)
agent = LlmAgent(model="gemini-2.0-flash", name="config_agent", tools=toolsets)
```

**Note**: For a complete working implementation of this pattern (including auto-start of local servers and remote server connection), see:
- [MCP Dynamic Configuration and Server Management](16-MCP-Dynamic-Configuration-and-Server-Management.md) - Complete guide
- `examples/mcp_dynamic_config.py` - Full implementation
- `examples/mcp_config.json` - Example configuration file
```

### Pattern 5: API-Driven Tool Configuration

Expose an API endpoint to configure tools dynamically:

```python
from fastapi import FastAPI, HTTPException
from google.adk.apps import App
from google.adk.agents import LlmAgent
from google.adk.tools.mcp_tool import McpToolset

app = FastAPI()
tool_manager = {}  # session_id -> agent mapping

@app.post("/sessions/{session_id}/tools")
async def add_tool_to_session(session_id: str, tool_config: dict):
    """Add an MCP tool to a session."""
    
    # Create toolset from config
    toolset = McpToolset(
        connection_params=StdioConnectionParams(
            server_params=StdioServerParameters(
                command=tool_config['command'],
                args=tool_config.get('args', [])
            )
        )
    )
    
    # Get or create agent for session
    if session_id not in tool_manager:
        agent = LlmAgent(
            model="gemini-2.0-flash",
            name=f"session_{session_id}",
            tools=[toolset]
        )
        tool_manager[session_id] = agent
    else:
        # Add toolset to existing agent
        agent = tool_manager[session_id]
        agent.tools.append(toolset)
    
    return {"status": "tool_added", "session_id": session_id}

@app.delete("/sessions/{session_id}/tools/{toolset_name}")
async def remove_tool_from_session(session_id: str, toolset_name: str):
    """Remove a toolset from a session."""
    if session_id not in tool_manager:
        raise HTTPException(status_code=404, detail="Session not found")
    
    agent = tool_manager[session_id]
    agent.tools = [
        ts for ts in agent.tools 
        if getattr(ts, 'name', '') != toolset_name
    ]
    
    return {"status": "tool_removed"}
```

---

## Best Practices

### 1. Connection Management

**✅ DO:**
- Reuse toolsets across multiple agent invocations
- Let session manager handle connection pooling
- Close toolsets when no longer needed

```python
# Good: Reuse toolset
toolset = McpToolset(...)
agent1 = LlmAgent(tools=[toolset])
agent2 = LlmAgent(tools=[toolset])  # Reuses same connection

# Cleanup when done
await toolset.close()
```

**❌ DON'T:**
- Create new toolsets for every request
- Manually manage MCP connections
- Forget to close toolsets

```python
# Bad: Creates new connection every time
async def handle_request():
    toolset = McpToolset(...)  # New connection each time!
    agent = LlmAgent(tools=[toolset])
    # Connection not closed
```

### 2. Error Handling

**✅ DO:**
- Handle connection errors gracefully
- Implement retry logic for transient failures
- Provide fallback behavior

```python
from google.adk.tools.mcp_tool.mcp_session_manager import retry_on_errors

@retry_on_errors
async def get_tools_safely(toolset: McpToolset):
    try:
        return await toolset.get_tools()
    except ConnectionError as e:
        logger.error(f"MCP connection failed: {e}")
        return []  # Return empty list, agent continues without these tools
```

### 3. Security

**✅ DO:**
- Validate user permissions before adding tools
- Use authentication headers for secure connections
- Filter tools based on user context

```python
# Secure toolset creation
def create_secure_toolset(user: User, config: dict):
    # Check permissions
    if not user.has_permission('filesystem_access'):
        raise PermissionError("User lacks filesystem access")
    
    # Use user-specific credentials
    toolset = McpToolset(
        connection_params=...,
        auth_credential=user.get_mcp_credentials(),
        tool_filter=RoleBasedToolFilter(user.role)
    )
    return toolset
```

### 4. Performance

**✅ DO:**
- Use connection pooling (automatic with MCPSessionManager)
- Cache tool lists when appropriate
- Use appropriate timeouts

```python
# Good: Configured timeouts
toolset = McpToolset(
    connection_params=StdioConnectionParams(
        server_params=...,
        timeout=5.0  # Reasonable timeout
    )
)
```

**❌ DON'T:**
- Block on tool discovery
- Use very long timeouts
- Fetch tools synchronously

### 5. Testing

**✅ DO:**
- Mock MCP servers in tests
- Test tool filtering logic
- Test error scenarios

```python
import pytest
from unittest.mock import AsyncMock, MagicMock

@pytest.mark.asyncio
async def test_toolset_filtering():
    # Mock MCP session
    mock_session = AsyncMock()
    mock_session.list_tools.return_value = MagicMock(
        tools=[
            MagicMock(name="read_file", description="Read a file"),
            MagicMock(name="write_file", description="Write a file"),
            MagicMock(name="delete_file", description="Delete a file")
        ]
    )
    
    # Test filtering
    toolset = McpToolset(
        connection_params=...,
        tool_filter=['read_file', 'write_file']
    )
    
    tools = await toolset.get_tools()
    assert len(tools) == 2
    assert all(t.name in ['read_file', 'write_file'] for t in tools)
```

---

## Advanced Patterns

### Pattern 6: Tool Discovery Service

Implement a service that discovers available MCP servers:

```python
class MCPDiscoveryService:
    """Discovers and manages available MCP servers."""
    
    def __init__(self):
        self._known_servers = {}
        self._server_registry = []
    
    async def discover_servers(self) -> List[Dict]:
        """Discover available MCP servers."""
        # Could query a registry, scan network, etc.
        discovered = []
        
        # Example: Check local registry
        for server_info in self._server_registry:
            if await self._is_server_available(server_info):
                discovered.append(server_info)
        
        return discovered
    
    async def _is_server_available(self, server_info: Dict) -> bool:
        """Check if an MCP server is available."""
        try:
            # Try to connect and list tools
            toolset = McpToolset(connection_params=...)
            tools = await toolset.get_tools()
            await toolset.close()
            return len(tools) > 0
        except Exception:
            return False
    
    async def create_toolset_for_server(self, server_id: str) -> McpToolset:
        """Create a toolset for a discovered server."""
        server_info = self._known_servers.get(server_id)
        if not server_info:
            raise ValueError(f"Server {server_id} not found")
        
        return McpToolset(connection_params=server_info['connection_params'])
```

### Pattern 7: Tool Composition

Combine multiple toolsets with different scopes:

```python
class CompositeToolsetManager:
    """Manages multiple toolsets with different scopes."""
    
    def __init__(self):
        self._global_toolsets = []  # Available to all agents
        self._user_toolsets = {}    # user_id -> toolsets
        self._session_toolsets = {} # session_id -> toolsets
    
    def add_global_toolset(self, toolset: McpToolset):
        """Add a toolset available to all agents."""
        self._global_toolsets.append(toolset)
    
    def add_user_toolset(self, user_id: str, toolset: McpToolset):
        """Add a toolset for a specific user."""
        if user_id not in self._user_toolsets:
            self._user_toolsets[user_id] = []
        self._user_toolsets[user_id].append(toolset)
    
    def add_session_toolset(self, session_id: str, toolset: McpToolset):
        """Add a toolset for a specific session."""
        if session_id not in self._session_toolsets:
            self._session_toolsets[session_id] = []
        self._session_toolsets[session_id].append(toolset)
    
    def get_toolsets_for_context(
        self, 
        user_id: str = None, 
        session_id: str = None
    ) -> List[McpToolset]:
        """Get all toolsets for a given context."""
        toolsets = list(self._global_toolsets)
        
        if user_id and user_id in self._user_toolsets:
            toolsets.extend(self._user_toolsets[user_id])
        
        if session_id and session_id in self._session_toolsets:
            toolsets.extend(self._session_toolsets[session_id])
        
        return toolsets

# Usage
manager = CompositeToolsetManager()

# Global toolsets (available to everyone)
manager.add_global_toolset(filesystem_toolset)

# User-specific toolsets
manager.add_user_toolset("user123", premium_toolset)

# Session-specific toolsets
manager.add_session_toolset("session456", temporary_toolset)

# Create agent with context-appropriate tools
toolsets = manager.get_toolsets_for_context(
    user_id="user123",
    session_id="session456"
)
agent = LlmAgent(model="gemini-2.0-flash", tools=toolsets)
```

### Pattern 8: Tool Versioning

Manage different versions of MCP servers:

```python
class VersionedMCPToolset:
    """Manages versioned MCP toolsets."""
    
    def __init__(self):
        self._versions = {}  # version -> toolset
    
    def register_version(self, version: str, toolset: McpToolset):
        """Register a toolset version."""
        self._versions[version] = toolset
    
    def get_toolset_for_version(self, version: str) -> McpToolset:
        """Get toolset for a specific version."""
        if version not in self._versions:
            raise ValueError(f"Version {version} not found")
        return self._versions[version]
    
    def get_latest_version(self) -> str:
        """Get the latest version."""
        return max(self._versions.keys())

# Usage
versioned = VersionedMCPToolset()
versioned.register_version("1.0.0", old_toolset)
versioned.register_version("2.0.0", new_toolset)

# Use specific version
toolset = versioned.get_toolset_for_version("2.0.0")
```

---

## Summary

### Key Takeaways

1. **Lazy Loading**: Google ADK loads MCP tools dynamically when `get_tools()` is called, not at initialization
2. **Session Pooling**: Connections are efficiently reused based on authentication headers
3. **Context-Aware Filtering**: Tools can be filtered based on runtime context
4. **Backend Configuration**: Unlike Claude/ChatGPT, tools are configured in code, not UI
5. **Flexible Patterns**: Multiple patterns exist for implementing dynamic tool loading

### When to Use Each Approach

- **Static Configuration**: When tools are known at development time and don't change
- **Runtime Creation**: When tools depend on user configuration or permissions
- **Context Filtering**: When tools should be available based on user role or session state
- **API-Driven**: When you need end-user control similar to Claude/ChatGPT
- **Session-Scoped**: When tools should be added/removed during a conversation

### Architecture Decision

**Google ADK's approach** is ideal for:
- Production applications with stable tool requirements
- Developer-controlled tool configurations
- Version-controlled deployments
- Security-focused applications

**Claude/ChatGPT's approach** is ideal for:
- User-facing applications where users need flexibility
- SaaS platforms with multi-tenancy
- Rapid prototyping and experimentation
- End-user tool discovery

---

## Related Documentation

- [Tools Package](02-Tools-Package.md) - General tools documentation
- [Agents Package](01-Agents-Package.md) - How agents use tools
- [Sessions Package](07-Sessions-Package.md) - Session management
- [State Management](11-State-Management.md) - Managing application state
- [A2A Package](04-A2A-Package.md) - Multi-agent systems

---

## References

- [Google ADK MCP Tools Documentation](https://google.github.io/adk-docs/tools-custom/mcp-tools/)
- [Model Context Protocol Specification](https://modelcontextprotocol.io/)
- [MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk)

---

**Last Updated:** 2025-01-26  
**Google ADK Version:** 1.22.1
