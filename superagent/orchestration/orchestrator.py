"""
Central Orchestrator - Coordinates all agents and subsystems.
"""

import asyncio
from typing import Dict, List, Optional
from uuid import uuid4

from superagent.agents.advanced_planner import UnifiedAdvancedPlanner
from superagent.agents.executor import Executor  # Fixed import from TaskExecutor to Executor
from superagent.core.config import SuperAgentConfig  # Fixed import from Settings to SuperAgentConfig
from superagent.core.logger import get_logger
from superagent.llm.provider import UnifiedLLMProvider
from superagent.memory.manager import MemoryManager
from superagent.monitoring.metrics import MetricsCollector
from superagent.orchestration.agents import (
    ExecutorAgent,
    MemoryAgent,
    MonitorAgent,
    PlannerAgent,
)
from superagent.orchestration.context_fusion import ContextFusionEngine, UnifiedContext
from superagent.orchestration.event_bus import Event, EventBus, EventType
from superagent.tools.registry import ToolRegistry

logger = get_logger(__name__)


class Orchestrator:
    """
    Central orchestrator for autonomous multi-agent coordination.

    Manages:
    - Event bus for inter-agent communication
    - Context fusion engine
    - Specialized agents (Planner, Executor, Memory, Monitor)
    - Autonomous workflow loops
    """

    def __init__(
        self,
        config: SuperAgentConfig,  # Fixed parameter type from settings to config
        llm_provider: UnifiedLLMProvider,
        tool_registry: ToolRegistry,
        memory_manager: MemoryManager,
        metrics_collector: MetricsCollector,
    ):
        self.config = config  # Renamed from settings to config
        self.llm_provider = llm_provider
        self.tool_registry = tool_registry
        self.memory_manager = memory_manager
        self.metrics_collector = metrics_collector

        # Core components
        self.event_bus = EventBus()
        self.context_fusion = ContextFusionEngine(memory_manager)

        # Agents
        self.agents: Dict[str, any] = {}
        self._initialize_agents()

        self.is_running = False

    def _initialize_agents(self) -> None:
        """Initialize specialized agents."""
        # Planner agent
        planner = UnifiedAdvancedPlanner(
            llm_provider=self.llm_provider,
            tool_registry=self.tool_registry,
        )
        self.agents["planner"] = PlannerAgent(
            agent_id="planner_001",
            event_bus=self.event_bus,
            planner=planner,
        )

        # Executor agent
        executor = Executor(  # Fixed class name from TaskExecutor to Executor
            tool_registry=self.tool_registry,
            llm_provider=self.llm_provider,
        )
        self.agents["executor"] = ExecutorAgent(
            agent_id="executor_001",
            event_bus=self.event_bus,
            executor=executor,
        )

        # Memory agent
        self.agents["memory"] = MemoryAgent(
            agent_id="memory_001",
            event_bus=self.event_bus,
            memory_manager=self.memory_manager,
        )

        # Monitor agent
        self.agents["monitor"] = MonitorAgent(
            agent_id="monitor_001",
            event_bus=self.event_bus,
            metrics_collector=self.metrics_collector,
        )

    async def start(self) -> None:
        """Start the orchestrator and all agents."""
        if self.is_running:
            logger.warning("Orchestrator already running")
            return

        logger.info("Starting orchestrator...")
        self.is_running = True

        # Start all agents
        for agent_id, agent in self.agents.items():
            await agent.start()
            logger.info(f"Started agent: {agent_id}")

        logger.info("Orchestrator started successfully")

    async def stop(self) -> None:
        """Stop the orchestrator and all agents."""
        if not self.is_running:
            return

        logger.info("Stopping orchestrator...")
        self.is_running = False

        # Stop all agents
        for agent_id, agent in self.agents.items():
            await agent.stop()
            logger.info(f"Stopped agent: {agent_id}")

        logger.info("Orchestrator stopped")

    async def execute_goal(
        self,
        goal: str,
        session_id: str,
        conversation_history: Optional[List[Dict[str, str]]] = None,
        active_files: Optional[List[str]] = None,
    ) -> Dict[str, any]:
        """
        Execute a goal autonomously through agent coordination.

        Args:
            goal: User goal to achieve
            session_id: Session identifier
            conversation_history: Recent conversation
            active_files: Files in context

        Returns:
            Execution result with plan, steps, and outputs
        """
        correlation_id = str(uuid4())

        logger.info(
            f"Executing goal: {goal}",
            extra={"session_id": session_id, "correlation_id": correlation_id},
        )

        # Fuse context
        context = await self.context_fusion.fuse_context(
            session_id=session_id,
            conversation_history=conversation_history or [],
            active_files=active_files,
            query=goal,
        )

        # Publish plan creation event
        await self.event_bus.publish(
            Event(
                type=EventType.PLAN_CREATED,
                source="orchestrator",
                data={"goal": goal, "context": context.model_dump()},
                correlation_id=correlation_id,
            )
        )

        # Wait for plan completion or failure
        result = await self._wait_for_completion(correlation_id, timeout=60.0)

        return result

    async def _wait_for_completion(
        self, correlation_id: str, timeout: float = 60.0
    ) -> Dict[str, any]:
        """Wait for execution to complete."""
        start_time = asyncio.get_event_loop().time()

        while asyncio.get_event_loop().time() - start_time < timeout:
            # Check event history for completion
            events = self.event_bus.get_history(correlation_id=correlation_id)

            # Check for completion or failure
            for event in reversed(events):
                if event.type == EventType.PLAN_COMPLETED:
                    return {"status": "completed", "data": event.data}
                elif event.type == EventType.PLAN_FAILED:
                    return {"status": "failed", "error": event.data.get("error")}

            await asyncio.sleep(0.1)

        return {"status": "timeout", "error": "Execution timed out"}

    def get_unified_context(self, session_id: str) -> Optional[UnifiedContext]:
        """Get the current unified context for a session."""
        return self.context_fusion.get_cached_context(session_id)
