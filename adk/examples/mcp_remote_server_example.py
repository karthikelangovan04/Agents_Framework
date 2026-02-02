"""
Example: Connecting to Remote MCP Servers

This example demonstrates how to connect to remote MCP servers from the
MCP marketplace or other hosted services.
"""

import asyncio
import logging
from google.adk.agents import LlmAgent
from google.adk.tools.mcp_tool import McpToolset, SseConnectionParams, StreamableHTTPConnectionParams
import sys
from pathlib import Path

# Add examples directory to path for imports
examples_dir = Path(__file__).parent
sys.path.insert(0, str(examples_dir))

from mcp_dynamic_config import DynamicMCPConfigManager, MCPServerConfig

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def example_remote_sse_server():
    """
    Example: Connect to a remote SSE MCP server.
    
    SSE (Server-Sent Events) servers are typically hosted services that
    expose MCP tools via HTTP with SSE transport.
    """
    
    # Example: AWS Marketplace MCP Server
    aws_config = MCPServerConfig(
        name="aws_marketplace",
        type="sse",
        url="https://mcp-server.example.com/sse",  # Replace with actual URL
        headers={
            "Authorization": "Bearer your_aws_token",
            "X-API-Version": "2024-01-01"
        },
        timeout=15.0,
        sse_read_timeout=300.0
    )
    
    manager = DynamicMCPConfigManager()
    manager.add_server(aws_config)
    
    toolset = await manager.create_toolset("aws_marketplace")
    
    if toolset:
        agent = LlmAgent(
            model="gemini-2.0-flash",
            name="aws_agent",
            tools=[toolset]
        )
        logger.info("Created agent with AWS Marketplace MCP tools")
        return agent
    
    return None


async def example_remote_http_server():
    """
    Example: Connect to a remote HTTP MCP server.
    
    HTTP servers use the Streamable HTTP transport protocol.
    """
    
    # Example: Vercel-hosted MCP Server
    vercel_config = MCPServerConfig(
        name="vercel_mcp",
        type="http",
        url="https://your-app.vercel.app/api/mcp",
        headers={
            "Authorization": "Bearer vercel_token",
            "Content-Type": "application/json"
        },
        timeout=10.0,
        sse_read_timeout=300.0
    )
    
    manager = DynamicMCPConfigManager()
    manager.add_server(vercel_config)
    
    toolset = await manager.create_toolset("vercel_mcp")
    
    if toolset:
        agent = LlmAgent(
            model="gemini-2.0-flash",
            name="vercel_agent",
            tools=[toolset]
        )
        logger.info("Created agent with Vercel MCP tools")
        return agent
    
    return None


async def example_mcp_marketplace_servers():
    """
    Example: Connect to multiple MCP servers from marketplace.
    
    This demonstrates how you might discover and connect to various
    MCP servers available in the ecosystem.
    """
    
    manager = DynamicMCPConfigManager()
    
    # Example marketplace servers (replace with actual URLs)
    marketplace_servers = [
        {
            "name": "github_mcp",
            "type": "sse",
            "url": "https://mcp-github.example.com/sse",
            "headers": {"Authorization": "Bearer github_token"}
        },
        {
            "name": "slack_mcp",
            "type": "http",
            "url": "https://mcp-slack.example.com/api/mcp",
            "headers": {"Authorization": "Bearer slack_token"}
        },
        {
            "name": "database_mcp",
            "type": "sse",
            "url": "https://mcp-db.example.com/sse",
            "headers": {
                "Authorization": "Bearer db_token",
                "X-Database-ID": "db_123"
            }
        }
    ]
    
    toolsets = []
    for server_config in marketplace_servers:
        config = MCPServerConfig(**server_config)
        manager.add_server(config)
        
        toolset = await manager.create_toolset(config.name)
        if toolset:
            toolsets.append(toolset)
            logger.info(f"Connected to {config.name} MCP server")
    
    # Create agent with all marketplace tools
    if toolsets:
        agent = LlmAgent(
            model="gemini-2.0-flash",
            name="marketplace_agent",
            tools=toolsets
        )
        logger.info(f"Created agent with {len(toolsets)} marketplace MCP servers")
        return agent
    
    return None


async def example_discover_and_connect():
    """
    Example: Discover MCP servers and connect dynamically.
    
    This pattern could be used to:
    1. Query an MCP registry/marketplace
    2. Discover available servers
    3. Connect to them dynamically
    """
    
    # Simulated discovery (in real implementation, this would query a registry)
    discovered_servers = [
        {
            "name": "discovered_server_1",
            "type": "sse",
            "url": "https://server1.example.com/mcp",
            "description": "File operations server",
            "auth_required": True
        },
        {
            "name": "discovered_server_2",
            "type": "http",
            "url": "https://server2.example.com/api/mcp",
            "description": "API integration server",
            "auth_required": False
        }
    ]
    
    manager = DynamicMCPConfigManager()
    
    for server_info in discovered_servers:
        # Check if authentication is needed
        headers = {}
        if server_info.get("auth_required"):
            # In real implementation, get token from user or keychain
            headers["Authorization"] = "Bearer discovered_token"
        
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
                # Try to get tools to verify connection
                tools = await toolset.get_tools()
                logger.info(
                    f"Successfully connected to {config.name}: "
                    f"{len(tools)} tools available"
                )
        except Exception as e:
            logger.warning(f"Failed to connect to {config.name}: {e}")
    
    # Get all successfully connected toolsets
    toolsets = await manager.get_all_toolsets()
    
    if toolsets:
        agent = LlmAgent(
            model="gemini-2.0-flash",
            name="discovered_agent",
            tools=toolsets
        )
        logger.info(f"Created agent with {len(toolsets)} discovered servers")
        return agent
    
    return None


async def main():
    """Run examples."""
    print("=" * 60)
    print("Remote MCP Server Examples")
    print("=" * 60)
    
    print("\n1. Remote SSE Server Example")
    await example_remote_sse_server()
    
    print("\n2. Remote HTTP Server Example")
    await example_remote_http_server()
    
    print("\n3. Marketplace Servers Example")
    await example_mcp_marketplace_servers()
    
    print("\n4. Discover and Connect Example")
    await example_discover_and_connect()
    
    print("\n" + "=" * 60)
    print("Examples completed!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
