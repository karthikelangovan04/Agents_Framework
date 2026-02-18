"""
ADK Agent with Remote MCP Server Connection

This agent connects to a remote MCP server running on Cloud Run
and uses service-to-service authentication.
SSE transport used to avoid Streamable HTTP cancel-scope issues.
"""

import logging
import os

from dotenv import load_dotenv
from google.adk.agents import LlmAgent
from google.adk.tools.mcp_tool import MCPToolset
from google.adk.tools.mcp_tool.mcp_session_manager import SseConnectionParams

from auth_helper import get_authenticated_headers

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)
logging.basicConfig(
    format="[%(levelname)s]: %(message)s",
    level=logging.INFO
)

# System instruction for the currency agent
SYSTEM_INSTRUCTION = (
    "You are a specialized assistant for currency conversions. "
    "Your sole purpose is to use the 'get_exchange_rate' tool to answer "
    "questions about currency exchange rates. "
    "If the user asks about anything other than currency conversion or "
    "exchange rates, politely state that you cannot help with that topic "
    "and can only assist with currency-related queries. "
    "Do not attempt to answer unrelated questions or use tools for other "
    "purposes."
)

logger.info("--- 🔧 Loading MCP tools from remote MCP Server... ---")
logger.info("--- 🤖 Creating ADK Currency Agent... ---")

# Get MCP server URL from environment
# This will be set to the Cloud Run service URL after deployment
MCP_SERVER_URL = os.getenv(
    "MCP_SERVER_URL",
    "http://localhost:8080/sse"  # Default for local testing
)

# Create a function to get headers dynamically (called when MCP connection is established)
# This ensures credentials are available in the Cloud Run environment
def get_mcp_headers(context) -> dict:
    """Get authenticated headers for MCP server requests.
    
    This is called dynamically when the MCP connection is established,
    ensuring Cloud Run credentials are available.
    
    Returns empty dict if authentication fails (MCP server allows unauthenticated access).
    """
    try:
        headers = get_authenticated_headers(MCP_SERVER_URL)
        if headers:
            logger.info("✅ Using authenticated headers for MCP connection")
            return headers
        else:
            logger.warning("⚠️ Could not get auth headers, trying without authentication")
            return {}
    except Exception as e:
        logger.warning(f"⚠️ Error getting auth headers: {e}, trying without authentication")
        return {}

# Create SSE connection params for remote MCP server
# Headers will be generated dynamically via header_provider when connection is established
connection_params = SseConnectionParams(
    url=MCP_SERVER_URL,
    headers=None  # Headers will be provided via header_provider
)

# Create the root agent with MCP tools
# Use header_provider to generate auth headers dynamically when connection is established
root_agent = LlmAgent(
    model=os.getenv("GOOGLE_MODEL", "gemini-2.5-flash"),
    name="currency_agent",
    description="An agent that can help with currency conversions",
    instruction=SYSTEM_INSTRUCTION,
    tools=[
        MCPToolset(
            connection_params=connection_params,
            header_provider=get_mcp_headers
        )
    ],
)
