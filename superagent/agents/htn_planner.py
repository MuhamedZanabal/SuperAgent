"""
Hierarchical Task Network (HTN) planner for advanced task decomposition.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Callable, Dict, Any, Set
from enum import Enum
import uuid
import asyncio
from collections import defaultdict

from superagent.agents.models import Task, Plan, Step
from superagent.llm.provider import UnifiedLLMProvider
from superagent.llm.models import LLMRequest, Message
from superagent.tools.registry import ToolRegistry
from superagent.core.logger import get_logger

logger = get_logger(__name__)


class TaskType(Enum):
    """Task decomposition types."""
    ATOMIC = "atomic"  # Cannot be decomposed further
    COMPOSITE = "composite"  # Can be decomposed into subtasks
    CONDITIONAL = "conditional"  # Execution depends on conditions


class ExecutionStrategy(Enum):
    """Task execution strategies."""
    SEQUENTIAL = "sequential"  # Execute subtasks in order
    PARALLEL = "parallel"  # Execute subtasks concurrently
    CONDITIONAL = "conditional"  # Execute based on conditions


@dataclass
class TaskNode:
    """Recursive task decomposition structure."""
    task_id: str
    description: str
    task_type: TaskType
    preconditions: List[Callable] = field(default_factory=list)
    postconditions: List[Callable] = field(default_factory=list)
    subtasks: List['TaskNode'] = field(default_factory=list)
    estimated_complexity: float = 1.0
    execution_strategy: ExecutionStrategy = ExecutionStrategy.SEQUENTIAL
    tool_name: Optional[str] = None
    parameters: Dict[str, Any] = field(default_factory=dict)
    dependencies: Set[str] = field(default_factory=set)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TaskGraph:
    """Directed acyclic graph of tasks with dependencies."""
    nodes: Dict[str, TaskNode]
    edges: Dict[str, Set[str]]  # task_id -> set of dependent task_ids
    root_tasks: List[str]
    
    def get_execution_levels(self) -> List[List[str]]:
        """
        Get tasks grouped by execution level (topological sort).
        
        Returns:
            List of task ID lists, where each inner list can be executed in parallel
        """
        # Calculate in-degree for each node
        in_degree = defaultdict(int)
        for task_id in self.nodes:
            in_degree[task_id] = 0
        
        for task_id, dependents in self.edges.items():
            for dependent in dependents:
                in_degree[dependent] += 1
        
        # Find nodes with no dependencies
        queue = [task_id for task_id in self.nodes if in_degree[task_id] == 0]
        levels = []
        
        while queue:
            # Current level - all tasks with no remaining dependencies
            current_level = queue[:]
            levels.append(current_level)
            queue = []
            
            # Process current level
            for task_id in current_level:
                # Reduce in-degree for dependent tasks
                for dependent in self.edges.get(task_id, set()):
                    in_degree[dependent] -= 1
                    if in_degree[dependent] == 0:
                        queue.append(dependent)
        
        return levels


class HTNPlanner:
    """
    Hierarchical Task Network planner with constraint satisfaction.
    
    Decomposes complex tasks into hierarchical structures with
    dependency management and parallel execution optimization.
    """
    
    def __init__(
        self,
        llm_provider: UnifiedLLMProvider,
        tool_registry: ToolRegistry,
        model: str = "gpt-4-turbo-preview",
        max_decomposition_depth: int = 5,
    ):
        """
        Initialize HTN planner.
        
        Args:
            llm_provider: LLM provider for planning
            tool_registry: Tool registry for available actions
            model: Model to use for planning
            max_decomposition_depth: Maximum task decomposition depth
        """
        self.llm_provider = llm_provider
        self.tool_registry = tool_registry
        self.model = model
        self.max_decomposition_depth = max_decomposition_depth
    
    async def decompose_query(self, query: str, context: Optional[Dict[str, Any]] = None) -> TaskGraph:
        """
        Multi-stage task decomposition with dependency analysis.
        
        Args:
            query: User query to decompose
            context: Optional context information
            
        Returns:
            TaskGraph with hierarchical task structure
        """
        logger.info(f"Decomposing query: {query[:100]}...")
        
        # Stage 1: Intent classification
        intent = await self._classify_intent(query)
        logger.debug(f"Classified intent: {intent}")
        
        # Stage 2: Extract dependencies
        dependencies = await self._extract_dependencies(query, context)
        logger.debug(f"Extracted {len(dependencies)} dependencies")
        
        # Stage 3: Build constraint network
        task_graph = await self._build_constraint_network(
            query=query,
            intent=intent,
            dependencies=dependencies,
            context=context,
        )
        
        # Stage 4: Optimize execution plan
        optimized_graph = await self._optimize_execution_plan(task_graph)
        
        logger.info(f"Created task graph with {len(optimized_graph.nodes)} nodes")
        return optimized_graph
    
    async def _classify_intent(self, query: str) -> Dict[str, Any]:
        """
        Classify query intent (question/action/hybrid).
        
        Args:
            query: User query
            
        Returns:
            Intent classification with confidence scores
        """
        system_prompt = """Classify the user's intent into one of these categories:
- QUESTION: User is asking for information
- ACTION: User wants to perform an action or task
- HYBRID: Query contains both questions and actions

Also identify:
- Primary goal
- Required capabilities (e.g., file_access, web_search, code_execution)
- Estimated complexity (1-10)

Respond in JSON format."""
        
        request = LLMRequest(
            model=self.model,
            messages=[
                Message(role="system", content=system_prompt),
                Message(role="user", content=f"Query: {query}"),
            ],
            temperature=0.3,
        )
        
        response = await self.llm_provider.generate(request)
        
        # Parse JSON response (simplified - add proper error handling)
        try:
            import json
            intent = json.loads(response.content)
        except:
            intent = {
                "type": "ACTION",
                "primary_goal": query,
                "capabilities": [],
                "complexity": 5,
            }
        
        return intent
    
    async def _extract_dependencies(
        self,
        query: str,
        context: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Extract task dependencies from query.
        
        Args:
            query: User query
            context: Optional context
            
        Returns:
            List of dependency relationships
        """
        system_prompt = """Analyze the query and identify task dependencies.
For each subtask, identify:
- What needs to be done
- What it depends on (prerequisites)
- What it enables (dependents)

Respond in JSON format with a list of tasks and their dependencies."""
        
        request = LLMRequest(
            model=self.model,
            messages=[
                Message(role="system", content=system_prompt),
                Message(role="user", content=f"Query: {query}\nContext: {context or {}}"),
            ],
            temperature=0.3,
        )
        
        response = await self.llm_provider.generate(request)
        
        # Parse dependencies (simplified)
        try:
            import json
            dependencies = json.loads(response.content)
            if isinstance(dependencies, dict):
                dependencies = dependencies.get("tasks", [])
        except:
            dependencies = []
        
        return dependencies
    
    async def _build_constraint_network(
        self,
        query: str,
        intent: Dict[str, Any],
        dependencies: List[Dict[str, Any]],
        context: Optional[Dict[str, Any]] = None,
    ) -> TaskGraph:
        """
        Build constraint satisfaction network from dependencies.
        
        Args:
            query: User query
            intent: Intent classification
            dependencies: Task dependencies
            context: Optional context
            
        Returns:
            TaskGraph with constraints
        """
        nodes = {}
        edges = defaultdict(set)
        root_tasks = []
        
        # Get available tools
        available_tools = {
            tool['name']: tool
            for tool in self.tool_registry.get_function_definitions()
        }
        
        # Create root task
        root_id = str(uuid.uuid4())
        root_node = TaskNode(
            task_id=root_id,
            description=query,
            task_type=TaskType.COMPOSITE,
            estimated_complexity=intent.get("complexity", 5),
        )
        nodes[root_id] = root_node
        root_tasks.append(root_id)
        
        # Create subtasks from dependencies
        for dep in dependencies:
            task_id = str(uuid.uuid4())
            task_desc = dep.get("description", dep.get("task", ""))
            
            # Determine if atomic or composite
            task_type = TaskType.ATOMIC if dep.get("atomic", False) else TaskType.COMPOSITE
            
            # Match to tool if possible
            tool_name = None
            for tool_id, tool_def in available_tools.items():
                if tool_id.lower() in task_desc.lower():
                    tool_name = tool_id
                    task_type = TaskType.ATOMIC
                    break
            
            node = TaskNode(
                task_id=task_id,
                description=task_desc,
                task_type=task_type,
                tool_name=tool_name,
                estimated_complexity=dep.get("complexity", 1.0),
            )
            nodes[task_id] = node
            
            # Add dependencies
            for prereq in dep.get("prerequisites", []):
                # Find matching node
                for other_id, other_node in nodes.items():
                    if prereq.lower() in other_node.description.lower():
                        edges[other_id].add(task_id)
                        node.dependencies.add(other_id)
        
        return TaskGraph(nodes=nodes, edges=edges, root_tasks=root_tasks)
    
    async def _optimize_execution_plan(self, graph: TaskGraph) -> TaskGraph:
        """
        Optimize execution plan for parallelism and efficiency.
        
        Args:
            graph: Initial task graph
            
        Returns:
            Optimized task graph
        """
        # Get execution levels for parallel optimization
        levels = graph.get_execution_levels()
        
        # Mark tasks in same level for parallel execution
        for level in levels:
            if len(level) > 1:
                for task_id in level:
                    node = graph.nodes[task_id]
                    if node.task_type == TaskType.ATOMIC:
                        node.execution_strategy = ExecutionStrategy.PARALLEL
        
        # Estimate total complexity
        total_complexity = sum(node.estimated_complexity for node in graph.nodes.values())
        logger.debug(f"Optimized plan complexity: {total_complexity:.2f}")
        
        return graph
    
    async def create_plan_from_graph(self, graph: TaskGraph) -> Plan:
        """
        Convert task graph to executable plan.
        
        Args:
            graph: Task graph
            
        Returns:
            Executable plan
        """
        steps = []
        
        # Convert nodes to steps in execution order
        levels = graph.get_execution_levels()
        for level in levels:
            for task_id in level:
                node = graph.nodes[task_id]
                
                # Create step from node
                step = Step(
                    id=node.task_id,
                    type=self._map_task_type_to_step_type(node.task_type),
                    description=node.description,
                    tool_name=node.tool_name,
                    parameters=node.parameters,
                )
                steps.append(step)
        
        plan = Plan(
            task_id=graph.root_tasks[0] if graph.root_tasks else str(uuid.uuid4()),
            steps=steps,
            reasoning=f"Hierarchical plan with {len(steps)} steps across {len(levels)} execution levels",
        )
        
        return plan
    
    def _map_task_type_to_step_type(self, task_type: TaskType):
        """Map TaskType to StepType."""
        from superagent.agents.models import StepType
        
        if task_type == TaskType.ATOMIC:
            return StepType.ACT
        elif task_type == TaskType.COMPOSITE:
            return StepType.THINK
        else:
            return StepType.OBSERVE
