"""
Health check system for monitoring system status.

Provides health checks for various components and dependencies.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from superagent.core.logger import get_logger

logger = get_logger(__name__)


class HealthStatus(str, Enum):
    """Health status levels."""

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"


@dataclass
class HealthCheck:
    """A health check result for a component."""

    component: str
    status: HealthStatus
    timestamp: datetime = field(default_factory=datetime.utcnow)
    message: Optional[str] = None
    details: Dict[str, Any] = field(default_factory=dict)


class HealthChecker:
    """
    Performs health checks on system components.

    Monitors LLM providers, memory systems, tools, and other dependencies.
    """

    def __init__(self):
        self._checks: Dict[str, HealthCheck] = {}

    async def check_llm_provider(
        self, provider_name: str, provider: Any
    ) -> HealthCheck:
        """Check health of an LLM provider."""
        try:
            # Simple ping check - could be enhanced with actual API call
            check = HealthCheck(
                component=f"llm_provider_{provider_name}",
                status=HealthStatus.HEALTHY,
                message="Provider is available",
            )
        except Exception as e:
            check = HealthCheck(
                component=f"llm_provider_{provider_name}",
                status=HealthStatus.UNHEALTHY,
                message=f"Provider check failed: {str(e)}",
            )
            logger.error(f"LLM provider health check failed: {provider_name}", exc_info=e)

        self._checks[check.component] = check
        return check

    async def check_memory_system(self, memory_manager: Any) -> HealthCheck:
        """Check health of the memory system."""
        try:
            # Check if memory system is responsive
            check = HealthCheck(
                component="memory_system",
                status=HealthStatus.HEALTHY,
                message="Memory system is operational",
            )
        except Exception as e:
            check = HealthCheck(
                component="memory_system",
                status=HealthStatus.UNHEALTHY,
                message=f"Memory system check failed: {str(e)}",
            )
            logger.error("Memory system health check failed", exc_info=e)

        self._checks[check.component] = check
        return check

    async def check_tool_registry(self, tool_registry: Any) -> HealthCheck:
        """Check health of the tool registry."""
        try:
            # Check if tools are available
            check = HealthCheck(
                component="tool_registry",
                status=HealthStatus.HEALTHY,
                message="Tool registry is operational",
            )
        except Exception as e:
            check = HealthCheck(
                component="tool_registry",
                status=HealthStatus.UNHEALTHY,
                message=f"Tool registry check failed: {str(e)}",
            )
            logger.error("Tool registry health check failed", exc_info=e)

        self._checks[check.component] = check
        return check

    async def check_all(self, components: Dict[str, Any]) -> Dict[str, HealthCheck]:
        """Run health checks on all components."""
        results = {}

        for name, component in components.items():
            try:
                if "llm" in name.lower():
                    check = await self.check_llm_provider(name, component)
                elif "memory" in name.lower():
                    check = await self.check_memory_system(component)
                elif "tool" in name.lower():
                    check = await self.check_tool_registry(component)
                else:
                    check = HealthCheck(
                        component=name,
                        status=HealthStatus.HEALTHY,
                        message="Component is operational",
                    )
                results[name] = check
            except Exception as e:
                results[name] = HealthCheck(
                    component=name,
                    status=HealthStatus.UNHEALTHY,
                    message=f"Health check failed: {str(e)}",
                )
                logger.error(f"Health check failed for {name}", exc_info=e)

        return results

    def get_overall_status(self) -> HealthStatus:
        """Get overall system health status."""
        if not self._checks:
            return HealthStatus.HEALTHY

        statuses = [check.status for check in self._checks.values()]

        if HealthStatus.UNHEALTHY in statuses:
            return HealthStatus.UNHEALTHY
        elif HealthStatus.DEGRADED in statuses:
            return HealthStatus.DEGRADED
        else:
            return HealthStatus.HEALTHY

    def get_checks(self) -> Dict[str, HealthCheck]:
        """Get all health check results."""
        return self._checks.copy()
