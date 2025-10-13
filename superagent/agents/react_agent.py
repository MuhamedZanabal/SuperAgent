"""
ReAct (Reasoning + Acting) agent implementation.
"""

import time
import uuid
from typing import Optional

from superagent.agents.base import BaseAgent, AgentState
from superagent.agents.models import (
    Task,
    ExecutionResult,
    AgentConfig,
    Plan,
    Step,
    StepType,
    StepResult,
)
from superagent.agents.planner import Planner
from superagent.agents.executor import Executor
from superagent.llm.provider import UnifiedLLMProvider
from superagent.llm.models import LLMRequest, Message
from superagent.memory.manager import MemoryManager
from superagent.tools.registry import ToolRegistry
from superagent.tools.executor import ToolExecutor
from superagent.core.logger import get_logger

logger = get_logger(__name__)


class ReActAgent(BaseAgent):
    """
    ReAct agent that alternates between reasoning and acting.
    
    Implements the ReAct pattern: Reason about what to do, Act with tools,
    Observe results, and repeat until task is complete.
    """
    
    def __init__(
        self,
        config: AgentConfig,
        llm_provider: UnifiedLLMProvider,
        memory_manager: MemoryManager,
        tool_registry: ToolRegistry,
    ):
        """Initialize ReAct agent."""
        super().__init__(config, llm_provider, memory_manager, tool_registry)
        
        # Initialize planner and executor
        self.planner = Planner(llm_provider, tool_registry, config.model)
        
        tool_executor = ToolExecutor(tool_registry)
        self.executor = Executor(tool_executor, llm_provider, config.model)
        
        # System prompt for ReAct
        self.system_prompt = config.system_prompt or """You are an autonomous AI agent using the ReAct pattern.

For each task:
1. THINK: Reason about what to do next
2. ACT: Use tools to take action
3. OBSERVE: Check the results
4. Repeat until task is complete

Be systematic, break down complex tasks, and verify your work."""
    
    async def run(self, task: Task) -> ExecutionResult:
        """
        Run the agent on a task using ReAct pattern.
        
        Args:
            task: Task to execute
            
        Returns:
            ExecutionResult with outcome
        """
        logger.info(f"ReAct agent starting task: {task.id}")
        start_time = time.time()
        
        self.current_task = task
        self.state = AgentState.PLANNING
        
        try:
            # Create plan
            plan = await self.plan(task)
            
            # Execute plan
            self.state = AgentState.EXECUTING
            step_results = await self.executor.execute_plan(plan)
            
            # Determine overall success
            success = all(r.success for r in step_results if r.success is not None)
            
            # Collect output
            output = {
                "plan": plan.reasoning,
                "steps": [
                    {
                        "description": step.description,
                        "result": result.output,
                        "success": result.success,
                    }
                    for step, result in zip(plan.steps, step_results)
                ],
            }
            
            # Create result
            total_time = (time.time() - start_time) * 1000
            result = ExecutionResult(
                task_id=task.id,
                success=success,
                output=output,
                steps_executed=len(step_results),
                step_results=step_results,
                total_time_ms=total_time,
            )
            
            # Reflect if enabled
            if self.config.enable_reflection:
                reflection = await self.reflect(result)
                result.output["reflection"] = reflection
            
            self.state = AgentState.COMPLETED if success else AgentState.FAILED
            self.execution_history.append(result)
            
            logger.info(f"Task completed: {task.id} (success={success})")
            return result
            
        except Exception as e:
            logger.error(f"Task execution failed: {e}")
            total_time = (time.time() - start_time) * 1000
            
            result = ExecutionResult(
                task_id=task.id,
                success=False,
                output=None,
                error=str(e),
                total_time_ms=total_time,
            )
            
            self.state = AgentState.FAILED
            self.execution_history.append(result)
            
            return result
    
    async def plan(self, task: Task) -> Plan:
        """
        Create a plan for the task.
        
        Args:
            task: Task to plan for
            
        Returns:
            Plan with steps
        """
        return await self.planner.create_plan(task)
    
    async def execute_step(self, step: Step) -> StepResult:
        """
        Execute a single step.
        
        Args:
            step: Step to execute
            
        Returns:
            Step result
        """
        return await self.executor.execute_step(step, {})
