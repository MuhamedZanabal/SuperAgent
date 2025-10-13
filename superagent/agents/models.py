"""
Pydantic models for agent system.
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum


class TaskPriority(str, Enum):
    """Task priority levels."""
    
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class Task(BaseModel):
    """A task for the agent to execute."""
    
    id: str
    description: str
    priority: TaskPriority = TaskPriority.MEDIUM
    context: Dict[str, Any] = Field(default_factory=dict)
    constraints: List[str] = Field(default_factory=list)
    success_criteria: List[str] = Field(default_factory=list)
    max_steps: int = 10
    timeout_seconds: int = 300
    created_at: datetime = Field(default_factory=datetime.utcnow)


class StepType(str, Enum):
    """Types of execution steps."""
    
    THINK = "think"
    ACT = "act"
    OBSERVE = "observe"
    REFLECT = "reflect"


class Step(BaseModel):
    """A single step in a plan."""
    
    id: str
    type: StepType
    description: str
    tool_name: Optional[str] = None
    tool_parameters: Dict[str, Any] = Field(default_factory=dict)
    expected_outcome: Optional[str] = None
    dependencies: List[str] = Field(default_factory=list)


class Plan(BaseModel):
    """A plan for executing a task."""
    
    task_id: str
    steps: List[Step]
    reasoning: str
    estimated_duration: Optional[int] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)


class StepResult(BaseModel):
    """Result from executing a step."""
    
    step_id: str
    success: bool
    output: Any
    error: Optional[str] = None
    observations: List[str] = Field(default_factory=list)
    execution_time_ms: float = 0.0
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class ExecutionResult(BaseModel):
    """Result from executing a task."""
    
    task_id: str
    success: bool
    output: Any
    error: Optional[str] = None
    steps_executed: int = 0
    step_results: List[StepResult] = Field(default_factory=list)
    total_time_ms: float = 0.0
    completed_at: datetime = Field(default_factory=datetime.utcnow)


class AgentConfig(BaseModel):
    """Configuration for an agent."""
    
    name: str
    model: str = "gpt-4-turbo-preview"
    temperature: float = 0.7
    max_iterations: int = 10
    enable_reflection: bool = True
    enable_memory: bool = True
    verbose: bool = False
    system_prompt: Optional[str] = None
