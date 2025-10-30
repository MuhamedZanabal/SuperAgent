"""
MCP Client - Call external MCP servers.
"""

from __future__ import annotations
from typing import Dict, Any, List, Optional
import httpx

from superagent.core.logger import get_logger

logger = get_logger(__name__)


class MCPClient:
    """
    MCP Client for calling external MCP servers.
    
    Normalizes tool schemas and results from external servers.
    """
    
    def __init__(self, server_url: str, timeout: int = 30):
        """
        Initialize MCP client.
        
        Args:
            server_url: URL of MCP server
            timeout: Request timeout in seconds
        """
        self.server_url = server_url.rstrip("/")
        self.timeout = timeout
        self.client = httpx.AsyncClient(timeout=timeout)
        logger.info(f"MCP client initialized for: {server_url}")
    
    async def list_tools(self) -> List[Dict[str, Any]]:
        """List available tools from server."""
        try:
            response = await self.client.get(f"{self.server_url}/tools")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Failed to list tools: {e}")
            return []
    
    async def call_tool(
        self,
        tool_name: str,
        args: Dict[str, Any],
    ) -> Any:
        """Call a tool on the server."""
        try:
            response = await self.client.post(
                f"{self.server_url}/tools/{tool_name}",
                json=args,
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Failed to call tool {tool_name}: {e}")
            raise
    
    async def get_context(
        self,
        provider_name: str,
        params: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Get context from a provider."""
        try:
            response = await self.client.post(
                f"{self.server_url}/context/{provider_name}",
                json=params or {},
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Failed to get context from {provider_name}: {e}")
            raise
    
    async def close(self) -> None:
        """Close client connection."""
        await self.client.aclose()
