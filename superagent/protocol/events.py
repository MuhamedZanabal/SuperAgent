"""
NDJSON event protocol implementation.
"""

from __future__ import annotations
from pydantic import BaseModel, Field
from typing import Optional, Literal, List, Dict, Any
from datetime import datetime
import uuid
import sys
import json

from superagent.compat import StrEnum


class EventType(StrEnum):
    """Event types for protocol."""
    # Session events
    SESSION_STARTED = "session.started"
    SESSION_RESTORED = "session.restored"
    SESSION_CHECKPOINTED = "session.checkpointed"
    
    # Plan events
    PLAN_CREATED = "plan.created"
    PLAN_STEP_STARTED = "plan.step_started"
    PLAN_STEP_FINISHED = "plan.step_finished"
    
    # Tool events
    TOOL_REQUESTED = "tool.requested"
    TOOL_APPROVED = "tool.approved"
    TOOL_REJECTED = "tool.rejected"
    TOOL_RESULT = "tool.result"
    
    # Diff events
    DIFF_PREVIEW = "diff.preview"
    DIFF_APPLIED = "diff.applied"
    DIFF_PARTIAL_APPLIED = "diff.partial_applied"
    DIFF_ROLLBACK = "diff.rollback"
    
    # Error events
    ERROR_USER = "error.user"
    ERROR_SYSTEM = "error.system"
    ERROR_TOOL = "error.tool"
    
    # Metrics events
    METRICS_TICK = "metrics.tick"
    
    # User events
    USER_CANCEL = "user.cancel"


class BaseEvent(BaseModel):
    """Base event with required fields."""
    event: str
    ts: datetime = Field(default_factory=datetime.utcnow)
    session_id: str
    request_id: str = Field(default_factory=lambda: uuid.uuid4().hex)
    correlation_id: Optional[str] = None


class SessionEvent(BaseEvent):
    """Session lifecycle events."""
    event: Literal[
        EventType.SESSION_STARTED,
        EventType.SESSION_RESTORED,
        EventType.SESSION_CHECKPOINTED,
    ]
    checkpoint_id: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class PlanEvent(BaseEvent):
    """Plan execution events."""
    event: Literal[
        EventType.PLAN_CREATED,
        EventType.PLAN_STEP_STARTED,
        EventType.PLAN_STEP_FINISHED,
    ]
    steps: Optional[List[str]] = None
    step_index: Optional[int] = None
    step_name: Optional[str] = None
    intent: Optional[str] = None
    confidence: Optional[float] = None
    result: Optional[Dict[str, Any]] = None


class ToolEvent(BaseEvent):
    """Tool execution events."""
    event: Literal[
        EventType.TOOL_REQUESTED,
        EventType.TOOL_APPROVED,
        EventType.TOOL_REJECTED,
        EventType.TOOL_RESULT,
    ]
    tool_name: str
    tool_args: Dict[str, Any] = Field(default_factory=dict)
    result: Optional[Any] = None
    error: Optional[str] = None
    requires_consent: bool = False


class DiffEvent(BaseEvent):
    """Diff operation events."""
    event: Literal[
        EventType.DIFF_PREVIEW,
        EventType.DIFF_APPLIED,
        EventType.DIFF_PARTIAL_APPLIED,
        EventType.DIFF_ROLLBACK,
    ]
    file_path: str
    diff_content: Optional[str] = None
    hunks_applied: Optional[List[int]] = None
    checkpoint_id: Optional[str] = None


class ErrorEvent(BaseEvent):
    """Error events."""
    event: Literal[
        EventType.ERROR_USER,
        EventType.ERROR_SYSTEM,
        EventType.ERROR_TOOL,
    ]
    error_type: str
    error_message: str
    error_details: Optional[Dict[str, Any]] = None
    recoverable: bool = False


class MetricsEvent(BaseEvent):
    """Metrics tick events."""
    event: Literal[EventType.METRICS_TICK]
    metrics: Dict[str, Any]


def emit(e: BaseEvent) -> None:
    """
    Emit event as NDJSON to stdout.
    
    Args:
        e: Event to emit
    """
    sys.stdout.write(json.dumps(e.model_dump(mode="json"), default=str) + "\n")
    sys.stdout.flush()
