"""
Tool registry for managing available tools.
"""

from typing import Dict, List, Optional, Type
import importlib
import inspect
from pathlib import Path

from superagent.tools.base import BaseTool
from superagent.core.logger import get_logger

logger = get_logger(__name__)


class ToolRegistry:
    """
    Registry for managing tools.
    
    Provides tool discovery, registration, and retrieval.
    """
    
    def __init__(self):
        """Initialize the tool registry."""
        self._tools: Dict[str, BaseTool] = {}
        self._tool_classes: Dict[str, Type[BaseTool]] = {}
    
    def register(self, tool: BaseTool) -> None:
        """
        Register a tool instance.
        
        Args:
            tool: Tool instance to register
        """
        if tool.name in self._tools:
            logger.warning(f"Tool {tool.name} already registered, overwriting")
        
        self._tools[tool.name] = tool
        self._tool_classes[tool.name] = type(tool)
        logger.info(f"Registered tool: {tool.name}")
    
    def register_class(self, tool_class: Type[BaseTool]) -> None:
        """
        Register a tool class.
        
        Args:
            tool_class: Tool class to register
        """
        tool = tool_class()
        self.register(tool)
    
    def unregister(self, tool_name: str) -> bool:
        """
        Unregister a tool.
        
        Args:
            tool_name: Name of the tool to unregister
            
        Returns:
            True if successful, False if tool not found
        """
        if tool_name in self._tools:
            del self._tools[tool_name]
            if tool_name in self._tool_classes:
                del self._tool_classes[tool_name]
            logger.info(f"Unregistered tool: {tool_name}")
            return True
        return False
    
    def get(self, tool_name: str) -> Optional[BaseTool]:
        """
        Get a tool by name.
        
        Args:
            tool_name: Name of the tool
            
        Returns:
            Tool instance if found, None otherwise
        """
        return self._tools.get(tool_name)
    
    def list_tools(self) -> List[str]:
        """
        List all registered tool names.
        
        Returns:
            List of tool names
        """
        return list(self._tools.keys())
    
    def get_all_tools(self) -> Dict[str, BaseTool]:
        """
        Get all registered tools.
        
        Returns:
            Dictionary of tool name to tool instance
        """
        return self._tools.copy()
    
    def get_function_definitions(self) -> List[Dict]:
        """
        Get function definitions for all tools.
        
        Returns:
            List of function definitions in OpenAI format
        """
        return [tool.to_function_definition() for tool in self._tools.values()]
    
    def discover_tools(self, directory: Path) -> int:
        """
        Discover and register tools from a directory.
        
        Args:
            directory: Directory to search for tools
            
        Returns:
            Number of tools discovered
        """
        if not directory.exists():
            logger.warning(f"Tool directory does not exist: {directory}")
            return 0
        
        count = 0
        
        # Find all Python files
        for file_path in directory.rglob("*.py"):
            if file_path.name.startswith("_"):
                continue
            
            try:
                # Import module
                module_path = str(file_path.relative_to(directory.parent)).replace("/", ".").replace("\\", ".")[:-3]
                module = importlib.import_module(module_path)
                
                # Find tool classes
                for name, obj in inspect.getmembers(module, inspect.isclass):
                    if issubclass(obj, BaseTool) and obj != BaseTool:
                        self.register_class(obj)
                        count += 1
                        
            except Exception as e:
                logger.error(f"Error loading tools from {file_path}: {e}")
        
        logger.info(f"Discovered {count} tools from {directory}")
        return count
    
    def clear(self) -> None:
        """Clear all registered tools."""
        self._tools.clear()
        self._tool_classes.clear()
        logger.info("Cleared all tools from registry")


# Global registry instance
_registry: Optional[ToolRegistry] = None


def get_registry() -> ToolRegistry:
    """
    Get global tool registry.
    
    Returns:
        ToolRegistry singleton instance
    """
    global _registry
    if _registry is None:
        _registry = ToolRegistry()
    return _registry
