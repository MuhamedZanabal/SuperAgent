"""Performance and benchmark tests."""

import pytest
import time
import asyncio
from superagent.core.runtime import SuperAgentRuntime
from superagent.llm.models import LLMRequest, Message


@pytest.mark.asyncio
async def test_llm_response_time():
    """Test LLM response time."""
    runtime = SuperAgentRuntime()
    await runtime.initialize()
    
    request = LLMRequest(
        model="gpt-3.5-turbo",
        messages=[Message(role="user", content="Say hello")],
        max_tokens=10,
    )
    
    start = time.time()
    response = await runtime.llm_provider.generate(request)
    duration = time.time() - start
    
    assert response.success
    assert duration < 5.0  # Should respond within 5 seconds
    
    await runtime.cleanup()


@pytest.mark.asyncio
async def test_memory_search_performance():
    """Test memory search performance."""
    from superagent.memory.manager import MemoryManager
    from superagent.memory.models import MemoryItem, MemoryQuery, MemoryType
    
    manager = MemoryManager()
    await manager.initialize()
    
    # Store 100 items
    for i in range(100):
        item = MemoryItem(
            content=f"Test item {i}",
            memory_type=MemoryType.SHORT_TERM,
        )
        await manager.store(item)
    
    # Measure search time
    query = MemoryQuery(query="Test item", limit=10)
    
    start = time.time()
    results = await manager.search(query)
    duration = time.time() - start
    
    assert len(results) > 0
    assert duration < 1.0  # Should search within 1 second
    
    await manager.cleanup()


@pytest.mark.asyncio
async def test_concurrent_tool_execution():
    """Test concurrent tool execution."""
    from superagent.tools.executor import ToolExecutor
    from superagent.tools.models import ToolCall
    from superagent.core.security import SecurityManager
    
    security = SecurityManager()
    executor = ToolExecutor(security_manager=security)
    
    # Create multiple tool calls
    calls = [
        ToolCall(
            tool_name="system_info",
            parameters={},
        )
        for _ in range(10)
    ]
    
    start = time.time()
    results = await asyncio.gather(*[executor.execute(call) for call in calls])
    duration = time.time() - start
    
    assert len(results) == 10
    assert all(r.success for r in results)
    assert duration < 2.0  # Should complete within 2 seconds
