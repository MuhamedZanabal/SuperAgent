"""
Tests for agent system.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock
import uuid

from superagent.agents.models import Task, TaskPriority, AgentConfig
from superagent.agents.react_agent import ReActAgent
from superagent.agents.planner import Planner
from superagent.llm.models import LLMResponse


@pytest.fixture
def sample_task():
    """Create a sample task."""
    return Task(
        id=str(uuid.uuid4()),
        description="Write a Python function to calculate fibonacci numbers",
        priority=TaskPriority.MEDIUM,
        max_steps=5,
    )


@pytest.fixture
def agent_config():
    """Create agent configuration."""
    return AgentConfig(
        name="test_agent",
        model="gpt-4-turbo-preview",
        max_iterations=5,
    )


@pytest.mark.asyncio
async def test_planner_creates_plan(sample_task):
    """Test planner creates a plan."""
    mock_llm = MagicMock()
    mock_llm.generate = AsyncMock(return_value=LLMResponse(
        id="test",
        model="gpt-4",
        content="Step 1: Think about the problem\nStep 2: Write the function\nStep 3: Test it",
        provider="test",
    ))
    
    mock_registry = MagicMock()
    mock_registry.get_function_definitions.return_value = []
    
    planner = Planner(mock_llm, mock_registry)
    plan = await planner.create_plan(sample_task)
    
    assert plan.task_id == sample_task.id
    assert len(plan.steps) > 0
    assert plan.reasoning


@pytest.mark.asyncio
async def test_react_agent_execution(sample_task, agent_config):
    """Test ReAct agent execution."""
    mock_llm = MagicMock()
    mock_llm.generate = AsyncMock(return_value=LLMResponse(
        id="test",
        model="gpt-4",
        content="Step 1: Analyze requirements",
        provider="test",
    ))
    
    mock_memory = MagicMock()
    mock_registry = MagicMock()
    mock_registry.get_function_definitions.return_value = []
    
    agent = ReActAgent(
        config=agent_config,
        llm_provider=mock_llm,
        memory_manager=mock_memory,
        tool_registry=mock_registry,
    )
    
    result = await agent.run(sample_task)
    
    assert result.task_id == sample_task.id
    assert result.steps_executed >= 0
