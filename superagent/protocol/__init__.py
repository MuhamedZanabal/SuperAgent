"""
NDJSON event protocol for headless mode.
"""

from superagent.protocol.events import (
    BaseEvent,
    SessionEvent,
    PlanEvent,
    ToolEvent,
    DiffEvent,
    ErrorEvent,
    MetricsEvent,
    emit,
)

__all__ = [
    "BaseEvent",
    "SessionEvent",
    "PlanEvent",
    "ToolEvent",
    "DiffEvent",
    "ErrorEvent",
    "MetricsEvent",
    "emit",
]
