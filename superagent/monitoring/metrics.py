"""
Metrics collection and tracking system.

Provides counters, gauges, histograms, and timers for performance monitoring.
"""

import time
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from superagent.core.logger import get_logger

logger = get_logger(__name__)


class MetricType(str, Enum):
    """Types of metrics that can be collected."""

    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    TIMER = "timer"


@dataclass
class Metric:
    """A single metric data point."""

    name: str
    type: MetricType
    value: float
    timestamp: datetime = field(default_factory=datetime.utcnow)
    tags: Dict[str, str] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


class MetricsCollector:
    """
    Collects and aggregates metrics for monitoring.

    Supports counters, gauges, histograms, and timers.
    """

    def __init__(self):
        self._counters: Dict[str, float] = defaultdict(float)
        self._gauges: Dict[str, float] = {}
        self._histograms: Dict[str, List[float]] = defaultdict(list)
        self._timers: Dict[str, List[float]] = defaultdict(list)
        self._metrics_history: List[Metric] = []

    def increment(
        self, name: str, value: float = 1.0, tags: Optional[Dict[str, str]] = None
    ) -> None:
        """Increment a counter metric."""
        self._counters[name] += value
        metric = Metric(
            name=name,
            type=MetricType.COUNTER,
            value=self._counters[name],
            tags=tags or {},
        )
        self._metrics_history.append(metric)
        logger.debug(f"Counter incremented: {name}={self._counters[name]}")

    def set_gauge(
        self, name: str, value: float, tags: Optional[Dict[str, str]] = None
    ) -> None:
        """Set a gauge metric to a specific value."""
        self._gauges[name] = value
        metric = Metric(
            name=name, type=MetricType.GAUGE, value=value, tags=tags or {}
        )
        self._metrics_history.append(metric)
        logger.debug(f"Gauge set: {name}={value}")

    def record_histogram(
        self, name: str, value: float, tags: Optional[Dict[str, str]] = None
    ) -> None:
        """Record a value in a histogram."""
        self._histograms[name].append(value)
        metric = Metric(
            name=name, type=MetricType.HISTOGRAM, value=value, tags=tags or {}
        )
        self._metrics_history.append(metric)
        logger.debug(f"Histogram recorded: {name}={value}")

    def record_timer(
        self, name: str, duration: float, tags: Optional[Dict[str, str]] = None
    ) -> None:
        """Record a timing measurement."""
        self._timers[name].append(duration)
        metric = Metric(
            name=name, type=MetricType.TIMER, value=duration, tags=tags or {}
        )
        self._metrics_history.append(metric)
        logger.debug(f"Timer recorded: {name}={duration:.3f}s")

    def get_counter(self, name: str) -> float:
        """Get the current value of a counter."""
        return self._counters.get(name, 0.0)

    def get_gauge(self, name: str) -> Optional[float]:
        """Get the current value of a gauge."""
        return self._gauges.get(name)

    def get_histogram_stats(self, name: str) -> Dict[str, float]:
        """Get statistics for a histogram."""
        values = self._histograms.get(name, [])
        if not values:
            return {}

        sorted_values = sorted(values)
        n = len(sorted_values)

        return {
            "count": n,
            "min": sorted_values[0],
            "max": sorted_values[-1],
            "mean": sum(sorted_values) / n,
            "median": sorted_values[n // 2],
            "p95": sorted_values[int(n * 0.95)] if n > 0 else 0,
            "p99": sorted_values[int(n * 0.99)] if n > 0 else 0,
        }

    def get_timer_stats(self, name: str) -> Dict[str, float]:
        """Get statistics for a timer."""
        return self.get_histogram_stats(name)

    def get_all_metrics(self) -> Dict[str, Any]:
        """Get all current metrics."""
        return {
            "counters": dict(self._counters),
            "gauges": dict(self._gauges),
            "histograms": {
                name: self.get_histogram_stats(name)
                for name in self._histograms.keys()
            },
            "timers": {
                name: self.get_timer_stats(name) for name in self._timers.keys()
            },
        }

    def get_metrics_history(
        self, limit: Optional[int] = None
    ) -> List[Metric]:
        """Get metrics history."""
        if limit:
            return self._metrics_history[-limit:]
        return self._metrics_history

    def reset(self) -> None:
        """Reset all metrics."""
        self._counters.clear()
        self._gauges.clear()
        self._histograms.clear()
        self._timers.clear()
        self._metrics_history.clear()
        logger.info("All metrics reset")


class Timer:
    """Context manager for timing operations."""

    def __init__(
        self,
        collector: MetricsCollector,
        name: str,
        tags: Optional[Dict[str, str]] = None,
    ):
        self.collector = collector
        self.name = name
        self.tags = tags
        self.start_time: Optional[float] = None

    def __enter__(self):
        self.start_time = time.time()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.start_time is not None:
            duration = time.time() - self.start_time
            self.collector.record_timer(self.name, duration, self.tags)
