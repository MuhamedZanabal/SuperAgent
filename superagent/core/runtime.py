"""
SuperAgent Runtime - Central runtime coordinator for the entire system.
"""

import asyncio
from typing import Optional
from pathlib import Path

from superagent.core.config import SuperAgentConfig, get_config
from superagent.core.logger import get_logger, setup_logging
from superagent.llm.factory import create_default_provider
from superagent.llm.provider import UnifiedLLMProvider
from superagent.memory.manager import MemoryManager
from superagent.memory.embeddings import SentenceTransformerEmbeddings
from superagent.memory.vector_store import ChromaDBStore
from superagent.tools.registry import ToolRegistry, get_global_registry
from superagent.tools.builtin import (
    ReadFileTool,
    WriteFileTool,
    ListFilesTool,
    WebSearchTool,
    WebScrapeTool,
    PythonExecuteTool,
    ShellCommandTool,
)
from superagent.monitoring.metrics import MetricsCollector
from superagent.monitoring.telemetry import TelemetryManager
from superagent.security.audit import AuditLogger

logger = get_logger(__name__)


class SuperAgentRuntime:
    """
    Central runtime that initializes and coordinates all SuperAgent subsystems.
    
    This is the main entry point for programmatic usage of SuperAgent.
    It handles initialization, configuration, and lifecycle management of all components.
    """
    
    def __init__(self, config: Optional[SuperAgentConfig] = None):
        """
        Initialize the SuperAgent runtime.
        
        Args:
            config: Optional configuration. If not provided, loads from environment/file.
        """
        self.config = config or get_config()
        self._initialized = False
        
        # Core components
        self.llm_provider: Optional[UnifiedLLMProvider] = None
        self.memory_manager: Optional[MemoryManager] = None
        self.tool_registry: Optional[ToolRegistry] = None
        self.metrics_collector: Optional[MetricsCollector] = None
        self.telemetry_manager: Optional[TelemetryManager] = None
        self.audit_logger: Optional[AuditLogger] = None
        
        logger.info("SuperAgent runtime created", extra={"version": "0.1.0"})
    
    async def initialize(self) -> None:
        """Initialize all subsystems."""
        if self._initialized:
            logger.warning("Runtime already initialized")
            return
        
        logger.info("Initializing SuperAgent runtime...")
        
        # Setup logging
        setup_logging(self.config.log_level, self.config.log_file)
        
        # Initialize LLM provider
        logger.info("Initializing LLM provider...")
        self.llm_provider = create_default_provider(self.config)
        
        # Initialize memory system
        logger.info("Initializing memory system...")
        embeddings = SentenceTransformerEmbeddings()
        vector_store = ChromaDBStore(
            collection_name="superagent_memory",
            persist_directory=str(self.config.data_dir / "chroma"),
            embedding_provider=embeddings,
        )
        self.memory_manager = MemoryManager(
            vector_store=vector_store,
            embedding_provider=embeddings,
        )
        
        # Initialize tool registry
        logger.info("Initializing tool registry...")
        self.tool_registry = get_global_registry()
        self._register_builtin_tools()
        
        # Initialize monitoring
        logger.info("Initializing monitoring...")
        self.metrics_collector = MetricsCollector()
        self.telemetry_manager = TelemetryManager()
        self.audit_logger = AuditLogger(log_dir=self.config.data_dir / "audit")
        
        self._initialized = True
        logger.info("SuperAgent runtime initialized successfully")
    
    def _register_builtin_tools(self) -> None:
        """Register built-in tools."""
        tools = [
            ReadFileTool(),
            WriteFileTool(),
            ListFilesTool(),
            WebSearchTool(),
            WebScrapeTool(),
            PythonExecuteTool(),
            ShellCommandTool(),
        ]
        
        for tool in tools:
            self.tool_registry.register(tool)
        
        logger.info(f"Registered {len(tools)} built-in tools")
    
    async def shutdown(self) -> None:
        """Shutdown all subsystems gracefully."""
        if not self._initialized:
            return
        
        logger.info("Shutting down SuperAgent runtime...")
        
        # Cleanup resources
        if self.memory_manager:
            # Save any pending memory
            pass
        
        if self.metrics_collector:
            # Flush metrics
            pass
        
        self._initialized = False
        logger.info("SuperAgent runtime shutdown complete")
    
    async def __aenter__(self):
        """Async context manager entry."""
        await self.initialize()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.shutdown()
    
    def is_initialized(self) -> bool:
        """Check if runtime is initialized."""
        return self._initialized


# Global runtime instance
_runtime: Optional[SuperAgentRuntime] = None


def get_runtime() -> SuperAgentRuntime:
    """Get or create the global runtime instance."""
    global _runtime
    if _runtime is None:
        _runtime = SuperAgentRuntime()
    return _runtime


async def initialize_runtime(config: Optional[SuperAgentConfig] = None) -> SuperAgentRuntime:
    """Initialize and return the global runtime."""
    global _runtime
    if _runtime is None:
        _runtime = SuperAgentRuntime(config)
    
    if not _runtime.is_initialized():
        await _runtime.initialize()
    
    return _runtime
