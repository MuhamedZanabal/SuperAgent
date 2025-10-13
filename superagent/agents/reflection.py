"""
Adaptive Reflection System - Learns from execution history and improves decisions.
"""

import asyncio
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum

from superagent.core.logger import get_logger
from superagent.agents.models import Task, TaskStatus, ExecutionResult

logger = get_logger(__name__)


class ReflectionType(str, Enum):
    """Types of reflection analysis."""
    SUCCESS_ANALYSIS = "success_analysis"
    FAILURE_ANALYSIS = "failure_analysis"
    PERFORMANCE_REVIEW = "performance_review"
    STRATEGY_OPTIMIZATION = "strategy_optimization"


@dataclass
class ReflectionInsight:
    """Insight gained from reflection."""
    
    type: ReflectionType
    category: str  # "planning", "execution", "tool_selection", "error_handling"
    insight: str
    confidence: float  # 0-1
    evidence: List[str]
    recommendation: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class LearningPattern:
    """Learned pattern from execution history."""
    
    pattern_id: str
    description: str
    success_rate: float
    usage_count: int
    avg_duration: float
    context: Dict[str, Any]
    created_at: datetime = field(default_factory=datetime.now)
    last_used: datetime = field(default_factory=datetime.now)


class AdaptiveReflectionSystem:
    """
    Analyzes execution history and learns from outcomes.
    
    Capabilities:
    - Success/failure pattern recognition
    - Performance trend analysis
    - Strategy optimization recommendations
    - Adaptive weight adjustment for planners
    """
    
    def __init__(self):
        self.insights: List[ReflectionInsight] = []
        self.patterns: Dict[str, LearningPattern] = {}
        self.execution_history: List[ExecutionResult] = []
        
        # Adaptive weights for planner
        self.planner_weights = {
            "complexity_penalty": 0.1,
            "tool_preference": {},  # tool_name -> weight
            "strategy_preference": {},  # strategy -> weight
        }
    
    async def reflect_on_execution(
        self,
        result: ExecutionResult,
        task: Task
    ) -> List[ReflectionInsight]:
        """
        Reflect on execution result and generate insights.
        
        Args:
            result: Execution result to analyze
            task: Original task
            
        Returns:
            List of insights gained
        """
        self.execution_history.append(result)
        insights = []
        
        # Analyze based on outcome
        if result.success:
            insights.extend(await self._analyze_success(result, task))
        else:
            insights.extend(await self._analyze_failure(result, task))
        
        # Performance analysis
        insights.extend(await self._analyze_performance(result, task))
        
        # Update learned patterns
        await self._update_patterns(result, task)
        
        # Adjust planner weights
        await self._adjust_weights(insights)
        
        self.insights.extend(insights)
        
        logger.info(
            f"Reflection complete: {len(insights)} insights",
            extra={
                "task_id": task.id,
                "success": result.success,
                "insights": len(insights)
            }
        )
        
        return insights
    
    async def _analyze_success(
        self,
        result: ExecutionResult,
        task: Task
    ) -> List[ReflectionInsight]:
        """Analyze successful execution."""
        insights = []
        
        # Check if execution was efficient
        if result.metadata.get("duration", 0) < 5.0:
            insights.append(ReflectionInsight(
                type=ReflectionType.SUCCESS_ANALYSIS,
                category="performance",
                insight="Task completed efficiently",
                confidence=0.9,
                evidence=[f"Duration: {result.metadata.get('duration')}s"],
                recommendation="Reuse this execution strategy for similar tasks"
            ))
        
        # Analyze tool usage
        tools_used = result.metadata.get("tools_used", [])
        if tools_used:
            insights.append(ReflectionInsight(
                type=ReflectionType.SUCCESS_ANALYSIS,
                category="tool_selection",
                insight=f"Effective tool combination: {', '.join(tools_used)}",
                confidence=0.8,
                evidence=[f"Tools: {tools_used}"],
                recommendation="Prioritize these tools for similar tasks"
            ))
        
        return insights
    
    async def _analyze_failure(
        self,
        result: ExecutionResult,
        task: Task
    ) -> List[ReflectionInsight]:
        """Analyze failed execution."""
        insights = []
        
        error = result.error or "Unknown error"
        
        # Categorize error
        if "timeout" in error.lower():
            insights.append(ReflectionInsight(
                type=ReflectionType.FAILURE_ANALYSIS,
                category="execution",
                insight="Task timed out - may need decomposition",
                confidence=0.85,
                evidence=[error],
                recommendation="Break down complex tasks into smaller steps"
            ))
        elif "permission" in error.lower() or "access" in error.lower():
            insights.append(ReflectionInsight(
                type=ReflectionType.FAILURE_ANALYSIS,
                category="error_handling",
                insight="Permission or access error",
                confidence=0.9,
                evidence=[error],
                recommendation="Check security settings and permissions"
            ))
        else:
            insights.append(ReflectionInsight(
                type=ReflectionType.FAILURE_ANALYSIS,
                category="execution",
                insight=f"Execution failed: {error}",
                confidence=0.7,
                evidence=[error],
                recommendation="Review error handling and add fallback strategies"
            ))
        
        return insights
    
    async def _analyze_performance(
        self,
        result: ExecutionResult,
        task: Task
    ) -> List[ReflectionInsight]:
        """Analyze performance metrics."""
        insights = []
        
        duration = result.metadata.get("duration", 0)
        
        # Check if task took too long
        if duration > 30.0:
            insights.append(ReflectionInsight(
                type=ReflectionType.PERFORMANCE_REVIEW,
                category="performance",
                insight=f"Task took {duration:.1f}s - optimization needed",
                confidence=0.8,
                evidence=[f"Duration: {duration}s"],
                recommendation="Consider caching, parallelization, or algorithm optimization"
            ))
        
        return insights
    
    async def _update_patterns(self, result: ExecutionResult, task: Task):
        """Update learned patterns from execution."""
        # Create pattern signature
        tools_used = result.metadata.get("tools_used", [])
        pattern_id = f"{task.type}:{':'.join(sorted(tools_used))}"
        
        if pattern_id in self.patterns:
            # Update existing pattern
            pattern = self.patterns[pattern_id]
            pattern.usage_count += 1
            pattern.last_used = datetime.now()
            
            # Update success rate
            if result.success:
                pattern.success_rate = (
                    pattern.success_rate * (pattern.usage_count - 1) + 1.0
                ) / pattern.usage_count
            else:
                pattern.success_rate = (
                    pattern.success_rate * (pattern.usage_count - 1)
                ) / pattern.usage_count
            
            # Update average duration
            duration = result.metadata.get("duration", 0)
            pattern.avg_duration = (
                pattern.avg_duration * (pattern.usage_count - 1) + duration
            ) / pattern.usage_count
        else:
            # Create new pattern
            self.patterns[pattern_id] = LearningPattern(
                pattern_id=pattern_id,
                description=f"Task type: {task.type}, Tools: {tools_used}",
                success_rate=1.0 if result.success else 0.0,
                usage_count=1,
                avg_duration=result.metadata.get("duration", 0),
                context={
                    "task_type": task.type,
                    "tools": tools_used
                }
            )
    
    async def _adjust_weights(self, insights: List[ReflectionInsight]):
        """Adjust planner weights based on insights."""
        for insight in insights:
            if insight.category == "tool_selection" and insight.confidence > 0.7:
                # Increase weight for successful tools
                tools = insight.metadata.get("tools", [])
                for tool in tools:
                    current = self.planner_weights["tool_preference"].get(tool, 1.0)
                    self.planner_weights["tool_preference"][tool] = min(2.0, current + 0.1)
    
    def get_recommendations(
        self,
        task_type: Optional[str] = None,
        limit: int = 5
    ) -> List[ReflectionInsight]:
        """Get top recommendations for task execution."""
        relevant_insights = self.insights
        
        if task_type:
            relevant_insights = [
                i for i in self.insights
                if i.metadata.get("task_type") == task_type
            ]
        
        # Sort by confidence and recency
        sorted_insights = sorted(
            relevant_insights,
            key=lambda i: (i.confidence, i.timestamp),
            reverse=True
        )
        
        return sorted_insights[:limit]
    
    def get_best_patterns(
        self,
        task_type: Optional[str] = None,
        min_success_rate: float = 0.7,
        limit: int = 5
    ) -> List[LearningPattern]:
        """Get best performing patterns."""
        patterns = list(self.patterns.values())
        
        # Filter by task type if specified
        if task_type:
            patterns = [
                p for p in patterns
                if p.context.get("task_type") == task_type
            ]
        
        # Filter by success rate
        patterns = [p for p in patterns if p.success_rate >= min_success_rate]
        
        # Sort by success rate and usage count
        sorted_patterns = sorted(
            patterns,
            key=lambda p: (p.success_rate, p.usage_count),
            reverse=True
        )
        
        return sorted_patterns[:limit]
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get reflection statistics."""
        if not self.execution_history:
            return {"message": "No execution history"}
        
        total = len(self.execution_history)
        successful = sum(1 for r in self.execution_history if r.success)
        
        return {
            "total_executions": total,
            "successful": successful,
            "failed": total - successful,
            "success_rate": successful / total * 100,
            "insights_generated": len(self.insights),
            "patterns_learned": len(self.patterns),
            "avg_confidence": sum(i.confidence for i in self.insights) / len(self.insights) if self.insights else 0
        }
