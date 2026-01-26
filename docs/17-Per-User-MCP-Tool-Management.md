# Per-User MCP Tool Management in Google ADK

**File Path**: `docs/17-Per-User-MCP-Tool-Management.md`  
**Package**: `google.adk.tools.mcp_tool`, `google.adk.sessions`, `google.adk.sessions.state`  
**Related Documentation**: 
- [MCP Dynamic Configuration](16-MCP-Dynamic-Configuration-and-Server-Management.md) - Server management
- [MCP Tools Dynamic Loading](15-MCP-Tools-Dynamic-Loading.md) - General MCP tools
- [Sessions Package](07-Sessions-Package.md) - Session management
- [State Management](11-State-Management.md) - State scopes

## Overview

This document explains how to implement **per-user MCP tool management** similar to how Claude Desktop and Cursor work, where each user can configure their own set of MCP tools. It covers:

1. How Claude/Cursor handle per-user MCP configurations
2. Frontend-to-backend flow
3. How Google ADK supports this with Sessions and State Management
4. User-level vs Session-level tool management
5. Application-level tools (default tools for all users)
6. Complete working examples

## Table of Contents

1. [How Claude/Cursor Handle Per-User MCP Tools](#how-claudecursor-handle-per-user-mcp-tools)
2. [Frontend-to-Backend Flow](#frontend-to-backend-flow)
3. [Google ADK Implementation](#google-adk-implementation)
4. [User-Level vs Session-Level Tools](#user-level-vs-session-level-tools)
5. [Application-Level MCP Tools](#application-level-mcp-tools-default-tools-for-all-users)
6. [Required Google ADK Packages](#required-google-adk-packages)
7. [Complete Examples](#complete-examples)

---

## How Claude/Cursor Handle Per-User MCP Tools

### Architecture Overview

In Claude Desktop and Cursor, each user has their own MCP configuration file:

```
~/.config/claude/claude_desktop_config.json  (Claude Desktop)
~/.cursor/mcp_config.json                    (Cursor)
```

### Key Characteristics

1. **Per-User Configuration**: Each user edits their own config file
2. **Frontend UI**: Users configure tools through the application UI
3. **Backend Loading**: Application loads tools from user's config when they start a chat
4. **Persistence**: Config persists across sessions
5. **Isolation**: User A's tools don't affect User B

### Example Claude Desktop Config

```json
{
  "mcpServers": {
    "filesystem": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-filesystem", "/home/user"]
    },
    "github": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-github"],
      "env": {
        "GITHUB_TOKEN": "user_specific_token"
      }
    }
  }
}
```

### How It Works

```
┌─────────────────────────────────────────────────────────┐
│ 1. User Opens Claude Desktop                            │
│    - Application reads user's config file                │
│    - Loads MCP servers from config                      │
└─────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────┐
│ 2. User Starts Chat                                      │
│    - Backend creates agent with user's MCP tools        │
│    - Tools are loaded from user's config                 │
└─────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────┐
│ 3. User Updates Config via UI                           │
│    - Frontend updates config file                       │
│    - Backend reloads tools for that user                 │
└─────────────────────────────────────────────────────────┘
```

---

## Frontend-to-Backend Flow

### Step-by-Step Flow

#### 1. User Configures Tools (Frontend)

```javascript
// Frontend: User adds MCP server via UI
const mcpConfig = {
  name: "filesystem",
  type: "stdio",
  command: "npx",
  args: ["-y", "@modelcontextprotocol/server-filesystem", "/home/user"]
};

// Frontend sends to backend
await fetch(`/api/users/${userId}/mcp-config`, {
  method: 'POST',
  body: JSON.stringify({ mcp_servers: [mcpConfig] })
});
```

#### 2. Backend Stores Config (User-Level State)

```python
# Backend: Store in user-level state
await tool_manager.set_user_mcp_config(
    user_id=user_id,
    mcp_servers=[mcp_config]
)

# This stores in: user:mcp_servers (user-level state)
# Persists across all sessions for this user
```

#### 3. User Starts Chat (Backend Loads Tools)

```python
# Backend: When user starts conversation
toolsets = await tool_manager.get_toolsets_for_user(user_id)

# Create agent with user's tools
agent = LlmAgent(
    model="gemini-2.0-flash",
    tools=toolsets  # User's specific tools
)
```

#### 4. Tools Are Used (Dynamic Loading)

```python
# When agent needs tools, they're loaded from user's config
# Local stdio servers auto-start
# Remote servers connect if running
tools = await toolset.get_tools()  # Loads from user's config
```

### Complete Flow Diagram

```
┌──────────────┐         ┌──────────────┐         ┌──────────────┐
│   Frontend   │────────▶│   Backend    │────────▶│  User State  │
│              │         │              │         │              │
│ User updates │  POST   │ Store config │  Save   │ user:mcp_    │
│ MCP config   │────────▶│ in user state│────────▶│ servers      │
└──────────────┘         └──────────────┘         └──────────────┘
                                                          │
                                                          │ Load
                                                          ↓
┌──────────────┐         ┌──────────────┐         ┌──────────────┐
│   Frontend   │────────▶│   Backend    │────────▶│   Agent      │
│              │         │              │         │              │
│ User starts  │  GET    │ Load tools   │ Create  │ With user's  │
│ chat         │────────▶│ from config  │────────▶│ MCP tools    │
└──────────────┘         └──────────────┘         └──────────────┘
```

---

## Google ADK Implementation

### Required Packages

To implement per-user MCP tool management, you need:

1. **`google.adk.sessions`**: For session and user management
2. **`google.adk.sessions.state`**: For storing user-level MCP configs
3. **`google.adk.tools.mcp_tool`**: For MCP tool integration
4. **`google.adk.agents`**: For creating agents with user-specific tools

### Architecture

```python
from google.adk.sessions import DatabaseSessionService
from google.adk.sessions.state import State
from google.adk.tools.mcp_tool import McpToolset
from google.adk.agents import LlmAgent

# 1. Session Service (manages users and sessions)
session_service = DatabaseSessionService(db_url="...")

# 2. Tool Manager (manages per-user MCP tools)
tool_manager = PerUserMCPToolManager(
    session_service=session_service,
    app_name="my_app"
)

# 3. Store user's MCP config in user-level state
await tool_manager.set_user_mcp_config(
    user_id="user_001",
    mcp_servers=[...]  # User's MCP server configs
)

# 4. Load tools when user starts chat
toolsets = await tool_manager.get_toolsets_for_user("user_001")

# 5. Create agent with user's tools
agent = LlmAgent(
    model="gemini-2.0-flash",
    tools=toolsets  # User-specific tools
)
```

### Key Components

#### 1. PerUserMCPToolManager

Manages MCP tools per user:

- **Stores config in user-level state**: `user:mcp_servers`
- **Loads tools dynamically**: Based on user's config
- **Caches toolsets**: For performance
- **Supports session-level tools**: Temporary tools per session

#### 2. User-Level State Storage

```python
# MCP config stored in user-level state
state["user:mcp_servers"] = [
    {
        "name": "filesystem",
        "type": "stdio",
        "command": "npx",
        "args": ["-y", "@modelcontextprotocol/server-filesystem", "/tmp"]
    }
]

# This persists across ALL sessions for this user
```

#### 3. Dynamic Tool Loading

```python
# Tools are loaded when needed
async def get_toolsets_for_user(self, user_id: str):
    # 1. Get user's config from user-level state
    mcp_config = await self.get_user_mcp_config(user_id)
    
    # 2. Create toolsets from config
    toolsets = []
    for server_config in mcp_config:
        toolset = create_toolset(server_config)
        toolsets.append(toolset)
    
    # 3. Return toolsets (local servers auto-start when used)
    return toolsets
```

---

## User-Level vs Session-Level Tools

### When to Use Each

#### User-Level Tools (Persistent)

**Stored in**: `user:mcp_servers` (user-level state)

**Use for**:
- Tools user wants in all their chats
- User's personal MCP servers
- Tools configured via settings/preferences
- Tools that persist across sessions

**Example**:
```python
# User configures filesystem tool in settings
# This tool is available in ALL their sessions
await tool_manager.set_user_mcp_config(
    user_id="user_001",
    mcp_servers=[{
        "name": "filesystem",
        "type": "stdio",
        "command": "npx",
        "args": ["-y", "@modelcontextprotocol/server-filesystem", "/home/user"]
    }]
)
```

#### Session-Level Tools (Temporary)

**Stored in**: `session_mcp_servers` (session-level state)

**Use for**:
- Tools added during a specific conversation
- Temporary tools for one chat
- Tools that don't persist after session ends
- Context-specific tools

**Example**:
```python
# User adds temporary tool during a chat
# This tool only exists for this session
await tool_manager.add_session_tool(
    user_id="user_001",
    session_id="session_123",
    server_config={
        "name": "temp_analysis",
        "type": "stdio",
        "command": "python",
        "args": ["-m", "analysis_tool"]
    }
)
```

### Combining Both

```python
# Get toolsets combines both user and session tools
toolsets = await tool_manager.get_toolsets_for_session(
    user_id="user_001",
    session_id="session_123"
)

# Returns:
# 1. User-level toolsets (from user:mcp_servers)
# 2. Session-level toolsets (from session_mcp_servers)
```

### State Hierarchy

```
Application State (app:)
    └── app:mcp_servers  ← Default tools for ALL users (like Claude/Cursor built-ins)
    └── Shared across all users
    
User State (user:)
    └── user:mcp_servers  ← User's MCP config (persists across sessions)
    └── user:preferences
    └── ...
    
Session State (no prefix)
    └── session_mcp_servers  ← Temporary tools (session only)
    └── conversation_context
    └── ...
```

---

## Application-Level MCP Tools (Default Tools for All Users)

### What Are Application-Level Tools?

**Application-level MCP tools** are **preloaded default tools** that are available to **ALL users** by default, similar to how Claude Desktop and Cursor offer built-in tools to all users.

### Real-World Examples

- **Claude Desktop**: Offers default tools like web search, code execution (if enabled)
- **Cursor**: Provides default IDE integration tools to all users
- **Your App**: Could offer default MCP tools like:
  - Google Search (for all users)
  - Company-specific API tools
  - Shared database connectors
  - Common utility tools

### Key Characteristics

1. **Available to Everyone**: All users get these tools automatically
2. **No User Configuration Needed**: Users don't need to add them
3. **Managed by Admins**: Only admins/developers can change app-level tools
4. **Persistent**: Stored in application-level state (`app:mcp_servers`)

### Implementation Example

```python
# Setup app-level tools (done once by admin/developer)
async def setup_app_level_tools(session_service, app_name):
    """Setup default MCP tools for all users."""
    
    # Get or create admin session to access app-level state
    admin_session = await session_service.get_session(
        app_name=app_name,
        user_id="admin",
        session_id="app_config"
    )
    
    if not admin_session:
        admin_session = await session_service.create_session(
            app_name=app_name,
            user_id="admin",
            session_id="app_config"
        )
    
    # Store in application-level state
    state = State(value=admin_session.state.value, delta=admin_session.state.delta)
    
    # App-level MCP servers (available to ALL users)
    state["app:mcp_servers"] = [
        {
            "name": "google_search",
            "type": "stdio",
            "command": "npx",
            "args": ["-y", "@modelcontextprotocol/server-google-search"],
            "enabled": True
        },
        {
            "name": "company_api",
            "type": "sse",
            "url": "https://api.company.com/mcp",
            "headers": {"Authorization": "Bearer company_token"},
            "enabled": True
        }
    ]
    
    # Save state
    await session_service.append_event(
        app_name=app_name,
        user_id="admin",
        session_id=admin_session.id,
        event={"type": "app_config_update", "data": state.delta}
    )

# Load app-level tools (available to all users)
async def get_app_level_toolsets(session_service, app_name, tool_manager) -> List[McpToolset]:
    """Get application-level MCP toolsets."""
    
    # Access app-level state
    admin_session = await session_service.get_session(
        app_name=app_name,
        user_id="admin",
        session_id="app_config"
    )
    
    if not admin_session:
        return []
    
    state = State(value=admin_session.state.value, delta=admin_session.state.delta)
    app_mcp_config = state.get("app:mcp_servers", [])
    
    # Create toolsets from app config
    toolsets = []
    for server_config_dict in app_mcp_config:
        if not server_config_dict.get("enabled", True):
            continue
        
        try:
            # Use tool_manager's methods to create toolsets
            # (implementation depends on your tool_manager structure)
            server_config = MCPServerConfig(**server_config_dict)
            # Create toolset based on type...
            # (See example code for full implementation)
        except Exception as e:
            logger.error(f"Error creating app-level toolset: {e}")
    
    return toolsets
```

### Combining All Three Levels

When creating an agent, combine tools from all three levels:

```python
async def get_all_toolsets_for_user(
    tool_manager: PerUserMCPToolManager,
    session_service: DatabaseSessionService,
    app_name: str,
    user_id: str,
    session_id: str
) -> List[McpToolset]:
    """Get toolsets from all three levels."""
    
    all_toolsets = []
    
    # 1. Application-level tools (default for all users)
    app_toolsets = await get_app_level_toolsets(session_service, app_name, tool_manager)
    all_toolsets.extend(app_toolsets)
    
    # 2. User-level tools (user's personal tools)
    user_toolsets = await tool_manager.get_toolsets_for_user(user_id)
    all_toolsets.extend(user_toolsets)
    
    # 3. Session-level tools (temporary tools)
    # Note: get_toolsets_for_session already includes user tools
    # We need to get only session-specific tools
    session = await session_service.get_session(app_name, user_id, session_id)
    if session:
        state = State(value=session.state.value, delta=session.state.delta)
        session_mcp_config = state.get("session_mcp_servers", [])
        for server_config_dict in session_mcp_config:
            # Create session toolsets...
            pass
    
    return all_toolsets

# Create agent with all tools
agent = LlmAgent(
    model="gemini-2.0-flash",
    tools=all_toolsets  # App + User + Session tools
)
```

### Tool Priority/Order

The order matters! Typically:

1. **Application-level** (lowest priority, can be overridden)
2. **User-level** (user's preferences override app defaults)
3. **Session-level** (highest priority, temporary overrides)

### When to Use Each Level

| Level | Use For | Example |
|-------|---------|---------|
| **Application** | Default tools for all users | Google Search, company APIs, shared utilities |
| **User** | User's personal tools | Personal filesystem access, user's API keys |
| **Session** | Temporary tools | One-time analysis, context-specific tools |

---

## Required Google ADK Packages

### 1. Sessions Package (`google.adk.sessions`)

**Purpose**: Manage users and sessions

**Key Classes**:
- `DatabaseSessionService`: Persistent session storage
- `Session`: Session data model

**Usage**:
```python
from google.adk.sessions import DatabaseSessionService

session_service = DatabaseSessionService(
    db_url="sqlite+aiosqlite:///sessions.db"
)

# Create session for user
session = await session_service.create_session(
    app_name="my_app",
    user_id="user_001",
    session_id="session_123"
)
```

### 2. State Management (`google.adk.sessions.state`)

**Purpose**: Store user-level MCP configurations

**Key Classes**:
- `State`: State management with scopes

**Usage**:
```python
from google.adk.sessions.state import State

# Access user-level state
state = State(value=session.state.value, delta=session.state.delta)

# Store MCP config in user-level state
state["user:mcp_servers"] = [
    {"name": "filesystem", "type": "stdio", ...}
]
```

### 3. MCP Tools (`google.adk.tools.mcp_tool`)

**Purpose**: MCP tool integration

**Key Classes**:
- `McpToolset`: MCP tool collection
- `StdioConnectionParams`, `SseConnectionParams`, etc.

**Usage**:
```python
from google.adk.tools.mcp_tool import McpToolset, StdioConnectionParams
from mcp import StdioServerParameters

toolset = McpToolset(
    connection_params=StdioConnectionParams(
        server_params=StdioServerParameters(
            command="npx",
            args=["-y", "@modelcontextprotocol/server-filesystem", "/tmp"]
        )
    )
)
```

### 4. Agents (`google.adk.agents`)

**Purpose**: Create agents with user-specific tools

**Key Classes**:
- `LlmAgent`: LLM-powered agent

**Usage**:
```python
from google.adk.agents import LlmAgent

agent = LlmAgent(
    model="gemini-2.0-flash",
    tools=user_toolsets  # User's specific tools
)
```

### Package Dependencies

```
google.adk.sessions
    ├── Requires: sqlalchemy>=2.0 (for DatabaseSessionService)
    └── Provides: Session management, state storage

google.adk.sessions.state
    ├── Part of: google.adk.sessions
    └── Provides: State scopes (app, user, session)

google.adk.tools.mcp_tool
    ├── Requires: mcp (MCP Python SDK)
    └── Provides: MCP tool integration

google.adk.agents
    └── Provides: Agent creation with tools
```

---

## Complete Examples

### Example 1: Basic Per-User MCP Tools

```python
import asyncio
from google.adk.sessions import DatabaseSessionService
from examples.mcp_per_user_tools import PerUserMCPToolManager, MCPConfigAPI

async def basic_example():
    # Setup
    session_service = DatabaseSessionService(
        db_url="sqlite+aiosqlite:///users.db"
    )
    
    tool_manager = PerUserMCPToolManager(
        session_service=session_service,
        app_name="my_app"
    )
    
    api = MCPConfigAPI(tool_manager)
    
    # User 1 configures their tools
    user1_config = [
        {
            "name": "filesystem",
            "type": "stdio",
            "command": "npx",
            "args": ["-y", "@modelcontextprotocol/server-filesystem", "/tmp"]
        }
    ]
    
    await api.update_user_mcp_config("user_001", user1_config)
    
    # User 1 starts chat (tools loaded from their config)
    agent = await api.create_agent_for_user(
        user_id="user_001",
        session_id="session_001"
    )
    
    print(f"Agent created with {len(agent.tools)} toolsets")

asyncio.run(basic_example())
```

### Example 2: Multiple Users with Different Tools

```python
async def multi_user_example():
    session_service = DatabaseSessionService(
        db_url="sqlite+aiosqlite:///multi_user.db"
    )
    
    tool_manager = PerUserMCPToolManager(session_service, "my_app")
    api = MCPConfigAPI(tool_manager)
    
    # User 1: Filesystem tools
    await api.update_user_mcp_config("user_001", [
        {"name": "filesystem", "type": "stdio", "command": "npx",
         "args": ["-y", "@modelcontextprotocol/server-filesystem", "/home/user1"]}
    ])
    
    # User 2: GitHub tools
    await api.update_user_mcp_config("user_002", [
        {"name": "github", "type": "sse", "url": "http://localhost:8000/mcp",
         "headers": {"Authorization": "Bearer token_002"}}
    ])
    
    # User 3: Google Maps tools
    await api.update_user_mcp_config("user_003", [
        {"name": "maps", "type": "stdio", "command": "npx",
         "args": ["-y", "@modelcontextprotocol/server-google-maps"],
         "env": {"GOOGLE_MAPS_API_KEY": "key_003"}}
    ])
    
    # Each user gets their own tools
    agent1 = await api.create_agent_for_user("user_001", "session_001")
    agent2 = await api.create_agent_for_user("user_002", "session_002")
    agent3 = await api.create_agent_for_user("user_003", "session_003")
    
    print(f"User 1: {len(agent1.tools)} toolsets")
    print(f"User 2: {len(agent2.tools)} toolsets")
    print(f"User 3: {len(agent3.tools)} toolsets")

asyncio.run(multi_user_example())
```

### Example 3: User + Session Level Tools

```python
async def user_and_session_example():
    session_service = DatabaseSessionService(
        db_url="sqlite+aiosqlite:///combined.db"
    )
    
    tool_manager = PerUserMCPToolManager(session_service, "my_app")
    api = MCPConfigAPI(tool_manager)
    
    user_id = "user_001"
    session_id = "session_001"
    
    # User-level tool (persists across sessions)
    await api.update_user_mcp_config(user_id, [
        {"name": "filesystem", "type": "stdio", "command": "npx",
         "args": ["-y", "@modelcontextprotocol/server-filesystem", "/home/user"]}
    ])
    
    # Session-level tool (temporary, only for this session)
    await tool_manager.add_session_tool(
        user_id=user_id,
        session_id=session_id,
        server_config={
            "name": "temp_analysis",
            "type": "stdio",
            "command": "python",
            "args": ["-m", "analysis_tool"]
        }
    )
    
    # Agent gets both user and session tools
    agent = await api.create_agent_for_user(user_id, session_id)
    
    print(f"Agent has {len(agent.tools)} toolsets (user + session)")

asyncio.run(user_and_session_example())
```

### Example 4: With Runner (Production)

```python
from google.adk.runners import Runner

async def runner_example():
    session_service = DatabaseSessionService(
        db_url="sqlite+aiosqlite:///runner.db"
    )
    
    tool_manager = PerUserMCPToolManager(session_service, "my_app")
    api = MCPConfigAPI(tool_manager)
    
    user_id = "user_001"
    session_id = "session_001"
    
    # Configure user's tools
    await api.update_user_mcp_config(user_id, [
        {"name": "filesystem", "type": "stdio", "command": "npx",
         "args": ["-y", "@modelcontextprotocol/server-filesystem", "/tmp"]}
    ])
    
    # Create agent with user's tools
    agent = await api.create_agent_for_user(user_id, session_id)
    
    # Create runner
    runner = Runner(
        agent=agent,
        session_service=session_service
    )
    
    # User interacts (tools loaded from user's config)
    async for event in runner.run(
        "List files in /tmp",
        app_name="my_app",
        user_id=user_id,
        session_id=session_id
    ):
        if hasattr(event, 'content'):
            print(event.content)

asyncio.run(runner_example())
```

---

## Summary

### Key Takeaways

1. **User-Level State**: Store MCP configs in `user:mcp_servers` (persists across sessions)
2. **Session-Level State**: Store temporary tools in `session_mcp_servers` (session only)
3. **Dynamic Loading**: Tools are loaded when user starts chat, not at app startup
4. **Isolation**: Each user has their own tools, no interference
5. **Frontend Integration**: Frontend updates config → Backend stores in user state → Tools loaded on demand

### Required Packages

- **`google.adk.sessions`**: User and session management
- **`google.adk.sessions.state`**: State storage (user-level, session-level)
- **`google.adk.tools.mcp_tool`**: MCP tool integration
- **`google.adk.agents`**: Agent creation

### Architecture Pattern

```
Frontend → Backend API → User State → Tool Manager → Agent with User's Tools
```

### State Scopes

- **User-Level** (`user:mcp_servers`): Persistent tools for all user's sessions
- **Session-Level** (`session_mcp_servers`): Temporary tools for one session
- **Application-Level** (`app:mcp_servers`): Shared tools for all users (optional)

---

## Related Documentation

- [MCP Dynamic Configuration](16-MCP-Dynamic-Configuration-and-Server-Management.md) - Server management
- [MCP Tools Dynamic Loading](15-MCP-Tools-Dynamic-Loading.md) - General MCP tools
- [Sessions Package](07-Sessions-Package.md) - Session management
- [State Management](11-State-Management.md) - State scopes and management
- [Examples](../examples/mcp_per_user_tools.py) - Complete implementation

---

**Last Updated:** 2025-01-26  
**Google ADK Version:** 1.22.1
