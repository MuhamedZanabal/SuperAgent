"""
Analytics and usage tracking system.

Provides cost analysis, usage statistics, and performance insights.
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from superagent.core.logger import get_logger

logger = get_logger(__name__)


@dataclass
class UsageStats:
    """Usage statistics for a time period."""

    period_start: datetime
    period_end: datetime
    total_requests: int = 0
    total_tokens: int = 0
    total_cost: float = 0.0
    successful_requests: int = 0
    failed_requests: int = 0
    average_latency: float = 0.0
    providers_used: Dict[str, int] = field(default_factory=dict)
    models_used: Dict[str, int] = field(default_factory=dict)
    tools_executed: Dict[str, int] = field(default_factory=dict)


class AnalyticsTracker:
    """
    Tracks usage analytics and generates insights.

    Monitors costs, usage patterns, and performance metrics.
    """

    def __init__(self):
        self._requests: List[Dict] = []
        self._token_costs: Dict[str, float] = {
            "gpt-4": 0.03 / 1000,  # per token
            "gpt-3.5-turbo": 0.002 / 1000,
            "claude-3-opus": 0.015 / 1000,
            "claude-3-sonnet": 0.003 / 1000,
        }

    def track_request(
        self,
        provider: str,
        model: str,
        tokens: int,
        latency: float,
        success: bool,
        tool_calls: Optional[List[str]] = None,
    ) -> None:
        """Track an API request."""
        cost = self._calculate_cost(model, tokens)

        request = {
            "timestamp": datetime.utcnow(),
            "provider": provider,
            "model": model,
            "tokens": tokens,
            "latency": latency,
            "success": success,
            "cost": cost,
            "tool_calls": tool_calls or [],
        }

        self._requests.append(request)
        logger.debug(
            f"Request tracked: {provider}/{model} - {tokens} tokens, ${cost:.4f}"
        )

    def _calculate_cost(self, model: str, tokens: int) -> float:
        """Calculate cost for a request."""
        # Find matching cost rate
        for model_prefix, rate in self._token_costs.items():
            if model.startswith(model_prefix):
                return tokens * rate
        # Default rate if model not found
        return tokens * 0.001 / 1000

    def get_usage_stats(
        self,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
    ) -> UsageStats:
        """Get usage statistics for a time period."""
        if start_time is None:
            start_time = datetime.utcnow() - timedelta(days=1)
        if end_time is None:
            end_time = datetime.utcnow()

        # Filter requests by time period
        period_requests = [
            r
            for r in self._requests
            if start_time <= r["timestamp"] <= end_time
        ]

        if not period_requests:
            return UsageStats(period_start=start_time, period_end=end_time)

        # Calculate statistics
        stats = UsageStats(period_start=start_time, period_end=end_time)
        stats.total_requests = len(period_requests)
        stats.total_tokens = sum(r["tokens"] for r in period_requests)
        stats.total_cost = sum(r["cost"] for r in period_requests)
        stats.successful_requests = sum(1 for r in period_requests if r["success"])
        stats.failed_requests = stats.total_requests - stats.successful_requests
        stats.average_latency = sum(r["latency"] for r in period_requests) / len(
            period_requests
        )

        # Count providers and models
        for request in period_requests:
            provider = request["provider"]
            model = request["model"]
            stats.providers_used[provider] = stats.providers_used.get(provider, 0) + 1
            stats.models_used[model] = stats.models_used.get(model, 0) + 1

            # Count tool executions
            for tool in request["tool_calls"]:
                stats.tools_executed[tool] = stats.tools_executed.get(tool, 0) + 1

        return stats

    def get_cost_breakdown(self) -> Dict[str, float]:
        """Get cost breakdown by provider and model."""
        breakdown = {}

        for request in self._requests:
            key = f"{request['provider']}/{request['model']}"
            breakdown[key] = breakdown.get(key, 0.0) + request["cost"]

        return breakdown

    def get_top_models(self, limit: int = 5) -> List[tuple]:
        """Get most used models."""
        model_counts = {}
        for request in self._requests:
            model = request["model"]
            model_counts[model] = model_counts.get(model, 0) + 1

        return sorted(model_counts.items(), key=lambda x: x[1], reverse=True)[:limit]

    def get_top_tools(self, limit: int = 5) -> List[tuple]:
        """Get most used tools."""
        tool_counts = {}
        for request in self._requests:
            for tool in request["tool_calls"]:
                tool_counts[tool] = tool_counts.get(tool, 0) + 1

        return sorted(tool_counts.items(), key=lambda x: x[1], reverse=True)[:limit]

    def reset(self) -> None:
        """Reset all analytics data."""
        self._requests.clear()
        logger.info("Analytics data reset")
