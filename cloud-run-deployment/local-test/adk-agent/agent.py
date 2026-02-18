"""
ADK Agent - Local Test (No authentication)

Connects to local MCP server via SSE. Uses Gemini API key (not Vertex AI).
No auth_helper - local MCP server has no auth.
SSE transport used to avoid Streamable HTTP cancel-scope issues.
"""

import logging
import os

from dotenv import load_dotenv
from google.adk.agents import LlmAgent
from google.adk.tools.mcp_tool import MCPToolset
from google.adk.tools.mcp_tool.mcp_session_manager import SseConnectionParams

load_dotenv()

logger = logging.getLogger(__name__)
logging.basicConfig(format="[%(levelname)s]: %(message)s", level=logging.INFO)

# SSE endpoint (default port 9090)
MCP_SERVER_URL = os.getenv("MCP_SERVER_URL", "http://localhost:9090/sse")

SYSTEM_INSTRUCTION = (
    "You are a currency conversion assistant. Use the 'get_exchange_rate' tool "
    "to answer questions about exchange rates. Only help with currency-related queries."
)

# No auth - local MCP server; SSE transport
connection_params = SseConnectionParams(
    url=MCP_SERVER_URL,
    headers=None,
)

root_agent = LlmAgent(
    model=os.getenv("GOOGLE_MODEL", "gemini-2.5-flash"),
    name="currency_agent",
    description="Currency conversion assistant",
    instruction=SYSTEM_INSTRUCTION,
    tools=[MCPToolset(connection_params=connection_params)],
)
