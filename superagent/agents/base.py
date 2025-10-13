"""
Base agent classes and interfaces.
"""

from abc import ABC, abstractmethod
from enum import Enum
from typing import Any, Dict, List, Optional
from datetime import datetime

from superagent.agents.models import Task, ExecutionResult, AgentConfig
from superagent.llm.provider import UnifiedLLMProvider
from superagent.memory.manager import MemoryManager
from superagent.tools.registry import ToolRegistry


class AgentState(str, Enum):
    """States an agent can be in."""
    
    IDLE = "idle"
    PLANNING = "planning"
    EXECUTING = "executing"
    REFLECTING = "reflecting"
    COMPLETED = "completed"
    FAILED = "failed"
    PAUSED = "paused"


class BaseAgent(ABC):
    """
    Abstract base class for agents.
    
    Defines the interface for autonomous agents with reasoning and execution.
    """
    
    def __init__(
        self,
        config: AgentConfig,
        llm_provider: UnifiedLLMProvider,
        memory_manager: MemoryManager,
        tool_registry: ToolRegistry,
    ):
        """
        Initialize the agent.
        
        Args:
            config: Agent configuration
            llm_provider: LLM provider for reasoning
            memory_manager: Memory manager for context
            tool_registry: Tool registry for actions
        """
        self.config = config
        self.llm_provider = llm_provider
        self.memory_manager = memory_manager
        self.tool_registry = tool_registry
        
        self.state = AgentState.IDLE
        self.current_task: Optional[Task] = None
        self.execution_history: List[ExecutionResult] = []
    
    @abstractmethod
    async def run(self, task: Task) -> ExecutionResult:
        """
        Run the agent on a task.
        
        Args:
            task: Task to execute
            
        Returns:
            ExecutionResult with outcome
        """
        pass
    
    @abstractmethod
    async def plan(self, task: Task) -> Any:
        """
        Create a plan for the task.
        
        Args:
            task: Task to plan for
            
        Returns:
            Plan object
        """
        pass
    
    @abstractmethod
    async def execute_step(self, step: Any) -> Any:
        """
        Execute a single step.
        
        Args:
            step: Step to execute
            
        Returns:
            Step result
        """
        pass
    
    async def reflect(self, result: ExecutionResult) -> Dict[str, Any]:
        """
        Reflect on execution result.
        
        Args:
            result: Execution result to reflect on
            
        Returns:
            Reflection insights
        """
        self.state = AgentState.REFLECTING
        
        # Basic reflection - can be overridden
        reflection = {
            "success": result.success,
            "lessons_learned": [],
            "improvements": [],
        }
        
        if not result.success:
            reflection["lessons_learned"].append(f"Failed: {result.error}")
            reflection["improvements"].append("Review error handling")
        
        return reflection
    
    def get_state(self) -> AgentState:
        """Get current agent state."""
        return self.state
    
    def pause(self) -> None:
        """Pause agent execution."""
        self.state = AgentState.PAUSED
    
    def resume(self) -> None:
        """Resume agent execution."""
        if self.state == AgentState.PAUSED:
            self.state = AgentState.EXECUTING
