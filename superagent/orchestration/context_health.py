"""
Context Health Monitor - Validates semantic coherence and context quality.
"""

import asyncio
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

from superagent.core.logger import get_logger
from superagent.orchestration.context_fusion import ContextFusionEngine, UnifiedContext

logger = get_logger(__name__)


class HealthStatus(str, Enum):
    """Context health status levels."""
    HEALTHY = "healthy"
    WARNING = "warning"
    CRITICAL = "critical"
    UNKNOWN = "unknown"


@dataclass
class HealthIssue:
    """Detected context health issue."""
    
    severity: HealthStatus
    category: str  # "redundancy", "drift", "token_overflow", "coherence"
    description: str
    recommendation: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class ContextHealthReport:
    """Comprehensive context health report."""
    
    status: HealthStatus
    score: float  # 0-100
    issues: List[HealthIssue]
    metrics: Dict[str, Any]
    timestamp: datetime = field(default_factory=datetime.now)
    
    @property
    def is_healthy(self) -> bool:
        return self.status == HealthStatus.HEALTHY
    
    @property
    def critical_issues(self) -> List[HealthIssue]:
        return [i for i in self.issues if i.severity == HealthStatus.CRITICAL]


class ContextHealthMonitor:
    """
    Monitors context health and semantic stability.
    
    Checks for:
    - Semantic drift and redundancy
    - Token utilization and overflow
    - Embedding coherence
    - Context lifespan and freshness
    """
    
    def __init__(self, fusion_engine: ContextFusionEngine):
        self.fusion_engine = fusion_engine
        self.health_history: List[ContextHealthReport] = []
        
        # Thresholds
        self.thresholds = {
            "token_utilization": 0.9,  # 90% of max tokens
            "redundancy_ratio": 0.3,  # 30% duplicate content
            "coherence_score": 0.7,  # Minimum coherence
            "max_age_hours": 24,  # Maximum context age
        }
    
    async def check_health(self, context: UnifiedContext) -> ContextHealthReport:
        """
        Perform comprehensive health check on context.
        
        Args:
            context: Unified context to check
            
        Returns:
            Health report with status, score, and issues
        """
        issues: List[HealthIssue] = []
        metrics: Dict[str, Any] = {}
        
        # Check token utilization
        token_issues = await self._check_token_utilization(context)
        issues.extend(token_issues)
        metrics["token_count"] = context.metadata.get("token_count", 0)
        metrics["token_limit"] = context.metadata.get("token_limit", 0)
        
        # Check redundancy
        redundancy_issues = await self._check_redundancy(context)
        issues.extend(redundancy_issues)
        metrics["redundancy_ratio"] = await self._calculate_redundancy(context)
        
        # Check semantic coherence
        coherence_issues = await self._check_coherence(context)
        issues.extend(coherence_issues)
        metrics["coherence_score"] = await self._calculate_coherence(context)
        
        # Check context age
        age_issues = await self._check_age(context)
        issues.extend(age_issues)
        metrics["age_hours"] = (datetime.now() - context.created_at).total_seconds() / 3600
        
        # Calculate overall health score
        score = self._calculate_health_score(issues, metrics)
        
        # Determine status
        status = self._determine_status(score, issues)
        
        report = ContextHealthReport(
            status=status,
            score=score,
            issues=issues,
            metrics=metrics
        )
        
        self.health_history.append(report)
        
        logger.info(
            f"Context health check: {status.value}",
            extra={
                "score": score,
                "issues_count": len(issues),
                "critical_issues": len(report.critical_issues)
            }
        )
        
        return report
    
    async def _check_token_utilization(self, context: UnifiedContext) -> List[HealthIssue]:
        """Check if token usage is approaching limits."""
        issues = []
        
        token_count = context.metadata.get("token_count", 0)
        token_limit = context.metadata.get("token_limit", 8000)
        
        if token_limit > 0:
            utilization = token_count / token_limit
            
            if utilization > self.thresholds["token_utilization"]:
                issues.append(HealthIssue(
                    severity=HealthStatus.CRITICAL,
                    category="token_overflow",
                    description=f"Token utilization at {utilization*100:.1f}%",
                    recommendation="Summarize or prune old context entries",
                    metadata={"token_count": token_count, "token_limit": token_limit}
                ))
            elif utilization > 0.75:
                issues.append(HealthIssue(
                    severity=HealthStatus.WARNING,
                    category="token_overflow",
                    description=f"Token utilization at {utilization*100:.1f}%",
                    recommendation="Consider context cleanup soon",
                    metadata={"token_count": token_count, "token_limit": token_limit}
                ))
        
        return issues
    
    async def _check_redundancy(self, context: UnifiedContext) -> List[HealthIssue]:
        """Check for redundant or duplicate content."""
        issues = []
        
        redundancy_ratio = await self._calculate_redundancy(context)
        
        if redundancy_ratio > self.thresholds["redundancy_ratio"]:
            issues.append(HealthIssue(
                severity=HealthStatus.WARNING,
                category="redundancy",
                description=f"High content redundancy: {redundancy_ratio*100:.1f}%",
                recommendation="Deduplicate context entries or merge similar content",
                metadata={"redundancy_ratio": redundancy_ratio}
            ))
        
        return issues
    
    async def _calculate_redundancy(self, context: UnifiedContext) -> float:
        """Calculate redundancy ratio in context."""
        # Simple heuristic: check for repeated phrases in conversation
        if not context.conversation_history:
            return 0.0
        
        messages = [msg.content for msg in context.conversation_history]
        total_words = sum(len(msg.split()) for msg in messages)
        
        if total_words == 0:
            return 0.0
        
        # Count unique words vs total words
        all_words = " ".join(messages).lower().split()
        unique_words = set(all_words)
        
        redundancy = 1.0 - (len(unique_words) / len(all_words))
        return redundancy
    
    async def _check_coherence(self, context: UnifiedContext) -> List[HealthIssue]:
        """Check semantic coherence of context."""
        issues = []
        
        coherence_score = await self._calculate_coherence(context)
        
        if coherence_score < self.thresholds["coherence_score"]:
            issues.append(HealthIssue(
                severity=HealthStatus.WARNING,
                category="coherence",
                description=f"Low semantic coherence: {coherence_score:.2f}",
                recommendation="Review context relevance and remove off-topic entries",
                metadata={"coherence_score": coherence_score}
            ))
        
        return issues
    
    async def _calculate_coherence(self, context: UnifiedContext) -> float:
        """Calculate semantic coherence score."""
        # Simplified coherence check
        # In production, use embedding similarity between context parts
        
        if not context.conversation_history:
            return 1.0
        
        # Check if messages are related (simple keyword overlap)
        messages = [msg.content.lower() for msg in context.conversation_history]
        
        if len(messages) < 2:
            return 1.0
        
        # Calculate average keyword overlap between consecutive messages
        overlaps = []
        for i in range(len(messages) - 1):
            words1 = set(messages[i].split())
            words2 = set(messages[i + 1].split())
            
            if words1 and words2:
                overlap = len(words1 & words2) / len(words1 | words2)
                overlaps.append(overlap)
        
        return sum(overlaps) / len(overlaps) if overlaps else 0.5
    
    async def _check_age(self, context: UnifiedContext) -> List[HealthIssue]:
        """Check context age and freshness."""
        issues = []
        
        age_hours = (datetime.now() - context.created_at).total_seconds() / 3600
        
        if age_hours > self.thresholds["max_age_hours"]:
            issues.append(HealthIssue(
                severity=HealthStatus.WARNING,
                category="freshness",
                description=f"Context is {age_hours:.1f} hours old",
                recommendation="Consider starting a new context or archiving old data",
                metadata={"age_hours": age_hours}
            ))
        
        return issues
    
    def _calculate_health_score(
        self,
        issues: List[HealthIssue],
        metrics: Dict[str, Any]
    ) -> float:
        """Calculate overall health score (0-100)."""
        base_score = 100.0
        
        # Deduct points for issues
        for issue in issues:
            if issue.severity == HealthStatus.CRITICAL:
                base_score -= 30
            elif issue.severity == HealthStatus.WARNING:
                base_score -= 15
        
        return max(0.0, min(100.0, base_score))
    
    def _determine_status(
        self,
        score: float,
        issues: List[HealthIssue]
    ) -> HealthStatus:
        """Determine overall health status."""
        critical_issues = [i for i in issues if i.severity == HealthStatus.CRITICAL]
        
        if critical_issues:
            return HealthStatus.CRITICAL
        elif score < 70:
            return HealthStatus.WARNING
        else:
            return HealthStatus.HEALTHY
    
    def get_health_trend(self, window: int = 10) -> Dict[str, Any]:
        """Get health trend over recent checks."""
        recent = self.health_history[-window:]
        
        if not recent:
            return {"message": "No health history"}
        
        avg_score = sum(r.score for r in recent) / len(recent)
        healthy_count = sum(1 for r in recent if r.is_healthy)
        
        return {
            "checks": len(recent),
            "avg_score": avg_score,
            "healthy_rate": healthy_count / len(recent) * 100,
            "trend": "improving" if recent[-1].score > recent[0].score else "declining"
        }
