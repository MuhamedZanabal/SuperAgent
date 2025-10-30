"""
Plugin loader for dynamic plugin loading.
"""
import importlib.util
import sys
from pathlib import Path
from typing import Optional, Type

from superagent.core.logger import get_logger
from .base import Plugin, PluginMetadata
from .registry import PluginRegistry

logger = get_logger(__name__)


class PluginLoader:
    """Load plugins dynamically."""
    
    def __init__(self, registry: PluginRegistry):
        self.registry = registry
    
    def load_from_file(self, filepath: Path) -> Optional[Plugin]:
        """Load plugin from Python file."""
        try:
            # Load module
            spec = importlib.util.spec_from_file_location(filepath.stem, filepath)
            if not spec or not spec.loader:
                logger.error(f"Failed to load spec for {filepath}")
                return None
            
            module = importlib.util.module_from_spec(spec)
            sys.modules[filepath.stem] = module
            spec.loader.exec_module(module)
            
            # Find Plugin class
            plugin_class = None
            for attr_name in dir(module):
                attr = getattr(module, attr_name)
                if isinstance(attr, type) and issubclass(attr, Plugin) and attr != Plugin:
                    plugin_class = attr
                    break
            
            if not plugin_class:
                logger.error(f"No Plugin class found in {filepath}")
                return None
            
            # Instantiate plugin
            plugin = plugin_class()
            self.registry.register(plugin)
            
            logger.info(f"Loaded plugin from {filepath}")
            return plugin
            
        except Exception as e:
            logger.error(f"Failed to load plugin from {filepath}: {e}")
            return None
    
    def load_from_directory(self, directory: Path) -> int:
        """Load all plugins from directory."""
        count = 0
        
        for filepath in directory.glob("*.py"):
            if filepath.stem.startswith("_"):
                continue
            
            if self.load_from_file(filepath):
                count += 1
        
        logger.info(f"Loaded {count} plugins from {directory}")
        return count
    
    def reload_plugin(self, name: str) -> bool:
        """Reload a plugin."""
        plugin = self.registry.get(name)
        if not plugin:
            logger.error(f"Plugin not found: {name}")
            return False
        
        try:
            # Cleanup old plugin
            plugin.cleanup()
            
            # Reload module
            module_name = plugin.metadata.entry_point.split(":")[0]
            if module_name in sys.modules:
                importlib.reload(sys.modules[module_name])
            
            logger.info(f"Reloaded plugin: {name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to reload plugin {name}: {e}")
            return False
