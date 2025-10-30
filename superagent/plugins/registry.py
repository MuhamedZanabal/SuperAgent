"""
Plugin registry for managing plugins.
"""
from typing import Dict, List, Optional
from pathlib import Path
import json

from superagent.core.logger import get_logger
from .base import Plugin, PluginMetadata

logger = get_logger(__name__)


class PluginRegistry:
    """Registry for managing plugins."""
    
    def __init__(self, plugins_dir: Optional[Path] = None):
        self.plugins_dir = plugins_dir or Path.home() / ".superagent" / "plugins"
        self.plugins_dir.mkdir(parents=True, exist_ok=True)
        
        self.plugins: Dict[str, Plugin] = {}
        self.metadata: Dict[str, PluginMetadata] = {}
    
    def register(self, plugin: Plugin) -> None:
        """Register a plugin."""
        name = plugin.metadata.name
        
        if name in self.plugins:
            logger.warning(f"Plugin {name} already registered, replacing")
        
        self.plugins[name] = plugin
        self.metadata[name] = plugin.metadata
        
        logger.info(f"Registered plugin: {name} v{plugin.metadata.version}")
    
    def unregister(self, name: str) -> None:
        """Unregister a plugin."""
        if name in self.plugins:
            del self.plugins[name]
            del self.metadata[name]
            logger.info(f"Unregistered plugin: {name}")
    
    def get(self, name: str) -> Optional[Plugin]:
        """Get plugin by name."""
        return self.plugins.get(name)
    
    def list_plugins(self) -> List[PluginMetadata]:
        """List all registered plugins."""
        return list(self.metadata.values())
    
    def list_enabled(self) -> List[Plugin]:
        """List enabled plugins."""
        return [p for p in self.plugins.values() if p.metadata.enabled]
    
    async def initialize_all(self, runtime: Any) -> None:
        """Initialize all enabled plugins."""
        for plugin in self.list_enabled():
            try:
                await plugin.initialize(runtime)
                logger.info(f"Initialized plugin: {plugin.metadata.name}")
            except Exception as e:
                logger.error(f"Failed to initialize plugin {plugin.metadata.name}: {e}")
    
    async def cleanup_all(self) -> None:
        """Cleanup all plugins."""
        for plugin in self.plugins.values():
            try:
                await plugin.cleanup()
            except Exception as e:
                logger.error(f"Failed to cleanup plugin {plugin.metadata.name}: {e}")
    
    def save_metadata(self) -> None:
        """Save plugin metadata to disk."""
        metadata_file = self.plugins_dir / "plugins.json"
        
        data = {
            name: {
                "name": meta.name,
                "version": meta.version,
                "description": meta.description,
                "author": meta.author,
                "dependencies": meta.dependencies,
                "entry_point": meta.entry_point,
                "enabled": meta.enabled
            }
            for name, meta in self.metadata.items()
        }
        
        with open(metadata_file, "w") as f:
            json.dump(data, f, indent=2)
    
    def load_metadata(self) -> None:
        """Load plugin metadata from disk."""
        metadata_file = self.plugins_dir / "plugins.json"
        
        if not metadata_file.exists():
            return
        
        with open(metadata_file) as f:
            data = json.load(f)
        
        for name, meta_dict in data.items():
            self.metadata[name] = PluginMetadata(**meta_dict)
