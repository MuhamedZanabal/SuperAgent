"""Tests for monitoring and analytics systems."""

import pytest
from datetime import datetime, timedelta

from superagent.monitoring.metrics import MetricsCollector, MetricType, Timer
from superagent.monitoring.telemetry import TelemetryManager
from superagent.monitoring.health import HealthChecker, HealthStatus
from superagent.monitoring.analytics import AnalyticsTracker


def test_metrics_collector():
    """Test metrics collection."""
    collector = MetricsCollector()

    # Test counter
    collector.increment("requests")
    collector.increment("requests", 2.0)
    assert collector.get_counter("requests") == 3.0

    # Test gauge
    collector.set_gauge("memory_usage", 1024.5)
    assert collector.get_gauge("memory_usage") == 1024.5

    # Test histogram
    collector.record_histogram("response_time", 0.5)
    collector.record_histogram("response_time", 1.0)
    collector.record_histogram("response_time", 0.8)
    stats = collector.get_histogram_stats("response_time")
    assert stats["count"] == 3
    assert stats["min"] == 0.5
    assert stats["max"] == 1.0

    # Test timer context manager
    with Timer(collector, "operation"):
        pass
    assert len(collector.get_timer_stats("operation")) > 0


def test_telemetry_manager():
    """Test telemetry tracking."""
    telemetry = TelemetryManager()

    telemetry.set_user_id("user123")
    telemetry.track_event("test_event", properties={"key": "value"})

    events = telemetry.get_events()
    assert len(events) == 1
    assert events[0].event_type == "test_event"
    assert events[0].user_id == "user123"

    # Test LLM call tracking
    telemetry.track_llm_call("openai", "gpt-4", 1000, 1.5, True)
    llm_events = telemetry.get_events(event_type="llm_call")
    assert len(llm_events) == 1


@pytest.mark.asyncio
async def test_health_checker():
    """Test health checking."""
    checker = HealthChecker()

    # Mock components
    components = {
        "llm_provider": {},
        "memory_system": {},
        "tool_registry": {},
    }

    results = await checker.check_all(components)
    assert len(results) == 3

    overall_status = checker.get_overall_status()
    assert overall_status == HealthStatus.HEALTHY


def test_analytics_tracker():
    """Test analytics tracking."""
    tracker = AnalyticsTracker()

    # Track some requests
    tracker.track_request("openai", "gpt-4", 1000, 1.5, True, ["search", "calculate"])
    tracker.track_request("anthropic", "claude-3-opus", 500, 0.8, True)

    # Get usage stats
    stats = tracker.get_usage_stats()
    assert stats.total_requests == 2
    assert stats.total_tokens == 1500
    assert stats.successful_requests == 2

    # Get cost breakdown
    breakdown = tracker.get_cost_breakdown()
    assert len(breakdown) > 0

    # Get top models
    top_models = tracker.get_top_models()
    assert len(top_models) > 0
