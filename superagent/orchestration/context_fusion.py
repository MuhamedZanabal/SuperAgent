"""
Context Fusion Engine - Merges conversation, memory, files, and state into unified context.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from superagent.core.logger import get_logger
from superagent.memory.manager import MemoryManager
from superagent.memory.models import MemoryQuery

logger = get_logger(__name__)


class ContextNode(BaseModel):
    """Node in the context graph representing a piece of context."""

    id: str
    type: str  # "file", "memory", "conversation", "tool", "plan"
    content: str
    metadata: Dict[str, Any] = Field(default_factory=dict)
    relevance_score: float = 0.0
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    relationships: List[str] = Field(default_factory=list)  # IDs of related nodes


class UnifiedContext(BaseModel):
    """Unified context object merging all relevant information."""

    session_id: str
    nodes: List[ContextNode] = Field(default_factory=list)
    conversation_history: List[Dict[str, str]] = Field(default_factory=list)
    active_files: List[str] = Field(default_factory=list)
    active_tools: List[str] = Field(default_factory=list)
    current_plan: Optional[Dict[str, Any]] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

    def get_context_summary(self) -> str:
        """Generate a text summary of the unified context."""
        summary_parts = []

        if self.conversation_history:
            summary_parts.append(
                f"Conversation: {len(self.conversation_history)} messages"
            )

        if self.active_files:
            summary_parts.append(f"Files: {', '.join(self.active_files)}")

        if self.active_tools:
            summary_parts.append(f"Tools: {', '.join(self.active_tools)}")

        if self.current_plan:
            summary_parts.append(f"Plan: {self.current_plan.get('goal', 'Active')}")

        memory_nodes = [n for n in self.nodes if n.type == "memory"]
        if memory_nodes:
            summary_parts.append(f"Memories: {len(memory_nodes)} relevant")

        return " | ".join(summary_parts) if summary_parts else "Empty context"


class ContextFusionEngine:
    """
    Context Fusion Engine - Merges all context sources into unified workspace.

    Integrates:
    - Conversation history
    - Memory vectors
    - File context
    - Tool state
    - Plan state
    """

    def __init__(self, memory_manager: Optional[MemoryManager] = None):
        self.memory_manager = memory_manager
        self._context_cache: Dict[str, UnifiedContext] = {}

    async def fuse_context(
        self,
        session_id: str,
        conversation_history: List[Dict[str, str]],
        active_files: Optional[List[str]] = None,
        active_tools: Optional[List[str]] = None,
        current_plan: Optional[Dict[str, Any]] = None,
        query: Optional[str] = None,
    ) -> UnifiedContext:
        """
        Fuse all context sources into a unified context object.

        Args:
            session_id: Session identifier
            conversation_history: Recent conversation messages
            active_files: Files currently in context
            active_tools: Tools currently available
            current_plan: Active execution plan
            query: Optional query for semantic memory retrieval

        Returns:
            Unified context object
        """
        context = UnifiedContext(
            session_id=session_id,
            conversation_history=conversation_history,
            active_files=active_files or [],
            active_tools=active_tools or [],
            current_plan=current_plan,
        )

        # Add conversation nodes
        for i, msg in enumerate(conversation_history[-10:]):  # Last 10 messages
            node = ContextNode(
                id=f"conv_{i}",
                type="conversation",
                content=msg.get("content", ""),
                metadata={"role": msg.get("role", "user"), "index": i},
                relevance_score=1.0 - (i * 0.1),  # Recent messages more relevant
            )
            context.nodes.append(node)

        # Add file nodes
        for file_path in active_files or []:
            node = ContextNode(
                id=f"file_{file_path}",
                type="file",
                content=file_path,
                metadata={"path": file_path},
                relevance_score=0.8,
            )
            context.nodes.append(node)

        # Add memory nodes from semantic search
        if self.memory_manager and query:
            try:
                memory_query = MemoryQuery(query=query, limit=5)
                memory_results = await self.memory_manager.search(memory_query)

                for result in memory_results.results:
                    node = ContextNode(
                        id=f"memory_{result.item.id}",
                        type="memory",
                        content=result.item.content,
                        metadata=result.item.metadata,
                        relevance_score=result.score,
                        timestamp=result.item.timestamp,
                    )
                    context.nodes.append(node)
            except Exception as e:
                logger.warning(f"Failed to retrieve memories: {e}")

        # Add plan node
        if current_plan:
            node = ContextNode(
                id="current_plan",
                type="plan",
                content=str(current_plan.get("goal", "")),
                metadata=current_plan,
                relevance_score=1.0,
            )
            context.nodes.append(node)

        # Cache context
        self._context_cache[session_id] = context

        logger.info(
            f"Context fused: {len(context.nodes)} nodes",
            extra={"session_id": session_id},
        )

        return context

    def get_cached_context(self, session_id: str) -> Optional[UnifiedContext]:
        """Retrieve cached context for a session."""
        return self._context_cache.get(session_id)

    def clear_cache(self, session_id: Optional[str] = None) -> None:
        """Clear context cache."""
        if session_id:
            self._context_cache.pop(session_id, None)
        else:
            self._context_cache.clear()
