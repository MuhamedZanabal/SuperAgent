"""
Integration tests for SuperAgent system.

Tests the complete system working together end-to-end.
"""

import pytest
import asyncio
from pathlib import Path
import tempfile

from superagent.core.runtime import SuperAgentRuntime, initialize_runtime
from superagent.core.config import SuperAgentConfig, ProviderType
from superagent.llm.models import LLMRequest, Message
from superagent.agents.models import Task
from superagent.memory.models import MemoryItem
from superagent.tools.models import ToolCall


@pytest.fixture
async def runtime():
    """Create a test runtime instance."""
    with tempfile.TemporaryDirectory() as tmpdir:
        config = SuperAgentConfig(
            data_dir=Path(tmpdir),
            log_level="INFO",
            providers=[
                {
                    "type": ProviderType.OPENAI,
                    "api_key": "test-key",
                    "models": ["gpt-4"],
                }
            ],
        )
        
        runtime = SuperAgentRuntime(config)
        await runtime.initialize()
        
        yield runtime
        
        await runtime.shutdown()


@pytest.mark.asyncio
async def test_runtime_initialization():
    """Test that runtime initializes all components correctly."""
    runtime = await initialize_runtime()
    
    assert runtime.is_initialized()
    assert runtime.llm_provider is not None
    assert runtime.memory_manager is not None
    assert runtime.tool_registry is not None
    assert runtime.metrics_collector is not None
    
    await runtime.shutdown()


@pytest.mark.asyncio
async def test_runtime_context_manager():
    """Test runtime as async context manager."""
    async with SuperAgentRuntime() as runtime:
        assert runtime.is_initialized()
        assert runtime.llm_provider is not None


@pytest.mark.asyncio
async def test_llm_provider_integration(runtime):
    """Test LLM provider integration."""
    provider = runtime.llm_provider
    
    # Test that provider is configured
    assert provider is not None
    assert len(provider.providers) > 0
    
    # Test provider capabilities
    capabilities = provider.get_capabilities()
    assert capabilities is not None


@pytest.mark.asyncio
async def test_memory_system_integration(runtime):
    """Test memory system integration."""
    memory = runtime.memory_manager
    
    # Store a memory item
    item = MemoryItem(
        content="Test memory content",
        metadata={"source": "test"},
    )
    
    await memory.store(item)
    
    # Retrieve memory
    results = await memory.search("Test memory", limit=5)
    assert len(results) > 0


@pytest.mark.asyncio
async def test_tool_registry_integration(runtime):
    """Test tool registry integration."""
    registry = runtime.tool_registry
    
    # Check that built-in tools are registered
    tools = registry.list_tools()
    assert len(tools) > 0
    
    # Check for specific built-in tools
    tool_names = [tool.name for tool in tools]
    assert "read_file" in tool_names
    assert "write_file" in tool_names


@pytest.mark.asyncio
async def test_orchestrator_integration(runtime):
    """Test orchestrator integration with all components."""
    from superagent.orchestration.orchestrator import Orchestrator
    
    orchestrator = Orchestrator(
        config=runtime.config,
        llm_provider=runtime.llm_provider,
        tool_registry=runtime.tool_registry,
        memory_manager=runtime.memory_manager,
        metrics_collector=runtime.metrics_collector,
    )
    
    await orchestrator.start()
    assert orchestrator.is_running
    
    # Test that all agents are initialized
    assert "planner" in orchestrator.agents
    assert "executor" in orchestrator.agents
    assert "memory" in orchestrator.agents
    assert "monitor" in orchestrator.agents
    
    await orchestrator.stop()
    assert not orchestrator.is_running


@pytest.mark.asyncio
async def test_event_bus_integration(runtime):
    """Test event bus communication between agents."""
    from superagent.orchestration.event_bus import EventBus, Event, EventType
    
    bus = EventBus()
    
    # Track received events
    received_events = []
    
    async def handler(event: Event):
        received_events.append(event)
    
    # Subscribe to events
    bus.subscribe(EventType.PLAN_CREATED, handler)
    
    # Publish event
    await bus.publish(
        Event(
            type=EventType.PLAN_CREATED,
            source="test",
            data={"test": "data"},
        )
    )
    
    # Wait for event processing
    await asyncio.sleep(0.1)
    
    # Verify event was received
    assert len(received_events) == 1
    assert received_events[0].type == EventType.PLAN_CREATED


@pytest.mark.asyncio
async def test_context_fusion_integration(runtime):
    """Test context fusion engine."""
    from superagent.orchestration.context_fusion import ContextFusionEngine
    
    fusion = ContextFusionEngine(runtime.memory_manager)
    
    # Fuse context
    context = await fusion.fuse_context(
        session_id="test-session",
        conversation_history=[
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there!"},
        ],
        query="What did we talk about?",
    )
    
    assert context is not None
    assert len(context.conversation_history) == 2


@pytest.mark.asyncio
async def test_monitoring_integration(runtime):
    """Test monitoring and metrics collection."""
    metrics = runtime.metrics_collector
    
    # Record some metrics
    metrics.increment("test.counter")
    metrics.gauge("test.gauge", 42.0)
    metrics.histogram("test.histogram", 100.0)
    
    # Get metrics
    all_metrics = metrics.get_all_metrics()
    assert len(all_metrics) > 0


@pytest.mark.asyncio
async def test_end_to_end_workflow(runtime):
    """Test complete end-to-end workflow."""
    from superagent.orchestration.orchestrator import Orchestrator
    
    # Create orchestrator
    orchestrator = Orchestrator(
        config=runtime.config,
        llm_provider=runtime.llm_provider,
        tool_registry=runtime.tool_registry,
        memory_manager=runtime.memory_manager,
        metrics_collector=runtime.metrics_collector,
    )
    
    await orchestrator.start()
    
    # Execute a simple goal
    result = await orchestrator.execute_goal(
        goal="List available tools",
        session_id="test-session",
    )
    
    # Verify result
    assert result is not None
    assert "status" in result
    
    await orchestrator.stop()


@pytest.mark.asyncio
async def test_plugin_system_integration(runtime):
    """Test plugin system integration."""
    from superagent.tools.plugin_system import UnifiedPluginSystem
    
    plugin_system = UnifiedPluginSystem(
        plugin_dir=runtime.config.data_dir / "plugins",
        tool_registry=runtime.tool_registry,
    )
    
    # Load plugins
    await plugin_system.load_all_plugins()
    
    # Check loaded plugins
    plugins = plugin_system.list_plugins()
    assert isinstance(plugins, list)


@pytest.mark.asyncio
async def test_security_integration(runtime):
    """Test security manager integration."""
    from superagent.core.security import SecurityManager
    
    security = SecurityManager()
    
    # Test file access validation
    assert security.validate_file_access("/tmp/test.txt")
    assert not security.validate_file_access("/etc/passwd")
    
    # Test encryption
    data = "sensitive data"
    encrypted = security.encrypt(data)
    decrypted = security.decrypt(encrypted)
    assert decrypted == data


@pytest.mark.asyncio
async def test_reflection_system_integration(runtime):
    """Test adaptive reflection system."""
    from superagent.agents.reflection import AdaptiveReflectionSystem
    from superagent.agents.models import ExecutionResult
    
    reflection = AdaptiveReflectionSystem()
    
    # Record execution
    result = ExecutionResult(
        task_id="test-task",
        success=True,
        output="Test output",
        steps_completed=3,
    )
    
    await reflection.record_execution(result)
    
    # Get statistics
    stats = reflection.get_statistics()
    assert "total_executions" in stats


@pytest.mark.asyncio
async def test_profiler_integration(runtime):
    """Test unified profiler."""
    from superagent.monitoring.profiler import UnifiedProfiler
    
    profiler = UnifiedProfiler()
    
    # Profile an operation
    async with profiler.profile_operation("test_operation"):
        await asyncio.sleep(0.01)
    
    # Get summary
    summary = profiler.get_summary()
    assert "total_operations" in summary or "message" in summary


@pytest.mark.asyncio
async def test_context_health_integration(runtime):
    """Test context health monitoring."""
    from superagent.orchestration.context_health import ContextHealthMonitor
    from superagent.orchestration.context_fusion import ContextFusionEngine, UnifiedContext
    
    fusion = ContextFusionEngine(runtime.memory_manager)
    monitor = ContextHealthMonitor(fusion)
    
    # Create test context
    context = UnifiedContext(
        conversation_history=[],
        memory_vectors=[],
        attached_files=[],
        active_plan=None,
    )
    
    # Check health
    report = await monitor.check_health(context)
    assert report is not None
    assert hasattr(report, "status")
    assert hasattr(report, "score")
