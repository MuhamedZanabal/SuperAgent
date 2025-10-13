"""
Tests for the Unified Plugin System.
"""

import pytest
from pathlib import Path
import json
import tempfile
import shutil

from superagent.tools.plugin_system import (
    UnifiedPluginSystem,
    PluginManifest,
    PluginPermissions,
)
from superagent.tools.registry import ToolRegistry


@pytest.fixture
def temp_plugin_dir():
    """Create temporary plugin directory."""
    temp_dir = Path(tempfile.mkdtemp())
    yield temp_dir
    shutil.rmtree(temp_dir)


@pytest.fixture
def sample_plugin(temp_plugin_dir):
    """Create a sample plugin."""
    plugin_dir = temp_plugin_dir / "test-plugin"
    plugin_dir.mkdir()
    
    # Create manifest
    manifest = {
        "name": "test-plugin",
        "version": "1.0.0",
        "description": "Test plugin",
        "author": "Test Author",
        "entry_point": "main.py",
        "dependencies": [],
        "permissions": {
            "file_read": True,
            "file_write": False,
            "network": False,
            "execute": False,
            "environment": False,
        },
        "tags": ["test"],
    }
    
    with open(plugin_dir / "plugin.json", "w") as f:
        json.dump(manifest, f)
    
    # Create main.py
    main_code = '''
from superagent.tools.base import BaseTool, ToolResult

class TestTool(BaseTool):
    name = "test_tool"
    description = "A test tool"
    parameters = []
    
    async def execute(self, **kwargs):
        return ToolResult(success=True, output="test output")
'''
    
    with open(plugin_dir / "main.py", "w") as f:
        f.write(main_code)
    
    return plugin_dir


@pytest.mark.asyncio
async def test_plugin_discovery(temp_plugin_dir, sample_plugin):
    """Test plugin discovery."""
    plugin_system = UnifiedPluginSystem(
        plugin_dirs=[temp_plugin_dir],
        auto_discover=False,
    )
    
    plugins = plugin_system.discover_plugins()
    assert len(plugins) == 1
    assert plugins[0].manifest.name == "test-plugin"


@pytest.mark.asyncio
async def test_plugin_loading(temp_plugin_dir, sample_plugin):
    """Test plugin loading."""
    tool_registry = ToolRegistry()
    plugin_system = UnifiedPluginSystem(
        plugin_dirs=[temp_plugin_dir],
        tool_registry=tool_registry,
        auto_discover=False,
    )
    
    metadata = await plugin_system.load_plugin("test-plugin")
    
    assert metadata.manifest.name == "test-plugin"
    assert len(metadata.tools) == 1
    assert "test_tool" in metadata.tools
    
    # Check tool is registered
    tool = tool_registry.get("test_tool")
    assert tool is not None


@pytest.mark.asyncio
async def test_plugin_unloading(temp_plugin_dir, sample_plugin):
    """Test plugin unloading."""
    tool_registry = ToolRegistry()
    plugin_system = UnifiedPluginSystem(
        plugin_dirs=[temp_plugin_dir],
        tool_registry=tool_registry,
        auto_discover=False,
    )
    
    await plugin_system.load_plugin("test-plugin")
    await plugin_system.unload_plugin("test-plugin")
    
    assert "test-plugin" not in plugin_system.plugins
    
    # Check tool is unregistered
    with pytest.raises(ValueError):
        tool_registry.get("test_tool")


@pytest.mark.asyncio
async def test_plugin_reload(temp_plugin_dir, sample_plugin):
    """Test plugin hot-reload."""
    tool_registry = ToolRegistry()
    plugin_system = UnifiedPluginSystem(
        plugin_dirs=[temp_plugin_dir],
        tool_registry=tool_registry,
        auto_discover=False,
    )
    
    metadata1 = await plugin_system.load_plugin("test-plugin")
    
    # Modify plugin file
    main_file = sample_plugin / "main.py"
    with open(main_file, "a") as f:
        f.write("\n# Modified\n")
    
    metadata2 = await plugin_system.reload_plugin("test-plugin")
    
    assert metadata1.checksum != metadata2.checksum


@pytest.mark.asyncio
async def test_check_updates(temp_plugin_dir, sample_plugin):
    """Test update checking."""
    plugin_system = UnifiedPluginSystem(
        plugin_dirs=[temp_plugin_dir],
        auto_discover=False,
    )
    
    await plugin_system.load_plugin("test-plugin")
    
    # No updates initially
    updates = await plugin_system.check_updates()
    assert updates["test-plugin"] is False
    
    # Modify plugin
    main_file = sample_plugin / "main.py"
    with open(main_file, "a") as f:
        f.write("\n# Modified\n")
    
    # Should detect update
    updates = await plugin_system.check_updates()
    assert updates["test-plugin"] is True
