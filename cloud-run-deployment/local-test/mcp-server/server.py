"""
MCP Server - Local Test (No authentication)

Same currency MCP server as Cloud Run, runs on localhost.
No auth needed - use for local testing only.
"""

import asyncio
import logging
import os

import httpx
from fastmcp import FastMCP

logger = logging.getLogger(__name__)
logging.basicConfig(format="[%(levelname)s]: %(message)s", level=logging.INFO)

mcp = FastMCP("Currency MCP Server 💵 (Local)")


@mcp.tool()
def get_exchange_rate(
    currency_from: str = 'USD',
    currency_to: str = 'EUR',
    currency_date: str = 'latest',
):
    """Use this to get current exchange rate."""
    logger.info(f"🛠️ get_exchange_rate: {currency_from} → {currency_to}")
    try:
        response = httpx.get(
            f'https://api.frankfurter.app/{currency_date}',
            params={'from': currency_from, 'to': currency_to},
        )
        response.raise_for_status()
        data = response.json()
        return data if 'rates' in data else {'error': 'Invalid API response'}
    except Exception as e:
        return {'error': str(e)}


if __name__ == "__main__":
    port = int(os.getenv('PORT', 9090))
    logger.info(f"🚀 MCP server SSE (local, no auth) on http://0.0.0.0:{port}/sse")
    asyncio.run(
        mcp.run_async(transport="sse", host="0.0.0.0", port=port)
    )
