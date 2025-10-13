"""
Event Bus - Central async communication hub for all agents and subsystems.
"""

import asyncio
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set
from uuid import uuid4

from pydantic import BaseModel, Field

from superagent.core.logger import get_logger

logger = get_logger(__name__)


class EventType(str, Enum):
    """Standard event types for agent communication."""

    # Planning events
    PLAN_CREATED = "plan_created"
    PLAN_UPDATED = "plan_updated"
    PLAN_COMPLETED = "plan_completed"
    PLAN_FAILED = "plan_failed"

    # Execution events
    TOOL_EXECUTED = "tool_executed"
    TOOL_FAILED = "tool_failed"
    STEP_STARTED = "step_started"
    STEP_COMPLETED = "step_completed"

    # Memory events
    MEMORY_UPDATED = "memory_updated"
    MEMORY_RETRIEVED = "memory_retrieved"
    CONTEXT_FUSED = "context_fused"

    # Agent events
    AGENT_SPAWNED = "agent_spawned"
    AGENT_TERMINATED = "agent_terminated"
    AGENT_MESSAGE = "agent_message"

    # System events
    ERROR_OCCURRED = "error_occurred"
    METRIC_RECORDED = "metric_recorded"
    AUDIT_LOG = "audit_log"


class Event(BaseModel):
    """Event model for inter-agent communication."""

    id: str = Field(default_factory=lambda: str(uuid4()))
    type: EventType
    source: str  # Agent or subsystem that emitted the event
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    data: Dict[str, Any] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    correlation_id: Optional[str] = None  # For tracing related events


class EventBus:
    """
    Central async event bus for publish-subscribe communication.

    Enables decoupled agent coordination through event-driven architecture.
    """

    def __init__(self):
        self._subscribers: Dict[EventType, Set[Callable]] = {}
        self._event_history: List[Event] = []
        self._max_history = 1000
        self._lock = asyncio.Lock()

    async def publish(self, event: Event) -> None:
        """
        Publish an event to all subscribers.

        Args:
            event: Event to publish
        """
        async with self._lock:
            # Store in history
            self._event_history.append(event)
            if len(self._event_history) > self._max_history:
                self._event_history.pop(0)

            logger.debug(
                f"Event published: {event.type}",
                extra={
                    "event_id": event.id,
                    "source": event.source,
                    "correlation_id": event.correlation_id,
                },
            )

        # Notify subscribers
        subscribers = self._subscribers.get(event.type, set())
        if subscribers:
            await asyncio.gather(
                *[self._notify_subscriber(sub, event) for sub in subscribers],
                return_exceptions=True,
            )

    async def _notify_subscriber(
        self, subscriber: Callable, event: Event
    ) -> None:
        """Notify a single subscriber with error handling."""
        try:
            if asyncio.iscoroutinefunction(subscriber):
                await subscriber(event)
            else:
                subscriber(event)
        except Exception as e:
            logger.error(
                f"Subscriber error: {e}",
                extra={"event_type": event.type, "event_id": event.id},
            )

    def subscribe(
        self, event_type: EventType, callback: Callable[[Event], None]
    ) -> None:
        """
        Subscribe to events of a specific type.

        Args:
            event_type: Type of events to subscribe to
            callback: Async or sync function to call when event occurs
        """
        if event_type not in self._subscribers:
            self._subscribers[event_type] = set()
        self._subscribers[event_type].add(callback)
        logger.debug(f"Subscribed to {event_type}")

    def unsubscribe(
        self, event_type: EventType, callback: Callable[[Event], None]
    ) -> None:
        """Unsubscribe from events."""
        if event_type in self._subscribers:
            self._subscribers[event_type].discard(callback)

    def get_history(
        self,
        event_type: Optional[EventType] = None,
        correlation_id: Optional[str] = None,
        limit: int = 100,
    ) -> List[Event]:
        """
        Retrieve event history with optional filtering.

        Args:
            event_type: Filter by event type
            correlation_id: Filter by correlation ID
            limit: Maximum number of events to return

        Returns:
            List of events matching filters
        """
        events = self._event_history

        if event_type:
            events = [e for e in events if e.type == event_type]

        if correlation_id:
            events = [e for e in events if e.correlation_id == correlation_id]

        return events[-limit:]

    def clear_history(self) -> None:
        """Clear event history."""
        self._event_history.clear()
