"""
UnifiedProfiler - Performance monitoring and bottleneck detection.
Tracks CPU, memory, async operations, and execution latency.
"""

import asyncio
import time
import psutil
import tracemalloc
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from datetime import datetime
from contextlib import asynccontextmanager
import functools

from superagent.core.logger import get_logger

logger = get_logger(__name__)


@dataclass
class ProfileMetrics:
    """Performance metrics for a profiled operation."""
    
    operation: str
    start_time: float
    end_time: float
    duration: float
    cpu_percent: float
    memory_mb: float
    memory_delta_mb: float
    async_tasks: int
    success: bool
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def duration_ms(self) -> float:
        """Duration in milliseconds."""
        return self.duration * 1000


@dataclass
class BottleneckReport:
    """Report of detected performance bottlenecks."""
    
    operation: str
    severity: str  # "critical", "warning", "info"
    issue: str
    metrics: ProfileMetrics
    recommendation: str
    timestamp: datetime = field(default_factory=datetime.now)


class UnifiedProfiler:
    """
    Unified performance profiler for SuperAgent.
    
    Tracks:
    - CPU and memory usage
    - Async operation performance
    - Execution latency and bottlenecks
    - Resource utilization patterns
    """
    
    def __init__(self):
        self.metrics_history: List[ProfileMetrics] = []
        self.bottlenecks: List[BottleneckReport] = []
        self.process = psutil.Process()
        self._tracking_memory = False
        
        # Thresholds for bottleneck detection
        self.thresholds = {
            "duration_ms": 1000,  # 1 second
            "cpu_percent": 80,
            "memory_mb": 500,
            "memory_delta_mb": 100,
        }
    
    @asynccontextmanager
    async def profile(
        self,
        operation: str,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Context manager for profiling an operation.
        
        Usage:
            async with profiler.profile("llm_call"):
                result = await llm.generate(...)
        """
        # Start tracking
        start_time = time.time()
        start_cpu = self.process.cpu_percent()
        start_memory = self.process.memory_info().rss / 1024 / 1024  # MB
        
        if not self._tracking_memory:
            tracemalloc.start()
            self._tracking_memory = True
        
        snapshot_before = tracemalloc.take_snapshot()
        
        # Count async tasks
        tasks_before = len(asyncio.all_tasks())
        
        success = True
        error = None
        
        try:
            yield
        except Exception as e:
            success = False
            error = str(e)
            raise
        finally:
            # End tracking
            end_time = time.time()
            duration = end_time - start_time
            
            end_cpu = self.process.cpu_percent()
            end_memory = self.process.memory_info().rss / 1024 / 1024
            
            snapshot_after = tracemalloc.take_snapshot()
            memory_stats = snapshot_after.compare_to(snapshot_before, 'lineno')
            memory_delta = sum(stat.size_diff for stat in memory_stats) / 1024 / 1024
            
            tasks_after = len(asyncio.all_tasks())
            
            # Create metrics
            metrics = ProfileMetrics(
                operation=operation,
                start_time=start_time,
                end_time=end_time,
                duration=duration,
                cpu_percent=(start_cpu + end_cpu) / 2,
                memory_mb=end_memory,
                memory_delta_mb=memory_delta,
                async_tasks=tasks_after - tasks_before,
                success=success,
                error=error,
                metadata=metadata or {}
            )
            
            self.metrics_history.append(metrics)
            
            # Detect bottlenecks
            self._detect_bottlenecks(metrics)
            
            # Log metrics
            logger.info(
                f"Profile: {operation}",
                extra={
                    "duration_ms": metrics.duration_ms,
                    "cpu_percent": metrics.cpu_percent,
                    "memory_mb": metrics.memory_mb,
                    "success": success
                }
            )
    
    def _detect_bottlenecks(self, metrics: ProfileMetrics):
        """Detect performance bottlenecks from metrics."""
        bottlenecks = []
        
        # Check duration
        if metrics.duration_ms > self.thresholds["duration_ms"]:
            severity = "critical" if metrics.duration_ms > 5000 else "warning"
            bottlenecks.append(BottleneckReport(
                operation=metrics.operation,
                severity=severity,
                issue=f"Slow execution: {metrics.duration_ms:.0f}ms",
                metrics=metrics,
                recommendation="Consider caching, parallelization, or optimization"
            ))
        
        # Check CPU
        if metrics.cpu_percent > self.thresholds["cpu_percent"]:
            bottlenecks.append(BottleneckReport(
                operation=metrics.operation,
                severity="warning",
                issue=f"High CPU usage: {metrics.cpu_percent:.1f}%",
                metrics=metrics,
                recommendation="Profile CPU-intensive operations and optimize algorithms"
            ))
        
        # Check memory
        if metrics.memory_delta_mb > self.thresholds["memory_delta_mb"]:
            bottlenecks.append(BottleneckReport(
                operation=metrics.operation,
                severity="warning",
                issue=f"High memory allocation: {metrics.memory_delta_mb:.1f}MB",
                metrics=metrics,
                recommendation="Check for memory leaks or optimize data structures"
            ))
        
        self.bottlenecks.extend(bottlenecks)
        
        for bottleneck in bottlenecks:
            logger.warning(
                f"Bottleneck detected: {bottleneck.issue}",
                extra={
                    "operation": bottleneck.operation,
                    "severity": bottleneck.severity,
                    "recommendation": bottleneck.recommendation
                }
            )
    
    def get_summary(self) -> Dict[str, Any]:
        """Get performance summary."""
        if not self.metrics_history:
            return {"message": "No metrics collected"}
        
        total_operations = len(self.metrics_history)
        successful = sum(1 for m in self.metrics_history if m.success)
        failed = total_operations - successful
        
        avg_duration = sum(m.duration_ms for m in self.metrics_history) / total_operations
        avg_cpu = sum(m.cpu_percent for m in self.metrics_history) / total_operations
        avg_memory = sum(m.memory_mb for m in self.metrics_history) / total_operations
        
        slowest = max(self.metrics_history, key=lambda m: m.duration_ms)
        
        return {
            "total_operations": total_operations,
            "successful": successful,
            "failed": failed,
            "success_rate": successful / total_operations * 100,
            "avg_duration_ms": avg_duration,
            "avg_cpu_percent": avg_cpu,
            "avg_memory_mb": avg_memory,
            "slowest_operation": {
                "name": slowest.operation,
                "duration_ms": slowest.duration_ms
            },
            "bottlenecks_detected": len(self.bottlenecks),
            "critical_bottlenecks": sum(1 for b in self.bottlenecks if b.severity == "critical")
        }
    
    def get_bottlenecks(self, severity: Optional[str] = None) -> List[BottleneckReport]:
        """Get detected bottlenecks, optionally filtered by severity."""
        if severity:
            return [b for b in self.bottlenecks if b.severity == severity]
        return self.bottlenecks
    
    def clear_history(self):
        """Clear metrics history."""
        self.metrics_history.clear()
        self.bottlenecks.clear()


def profile_async(operation: str = None):
    """
    Decorator for profiling async functions.
    
    Usage:
        @profile_async("my_operation")
        async def my_function():
            ...
    """
    def decorator(func: Callable):
        op_name = operation or func.__name__
        
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            profiler = UnifiedProfiler()
            async with profiler.profile(op_name):
                return await func(*args, **kwargs)
        
        return wrapper
    return decorator
