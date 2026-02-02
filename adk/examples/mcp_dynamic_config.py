"""
Dynamic MCP Configuration System for Google ADK

This example demonstrates how to create a Claude/Cursor-like dynamic MCP configuration
system that:
1. Loads MCP servers from a JSON configuration file
2. Automatically starts local stdio servers when needed
3. Connects to remote SSE/HTTP servers
4. Supports runtime toolset management
"""

import asyncio
import json
import logging
import os
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict

from google.adk.agents import LlmAgent
from google.adk.tools.mcp_tool import (
    McpToolset,
    StdioConnectionParams,
    SseConnectionParams,
    StreamableHTTPConnectionParams,
)
from mcp import StdioServerParameters

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


@dataclass
class MCPServerConfig:
    """Configuration for a single MCP server."""
    name: str
    type: str  # 'stdio', 'sse', or 'http'
    enabled: bool = True
    
    # Stdio-specific
    command: Optional[str] = None
    args: Optional[List[str]] = None
    env: Optional[Dict[str, str]] = None
    working_dir: Optional[str] = None
    timeout: float = 5.0
    
    # SSE/HTTP-specific
    url: Optional[str] = None
    headers: Optional[Dict[str, str]] = None
    sse_read_timeout: float = 300.0
    
    # Tool filtering
    tool_filter: Optional[List[str]] = None
    tool_name_prefix: Optional[str] = None
    
    # Authentication
    auth_scheme: Optional[str] = None
    auth_credential: Optional[Dict] = None


class DynamicMCPConfigManager:
    """
    Manages dynamic MCP server configuration similar to Claude Desktop.
    
    This class:
    - Loads configuration from JSON files
    - Automatically starts local stdio servers when needed
    - Manages connections to remote servers
    - Provides toolsets for agents
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize the MCP config manager.
        
        Args:
            config_path: Path to JSON configuration file. 
                        Defaults to ~/.adk/mcp_servers.json
        """
        if config_path is None:
            config_dir = Path.home() / ".adk"
            config_dir.mkdir(exist_ok=True)
            config_path = str(config_dir / "mcp_servers.json")
        
        self.config_path = Path(config_path)
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        self._servers: Dict[str, MCPServerConfig] = {}
        self._toolsets: Dict[str, McpToolset] = {}
        self._load_config()
    
    def _load_config(self):
        """Load configuration from JSON file."""
        if not self.config_path.exists():
            logger.info(f"Config file not found at {self.config_path}, creating default")
            self._save_config()
            return
        
        try:
            with open(self.config_path, 'r') as f:
                data = json.load(f)
            
            # Load servers from config
            servers_data = data.get('mcpServers', {})
            for name, server_data in servers_data.items():
                server_config = MCPServerConfig(
                    name=name,
                    **server_data
                )
                self._servers[name] = server_config
            
            logger.info(f"Loaded {len(self._servers)} MCP server configurations")
        except Exception as e:
            logger.error(f"Error loading config: {e}")
            self._servers = {}
    
    def _save_config(self):
        """Save current configuration to JSON file."""
        config_data = {
            'mcpServers': {
                name: {
                    k: v for k, v in asdict(server).items() 
                    if v is not None and k != 'name'
                }
                for name, server in self._servers.items()
            }
        }
        
        with open(self.config_path, 'w') as f:
            json.dump(config_data, f, indent=2)
        
        logger.info(f"Saved configuration to {self.config_path}")
    
    def add_server(self, config: MCPServerConfig):
        """Add or update an MCP server configuration."""
        self._servers[config.name] = config
        self._save_config()
        
        # Clear cached toolset for this server
        if config.name in self._toolsets:
            del self._toolsets[config.name]
    
    def remove_server(self, name: str):
        """Remove an MCP server configuration."""
        if name in self._servers:
            del self._servers[name]
            self._save_config()
        
        # Close and remove toolset
        if name in self._toolsets:
            toolset = self._toolsets[name]
            asyncio.create_task(toolset.close())
            del self._toolsets[name]
    
    def get_server_config(self, name: str) -> Optional[MCPServerConfig]:
        """Get configuration for a specific server."""
        return self._servers.get(name)
    
    def list_servers(self) -> List[str]:
        """List all configured server names."""
        return list(self._servers.keys())
    
    async def create_toolset(self, name: str) -> Optional[McpToolset]:
        """
        Create a toolset for a configured MCP server.
        
        For stdio servers, this will automatically start the server process
        when the toolset is first used (lazy loading).
        
        For SSE/HTTP servers, this assumes the server is already running.
        """
        if name in self._toolsets:
            return self._toolsets[name]
        
        config = self._servers.get(name)
        if not config or not config.enabled:
            logger.warning(f"Server {name} not found or disabled")
            return None
        
        try:
            toolset = await self._create_toolset_from_config(config)
            self._toolsets[name] = toolset
            logger.info(f"Created toolset for server: {name}")
            return toolset
        except Exception as e:
            logger.error(f"Error creating toolset for {name}: {e}")
            return None
    
    async def _create_toolset_from_config(self, config: MCPServerConfig) -> McpToolset:
        """Create a toolset from server configuration."""
        if config.type == 'stdio':
            return self._create_stdio_toolset(config)
        elif config.type == 'sse':
            return self._create_sse_toolset(config)
        elif config.type == 'http':
            return self._create_http_toolset(config)
        else:
            raise ValueError(f"Unknown server type: {config.type}")
    
    def _create_stdio_toolset(self, config: MCPServerConfig) -> McpToolset:
        """
        Create a stdio-based toolset.
        
        IMPORTANT: The stdio server process is NOT started here.
        It will be automatically started by the MCP SDK when:
        1. get_tools() is called on the toolset
        2. A tool from the toolset is invoked
        
        The stdio_client from mcp.client.stdio handles process management:
        - Starts the process with the specified command and args
        - Manages stdin/stdout streams
        - Handles process lifecycle
        """
        if not config.command:
            raise ValueError(f"Stdio server {config.name} requires 'command' field")
        
        server_params = StdioServerParameters(
            command=config.command,
            args=config.args or [],
            env=config.env or {},
        )
        
        if config.working_dir:
            # Note: StdioServerParameters doesn't directly support working_dir
            # You may need to modify the command or use a wrapper script
            pass
        
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
        """
        Create an SSE-based toolset.
        
        IMPORTANT: The remote SSE server must already be running.
        This toolset will connect to the server at the specified URL.
        """
        if not config.url:
            raise ValueError(f"SSE server {config.name} requires 'url' field")
        
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
        """
        Create an HTTP-based toolset.
        
        IMPORTANT: The remote HTTP server must already be running.
        This toolset will connect to the server at the specified URL.
        """
        if not config.url:
            raise ValueError(f"HTTP server {config.name} requires 'url' field")
        
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
    
    async def get_all_toolsets(self, enabled_only: bool = True) -> List[McpToolset]:
        """Get toolsets for all configured servers."""
        toolsets = []
        for name in self._servers.keys():
            config = self._servers[name]
            if enabled_only and not config.enabled:
                continue
            
            toolset = await self.create_toolset(name)
            if toolset:
                toolsets.append(toolset)
        
        return toolsets
    
    async def close_all(self):
        """Close all toolsets and cleanup resources."""
        for name, toolset in self._toolsets.items():
            try:
                await toolset.close()
            except Exception as e:
                logger.error(f"Error closing toolset {name}: {e}")
        
        self._toolsets.clear()


# Example usage
async def main():
    """Example: Using dynamic MCP configuration."""
    
    # Initialize config manager
    manager = DynamicMCPConfigManager()
    
    # Example 1: Add a local stdio server (filesystem)
    filesystem_config = MCPServerConfig(
        name="filesystem",
        type="stdio",
        command="npx",
        args=["-y", "@modelcontextprotocol/server-filesystem", "/tmp"],
        tool_filter=["read_file", "write_file", "list_directory"]
    )
    manager.add_server(filesystem_config)
    
    # Example 2: Add a remote SSE server
    remote_config = MCPServerConfig(
        name="remote_api",
        type="sse",
        url="http://localhost:8000/mcp",
        headers={"Authorization": "Bearer token123"},
        timeout=10.0
    )
    manager.add_server(remote_config)
    
    # Example 3: Create toolsets and use in agent
    filesystem_toolset = await manager.create_toolset("filesystem")
    remote_toolset = await manager.create_toolset("remote_api")
    
    # Create agent with dynamic toolsets
    agent = LlmAgent(
        model="gemini-2.0-flash",
        name="dynamic_mcp_agent",
        tools=[filesystem_toolset, remote_toolset] if filesystem_toolset and remote_toolset else []
    )
    
    print(f"Agent created with {len(agent.tools)} toolsets")
    print(f"Configured servers: {manager.list_servers()}")
    
    # Cleanup
    await manager.close_all()


if __name__ == "__main__":
    asyncio.run(main())
