"""
MCP Host - Expose context providers and tools as MCP endpoints.
"""

from __future__ import annotations
from typing import Dict, Any, List, Optional, TYPE_CHECKING
from dataclasses import dataclass
import asyncio

if TYPE_CHECKING:
    from superagent.tools.registry import ToolRegistry
    from superagent.security.rbac import RBACManager

from superagent.core.logger import get_logger

logger = get_logger(__name__)


@dataclass
class MCPContextProvider:
    """MCP context provider definition."""
    name: str
    description: str
    handler: callable
    scopes: List[str]


@dataclass
class MCPTool:
    """MCP tool definition."""
    name: str
    description: str
    parameters: Dict[str, Any]
    handler: callable
    scopes: List[str]
    requires_consent: bool = False


class MCPHost:
    """
    MCP Host exposing context providers and tools.
    
    Provides Model Context Protocol endpoints for:
    - Context providers (filesystem, git, session, etc.)
    - Registered tools with RBAC scoping
    """
    
    def __init__(
        self,
        tool_registry: Optional[ToolRegistry] = None,
        rbac_manager: Optional[RBACManager] = None,
    ):
        """
        Initialize MCP host.
        
        Args:
            tool_registry: Tool registry for exposing tools
            rbac_manager: RBAC manager for permission checks
        """
        self.tool_registry = tool_registry
        self.rbac_manager = rbac_manager
        
        self.context_providers: Dict[str, MCPContextProvider] = {}
        self.tools: Dict[str, MCPTool] = {}
        
        self._register_default_providers()
        logger.info("MCP host initialized")
    
    def _register_default_providers(self) -> None:
        """Register default context providers."""
        # Filesystem provider
        self.register_context_provider(
            name="filesystem",
            description="Access filesystem context",
            handler=self._filesystem_provider,
            scopes=["read:files"],
        )
        
        # Git provider
        self.register_context_provider(
            name="git",
            description="Access git repository metadata",
            handler=self._git_provider,
            scopes=["read:git"],
        )
        
        # Session provider
        self.register_context_provider(
            name="session",
            description="Access session history and checkpoints",
            handler=self._session_provider,
            scopes=["read:session"],
        )
    
    def register_context_provider(
        self,
        name: str,
        description: str,
        handler: callable,
        scopes: List[str],
    ) -> None:
        """Register a context provider."""
        provider = MCPContextProvider(
            name=name,
            description=description,
            handler=handler,
            scopes=scopes,
        )
        self.context_providers[name] = provider
        logger.info(f"Registered context provider: {name}")
    
    def register_tool(
        self,
        name: str,
        description: str,
        parameters: Dict[str, Any],
        handler: callable,
        scopes: List[str],
        requires_consent: bool = False,
    ) -> None:
        """Register a tool."""
        tool = MCPTool(
            name=name,
            description=description,
            parameters=parameters,
            handler=handler,
            scopes=scopes,
            requires_consent=requires_consent,
        )
        self.tools[name] = tool
        logger.info(f"Registered MCP tool: {name}")
    
    async def list_context_providers(self, user_scopes: List[str]) -> List[Dict[str, Any]]:
        """List available context providers based on user scopes."""
        providers = []
        
        for provider in self.context_providers.values():
            # Check if user has required scopes
            if self._check_scopes(user_scopes, provider.scopes):
                providers.append({
                    "name": provider.name,
                    "description": provider.description,
                    "scopes": provider.scopes,
                })
        
        return providers
    
    async def list_tools(self, user_scopes: List[str]) -> List[Dict[str, Any]]:
        """List available tools based on user scopes."""
        tools = []
        
        for tool in self.tools.values():
            # Check if user has required scopes
            if self._check_scopes(user_scopes, tool.scopes):
                tools.append({
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": tool.parameters,
                    "scopes": tool.scopes,
                    "requires_consent": tool.requires_consent,
                })
        
        return tools
    
    async def get_context(
        self,
        provider_name: str,
        user_scopes: List[str],
        params: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Get context from a provider."""
        if provider_name not in self.context_providers:
            raise ValueError(f"Unknown context provider: {provider_name}")
        
        provider = self.context_providers[provider_name]
        
        # Check scopes
        if not self._check_scopes(user_scopes, provider.scopes):
            raise PermissionError(f"Insufficient scopes for provider: {provider_name}")
        
        # Call handler
        return await provider.handler(params or {})
    
    async def call_tool(
        self,
        tool_name: str,
        user_scopes: List[str],
        args: Dict[str, Any],
    ) -> Any:
        """Call a tool."""
        if tool_name not in self.tools:
            raise ValueError(f"Unknown tool: {tool_name}")
        
        tool = self.tools[tool_name]
        
        # Check scopes
        if not self._check_scopes(user_scopes, tool.scopes):
            raise PermissionError(f"Insufficient scopes for tool: {tool_name}")
        
        # Call handler
        return await tool.handler(args)
    
    def _check_scopes(self, user_scopes: List[str], required_scopes: List[str]) -> bool:
        """Check if user has required scopes."""
        return all(scope in user_scopes for scope in required_scopes)
    
    async def _filesystem_provider(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Filesystem context provider."""
        import os
        from pathlib import Path
        
        cwd = params.get("cwd", os.getcwd())
        path = Path(cwd)
        
        return {
            "cwd": str(path.absolute()),
            "files": [str(f) for f in path.iterdir() if f.is_file()],
            "directories": [str(d) for d in path.iterdir() if d.is_dir()],
        }
    
    async def _git_provider(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Git context provider."""
        try:
            import subprocess
            
            # Get git info
            branch = subprocess.check_output(
                ["git", "rev-parse", "--abbrev-ref", "HEAD"],
                text=True,
            ).strip()
            
            commit = subprocess.check_output(
                ["git", "rev-parse", "HEAD"],
                text=True,
            ).strip()
            
            status = subprocess.check_output(
                ["git", "status", "--short"],
                text=True,
            ).strip()
            
            return {
                "branch": branch,
                "commit": commit,
                "status": status,
                "has_changes": bool(status),
            }
        except Exception as e:
            logger.warning(f"Git provider error: {e}")
            return {"error": str(e)}
    
    async def _session_provider(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Session context provider."""
        # TODO: Integrate with checkpoint manager
        return {
            "session_id": params.get("session_id", "unknown"),
            "checkpoints": [],
        }
