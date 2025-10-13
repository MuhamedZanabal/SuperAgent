"""
Context manager for conversation and task context.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
import uuid

from superagent.memory.models import ConversationContext, MemoryItem
from superagent.memory.base import MemoryType
from superagent.memory.manager import MemoryManager
from superagent.llm.models import Message
from superagent.core.logger import get_logger

logger = get_logger(__name__)


class ContextManager:
    """
    Manages conversation context and context windows.
    
    Handles token limits, summarization, and context retrieval.
    """
    
    def __init__(
        self,
        memory_manager: MemoryManager,
        max_context_tokens: int = 4096,
        summarization_threshold: int = 3000,
    ):
        """
        Initialize context manager.
        
        Args:
            memory_manager: Memory manager for storage
            max_context_tokens: Maximum tokens in context window
            summarization_threshold: Token count to trigger summarization
        """
        self.memory_manager = memory_manager
        self.max_context_tokens = max_context_tokens
        self.summarization_threshold = summarization_threshold
        
        # Active contexts
        self._contexts: Dict[str, ConversationContext] = {}
    
    def create_context(
        self,
        conversation_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> ConversationContext:
        """
        Create a new conversation context.
        
        Args:
            conversation_id: Optional conversation ID
            metadata: Optional metadata
            
        Returns:
            New ConversationContext
        """
        if conversation_id is None:
            conversation_id = str(uuid.uuid4())
        
        context = ConversationContext(
            conversation_id=conversation_id,
            metadata=metadata or {},
        )
        
        self._contexts[conversation_id] = context
        logger.debug(f"Created context: {conversation_id}")
        
        return context
    
    def get_context(self, conversation_id: str) -> Optional[ConversationContext]:
        """Get a conversation context by ID."""
        return self._contexts.get(conversation_id)
    
    async def add_message(
        self,
        conversation_id: str,
        message: Message,
        store_in_memory: bool = True,
    ) -> None:
        """
        Add a message to conversation context.
        
        Args:
            conversation_id: Conversation ID
            message: Message to add
            store_in_memory: Whether to store in long-term memory
        """
        context = self._contexts.get(conversation_id)
        if not context:
            context = self.create_context(conversation_id)
        
        # Add to context
        message_dict = {
            "role": message.role,
            "content": message.content,
        }
        context.messages.append(message_dict)
        context.updated_at = datetime.utcnow()
        
        # Estimate token count (rough approximation)
        context.token_count += len(message.content.split())
        
        # Store in memory if requested
        if store_in_memory:
            memory_item = MemoryItem(
                content=message.content,
                memory_type=MemoryType.EPISODIC,
                metadata={
                    "conversation_id": conversation_id,
                    "role": message.role,
                },
            )
            await self.memory_manager.add(memory_item)
        
        # Check if summarization needed
        if context.token_count > self.summarization_threshold:
            await self._summarize_context(context)
    
    def get_messages(
        self,
        conversation_id: str,
        limit: Optional[int] = None,
    ) -> List[Dict[str, str]]:
        """
        Get messages from conversation context.
        
        Args:
            conversation_id: Conversation ID
            limit: Optional limit on number of messages
            
        Returns:
            List of messages
        """
        context = self._contexts.get(conversation_id)
        if not context:
            return []
        
        messages = context.messages
        if limit:
            messages = messages[-limit:]
        
        return messages
    
    async def get_relevant_context(
        self,
        conversation_id: str,
        query: str,
        limit: int = 5,
    ) -> List[str]:
        """
        Get relevant context from memory.
        
        Args:
            conversation_id: Conversation ID
            query: Query for relevance
            limit: Maximum number of items
            
        Returns:
            List of relevant context strings
        """
        from superagent.memory.models import MemoryQuery
        
        # Search memory
        memory_query = MemoryQuery(
            text=query,
            memory_types=[MemoryType.EPISODIC, MemoryType.SEMANTIC],
            limit=limit,
            metadata_filters={"conversation_id": conversation_id},
        )
        
        results = await self.memory_manager.search(memory_query)
        
        return [r.item.content for r in results]
    
    async def _summarize_context(self, context: ConversationContext) -> None:
        """
        Summarize conversation context when it gets too long.
        
        Args:
            context: Context to summarize
        """
        # TODO: Implement summarization using LLM
        # For now, just truncate old messages
        if len(context.messages) > 20:
            # Keep system message and recent messages
            system_messages = [m for m in context.messages if m["role"] == "system"]
            recent_messages = context.messages[-15:]
            
            context.messages = system_messages + recent_messages
            context.token_count = sum(len(m["content"].split()) for m in context.messages)
            
            logger.debug(f"Truncated context: {context.conversation_id}")
    
    def clear_context(self, conversation_id: str) -> bool:
        """
        Clear a conversation context.
        
        Args:
            conversation_id: Conversation ID
            
        Returns:
            True if successful
        """
        if conversation_id in self._contexts:
            del self._contexts[conversation_id]
            return True
        return False
