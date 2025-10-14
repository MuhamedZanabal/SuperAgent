"""
User consent management for dangerous operations.
"""

from typing import Dict, Set, Optional, Callable
from dataclasses import dataclass
from enum import Enum

from superagent.core.logger import get_logger

logger = get_logger(__name__)


class ConsentLevel(str, Enum):
    """Consent levels for operations."""
    ALWAYS_ALLOW = "always_allow"
    PROMPT = "prompt"
    ALWAYS_DENY = "always_deny"


@dataclass
class ConsentRequest:
    """Request for user consent."""
    operation: str
    tool_name: str
    description: str
    risk_level: str  # "low", "medium", "high"
    details: Dict[str, any]


class ConsentManager:
    """
    Manages user consent for dangerous operations.
    
    Tracks consent decisions and enforces safety gates.
    """
    
    def __init__(self, auto_approve: bool = False):
        """
        Initialize consent manager.
        
        Args:
            auto_approve: If True, automatically approve all requests (headless mode)
        """
        self.auto_approve = auto_approve
        self._consent_cache: Dict[str, ConsentLevel] = {}
        self._dangerous_tools: Set[str] = {
            "execute_shell",
            "write_file",
            "delete_file",
            "execute_python",
        }
        self._consent_callback: Optional[Callable] = None
        
        logger.info(f"Consent manager initialized (auto_approve={auto_approve})")
    
    def set_consent_callback(self, callback: Callable) -> None:
        """
        Set callback for interactive consent prompts.
        
        Args:
            callback: Function that prompts user and returns bool
        """
        self._consent_callback = callback
    
    def mark_dangerous(self, tool_name: str) -> None:
        """
        Mark a tool as dangerous (requires consent).
        
        Args:
            tool_name: Name of the tool
        """
        self._dangerous_tools.add(tool_name)
        logger.info(f"Marked tool as dangerous: {tool_name}")
    
    def requires_consent(self, tool_name: str) -> bool:
        """
        Check if a tool requires user consent.
        
        Args:
            tool_name: Name of the tool
            
        Returns:
            True if consent is required
        """
        return tool_name in self._dangerous_tools
    
    async def request_consent(self, request: ConsentRequest) -> bool:
        """
        Request user consent for an operation.
        
        Args:
            request: Consent request details
            
        Returns:
            True if consent granted, False otherwise
        """
        # Check cache
        cache_key = f"{request.tool_name}:{request.operation}"
        if cache_key in self._consent_cache:
            level = self._consent_cache[cache_key]
            if level == ConsentLevel.ALWAYS_ALLOW:
                return True
            elif level == ConsentLevel.ALWAYS_DENY:
                return False
        
        # Auto-approve in headless mode
        if self.auto_approve:
            logger.info(f"Auto-approved: {request.tool_name} - {request.operation}")
            return True
        
        # Prompt user
        if self._consent_callback:
            try:
                granted = await self._consent_callback(request)
                logger.info(
                    f"Consent {'granted' if granted else 'denied'}: "
                    f"{request.tool_name} - {request.operation}"
                )
                return granted
            except Exception as e:
                logger.error(f"Consent callback error: {e}")
                return False
        
        # Default deny if no callback
        logger.warning(f"No consent callback, denying: {request.tool_name}")
        return False
    
    def cache_consent(
        self,
        tool_name: str,
        operation: str,
        level: ConsentLevel,
    ) -> None:
        """
        Cache a consent decision.
        
        Args:
            tool_name: Name of the tool
            operation: Operation being performed
            level: Consent level to cache
        """
        cache_key = f"{tool_name}:{operation}"
        self._consent_cache[cache_key] = level
        logger.info(f"Cached consent: {cache_key} = {level}")
    
    def clear_cache(self) -> None:
        """Clear all cached consent decisions."""
        self._consent_cache.clear()
        logger.info("Cleared consent cache")
