"""
Tool & Plugin System

Provides dynamic tool loading, sandboxed execution, and plugin orchestration.
"""

from superagent.tools.base import BaseTool, ToolParameter, ToolResult
from superagent.tools.registry import ToolRegistry
from superagent.tools.executor import ToolExecutor
from superagent.tools.models import ToolDefinition, ToolCall, ToolOutput
from superagent.tools.plugin_system import (
    UnifiedPluginSystem,
    PluginManifest,
    PluginMetadata,
    PluginDependency,
    PluginPermissions,
)

__all__ = [
    "BaseTool",
    "ToolParameter",
    "ToolResult",
    "ToolRegistry",
    "ToolExecutor",
    "ToolDefinition",
    "ToolCall",
    "ToolOutput",
    "UnifiedPluginSystem",
    "PluginManifest",
    "PluginMetadata",
    "PluginDependency",
    "PluginPermissions",
]
