"""
Telemetry system for tracking events and user actions.

Provides event tracking, session management, and usage analytics.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import uuid4

from superagent.core.logger import get_logger

logger = get_logger(__name__)


@dataclass
class TelemetryEvent:
    """A telemetry event representing a user action or system event."""

    event_type: str
    timestamp: datetime = field(default_factory=datetime.utcnow)
    session_id: Optional[str] = None
    user_id: Optional[str] = None
    properties: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


class TelemetryManager:
    """
    Manages telemetry events and session tracking.

    Tracks user actions, system events, and usage patterns.
    """

    def __init__(self):
        self._events: List[TelemetryEvent] = []
        self._session_id: str = str(uuid4())
        self._user_id: Optional[str] = None

    def set_user_id(self, user_id: str) -> None:
        """Set the current user ID."""
        self._user_id = user_id
        logger.info(f"User ID set: {user_id}")

    def set_session_id(self, session_id: str) -> None:
        """Set the current session ID."""
        self._session_id = session_id
        logger.info(f"Session ID set: {session_id}")

    def track_event(
        self,
        event_type: str,
        properties: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Track a telemetry event."""
        event = TelemetryEvent(
            event_type=event_type,
            session_id=self._session_id,
            user_id=self._user_id,
            properties=properties or {},
            metadata=metadata or {},
        )
        self._events.append(event)
        logger.debug(f"Event tracked: {event_type}", extra={"event": event})

    def track_llm_call(
        self,
        provider: str,
        model: str,
        tokens: int,
        duration: float,
        success: bool,
    ) -> None:
        """Track an LLM API call."""
        self.track_event(
            "llm_call",
            properties={
                "provider": provider,
                "model": model,
                "tokens": tokens,
                "duration": duration,
                "success": success,
            },
        )

    def track_tool_execution(
        self, tool_name: str, duration: float, success: bool, error: Optional[str] = None
    ) -> None:
        """Track a tool execution."""
        self.track_event(
            "tool_execution",
            properties={
                "tool_name": tool_name,
                "duration": duration,
                "success": success,
                "error": error,
            },
        )

    def track_agent_step(
        self, agent_type: str, step_type: str, success: bool
    ) -> None:
        """Track an agent execution step."""
        self.track_event(
            "agent_step",
            properties={
                "agent_type": agent_type,
                "step_type": step_type,
                "success": success,
            },
        )

    def get_events(
        self,
        event_type: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> List[TelemetryEvent]:
        """Get telemetry events, optionally filtered by type."""
        events = self._events
        if event_type:
            events = [e for e in events if e.event_type == event_type]
        if limit:
            events = events[-limit:]
        return events

    def get_session_events(self) -> List[TelemetryEvent]:
        """Get all events for the current session."""
        return [e for e in self._events if e.session_id == self._session_id]

    def clear_events(self) -> None:
        """Clear all telemetry events."""
        self._events.clear()
        logger.info("Telemetry events cleared")
