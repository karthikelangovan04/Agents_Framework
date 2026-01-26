"""
Per-User MCP Tool Management for Google ADK

This example demonstrates how to implement Claude/Cursor-like per-user MCP tool
configuration where each user can have their own set of MCP tools.

Key Concepts:
1. User-level state stores MCP server configurations
2. Tools are loaded dynamically based on user's configuration
3. Frontend updates config → Backend loads tools for that user
4. Session-level tool management for temporary tools
"""

import asyncio
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict

from google.adk.agents import LlmAgent
from google.adk.sessions import DatabaseSessionService, Session
from google.adk.sessions.state import State
from google.adk.runners import Runner
from google.adk.tools.mcp_tool import (
    McpToolset,
    StdioConnectionParams,
    SseConnectionParams,
    StreamableHTTPConnectionParams,
)
from mcp import StdioServerParameters

# Import the dynamic config manager
import sys
from pathlib import Path
examples_dir = Path(__file__).parent
sys.path.insert(0, str(examples_dir))
from mcp_dynamic_config import MCPServerConfig

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PerUserMCPToolManager:
    """
    Manages MCP tools per user, similar to how Claude/Cursor work.
    
    Architecture:
    - User-level state stores MCP server configurations
    - Tools are loaded dynamically when user interacts
    - Frontend can update user's MCP config
    - Backend loads tools based on user's config
    """
    
    def __init__(self, session_service: DatabaseSessionService, app_name: str):
        """
        Initialize per-user MCP tool manager.
        
        Args:
            session_service: Session service for state management
            app_name: Application name
        """
        self.session_service = session_service
        self.app_name = app_name
        self._user_toolsets_cache: Dict[str, List[McpToolset]] = {}
    
    async def get_user_mcp_config(self, user_id: str) -> List[Dict]:
        """
        Get MCP server configuration for a user from user-level state.
        
        This is stored in user-level state so it persists across sessions.
        """
        # Get or create a session to access state
        # We use a temporary session just to access user state
        temp_session = await self.session_service.get_session(
            app_name=self.app_name,
            user_id=user_id,
            session_id="temp_state_access"
        )
        
        if not temp_session:
            temp_session = await self.session_service.create_session(
                app_name=self.app_name,
                user_id=user_id,
                session_id="temp_state_access"
            )
        
        # Access user-level state
        state = State(value=temp_session.state.value, delta=temp_session.state.delta)
        
        # Get MCP config from user state
        mcp_config_key = "user:mcp_servers"
        mcp_config = state.get(mcp_config_key, [])
        
        return mcp_config if isinstance(mcp_config, list) else []
    
    async def set_user_mcp_config(
        self, 
        user_id: str, 
        mcp_servers: List[Dict]
    ) -> bool:
        """
        Set MCP server configuration for a user.
        
        This is called when frontend updates user's MCP config.
        Stores in user-level state so it persists across sessions.
        """
        # Get or create a session to update state
        session = await self.session_service.get_session(
            app_name=self.app_name,
            user_id=user_id,
            session_id="temp_state_access"
        )
        
        if not session:
            session = await self.session_service.create_session(
                app_name=self.app_name,
                user_id=user_id,
                session_id="temp_state_access"
            )
        
        # Update user-level state
        state = State(value=session.state.value, delta=session.state.delta)
        state["user:mcp_servers"] = mcp_servers
        
        # Save state by appending an event (state is persisted with events)
        await self.session_service.append_event(
            app_name=self.app_name,
            user_id=user_id,
            session_id=session.id,
            event={
                "type": "state_update",
                "data": {"mcp_servers": mcp_servers}
            }
        )
        
        # Clear cache for this user
        if user_id in self._user_toolsets_cache:
            # Close existing toolsets
            for toolset in self._user_toolsets_cache[user_id]:
                try:
                    await toolset.close()
                except Exception as e:
                    logger.warning(f"Error closing toolset: {e}")
            del self._user_toolsets_cache[user_id]
        
        logger.info(f"Updated MCP config for user {user_id}: {len(mcp_servers)} servers")
        return True
    
    async def get_toolsets_for_user(self, user_id: str) -> List[McpToolset]:
        """
        Get MCP toolsets for a user based on their configuration.
        
        This is called when creating an agent for the user.
        Tools are loaded dynamically from user's config.
        """
        # Check cache first
        if user_id in self._user_toolsets_cache:
            return self._user_toolsets_cache[user_id]
        
        # Get user's MCP config
        mcp_config = await self.get_user_mcp_config(user_id)
        
        if not mcp_config:
            logger.info(f"No MCP config found for user {user_id}")
            return []
        
        # Create toolsets from config
        toolsets = []
        for server_config_dict in mcp_config:
            try:
                # Convert dict to MCPServerConfig
                server_config = MCPServerConfig(**server_config_dict)
                
                # Create toolset based on type
                if server_config.type == 'stdio':
                    toolset = self._create_stdio_toolset(server_config)
                elif server_config.type == 'sse':
                    toolset = self._create_sse_toolset(server_config)
                elif server_config.type == 'http':
                    toolset = self._create_http_toolset(server_config)
                else:
                    logger.warning(f"Unknown server type: {server_config.type}")
                    continue
                
                toolsets.append(toolset)
                logger.info(f"Created toolset for user {user_id}: {server_config.name}")
                
            except Exception as e:
                logger.error(f"Error creating toolset for user {user_id}: {e}")
                continue
        
        # Cache toolsets
        self._user_toolsets_cache[user_id] = toolsets
        
        return toolsets
    
    def _create_stdio_toolset(self, config: MCPServerConfig) -> McpToolset:
        """Create stdio-based toolset."""
        server_params = StdioServerParameters(
            command=config.command,
            args=config.args or [],
            env=config.env or {},
        )
        
        connection_params = StdioConnectionParams(
            server_params=server_params,
            timeout=config.timeout
        )
        
        return McpToolset(
            connection_params=connection_params,
            tool_filter=config.tool_filter,
            tool_name_prefix=config.tool_name_prefix
        )
    
    def _create_sse_toolset(self, config: MCPServerConfig) -> McpToolset:
        """Create SSE-based toolset."""
        connection_params = SseConnectionParams(
            url=config.url,
            headers=config.headers,
            timeout=config.timeout,
            sse_read_timeout=config.sse_read_timeout
        )
        
        return McpToolset(
            connection_params=connection_params,
            tool_filter=config.tool_filter,
            tool_name_prefix=config.tool_name_prefix
        )
    
    def _create_http_toolset(self, config: MCPServerConfig) -> McpToolset:
        """Create HTTP-based toolset."""
        connection_params = StreamableHTTPConnectionParams(
            url=config.url,
            headers=config.headers,
            timeout=config.timeout,
            sse_read_timeout=config.sse_read_timeout
        )
        
        return McpToolset(
            connection_params=connection_params,
            tool_filter=config.tool_filter,
            tool_name_prefix=config.tool_name_prefix
        )
    
    async def get_toolsets_for_session(
        self, 
        user_id: str, 
        session_id: str
    ) -> List[McpToolset]:
        """
        Get toolsets for a specific session.
        
        Combines:
        1. User-level toolsets (from user's MCP config)
        2. Session-level toolsets (temporary tools for this session)
        """
        # Get user-level toolsets
        user_toolsets = await self.get_toolsets_for_user(user_id)
        
        # Get session-level toolsets (if any)
        session = await self.session_service.get_session(
            app_name=self.app_name,
            user_id=user_id,
            session_id=session_id
        )
        
        session_toolsets = []
        if session:
            state = State(value=session.state.value, delta=session.state.delta)
            session_mcp_config = state.get("session_mcp_servers", [])
            
            # Create toolsets from session config
            for server_config_dict in session_mcp_config:
                try:
                    server_config = MCPServerConfig(**server_config_dict)
                    if server_config.type == 'stdio':
                        toolset = self._create_stdio_toolset(server_config)
                    elif server_config.type == 'sse':
                        toolset = self._create_sse_toolset(server_config)
                    elif server_config.type == 'http':
                        toolset = self._create_http_toolset(server_config)
                    else:
                        continue
                    session_toolsets.append(toolset)
                except Exception as e:
                    logger.error(f"Error creating session toolset: {e}")
        
        # Combine user and session toolsets
        all_toolsets = user_toolsets + session_toolsets
        
        return all_toolsets
    
    async def add_session_tool(
        self,
        user_id: str,
        session_id: str,
        server_config: Dict
    ) -> bool:
        """
        Add a temporary tool to a specific session.
        
        This is useful for session-specific tools that don't persist.
        """
        session = await self.session_service.get_session(
            app_name=self.app_name,
            user_id=user_id,
            session_id=session_id
        )
        
        if not session:
            session = await self.session_service.create_session(
                app_name=self.app_name,
                user_id=user_id,
                session_id=session_id
            )
        
        # Get current session MCP config
        state = State(value=session.state.value, delta=session.state.delta)
        session_mcp_config = state.get("session_mcp_servers", [])
        
        # Add new server
        session_mcp_config.append(server_config)
        state["session_mcp_servers"] = session_mcp_config
        
        # Save state
        await self.session_service.append_event(
            app_name=self.app_name,
            user_id=user_id,
            session_id=session_id,
            event={
                "type": "session_tool_added",
                "data": {"server": server_config}
            }
        )
        
        logger.info(f"Added session tool for {user_id}/{session_id}")
        return True
    
    async def cleanup_user_cache(self, user_id: str):
        """Cleanup cached toolsets for a user."""
        if user_id in self._user_toolsets_cache:
            for toolset in self._user_toolsets_cache[user_id]:
                try:
                    await toolset.close()
                except Exception as e:
                    logger.warning(f"Error closing toolset: {e}")
            del self._user_toolsets_cache[user_id]


# Application-Level MCP Tools Manager
class AppLevelMCPToolManager:
    """
    Manages application-level MCP tools (default tools for all users).
    
    These are like built-in tools in Claude/Cursor that all users get by default.
    Stored in application-level state (app:mcp_servers).
    """
    
    def __init__(self, session_service: DatabaseSessionService, app_name: str):
        self.session_service = session_service
        self.app_name = app_name
        self._app_toolsets_cache: Optional[List[McpToolset]] = None
    
    async def get_app_mcp_config(self) -> List[Dict]:
        """Get application-level MCP config from app-level state."""
        # Use admin session to access app-level state
        admin_session = await self.session_service.get_session(
            app_name=self.app_name,
            user_id="admin",
            session_id="app_config"
        )
        
        if not admin_session:
            return []
        
        state = State(value=admin_session.state.value, delta=admin_session.state.delta)
        app_mcp_config = state.get("app:mcp_servers", [])
        
        return app_mcp_config if isinstance(app_mcp_config, list) else []
    
    async def set_app_mcp_config(self, mcp_servers: List[Dict]) -> bool:
        """
        Set application-level MCP config.
        
        This should only be called by admins/developers.
        These tools are available to ALL users by default.
        """
        # Get or create admin session
        admin_session = await self.session_service.get_session(
            app_name=self.app_name,
            user_id="admin",
            session_id="app_config"
        )
        
        if not admin_session:
            admin_session = await self.session_service.create_session(
                app_name=self.app_name,
                user_id="admin",
                session_id="app_config"
            )
        
        # Update app-level state
        state = State(value=admin_session.state.value, delta=admin_session.state.delta)
        state["app:mcp_servers"] = mcp_servers
        
        # Save state
        await self.session_service.append_event(
            app_name=self.app_name,
            user_id="admin",
            session_id=admin_session.id,
            event={
                "type": "app_config_update",
                "data": {"mcp_servers": mcp_servers}
            }
        )
        
        # Clear cache
        self._app_toolsets_cache = None
        
        logger.info(f"Updated app-level MCP config: {len(mcp_servers)} servers")
        return True
    
    async def get_app_toolsets(self) -> List[McpToolset]:
        """Get application-level toolsets (available to all users)."""
        # Check cache
        if self._app_toolsets_cache is not None:
            return self._app_toolsets_cache
        
        # Get app config
        app_config = await self.get_app_mcp_config()
        
        if not app_config:
            self._app_toolsets_cache = []
            return []
        
        # Create toolsets
        toolsets = []
        for server_config_dict in app_config:
            if not server_config_dict.get("enabled", True):
                continue
            
            try:
                server_config = MCPServerConfig(**server_config_dict)
                
                if server_config.type == 'stdio':
                    toolset = self._create_stdio_toolset(server_config)
                elif server_config.type == 'sse':
                    toolset = self._create_sse_toolset(server_config)
                elif server_config.type == 'http':
                    toolset = self._create_http_toolset(server_config)
                else:
                    continue
                
                toolsets.append(toolset)
            except Exception as e:
                logger.error(f"Error creating app-level toolset: {e}")
        
        self._app_toolsets_cache = toolsets
        return toolsets
    
    def _create_stdio_toolset(self, config: MCPServerConfig) -> McpToolset:
        server_params = StdioServerParameters(
            command=config.command,
            args=config.args or [],
            env=config.env or {},
        )
        connection_params = StdioConnectionParams(
            server_params=server_params,
            timeout=config.timeout
        )
        return McpToolset(
            connection_params=connection_params,
            tool_filter=config.tool_filter,
            tool_name_prefix=config.tool_name_prefix
        )
    
    def _create_sse_toolset(self, config: MCPServerConfig) -> McpToolset:
        connection_params = SseConnectionParams(
            url=config.url,
            headers=config.headers,
            timeout=config.timeout,
            sse_read_timeout=config.sse_read_timeout
        )
        return McpToolset(
            connection_params=connection_params,
            tool_filter=config.tool_filter,
            tool_name_prefix=config.tool_name_prefix
        )
    
    def _create_http_toolset(self, config: MCPServerConfig) -> McpToolset:
        connection_params = StreamableHTTPConnectionParams(
            url=config.url,
            headers=config.headers,
            timeout=config.timeout,
            sse_read_timeout=config.sse_read_timeout
        )
        return McpToolset(
            connection_params=connection_params,
            tool_filter=config.tool_filter,
            tool_name_prefix=config.tool_name_prefix
        )


# Example: Frontend-to-Backend Flow
class MCPConfigAPI:
    """
    API endpoints for managing per-user MCP configurations.
    
    This simulates how Claude/Cursor handle frontend updates.
    """
    
    def __init__(self, tool_manager: PerUserMCPToolManager):
        self.tool_manager = tool_manager
    
    async def update_user_mcp_config(
        self,
        user_id: str,
        mcp_servers: List[Dict]
    ) -> Dict:
        """
        Endpoint: POST /users/{user_id}/mcp-config
        
        Frontend calls this when user updates their MCP configuration.
        """
        success = await self.tool_manager.set_user_mcp_config(user_id, mcp_servers)
        
        return {
            "success": success,
            "user_id": user_id,
            "servers_count": len(mcp_servers)
        }
    
    async def get_user_mcp_config(self, user_id: str) -> Dict:
        """
        Endpoint: GET /users/{user_id}/mcp-config
        
        Frontend calls this to get user's current MCP configuration.
        """
        config = await self.tool_manager.get_user_mcp_config(user_id)
        
        return {
            "user_id": user_id,
            "mcp_servers": config
        }
    
    async def create_agent_for_user(
        self,
        user_id: str,
        session_id: str,
        model: str = "gemini-2.0-flash",
        app_tool_manager: Optional[AppLevelMCPToolManager] = None
    ) -> LlmAgent:
        """
        Create an agent with user's MCP tools.
        
        This is called when user starts a conversation.
        Tools are loaded dynamically based on user's config.
        
        Args:
            user_id: User identifier
            session_id: Session identifier
            model: LLM model to use
            app_tool_manager: Optional app-level tool manager for default tools
        """
        all_toolsets = []
        
        # 1. Get app-level toolsets (default tools for all users)
        if app_tool_manager:
            app_toolsets = await app_tool_manager.get_app_toolsets()
            all_toolsets.extend(app_toolsets)
            logger.info(f"Added {len(app_toolsets)} app-level toolsets")
        
        # 2. Get user-level and session-level toolsets
        user_session_toolsets = await self.tool_manager.get_toolsets_for_session(
            user_id=user_id,
            session_id=session_id
        )
        all_toolsets.extend(user_session_toolsets)
        
        # Create agent with all tools (app + user + session)
        agent = LlmAgent(
            model=model,
            name=f"user_{user_id}_agent",
            tools=all_toolsets
        )
        
        logger.info(
            f"Created agent for user {user_id} with {len(all_toolsets)} MCP toolsets "
            f"({len(app_toolsets) if app_tool_manager else 0} app-level, "
            f"{len(user_session_toolsets)} user/session-level)"
        )
        
        return agent


# Example Usage
async def example_per_user_mcp_tools():
    """Complete example showing per-user MCP tool management."""
    
    # Setup session service (using SQLite for simplicity)
    session_service = DatabaseSessionService(
        db_url="sqlite+aiosqlite:///per_user_mcp.db"
    )
    
    app_name = "mcp_app"
    
    # Initialize tool manager
    tool_manager = PerUserMCPToolManager(
        session_service=session_service,
        app_name=app_name
    )
    
    # Initialize API
    api = MCPConfigAPI(tool_manager)
    
    # Example: User 1 configures their MCP tools (via frontend)
    user1_id = "user_001"
    
    user1_mcp_config = [
        {
            "name": "filesystem",
            "type": "stdio",
            "enabled": True,
            "command": "npx",
            "args": ["-y", "@modelcontextprotocol/server-filesystem", "/tmp"],
            "tool_filter": ["read_file", "list_directory"]
        },
        {
            "name": "github",
            "type": "sse",
            "enabled": True,
            "url": "http://localhost:8000/mcp",
            "headers": {"Authorization": "Bearer github_token_123"}
        }
    ]
    
    # Frontend → Backend: Update user's MCP config
    result = await api.update_user_mcp_config(user1_id, user1_mcp_config)
    print(f"✓ User 1 config updated: {result}")
    
    # Example: User 2 configures different MCP tools
    user2_id = "user_002"
    
    user2_mcp_config = [
        {
            "name": "google_maps",
            "type": "stdio",
            "enabled": True,
            "command": "npx",
            "args": ["-y", "@modelcontextprotocol/server-google-maps"],
            "env": {"GOOGLE_MAPS_API_KEY": "maps_api_key_456"}
        }
    ]
    
    # Frontend → Backend: Update user 2's MCP config
    result = await api.update_user_mcp_config(user2_id, user2_mcp_config)
    print(f"✓ User 2 config updated: {result}")
    
    # Example: User 1 starts a conversation
    session1_id = "session_001"
    agent1 = await api.create_agent_for_user(
        user_id=user1_id,
        session_id=session1_id
    )
    print(f"✓ Agent for User 1 created with {len(agent1.tools)} toolsets")
    
    # Example: User 2 starts a conversation
    session2_id = "session_002"
    agent2 = await api.create_agent_for_user(
        user_id=user2_id,
        session_id=session2_id
    )
    print(f"✓ Agent for User 2 created with {len(agent2.tools)} toolsets")
    
    # Example: Add temporary session tool
    session_tool = {
        "name": "temp_tool",
        "type": "stdio",
        "command": "npx",
        "args": ["-y", "@modelcontextprotocol/server-filesystem", "/var/tmp"]
    }
    
    await tool_manager.add_session_tool(
        user_id=user1_id,
        session_id=session1_id,
        server_config=session_tool
    )
    print(f"✓ Added temporary tool to User 1's session")
    
    # Verify: Get user configs
    user1_config = await api.get_user_mcp_config(user1_id)
    user2_config = await api.get_user_mcp_config(user2_id)
    
    print(f"\nUser 1 MCP Config: {len(user1_config)} servers")
    print(f"User 2 MCP Config: {len(user2_config)} servers")
    
    # Cleanup
    await tool_manager.cleanup_user_cache(user1_id)
    await tool_manager.cleanup_user_cache(user2_id)


# Example: Using with Runner
async def example_with_runner():
    """Example showing per-user MCP tools with Runner."""
    
    session_service = DatabaseSessionService(
        db_url="sqlite+aiosqlite:///per_user_mcp_runner.db"
    )
    
    app_name = "mcp_app"
    tool_manager = PerUserMCPToolManager(session_service, app_name)
    api = MCPConfigAPI(tool_manager)
    
    user_id = "user_003"
    session_id = "session_003"
    
    # User configures their tools
    user_config = [
        {
            "name": "filesystem",
            "type": "stdio",
            "command": "npx",
            "args": ["-y", "@modelcontextprotocol/server-filesystem", "/tmp"]
        }
    ]
    
    await api.update_user_mcp_config(user_id, user_config)
    
    # Create agent with user's tools
    agent = await api.create_agent_for_user(user_id, session_id)
    
    # Create runner with session service
    runner = Runner(
        agent=agent,
        session_service=session_service
    )
    
    # User interacts with agent (tools are loaded from user's config)
    async for event in runner.run(
        "List files in /tmp",
        app_name=app_name,
        user_id=user_id,
        session_id=session_id
    ):
        if hasattr(event, 'content'):
            print(event.content)


if __name__ == "__main__":
    print("=" * 60)
    print("Per-User MCP Tool Management Example")
    print("=" * 60)
    
    asyncio.run(example_per_user_mcp_tools())
    
    print("\n" + "=" * 60)
    print("Example with Runner")
    print("=" * 60)
    
    # Uncomment to run runner example
    # asyncio.run(example_with_runner())


# Example: Application-Level Tools
async def example_app_level_tools():
    """Example showing application-level MCP tools (default tools for all users)."""
    
    session_service = DatabaseSessionService(
        db_url="sqlite+aiosqlite:///app_level_tools.db"
    )
    
    app_name = "mcp_app"
    
    # Initialize app-level tool manager
    app_tool_manager = AppLevelMCPToolManager(
        session_service=session_service,
        app_name=app_name
    )
    
    # Setup app-level tools (done once by admin)
    app_level_config = [
        {
            "name": "google_search",
            "type": "stdio",
            "enabled": True,
            "command": "npx",
            "args": ["-y", "@modelcontextprotocol/server-google-search"]
        },
        {
            "name": "company_api",
            "type": "sse",
            "enabled": True,
            "url": "http://localhost:8000/mcp",
            "headers": {"Authorization": "Bearer company_token"}
        }
    ]
    
    await app_tool_manager.set_app_mcp_config(app_level_config)
    print(f"✓ App-level tools configured: {len(app_level_config)} servers")
    
    # Initialize user tool manager
    user_tool_manager = PerUserMCPToolManager(session_service, app_name)
    api = MCPConfigAPI(user_tool_manager)
    
    # User 1 configures their personal tools
    user1_id = "user_001"
    user1_config = [
        {
            "name": "filesystem",
            "type": "stdio",
            "command": "npx",
            "args": ["-y", "@modelcontextprotocol/server-filesystem", "/home/user1"]
        }
    ]
    await api.update_user_mcp_config(user1_id, user1_config)
    
    # User 1 starts chat - gets BOTH app-level AND user-level tools
    agent1 = await api.create_agent_for_user(
        user_id=user1_id,
        session_id="session_001",
        app_tool_manager=app_tool_manager
    )
    print(f"✓ User 1 agent created with {len(agent1.tools)} toolsets")
    print(f"  (App-level: 2, User-level: 1)")
    
    # User 2 doesn't configure any personal tools
    user2_id = "user_002"
    
    # User 2 starts chat - gets ONLY app-level tools
    agent2 = await api.create_agent_for_user(
        user_id=user2_id,
        session_id="session_002",
        app_tool_manager=app_tool_manager
    )
    print(f"✓ User 2 agent created with {len(agent2.tools)} toolsets")
    print(f"  (App-level: 2, User-level: 0)")
    
    print("\n" + "=" * 60)
    print("Application-level tools are available to ALL users!")
    print("=" * 60)
