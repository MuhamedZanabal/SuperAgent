"""
Advanced Planning System with parallel execution and dependency management.
"""

from typing import List, Dict, Optional, Set
from enum import Enum
import uuid
import asyncio
from datetime import datetime

from pydantic import BaseModel, Field

from superagent.agents.models import Task, Plan, Step, StepType, StepStatus
from superagent.llm.provider import UnifiedLLMProvider
from superagent.llm.models import LLMRequest, Message
from superagent.tools.registry import ToolRegistry
from superagent.core.logger import get_logger

logger = get_logger(__name__)


class TaskPriority(str, Enum):
    """Task priority levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class StepDependency(BaseModel):
    """Step dependency specification."""
    step_id: str
    dependency_type: str = "requires"  # requires, suggests, conflicts


class EnhancedStep(Step):
    """Enhanced step with dependencies and metadata."""
    dependencies: List[StepDependency] = Field(default_factory=list)
    priority: TaskPriority = TaskPriority.MEDIUM
    estimated_duration: Optional[float] = None
    success_probability: float = 1.0
    retry_count: int = 0
    max_retries: int = 3
    parallel_group: Optional[str] = None


class EnhancedPlan(Plan):
    """Enhanced plan with dependency graph and execution metadata."""
    steps: List[EnhancedStep]
    dependency_graph: Dict[str, List[str]] = Field(default_factory=dict)
    parallel_groups: Dict[str, List[str]] = Field(default_factory=dict)
    estimated_total_duration: Optional[float] = None
    success_probability: float = 1.0


class UnifiedAdvancedPlanner:
    """
    Advanced planner with multi-step decomposition, dependency management,
    and parallel execution optimization.
    
    Features:
    - Intelligent task decomposition
    - Dependency graph construction
    - Parallel execution planning
    - Success probability estimation
    - Context propagation
    - Error recovery strategies
    """
    
    def __init__(
        self,
        llm_provider: UnifiedLLMProvider,
        tool_registry: ToolRegistry,
        model: str = "gpt-4-turbo-preview",
        max_parallel_steps: int = 5,
    ):
        """
        Initialize advanced planner.
        
        Args:
            llm_provider: LLM provider for planning
            tool_registry: Tool registry for available actions
            model: Model to use for planning
            max_parallel_steps: Maximum steps to execute in parallel
        """
        self.llm_provider = llm_provider
        self.tool_registry = tool_registry
        self.model = model
        self.max_parallel_steps = max_parallel_steps
    
    async def create_plan(
        self,
        task: Task,
        context: Optional[Dict] = None,
    ) -> EnhancedPlan:
        """
        Create an enhanced plan with dependency management.
        
        Args:
            task: Task to plan for
            context: Additional context for planning
            
        Returns:
            Enhanced plan with dependencies
        """
        logger.info(f"Creating advanced plan for task: {task.id}")
        
        # Get available tools
        tools = self.tool_registry.get_function_definitions()
        tool_descriptions = "\n".join([
            f"- {tool['name']}: {tool['description']}"
            for tool in tools
        ])
        
        # Build advanced planning prompt
        system_prompt = f"""You are an expert AI task planner with advanced reasoning capabilities.

Your goal is to create optimal execution plans that:
1. Break complex tasks into clear, executable steps
2. Identify dependencies between steps
3. Optimize for parallel execution where possible
4. Estimate success probability for each step
5. Include error recovery strategies

Available tools:
{tool_descriptions}

For each step, provide:
- Type: THINK (reasoning), ACT (use tool), OBSERVE (check result), REFLECT (evaluate)
- Description: Clear action to take
- Tool (if ACT): Specific tool to use with parameters
- Dependencies: Which previous steps must complete first
- Priority: LOW, MEDIUM, HIGH, or CRITICAL
- Success probability: 0.0 to 1.0
- Parallel group: Steps that can run in parallel (same group ID)

Use JSON format for structured output."""
        
        user_prompt = f"""Task: {task.description}

Context: {task.context}
Additional context: {context or 'None'}
Constraints: {', '.join(task.constraints) if task.constraints else 'None'}
Success criteria: {', '.join(task.success_criteria) if task.success_criteria else 'Complete the task'}
Max steps: {task.max_steps}

Create an optimized execution plan with:
1. Step-by-step breakdown
2. Dependency relationships
3. Parallel execution opportunities
4. Success probability estimates
5. Error recovery strategies"""
        
        # Generate plan
        request = LLMRequest(
            model=self.model,
            messages=[
                Message(role="system", content=system_prompt),
                Message(role="user", content=user_prompt),
            ],
            temperature=0.7,
        )
        
        response = await self.llm_provider.generate(request)
        
        # Parse enhanced plan
        steps = await self._parse_enhanced_plan(response.content, task)
        
        # Build dependency graph
        dependency_graph = self._build_dependency_graph(steps)
        
        # Identify parallel groups
        parallel_groups = self._identify_parallel_groups(steps, dependency_graph)
        
        # Estimate total duration and success probability
        estimated_duration = self._estimate_duration(steps, parallel_groups)
        success_probability = self._estimate_success_probability(steps)
        
        plan = EnhancedPlan(
            task_id=task.id,
            steps=steps,
            reasoning=response.content,
            dependency_graph=dependency_graph,
            parallel_groups=parallel_groups,
            estimated_total_duration=estimated_duration,
            success_probability=success_probability,
        )
        
        logger.info(
            f"Created advanced plan with {len(steps)} steps, "
            f"{len(parallel_groups)} parallel groups, "
            f"estimated duration: {estimated_duration:.2f}s, "
            f"success probability: {success_probability:.2%}"
        )
        
        return plan
    
    async def _parse_enhanced_plan(
        self,
        plan_text: str,
        task: Task,
    ) -> List[EnhancedStep]:
        """Parse plan text into enhanced steps."""
        steps = []
        
        # Try to parse as JSON first
        import json
        try:
            plan_data = json.loads(plan_text)
            if isinstance(plan_data, dict) and "steps" in plan_data:
                plan_data = plan_data["steps"]
            
            for step_data in plan_data:
                step = EnhancedStep(
                    id=step_data.get("id", str(uuid.uuid4())),
                    type=StepType(step_data.get("type", "act").lower()),
                    description=step_data.get("description", ""),
                    tool_name=step_data.get("tool"),
                    tool_args=step_data.get("tool_args", {}),
                    dependencies=[
                        StepDependency(step_id=dep)
                        for dep in step_data.get("dependencies", [])
                    ],
                    priority=TaskPriority(step_data.get("priority", "medium").lower()),
                    success_probability=step_data.get("success_probability", 1.0),
                    parallel_group=step_data.get("parallel_group"),
                )
                steps.append(step)
        
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            logger.warning(f"Failed to parse JSON plan, using fallback: {e}")
            # Fallback to simple parsing
            steps = self._fallback_parse(plan_text, task)
        
        return steps[:task.max_steps]
    
    def _fallback_parse(self, plan_text: str, task: Task) -> List[EnhancedStep]:
        """Fallback parsing for non-JSON plans."""
        steps = []
        lines = plan_text.split("\n")
        
        for i, line in enumerate(lines):
            line = line.strip()
            if line.startswith(("Step", str(i+1))):
                step = EnhancedStep(
                    id=str(uuid.uuid4()),
                    type=StepType.ACT,
                    description=line,
                    priority=TaskPriority.MEDIUM,
                    success_probability=0.9,
                )
                steps.append(step)
        
        if not steps:
            steps.append(EnhancedStep(
                id=str(uuid.uuid4()),
                type=StepType.ACT,
                description=task.description,
                priority=TaskPriority.HIGH,
                success_probability=0.8,
            ))
        
        return steps
    
    def _build_dependency_graph(
        self,
        steps: List[EnhancedStep],
    ) -> Dict[str, List[str]]:
        """Build dependency graph from steps."""
        graph = {}
        
        for step in steps:
            dependencies = [dep.step_id for dep in step.dependencies]
            graph[step.id] = dependencies
        
        return graph
    
    def _identify_parallel_groups(
        self,
        steps: List[EnhancedStep],
        dependency_graph: Dict[str, List[str]],
    ) -> Dict[str, List[str]]:
        """Identify steps that can execute in parallel."""
        parallel_groups = {}
        
        # Group steps by their parallel_group if specified
        for step in steps:
            if step.parallel_group:
                if step.parallel_group not in parallel_groups:
                    parallel_groups[step.parallel_group] = []
                parallel_groups[step.parallel_group].append(step.id)
        
        # Auto-detect parallel opportunities
        # Steps with no dependencies or same dependencies can run in parallel
        processed = set()
        group_id = 0
        
        for step in steps:
            if step.id in processed or step.parallel_group:
                continue
            
            # Find steps with same dependencies
            same_deps = [
                s.id for s in steps
                if s.id not in processed
                and dependency_graph.get(s.id) == dependency_graph.get(step.id)
                and not s.parallel_group
            ]
            
            if len(same_deps) > 1:
                group_name = f"auto_group_{group_id}"
                parallel_groups[group_name] = same_deps
                processed.update(same_deps)
                group_id += 1
        
        return parallel_groups
    
    def _estimate_duration(
        self,
        steps: List[EnhancedStep],
        parallel_groups: Dict[str, List[str]],
    ) -> float:
        """Estimate total execution duration."""
        # Simple estimation: sum of sequential steps, max of parallel groups
        total = 0.0
        processed = set()
        
        for step in steps:
            if step.id in processed:
                continue
            
            # Check if in parallel group
            in_group = False
            for group_steps in parallel_groups.values():
                if step.id in group_steps:
                    # Take max duration in group
                    group_duration = max(
                        s.estimated_duration or 5.0
                        for s in steps
                        if s.id in group_steps
                    )
                    total += group_duration
                    processed.update(group_steps)
                    in_group = True
                    break
            
            if not in_group:
                total += step.estimated_duration or 5.0
                processed.add(step.id)
        
        return total
    
    def _estimate_success_probability(
        self,
        steps: List[EnhancedStep],
    ) -> float:
        """Estimate overall success probability."""
        # Product of individual step probabilities
        probability = 1.0
        for step in steps:
            probability *= step.success_probability
        return probability
    
    async def replan(
        self,
        plan: EnhancedPlan,
        failed_step: EnhancedStep,
        error: str,
    ) -> EnhancedPlan:
        """
        Replan after a step failure.
        
        Args:
            plan: Original plan
            failed_step: Step that failed
            error: Error message
            
        Returns:
            Updated plan with recovery steps
        """
        logger.info(f"Replanning after step failure: {failed_step.id}")
        
        # Create recovery task
        recovery_task = Task(
            id=str(uuid.uuid4()),
            description=f"Recover from failure: {error}",
            context=f"Failed step: {failed_step.description}",
            max_steps=5,
        )
        
        # Generate recovery plan
        recovery_plan = await self.create_plan(recovery_task)
        
        # Insert recovery steps after failed step
        failed_index = next(
            i for i, s in enumerate(plan.steps)
            if s.id == failed_step.id
        )
        
        new_steps = (
            plan.steps[:failed_index + 1] +
            recovery_plan.steps +
            plan.steps[failed_index + 1:]
        )
        
        # Rebuild plan
        plan.steps = new_steps
        plan.dependency_graph = self._build_dependency_graph(new_steps)
        plan.parallel_groups = self._identify_parallel_groups(
            new_steps,
            plan.dependency_graph,
        )
        
        logger.info(f"Created recovery plan with {len(recovery_plan.steps)} steps")
        return plan
