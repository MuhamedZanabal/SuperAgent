"""Tests for memory systems."""

import pytest
from superagent.memory.models import MemoryItem, MemoryType, MemoryQuery
from superagent.memory.manager import MemoryManager
from superagent.memory.context import ContextManager


@pytest.fixture
async def memory_manager():
    """Create memory manager for testing."""
    manager = MemoryManager()
    await manager.initialize()
    yield manager
    await manager.cleanup()


@pytest.mark.asyncio
async def test_memory_storage(memory_manager):
    """Test storing and retrieving memories."""
    item = MemoryItem(
        content="Test memory content",
        memory_type=MemoryType.SHORT_TERM,
        metadata={"source": "test"},
    )
    
    await memory_manager.store(item)
    
    query = MemoryQuery(query="Test memory", limit=5)
    results = await memory_manager.search(query)
    
    assert len(results) > 0
    assert results[0].content == "Test memory content"


@pytest.mark.asyncio
async def test_memory_types(memory_manager):
    """Test different memory types."""
    short_term = MemoryItem(
        content="Short term memory",
        memory_type=MemoryType.SHORT_TERM,
    )
    
    long_term = MemoryItem(
        content="Long term memory",
        memory_type=MemoryType.LONG_TERM,
    )
    
    await memory_manager.store(short_term)
    await memory_manager.store(long_term)
    
    query = MemoryQuery(
        query="memory",
        memory_types=[MemoryType.SHORT_TERM],
    )
    results = await memory_manager.search(query)
    
    assert all(r.memory_type == MemoryType.SHORT_TERM for r in results)


@pytest.mark.asyncio
async def test_context_manager():
    """Test context management."""
    context_mgr = ContextManager(max_tokens=1000)
    
    context_mgr.add_message("user", "Hello")
    context_mgr.add_message("assistant", "Hi there!")
    
    messages = context_mgr.get_messages()
    assert len(messages) == 2
    
    context_mgr.clear()
    assert len(context_mgr.get_messages()) == 0
