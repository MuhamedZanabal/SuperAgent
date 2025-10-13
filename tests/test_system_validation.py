"""
System validation tests - verify all components are properly integrated.
"""

import pytest
from pathlib import Path

from superagent.core.runtime import SuperAgentRuntime
from superagent.core.config import SuperAgentConfig


def test_all_imports():
    """Test that all modules can be imported without errors."""
    # Core
    from superagent.core import (
        SuperAgentRuntime,
        SuperAgentConfig,
        get_logger,
        SecurityManager,
    )
    
    # LLM
    from superagent.llm import (
        BaseLLMProvider,
        UnifiedLLMProvider,
        LiteLLMProvider,
        create_default_provider,
    )
    
    # Memory
    from superagent.memory import (
        MemoryManager,
        VectorStore,
        EmbeddingProvider,
        ContextManager,
    )
    
    # Agents
    from superagent.agents import (
        BaseAgent,
        Planner,
        Executor,
        ReActAgent,
    )
    
    # Tools
    from superagent.tools import (
        BaseTool,
        ToolRegistry,
        ToolExecutor,
    )
    
    # Orchestration
    from superagent.orchestration import (
        EventBus,
        Orchestrator,
        ContextFusionEngine,
    )
    
    # Monitoring
    from superagent.monitoring import (
        MetricsCollector,
        TelemetryManager,
        HealthChecker,
    )
    
    # Security
    from superagent.security import (
        RBACManager,
        AuditLogger,
        SecretsManager,
    )
    
    # CLI
    from superagent.cli import (
        app,
        cli_main,
    )
    
    assert True  # All imports successful


def test_config_validation():
    """Test configuration validation."""
    config = SuperAgentConfig()
    
    # Check required fields
    assert config.data_dir is not None
    assert config.log_level is not None
    assert config.providers is not None
    
    # Check defaults
    assert isinstance(config.data_dir, Path)
    assert config.max_tokens > 0
    assert config.temperature >= 0.0


def test_runtime_structure():
    """Test runtime has all required components."""
    runtime = SuperAgentRuntime()
    
    # Check attributes exist
    assert hasattr(runtime, "config")
    assert hasattr(runtime, "llm_provider")
    assert hasattr(runtime, "memory_manager")
    assert hasattr(runtime, "tool_registry")
    assert hasattr(runtime, "metrics_collector")
    assert hasattr(runtime, "telemetry_manager")
    assert hasattr(runtime, "audit_logger")
    
    # Check methods exist
    assert hasattr(runtime, "initialize")
    assert hasattr(runtime, "shutdown")
    assert hasattr(runtime, "is_initialized")


def test_orchestrator_structure():
    """Test orchestrator has all required components."""
    from superagent.orchestration.orchestrator import Orchestrator
    from superagent.core.config import SuperAgentConfig
    from superagent.llm.factory import create_default_provider
    from superagent.tools.registry import get_global_registry
    from superagent.memory.manager import MemoryManager
    from superagent.monitoring.metrics import MetricsCollector
    from superagent.memory.embeddings import SentenceTransformerEmbeddings
    from superagent.memory.vector_store import ChromaDBStore
    
    config = SuperAgentConfig()
    provider = create_default_provider(config)
    registry = get_global_registry()
    
    embeddings = SentenceTransformerEmbeddings()
    vector_store = ChromaDBStore(
        collection_name="test",
        embedding_provider=embeddings,
    )
    memory = MemoryManager(vector_store=vector_store, embedding_provider=embeddings)
    metrics = MetricsCollector()
    
    orchestrator = Orchestrator(
        config=config,
        llm_provider=provider,
        tool_registry=registry,
        memory_manager=memory,
        metrics_collector=metrics,
    )
    
    # Check components
    assert orchestrator.config is not None
    assert orchestrator.llm_provider is not None
    assert orchestrator.tool_registry is not None
    assert orchestrator.memory_manager is not None
    assert orchestrator.event_bus is not None
    assert orchestrator.context_fusion is not None
    assert len(orchestrator.agents) == 4  # planner, executor, memory, monitor


def test_cli_commands_registered():
    """Test that all CLI commands are registered."""
    from superagent.cli.interactive.commands import CommandRegistry
    
    registry = CommandRegistry()
    commands = registry.get_all_commands()
    
    # Check essential commands exist
    command_names = [cmd.name for cmd in commands]
    
    assert "help" in command_names
    assert "settings" in command_names
    assert "clear" in command_names
    assert "exit" in command_names
    assert "model" in command_names
    assert "memory" in command_names
    assert "tools" in command_names
    assert "plan" in command_names
    assert "exec" in command_names
    assert "monitor" in command_names
    assert "health" in command_names
    assert "reflect" in command_names


def test_builtin_tools_available():
    """Test that built-in tools are available."""
    from superagent.tools.builtin import (
        ReadFileTool,
        WriteFileTool,
        ListFilesTool,
        WebSearchTool,
        WebScrapeTool,
        PythonExecuteTool,
        ShellCommandTool,
    )
    
    # Instantiate all tools
    tools = [
        ReadFileTool(),
        WriteFileTool(),
        ListFilesTool(),
        WebSearchTool(),
        WebScrapeTool(),
        PythonExecuteTool(),
        ShellCommandTool(),
    ]
    
    # Check all have required attributes
    for tool in tools:
        assert hasattr(tool, "name")
        assert hasattr(tool, "description")
        assert hasattr(tool, "parameters")
        assert hasattr(tool, "execute")


def test_event_types_defined():
    """Test that all event types are defined."""
    from superagent.orchestration.event_bus import EventType
    
    # Check essential event types exist
    assert hasattr(EventType, "PLAN_CREATED")
    assert hasattr(EventType, "PLAN_UPDATED")
    assert hasattr(EventType, "PLAN_COMPLETED")
    assert hasattr(EventType, "PLAN_FAILED")
    assert hasattr(EventType, "STEP_STARTED")
    assert hasattr(EventType, "STEP_COMPLETED")
    assert hasattr(EventType, "MEMORY_UPDATED")


def test_agent_states_defined():
    """Test that agent states are defined."""
    from superagent.agents.base import AgentState
    
    # Check states exist
    assert hasattr(AgentState, "IDLE")
    assert hasattr(AgentState, "PLANNING")
    assert hasattr(AgentState, "EXECUTING")
    assert hasattr(AgentState, "REFLECTING")
    assert hasattr(AgentState, "ERROR")


def test_memory_types_defined():
    """Test that memory types are defined."""
    from superagent.memory.base import MemoryType
    
    # Check types exist
    assert hasattr(MemoryType, "SHORT_TERM")
    assert hasattr(MemoryType, "WORKING")
    assert hasattr(MemoryType, "LONG_TERM")


def test_provider_types_defined():
    """Test that provider types are defined."""
    from superagent.core.config import ProviderType
    
    # Check types exist
    assert hasattr(ProviderType, "OPENAI")
    assert hasattr(ProviderType, "ANTHROPIC")
    assert hasattr(ProviderType, "GROQ")
    assert hasattr(ProviderType, "TOGETHER")
    assert hasattr(ProviderType, "OPENROUTER")
    assert hasattr(ProviderType, "OLLAMA")
