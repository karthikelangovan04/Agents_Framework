"""
Authentication helper for service-to-service communication.

This module provides functions to get ID tokens for authenticating
requests from the ADK agent to the MCP server on Cloud Run.
"""

import logging
import os
from typing import Optional
from urllib.parse import urlparse

import google.auth.transport.requests
from google.oauth2 import id_token

logger = logging.getLogger(__name__)


def get_id_token(audience: str) -> Optional[str]:
    """
    Get an ID token for service-to-service authentication.
    
    Args:
        audience: The URL of the service to authenticate to
                  (e.g., "https://mcp-server-xxx.run.app")
    
    Returns:
        ID token string, or None if authentication fails
    """
    try:
        request = google.auth.transport.requests.Request()
        token = id_token.fetch_id_token(request, audience)
        logger.info(f"✅ Successfully obtained ID token for {audience}")
        return token
    except Exception as e:
        logger.error(f"❌ Failed to get ID token: {e}")
        return None


def get_authenticated_headers(mcp_server_url: str) -> dict:
    """
    Get headers with authentication token for MCP server requests.
    
    Args:
        mcp_server_url: The full URL of the MCP server
                       (e.g., "https://mcp-server-xxx.run.app/sse")
    
    Returns:
        Dictionary with Authorization header
    """
    # Extract base URL (without path) for audience
    # The audience should be the service URL, not the full path
    parsed = urlparse(mcp_server_url)
    base_url = f"{parsed.scheme}://{parsed.netloc}"
    
    token = get_id_token(base_url)
    if token:
        return {
            "Authorization": f"Bearer {token}"
        }
    else:
        logger.warning(
            "⚠️ Could not get ID token. Requests may fail if MCP server "
            "requires authentication."
        )
        return {}
