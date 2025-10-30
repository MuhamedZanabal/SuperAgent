"""
OpenTelemetry integration for tracing and metrics.
"""

from typing import Optional
import os

from superagent.core.logger import get_logger

logger = get_logger(__name__)

# Global tracer and meter
_tracer = None
_meter = None


def setup_telemetry(service_name: str = "superagent") -> None:
    """
    Setup OpenTelemetry tracing and metrics.
    
    Args:
        service_name: Service name for telemetry
    """
    global _tracer, _meter
    
    try:
        from opentelemetry import trace, metrics
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import BatchSpanProcessor
        from opentelemetry.sdk.metrics import MeterProvider
        from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
        
        # Check if OTEL is enabled
        if not os.getenv("OTEL_ENABLED", "false").lower() == "true":
            logger.info("OpenTelemetry disabled")
            return
        
        # Setup tracing
        trace_provider = TracerProvider()
        
        # Add OTLP exporter if endpoint is configured
        otlp_endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT")
        if otlp_endpoint:
            try:
                from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
                
                otlp_exporter = OTLPSpanExporter(endpoint=otlp_endpoint)
                span_processor = BatchSpanProcessor(otlp_exporter)
                trace_provider.add_span_processor(span_processor)
                logger.info(f"OTLP trace exporter configured: {otlp_endpoint}")
            except ImportError:
                logger.warning("OTLP exporter not available, install opentelemetry-exporter-otlp")
        
        trace.set_tracer_provider(trace_provider)
        _tracer = trace.get_tracer(service_name)
        
        # Setup metrics
        meter_provider = MeterProvider()
        metrics.set_meter_provider(meter_provider)
        _meter = metrics.get_meter(service_name)
        
        logger.info("OpenTelemetry initialized")
        
    except ImportError:
        logger.warning("OpenTelemetry not available, install opentelemetry-api and opentelemetry-sdk")


def get_tracer():
    """Get OpenTelemetry tracer."""
    if _tracer is None:
        # Return no-op tracer
        try:
            from opentelemetry import trace
            return trace.get_tracer("superagent")
        except ImportError:
            return None
    return _tracer


def get_meter():
    """Get OpenTelemetry meter."""
    if _meter is None:
        # Return no-op meter
        try:
            from opentelemetry import metrics
            return metrics.get_meter("superagent")
        except ImportError:
            return None
    return _meter
