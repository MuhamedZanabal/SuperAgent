"""
Planning system for task decomposition.
"""

from typing import List
import uuid

from superagent.agents.models import Task, Plan, Step, StepType
from superagent.llm.provider import UnifiedLLMProvider
from superagent.llm.models import LLMRequest, Message
from superagent.tools.registry import ToolRegistry
from superagent.core.logger import get_logger

logger = get_logger(__name__)


class Planner:
    """
    Planner for decomposing tasks into executable steps.
    
    Uses LLM to create multi-step plans with tool usage.
    """
    
    def __init__(
        self,
        llm_provider: UnifiedLLMProvider,
        tool_registry: ToolRegistry,
        model: str = "gpt-4-turbo-preview",
    ):
        """
        Initialize planner.
        
        Args:
            llm_provider: LLM provider for planning
            tool_registry: Tool registry for available actions
            model: Model to use for planning
        """
        self.llm_provider = llm_provider
        self.tool_registry = tool_registry
        self.model = model
    
    async def create_plan(self, task: Task) -> Plan:
        """
        Create a plan for a task.
        
        Args:
            task: Task to plan for
            
        Returns:
            Plan with steps
        """
        logger.info(f"Creating plan for task: {task.id}")
        
        # Get available tools
        tools = self.tool_registry.get_function_definitions()
        tool_descriptions = "\n".join([
            f"- {tool['name']}: {tool['description']}"
            for tool in tools
        ])
        
        # Build planning prompt
        system_prompt = f"""You are an expert task planner. Break down tasks into clear, executable steps.

Available tools:
{tool_descriptions}

For each step, specify:
1. Type: THINK (reasoning), ACT (use tool), OBSERVE (check result), or REFLECT (evaluate)
2. Description: What to do
3. Tool (if ACT): Which tool to use
4. Expected outcome: What should happen

Create a logical sequence of steps to accomplish the task."""
        
        user_prompt = f"""Task: {task.description}

Context: {task.context}
Constraints: {', '.join(task.constraints) if task.constraints else 'None'}
Success criteria: {', '.join(task.success_criteria) if task.success_criteria else 'Complete the task'}
Max steps: {task.max_steps}

Create a detailed plan with specific steps."""
        
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
        
        # Parse plan from response
        steps = self._parse_plan(response.content, task)
        
        plan = Plan(
            task_id=task.id,
            steps=steps,
            reasoning=response.content,
        )
        
        logger.info(f"Created plan with {len(steps)} steps")
        return plan
    
    def _parse_plan(self, plan_text: str, task: Task) -> List[Step]:
        """
        Parse plan text into structured steps.
        
        Args:
            plan_text: Plan text from LLM
            task: Original task
            
        Returns:
            List of steps
        """
        steps = []
        
        # Simple parsing - in production, use more robust parsing
        lines = plan_text.split("\n")
        current_step = None
        
        for line in lines:
            line = line.strip()
            
            # Detect step markers
            if line.startswith(("Step", "1.", "2.", "3.", "4.", "5.", "6.", "7.", "8.", "9.")):
                if current_step:
                    steps.append(current_step)
                
                # Create new step
                step_id = str(uuid.uuid4())
                
                # Determine step type
                step_type = StepType.THINK
                if "use tool" in line.lower() or "execute" in line.lower():
                    step_type = StepType.ACT
                elif "observe" in line.lower() or "check" in line.lower():
                    step_type = StepType.OBSERVE
                elif "reflect" in line.lower() or "evaluate" in line.lower():
                    step_type = StepType.REFLECT
                
                current_step = Step(
                    id=step_id,
                    type=step_type,
                    description=line,
                )
            
            elif current_step and line:
                # Add to current step description
                current_step.description += f" {line}"
        
        # Add last step
        if current_step:
            steps.append(current_step)
        
        # Ensure we have at least one step
        if not steps:
            steps.append(Step(
                id=str(uuid.uuid4()),
                type=StepType.ACT,
                description=task.description,
            ))
        
        # Limit to max steps
        return steps[:task.max_steps]
