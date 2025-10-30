"""
Plugin system for SuperAgent v2.0.0

Provides dynamic plugin discovery, loading, and management.
"""
from .registry import PluginRegistry
from .base import Plugin, PluginMetadata
from .loader import PluginLoader

__all__ = ["PluginRegistry", "Plugin", "PluginMetadata", "PluginLoader"]
