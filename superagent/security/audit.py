"""
Audit logging system for security and compliance.

Tracks all security-relevant events and user actions.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

from superagent.core.logger import get_logger

logger = get_logger(__name__)


@dataclass
class AuditEvent:
    """An audit event representing a security-relevant action."""

    event_type: str
    user_id: Optional[str]
    timestamp: datetime = field(default_factory=datetime.utcnow)
    action: str = ""
    resource: str = ""
    result: str = "success"
    details: Dict[str, Any] = field(default_factory=dict)
    ip_address: Optional[str] = None


class AuditLogger:
    """
    Logs security and compliance events.

    Maintains an immutable audit trail of all security-relevant actions.
    """

    def __init__(self):
        self._events: List[AuditEvent] = []

    def log_event(
        self,
        event_type: str,
        user_id: Optional[str],
        action: str,
        resource: str,
        result: str = "success",
        details: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
    ) -> None:
        """Log an audit event."""
        event = AuditEvent(
            event_type=event_type,
            user_id=user_id,
            action=action,
            resource=resource,
            result=result,
            details=details or {},
            ip_address=ip_address,
        )
        self._events.append(event)
        logger.info(
            f"Audit event: {event_type} - {action} on {resource} by {user_id}",
            extra={"audit_event": event},
        )

    def log_authentication(
        self, user_id: str, success: bool, ip_address: Optional[str] = None
    ) -> None:
        """Log an authentication attempt."""
        self.log_event(
            event_type="authentication",
            user_id=user_id,
            action="login",
            resource="system",
            result="success" if success else "failure",
            ip_address=ip_address,
        )

    def log_authorization(
        self,
        user_id: str,
        permission: str,
        resource: str,
        granted: bool,
    ) -> None:
        """Log an authorization check."""
        self.log_event(
            event_type="authorization",
            user_id=user_id,
            action="check_permission",
            resource=resource,
            result="granted" if granted else "denied",
            details={"permission": permission},
        )

    def log_data_access(
        self, user_id: str, resource: str, action: str
    ) -> None:
        """Log data access."""
        self.log_event(
            event_type="data_access",
            user_id=user_id,
            action=action,
            resource=resource,
        )

    def log_configuration_change(
        self, user_id: str, setting: str, old_value: Any, new_value: Any
    ) -> None:
        """Log a configuration change."""
        self.log_event(
            event_type="configuration",
            user_id=user_id,
            action="update",
            resource=setting,
            details={"old_value": old_value, "new_value": new_value},
        )

    def get_events(
        self,
        user_id: Optional[str] = None,
        event_type: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: Optional[int] = None,
    ) -> List[AuditEvent]:
        """Query audit events with filters."""
        events = self._events

        if user_id:
            events = [e for e in events if e.user_id == user_id]

        if event_type:
            events = [e for e in events if e.event_type == event_type]

        if start_time:
            events = [e for e in events if e.timestamp >= start_time]

        if end_time:
            events = [e for e in events if e.timestamp <= end_time]

        if limit:
            events = events[-limit:]

        return events
