"""
Execution engine for running plans.
"""

import time
from typing import List, Optional

from superagent.agents.models import Plan, Step, StepResult, StepType
from superagent.tools.executor import ToolExecutor
from superagent.tools.models import ToolCall
from superagent.llm.provider import UnifiedLLMProvider
from superagent.llm.models import LLMRequest, Message
from superagent.core.logger import get_logger

logger = get_logger(__name__)


class Executor:
    """
    Executor for running plans with tool orchestration.
    
    Executes steps sequentially with observation and error handling.
    """
    
    def __init__(
        self,
        tool_executor: ToolExecutor,
        llm_provider: UnifiedLLMProvider,
        model: str = "gpt-4-turbo-preview",
    ):
        """
        Initialize executor.
        
        Args:
            tool_executor: Tool executor for actions
            llm_provider: LLM provider for reasoning
            model: Model to use
        """
        self.tool_executor = tool_executor
        self.llm_provider = llm_provider
        self.model = model
    
    async def execute_plan(
        self,
        plan: Plan,
        context: Optional[dict] = None,
    ) -> List[StepResult]:
        """
        Execute a plan.
        
        Args:
            plan: Plan to execute
            context: Execution context
            
        Returns:
            List of step results
        """
        logger.info(f"Executing plan for task: {plan.task_id}")
        
        results = []
        execution_context = context or {}
        
        for step in plan.steps:
            result = await self.execute_step(step, execution_context)
            results.append(result)
            
            # Update context with result
            execution_context[step.id] = result.output
            
            # Stop on failure if critical
            if not result.success and step.type == StepType.ACT:
                logger.warning(f"Step {step.id} failed, stopping execution")
                break
        
        logger.info(f"Completed execution with {len(results)} steps")
        return results
    
    async def execute_step(
        self,
        step: Step,
        context: dict,
    ) -> StepResult:
        """
        Execute a single step.
        
        Args:
            step: Step to execute
            context: Execution context
            
        Returns:
            Step result
        """
        start_time = time.time()
        
        try:
            if step.type == StepType.THINK:
                # Reasoning step
                result = await self._execute_think(step, context)
            elif step.type == StepType.ACT:
                # Action step with tool
                result = await self._execute_act(step, context)
            elif step.type == StepType.OBSERVE:
                # Observation step
                result = await self._execute_observe(step, context)
            elif step.type == StepType.REFLECT:
                # Reflection step
                result = await self._execute_reflect(step, context)
            else:
                result = StepResult(
                    step_id=step.id,
                    success=False,
                    output=None,
                    error=f"Unknown step type: {step.type}",
                )
            
            execution_time = (time.time() - start_time) * 1000
            result.execution_time_ms = execution_time
            
            return result
            
        except Exception as e:
            execution_time = (time.time() - start_time) * 1000
            logger.error(f"Step execution error: {e}")
            
            return StepResult(
                step_id=step.id,
                success=False,
                output=None,
                error=str(e),
                execution_time_ms=execution_time,
            )
    
    async def _execute_think(self, step: Step, context: dict) -> StepResult:
        """Execute a thinking/reasoning step."""
        # Use LLM to reason about the step
        request = LLMRequest(
            model=self.model,
            messages=[
                Message(
                    role="user",
                    content=f"Think about: {step.description}\n\nContext: {context}",
                ),
            ],
            temperature=0.7,
            max_tokens=500,
        )
        
        response = await self.llm_provider.generate(request)
        
        return StepResult(
            step_id=step.id,
            success=True,
            output=response.content,
            observations=[f"Reasoning: {response.content[:100]}..."],
        )
    
    async def _execute_act(self, step: Step, context: dict) -> StepResult:
        """Execute an action step with tool."""
        if not step.tool_name:
            return StepResult(
                step_id=step.id,
                success=False,
                output=None,
                error="No tool specified for ACT step",
            )
        
        # Create tool call
        tool_call = ToolCall(
            id=step.id,
            tool_name=step.tool_name,
            parameters=step.tool_parameters,
        )
        
        # Execute tool
        tool_output = await self.tool_executor.execute(tool_call)
        
        return StepResult(
            step_id=step.id,
            success=tool_output.success,
            output=tool_output.output,
            error=tool_output.error,
            observations=[f"Tool {step.tool_name} executed"],
        )
    
    async def _execute_observe(self, step: Step, context: dict) -> StepResult:
        """Execute an observation step."""
        # Observe previous results
        observations = []
        for key, value in context.items():
            if value:
                observations.append(f"{key}: {str(value)[:100]}")
        
        return StepResult(
            step_id=step.id,
            success=True,
            output=observations,
            observations=observations,
        )
    
    async def _execute_reflect(self, step: Step, context: dict) -> StepResult:
        """Execute a reflection step."""
        # Use LLM to reflect on progress
        request = LLMRequest(
            model=self.model,
            messages=[
                Message(
                    role="user",
                    content=f"Reflect on: {step.description}\n\nContext: {context}",
                ),
            ],
            temperature=0.7,
            max_tokens=300,
        )
        
        response = await self.llm_provider.generate(request)
        
        return StepResult(
            step_id=step.id,
            success=True,
            output=response.content,
            observations=[f"Reflection: {response.content[:100]}..."],
        )
