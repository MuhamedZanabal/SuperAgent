"""Tests for tool systems."""

import pytest
from pathlib import Path
from superagent.tools.registry import ToolRegistry
from superagent.tools.executor import ToolExecutor
from superagent.tools.models import ToolCall
from superagent.core.security import SecurityManager


@pytest.fixture
def tool_registry():
    """Create tool registry for testing."""
    return ToolRegistry()


@pytest.fixture
def tool_executor():
    """Create tool executor for testing."""
    security = SecurityManager()
    return ToolExecutor(security_manager=security)


def test_tool_registration(tool_registry):
    """Test tool registration."""
    from superagent.tools.builtin.file_tools import ReadFileTool
    
    security = SecurityManager()
    tool = ReadFileTool(security)
    
    tool_registry.register(tool)
    
    assert tool_registry.has_tool("read_file")
    retrieved = tool_registry.get_tool("read_file")
    assert retrieved is not None


def test_tool_discovery(tool_registry):
    """Test tool discovery."""
    tools = tool_registry.list_tools()
    assert isinstance(tools, list)


@pytest.mark.asyncio
async def test_tool_execution(tool_executor, tmp_path):
    """Test tool execution."""
    test_file = tmp_path / "test.txt"
    test_file.write_text("Hello, World!")
    
    tool_call = ToolCall(
        tool_name="read_file",
        parameters={"path": str(test_file)},
    )
    
    result = await tool_executor.execute(tool_call)
    assert result.success
    assert "Hello, World!" in str(result.output)
