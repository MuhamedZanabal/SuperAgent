"""
Base classes for memory systems.
"""

from abc import ABC, abstractmethod
from enum import Enum
from typing import List, Optional, Dict, Any
from datetime import datetime

from superagent.memory.models import MemoryItem, MemoryQuery, MemoryResult


class MemoryType(str, Enum):
    """Types of memory storage."""
    
    SHORT_TERM = "short_term"  # Recent interactions (last few messages)
    WORKING = "working"  # Current task context
    LONG_TERM = "long_term"  # Persistent knowledge
    EPISODIC = "episodic"  # Specific events/conversations
    SEMANTIC = "semantic"  # Facts and knowledge


class BaseMemory(ABC):
    """
    Abstract base class for memory systems.
    
    Defines the interface for storing and retrieving memories.
    """
    
    @abstractmethod
    async def add(self, item: MemoryItem) -> str:
        """
        Add a memory item.
        
        Args:
            item: Memory item to add
            
        Returns:
            ID of the added item
        """
        pass
    
    @abstractmethod
    async def get(self, item_id: str) -> Optional[MemoryItem]:
        """
        Get a memory item by ID.
        
        Args:
            item_id: ID of the item
            
        Returns:
            MemoryItem if found, None otherwise
        """
        pass
    
    @abstractmethod
    async def search(self, query: MemoryQuery) -> List[MemoryResult]:
        """
        Search for relevant memories.
        
        Args:
            query: Search query with filters
            
        Returns:
            List of matching memory results
        """
        pass
    
    @abstractmethod
    async def update(self, item_id: str, updates: Dict[str, Any]) -> bool:
        """
        Update a memory item.
        
        Args:
            item_id: ID of the item to update
            updates: Dictionary of fields to update
            
        Returns:
            True if successful, False otherwise
        """
        pass
    
    @abstractmethod
    async def delete(self, item_id: str) -> bool:
        """
        Delete a memory item.
        
        Args:
            item_id: ID of the item to delete
            
        Returns:
            True if successful, False otherwise
        """
        pass
    
    @abstractmethod
    async def clear(self, memory_type: Optional[MemoryType] = None) -> int:
        """
        Clear memories.
        
        Args:
            memory_type: Type of memories to clear (None for all)
            
        Returns:
            Number of items cleared
        """
        pass
    
    @abstractmethod
    async def count(self, memory_type: Optional[MemoryType] = None) -> int:
        """
        Count memory items.
        
        Args:
            memory_type: Type of memories to count (None for all)
            
        Returns:
            Number of items
        """
        pass
