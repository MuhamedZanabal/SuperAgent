"""
Specialized agents for autonomous coordination.
"""

import asyncio
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

from superagent.agents.advanced_planner import UnifiedAdvancedPlanner
from superagent.agents.executor import Executor  # Fixed import from TaskExecutor to Executor
from superagent.core.logger import get_logger
from superagent.memory.manager import MemoryManager
from superagent.monitoring.metrics import MetricsCollector
from superagent.orchestration.event_bus import Event, EventBus, EventType
from superagent.tools.registry import ToolRegistry

logger = get_logger(__name__)


class BaseAgent(ABC):
    """Base class for specialized agents."""

    def __init__(self, agent_id: str, event_bus: EventBus):
        self.agent_id = agent_id
        self.event_bus = event_bus
        self.is_running = False

    @abstractmethod
    async def start(self) -> None:
        """Start the agent."""
        pass

    @abstractmethod
    async def stop(self) -> None:
        """Stop the agent."""
        pass

    @abstractmethod
    async def handle_event(self, event: Event) -> None:
        """Handle an event from the event bus."""
        pass


class PlannerAgent(BaseAgent):
    """Agent responsible for task planning and decomposition."""

    def __init__(
        self,
        agent_id: str,
        event_bus: EventBus,
        planner: UnifiedAdvancedPlanner,
    ):
        super().__init__(agent_id, event_bus)
        self.planner = planner

    async def start(self) -> None:
        """Start listening for planning requests."""
        self.is_running = True
        self.event_bus.subscribe(EventType.PLAN_CREATED, self.handle_event)
        logger.info(f"PlannerAgent {self.agent_id} started")

    async def stop(self) -> None:
        """Stop the agent."""
        self.is_running = False
        self.event_bus.unsubscribe(EventType.PLAN_CREATED, self.handle_event)
        logger.info(f"PlannerAgent {self.agent_id} stopped")

    async def handle_event(self, event: Event) -> None:
        """Handle planning events."""
        if event.type == EventType.PLAN_CREATED:
            goal = event.data.get("goal")
            if goal:
                try:
                    plan = await self.planner.create_plan(goal)
                    await self.event_bus.publish(
                        Event(
                            type=EventType.PLAN_UPDATED,
                            source=self.agent_id,
                            data={"plan": plan.model_dump()},
                            correlation_id=event.correlation_id,
                        )
                    )
                except Exception as e:
                    logger.error(f"Planning failed: {e}")
                    await self.event_bus.publish(
                        Event(
                            type=EventType.PLAN_FAILED,
                            source=self.agent_id,
                            data={"error": str(e)},
                            correlation_id=event.correlation_id,
                        )
                    )


class ExecutorAgent(BaseAgent):
    """Agent responsible for executing plans and tools."""

    def __init__(
        self,
        agent_id: str,
        event_bus: EventBus,
        executor: Executor,  # Fixed type from TaskExecutor to Executor
    ):
        super().__init__(agent_id, event_bus)
        self.executor = executor

    async def start(self) -> None:
        """Start listening for execution requests."""
        self.is_running = True
        self.event_bus.subscribe(EventType.PLAN_UPDATED, self.handle_event)
        self.event_bus.subscribe(EventType.STEP_STARTED, self.handle_event)
        logger.info(f"ExecutorAgent {self.agent_id} started")

    async def stop(self) -> None:
        """Stop the agent."""
        self.is_running = False
        self.event_bus.unsubscribe(EventType.PLAN_UPDATED, self.handle_event)
        self.event_bus.unsubscribe(EventType.STEP_STARTED, self.handle_event)
        logger.info(f"ExecutorAgent {self.agent_id} stopped")

    async def handle_event(self, event: Event) -> None:
        """Handle execution events."""
        if event.type == EventType.PLAN_UPDATED:
            plan_data = event.data.get("plan")
            if plan_data:
                # Execute plan steps
                await self._execute_plan(plan_data, event.correlation_id)

    async def _execute_plan(
        self, plan_data: Dict[str, Any], correlation_id: Optional[str]
    ) -> None:
        """Execute a plan step by step."""
        try:
            # Simplified execution - in production, use full executor
            steps = plan_data.get("steps", [])
            for step in steps:
                await self.event_bus.publish(
                    Event(
                        type=EventType.STEP_STARTED,
                        source=self.agent_id,
                        data={"step": step},
                        correlation_id=correlation_id,
                    )
                )
                # Execute step...
                await asyncio.sleep(0.1)  # Simulate work
                await self.event_bus.publish(
                    Event(
                        type=EventType.STEP_COMPLETED,
                        source=self.agent_id,
                        data={"step": step},
                        correlation_id=correlation_id,
                    )
                )
        except Exception as e:
            logger.error(f"Execution failed: {e}")


class MemoryAgent(BaseAgent):
    """Agent responsible for memory management and retrieval."""

    def __init__(
        self,
        agent_id: str,
        event_bus: EventBus,
        memory_manager: MemoryManager,
    ):
        super().__init__(agent_id, event_bus)
        self.memory_manager = memory_manager

    async def start(self) -> None:
        """Start listening for memory events."""
        self.is_running = True
        self.event_bus.subscribe(EventType.MEMORY_UPDATED, self.handle_event)
        self.event_bus.subscribe(EventType.STEP_COMPLETED, self.handle_event)
        logger.info(f"MemoryAgent {self.agent_id} started")

    async def stop(self) -> None:
        """Stop the agent."""
        self.is_running = False
        self.event_bus.unsubscribe(EventType.MEMORY_UPDATED, self.handle_event)
        self.event_bus.unsubscribe(EventType.STEP_COMPLETED, self.handle_event)
        logger.info(f"MemoryAgent {self.agent_id} stopped")

    async def handle_event(self, event: Event) -> None:
        """Handle memory events."""
        if event.type == EventType.STEP_COMPLETED:
            # Store completed step in memory
            step_data = event.data.get("step")
            if step_data:
                # Store in memory...
                pass


class MonitorAgent(BaseAgent):
    """Agent responsible for monitoring and metrics."""

    def __init__(
        self,
        agent_id: str,
        event_bus: EventBus,
        metrics_collector: MetricsCollector,
    ):
        super().__init__(agent_id, event_bus)
        self.metrics_collector = metrics_collector

    async def start(self) -> None:
        """Start monitoring all events."""
        self.is_running = True
        # Subscribe to all event types
        for event_type in EventType:
            self.event_bus.subscribe(event_type, self.handle_event)
        logger.info(f"MonitorAgent {self.agent_id} started")

    async def stop(self) -> None:
        """Stop the agent."""
        self.is_running = False
        for event_type in EventType:
            self.event_bus.unsubscribe(event_type, self.handle_event)
        logger.info(f"MonitorAgent {self.agent_id} stopped")

    async def handle_event(self, event: Event) -> None:
        """Record metrics for all events."""
        self.metrics_collector.increment(f"event.{event.type}")
        self.metrics_collector.increment(f"agent.{event.source}.events")
