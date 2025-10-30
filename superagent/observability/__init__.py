"""
Observability layer with OpenTelemetry integration.
"""

from superagent.observability.otel import setup_telemetry, get_tracer, get_meter
from superagent.observability.redaction import redact_secrets

__all__ = ["setup_telemetry", "get_tracer", "get_meter", "redact_secrets"]
