"""
UX Orchestrator - Central state machine for interactive CLI experience.
"""

import asyncio
from enum import Enum
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field
from datetime import datetime

from superagent.core.logger import get_logger
from superagent.core.runtime import SuperAgentRuntime
from superagent.ux.intent_router import IntentRouter, Intent
from superagent.ux.diff_engine import DiffEngine
from superagent.ux.checkpoint import CheckpointManager
from superagent.orchestration.event_bus import EventBus, Event

logger = get_logger(__name__)


class UXState(str, Enum):
    """UX state machine states."""
    IDLE = "idle"
    PARSING_INPUT = "parsing_input"
    RESOLVING_INTENT = "resolving_intent"
    PLANNING = "planning"
    PREVIEWING = "previewing"
    CONFIRMING = "confirming"
    EXECUTING = "executing"
    STREAMING = "streaming"
    COMPLETED = "completed"
    ERROR = "error"


@dataclass
class UXContext:
    """Context for UX orchestration."""
    session_id: str
    user_input: str = ""
    intent: Optional[Intent] = None
    plan: Optional[Dict[str, Any]] = None
    preview: Optional[Any] = None
    execution_result: Optional[Any] = None
    error: Optional[Exception] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)


class UXOrchestrator:
    """
    Central UX orchestrator implementing GeminiCLI-style experience.
    
    Features:
    - Natural language intent resolution
    - Diff-first preview workflow
    - Checkpointing and session management
    - Event-driven state machine
    - Safety gates and RBAC integration
    """
    
    def __init__(
        self,
        runtime: SuperAgentRuntime,
        event_bus: Optional[EventBus] = None,
    ):
        """
        Initialize UX orchestrator.
        
        Args:
            runtime: SuperAgent runtime instance
            event_bus: Optional event bus for coordination
        """
        self.runtime = runtime
        self.event_bus = event_bus or EventBus()
        
        # Components
        self.intent_router = IntentRouter(runtime.llm_provider)
        self.diff_engine = DiffEngine()
        self.checkpoint_manager = CheckpointManager()
        
        # State
        self.state = UXState.IDLE
        self.context: Optional[UXContext] = None
        
        # Callbacks
        self._state_callbacks: Dict[UXState, List[callable]] = {}
        
        logger.info("UX orchestrator initialized")
    
    def on_state_change(self, state: UXState, callback: callable) -> None:
        """Register callback for state changes."""
        if state not in self._state_callbacks:
            self._state_callbacks[state] = []
        self._state_callbacks[state].append(callback)
    
    async def _transition_to(self, new_state: UXState) -> None:
        """Transition to new state and trigger callbacks."""
        old_state = self.state
        self.state = new_state
        
        logger.info(f"State transition: {old_state} -> {new_state}")
        
        # Emit event
        await self.event_bus.publish(Event(
            type="ux.state_changed",
            data={
                "old_state": old_state,
                "new_state": new_state,
                "context": self.context,
            },
        ))
        
        # Trigger callbacks
        if new_state in self._state_callbacks:
            for callback in self._state_callbacks[new_state]:
                try:
                    if asyncio.iscoroutinefunction(callback):
                        await callback(self.context)
                    else:
                        callback(self.context)
                except Exception as e:
                    logger.error(f"Callback error: {e}")
    
    async def process_input(
        self,
        user_input: str,
        session_id: Optional[str] = None,
        context_files: Optional[List[str]] = None,
    ) -> UXContext:
        """
        Process user input through the UX pipeline.
        
        Args:
            user_input: Natural language input from user
            session_id: Optional session ID for continuity
            context_files: Optional list of @mentioned files
        
        Returns:
            UXContext with results
        """
        # Create context
        self.context = UXContext(
            session_id=session_id or f"session_{datetime.now().timestamp()}",
            user_input=user_input,
            metadata={
                "context_files": context_files or [],
            },
        )
        
        try:
            # Parse input
            await self._transition_to(UXState.PARSING_INPUT)
            await self._parse_input()
            
            # Resolve intent
            await self._transition_to(UXState.RESOLVING_INTENT)
            await self._resolve_intent()
            
            # Create plan
            await self._transition_to(UXState.PLANNING)
            await self._create_plan()
            
            # Generate preview
            await self._transition_to(UXState.PREVIEWING)
            await self._generate_preview()
            
            # Wait for confirmation (handled externally)
            await self._transition_to(UXState.CONFIRMING)
            
            return self.context
            
        except Exception as e:
            logger.error(f"UX pipeline error: {e}", exc_info=True)
            self.context.error = e
            await self._transition_to(UXState.ERROR)
            return self.context
    
    async def execute_plan(self, apply_partial: bool = False) -> UXContext:
        """
        Execute the planned actions.
        
        Args:
            apply_partial: If True, allow partial application of changes
        
        Returns:
            Updated context with execution results
        """
        if not self.context or not self.context.plan:
            raise ValueError("No plan to execute")
        
        try:
            await self._transition_to(UXState.EXECUTING)
            
            # Create checkpoint before execution
            checkpoint_id = await self.checkpoint_manager.create_checkpoint(
                session_id=self.context.session_id,
                state=self.context,
            )
            
            logger.info(f"Created checkpoint: {checkpoint_id}")
            
            # Execute plan
            result = await self._execute_plan_steps(apply_partial)
            self.context.execution_result = result
            
            await self._transition_to(UXState.COMPLETED)
            
            return self.context
            
        except Exception as e:
            logger.error(f"Execution error: {e}", exc_info=True)
            self.context.error = e
            await self._transition_to(UXState.ERROR)
            
            # Offer rollback
            logger.info("Execution failed, checkpoint available for rollback")
            
            return self.context
    
    async def _parse_input(self) -> None:
        """Parse user input and extract context."""
        # Extract @mentions for file context
        context_files = self.context.metadata.get("context_files", [])
        
        # Load file contents if needed
        if context_files:
            file_contents = {}
            for file_path in context_files:
                try:
                    with open(file_path, 'r') as f:
                        file_contents[file_path] = f.read()
                except Exception as e:
                    logger.warning(f"Could not read {file_path}: {e}")
            
            self.context.metadata["file_contents"] = file_contents
    
    async def _resolve_intent(self) -> None:
        """Resolve user intent using NL2Task router."""
        intent = await self.intent_router.route(
            user_input=self.context.user_input,
            context=self.context.metadata,
        )
        
        self.context.intent = intent
        logger.info(f"Resolved intent: {intent.type} (confidence: {intent.confidence})")
    
    async def _create_plan(self) -> None:
        """Create execution plan based on intent."""
        # Use planner from runtime
        from superagent.agents.advanced_planner import UnifiedAdvancedPlanner
        
        planner = UnifiedAdvancedPlanner(
            llm_provider=self.runtime.llm_provider,
            tool_registry=self.runtime.tool_registry,
        )
        
        plan = await planner.create_plan(
            goal=self.context.user_input,
            context=self.context.metadata,
        )
        
        self.context.plan = plan
        logger.info(f"Created plan with {len(plan.steps)} steps")
    
    async def _generate_preview(self) -> None:
        """Generate diff preview of planned changes."""
        if not self.context.plan:
            return
        
        preview = await self.diff_engine.generate_preview(
            plan=self.context.plan,
            context=self.context.metadata,
        )
        
        self.context.preview = preview
        logger.info("Generated preview")
    
    async def _execute_plan_steps(self, apply_partial: bool) -> Dict[str, Any]:
        """Execute plan steps."""
        # Use executor from orchestration
        from superagent.orchestration.orchestrator import Orchestrator
        
        orchestrator = Orchestrator(
            event_bus=self.event_bus,
            llm_provider=self.runtime.llm_provider,
            memory_manager=self.runtime.memory_manager,
            tool_registry=self.runtime.tool_registry,
        )
        
        result = await orchestrator.execute_goal(
            goal=self.context.user_input,
            context=self.context.metadata,
        )
        
        return result
    
    async def rollback_to_checkpoint(self, checkpoint_id: str) -> bool:
        """Rollback to a previous checkpoint."""
        try:
            state = await self.checkpoint_manager.restore_checkpoint(checkpoint_id)
            self.context = state
            await self._transition_to(UXState.IDLE)
            logger.info(f"Rolled back to checkpoint: {checkpoint_id}")
            return True
        except Exception as e:
            logger.error(f"Rollback failed: {e}")
            return False
