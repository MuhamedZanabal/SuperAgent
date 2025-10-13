"""
Pydantic models for memory systems.
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum

from superagent.memory.base import MemoryType


class MemoryItem(BaseModel):
    """A single memory item."""
    
    id: Optional[str] = None
    content: str
    memory_type: MemoryType
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    embedding: Optional[List[float]] = None
    importance: float = Field(default=0.5, ge=0.0, le=1.0)
    access_count: int = Field(default=0, ge=0)
    last_accessed: Optional[datetime] = None


class MemoryQuery(BaseModel):
    """Query for searching memories."""
    
    text: str
    memory_types: Optional[List[MemoryType]] = None
    limit: int = Field(default=10, gt=0, le=100)
    min_relevance: float = Field(default=0.0, ge=0.0, le=1.0)
    time_range: Optional[tuple[datetime, datetime]] = None
    metadata_filters: Dict[str, Any] = Field(default_factory=dict)


class MemoryResult(BaseModel):
    """Result from memory search."""
    
    item: MemoryItem
    relevance_score: float = Field(ge=0.0, le=1.0)
    distance: Optional[float] = None


class ConversationContext(BaseModel):
    """Context for a conversation."""
    
    conversation_id: str
    messages: List[Dict[str, str]] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    token_count: int = 0
    summary: Optional[str] = None
