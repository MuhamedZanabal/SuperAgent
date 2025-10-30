"""
Base plugin interface for SuperAgent v2.0.0
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from datetime import datetime


@dataclass
class PluginMetadata:
    """Plugin metadata."""
    name: str
    version: str
    description: str
    author: str
    dependencies: List[str]
    entry_point: str
    enabled: bool = True
    loaded_at: Optional[datetime] = None


class Plugin(ABC):
    """Base plugin interface."""
    
    def __init__(self, metadata: PluginMetadata):
        self.metadata = metadata
        self._initialized = False
    
    @abstractmethod
    async def initialize(self, runtime: Any) -> None:
        """Initialize plugin with runtime context."""
        pass
    
    @abstractmethod
    async def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute plugin functionality."""
        pass
    
    @abstractmethod
    async def cleanup(self) -> None:
        """Cleanup plugin resources."""
        pass
    
    def get_capabilities(self) -> List[str]:
        """Return list of plugin capabilities."""
        return []
    
    def get_config_schema(self) -> Dict[str, Any]:
        """Return configuration schema."""
        return {}
