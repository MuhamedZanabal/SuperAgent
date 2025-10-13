"""
Memory manager for hierarchical memory management.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta

from superagent.memory.base import BaseMemory, MemoryType
from superagent.memory.models import MemoryItem, MemoryQuery, MemoryResult
from superagent.memory.vector_store import VectorStore
from superagent.memory.embeddings import EmbeddingProvider
from superagent.core.logger import get_logger

logger = get_logger(__name__)


class MemoryManager(BaseMemory):
    """
    Hierarchical memory manager.
    
    Manages different types of memory with automatic cleanup and retrieval.
    """
    
    def __init__(
        self,
        vector_store: VectorStore,
        embedding_provider: EmbeddingProvider,
        short_term_limit: int = 50,
        working_limit: int = 20,
        long_term_limit: int = 1000,
    ):
        """
        Initialize memory manager.
        
        Args:
            vector_store: Vector store for persistence
            embedding_provider: Provider for embeddings
            short_term_limit: Max items in short-term memory
            working_limit: Max items in working memory
            long_term_limit: Max items in long-term memory
        """
        self.vector_store = vector_store
        self.embedding_provider = embedding_provider
        self.short_term_limit = short_term_limit
        self.working_limit = working_limit
        self.long_term_limit = long_term_limit
        
        # In-memory caches for fast access
        self._short_term_cache: List[MemoryItem] = []
        self._working_cache: List[MemoryItem] = []
    
    async def add(self, item: MemoryItem) -> str:
        """
        Add a memory item.
        
        Args:
            item: Memory item to add
            
        Returns:
            ID of the added item
        """
        # Generate embedding if not provided
        if not item.embedding:
            item.embedding = await self.embedding_provider.embed(item.content)
        
        # Add to vector store
        ids = await self.vector_store.add([item])
        item.id = ids[0]
        
        # Add to appropriate cache
        if item.memory_type == MemoryType.SHORT_TERM:
            self._short_term_cache.append(item)
            await self._cleanup_short_term()
        elif item.memory_type == MemoryType.WORKING:
            self._working_cache.append(item)
            await self._cleanup_working()
        
        logger.debug(f"Added memory item: {item.id} ({item.memory_type})")
        return item.id
    
    async def get(self, item_id: str) -> Optional[MemoryItem]:
        """
        Get a memory item by ID.
        
        Args:
            item_id: ID of the item
            
        Returns:
            MemoryItem if found, None otherwise
        """
        # Check caches first
        for item in self._short_term_cache + self._working_cache:
            if item.id == item_id:
                item.access_count += 1
                item.last_accessed = datetime.utcnow()
                return item
        
        # Check vector store
        item = await self.vector_store.get(item_id)
        if item:
            item.access_count += 1
            item.last_accessed = datetime.utcnow()
            # Update in store
            await self.update(item_id, {
                "access_count": item.access_count,
                "last_accessed": item.last_accessed,
            })
        
        return item
    
    async def search(self, query: MemoryQuery) -> List[MemoryResult]:
        """
        Search for relevant memories.
        
        Args:
            query: Search query
            
        Returns:
            List of matching memory results
        """
        # Generate query embedding
        query_embedding = await self.embedding_provider.embed(query.text)
        
        # Build filters
        filters = {}
        if query.memory_types:
            filters["memory_types"] = query.memory_types
        if query.metadata_filters:
            filters.update(query.metadata_filters)
        
        # Search vector store
        results = await self.vector_store.search(
            query_embedding=query_embedding,
            limit=query.limit,
            filters=filters if filters else None,
        )
        
        # Filter by relevance threshold
        results = [
            r for r in results
            if r.relevance_score >= query.min_relevance
        ]
        
        # Update access counts
        for result in results:
            result.item.access_count += 1
            result.item.last_accessed = datetime.utcnow()
        
        return results
    
    async def update(self, item_id: str, updates: Dict[str, Any]) -> bool:
        """
        Update a memory item.
        
        Args:
            item_id: ID of the item
            updates: Fields to update
            
        Returns:
            True if successful
        """
        # Get current item
        item = await self.vector_store.get(item_id)
        if not item:
            return False
        
        # Apply updates
        for key, value in updates.items():
            if hasattr(item, key):
                setattr(item, key, value)
        
        # Re-add to vector store (ChromaDB doesn't have update)
        await self.vector_store.delete(item_id)
        await self.vector_store.add([item])
        
        return True
    
    async def delete(self, item_id: str) -> bool:
        """
        Delete a memory item.
        
        Args:
            item_id: ID of the item
            
        Returns:
            True if successful
        """
        # Remove from caches
        self._short_term_cache = [i for i in self._short_term_cache if i.id != item_id]
        self._working_cache = [i for i in self._working_cache if i.id != item_id]
        
        # Remove from vector store
        return await self.vector_store.delete(item_id)
    
    async def clear(self, memory_type: Optional[MemoryType] = None) -> int:
        """
        Clear memories.
        
        Args:
            memory_type: Type to clear (None for all)
            
        Returns:
            Number of items cleared
        """
        if memory_type is None:
            # Clear all
            count = await self.vector_store.clear()
            self._short_term_cache.clear()
            self._working_cache.clear()
            return count
        
        # Clear specific type
        if memory_type == MemoryType.SHORT_TERM:
            count = len(self._short_term_cache)
            self._short_term_cache.clear()
            return count
        elif memory_type == MemoryType.WORKING:
            count = len(self._working_cache)
            self._working_cache.clear()
            return count
        
        # For other types, would need to query and delete
        return 0
    
    async def count(self, memory_type: Optional[MemoryType] = None) -> int:
        """
        Count memory items.
        
        Args:
            memory_type: Type to count (None for all)
            
        Returns:
            Number of items
        """
        if memory_type == MemoryType.SHORT_TERM:
            return len(self._short_term_cache)
        elif memory_type == MemoryType.WORKING:
            return len(self._working_cache)
        
        # Would need to query vector store for accurate count
        return 0
    
    async def _cleanup_short_term(self):
        """Clean up short-term memory when limit exceeded."""
        if len(self._short_term_cache) > self.short_term_limit:
            # Remove oldest items
            self._short_term_cache.sort(key=lambda x: x.timestamp)
            removed = self._short_term_cache[:len(self._short_term_cache) - self.short_term_limit]
            self._short_term_cache = self._short_term_cache[-self.short_term_limit:]
            
            logger.debug(f"Cleaned up {len(removed)} short-term memories")
    
    async def _cleanup_working(self):
        """Clean up working memory when limit exceeded."""
        if len(self._working_cache) > self.working_limit:
            # Remove least important items
            self._working_cache.sort(key=lambda x: x.importance, reverse=True)
            self._working_cache = self._working_cache[:self.working_limit]
            
            logger.debug(f"Cleaned up working memory")
