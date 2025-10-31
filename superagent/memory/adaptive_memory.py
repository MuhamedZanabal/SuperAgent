"""
Multi-tier adaptive memory system with semantic compression.
"""

from typing import List, Optional, Dict, Any
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import deque
import asyncio

from superagent.memory.base import BaseMemory, MemoryType
from superagent.memory.models import MemoryItem, MemoryQuery, MemoryResult
from superagent.memory.vector_store import VectorStore
from superagent.memory.embeddings import EmbeddingProvider
from superagent.core.logger import get_logger

logger = get_logger(__name__)


@dataclass
class Summary:
    """Compressed memory summary."""
    content: str
    entities: List[str]
    relationships: Dict[str, List[str]]
    key_decisions: List[str]
    compression_ratio: float
    original_count: int
    timestamp: datetime = field(default_factory=datetime.utcnow)


@dataclass
class Context:
    """Retrieved context with relevance scoring."""
    content: str
    relevance_score: float
    temporal_weight: float
    source_type: str
    metadata: Dict[str, Any] = field(default_factory=dict)


class AdaptiveMemorySystem(BaseMemory):
    """
    Hierarchical memory with semantic compression and adaptive retrieval.
    
    Implements three-tier memory architecture:
    - Working memory: Recent, high-priority items (fast access)
    - Episodic memory: Compressed conversation history (semantic search)
    - Procedural memory: Learned patterns and skills (skill cache)
    """
    
    def __init__(
        self,
        vector_store: VectorStore,
        embedding_provider: EmbeddingProvider,
        working_capacity: int = 10,
        episodic_capacity: int = 1000,
        compression_threshold: int = 50,
        compression_ratio: float = 0.15,
    ):
        """
        Initialize adaptive memory system.
        
        Args:
            vector_store: Vector store for long-term storage
            embedding_provider: Embedding provider
            working_capacity: Working memory capacity
            episodic_capacity: Episodic memory capacity
            compression_threshold: Messages before compression
            compression_ratio: Target compression ratio
        """
        self.vector_store = vector_store
        self.embedding_provider = embedding_provider
        self.working_capacity = working_capacity
        self.episodic_capacity = episodic_capacity
        self.compression_threshold = compression_threshold
        self.compression_ratio = compression_ratio
        
        # Three-tier memory structure
        self.working_memory: deque = deque(maxlen=working_capacity)
        self.episodic_memory: List[MemoryItem] = []
        self.procedural_memory: Dict[str, Any] = {}  # Skill cache
        
        # Compression state
        self._pending_compression: List[MemoryItem] = []
        
        logger.info("Adaptive memory system initialized")
    
    async def add(self, item: MemoryItem) -> str:
        """
        Add memory item to appropriate tier.
        
        Args:
            item: Memory item to add
            
        Returns:
            Item ID
        """
        # Generate embedding if needed
        if not item.embedding:
            item.embedding = await self.embedding_provider.embed(item.content)
        
        # Add to working memory
        self.working_memory.append(item)
        
        # Add to pending compression
        self._pending_compression.append(item)
        
        # Check if compression needed
        if len(self._pending_compression) >= self.compression_threshold:
            await self._compress_and_archive()
        
        # Store in vector store for long-term
        ids = await self.vector_store.add([item])
        item.id = ids[0]
        
        logger.debug(f"Added memory item: {item.id}")
        return item.id
    
    async def retrieve_relevant_context(
        self,
        query: str,
        k: int = 5,
        temporal_weight: float = 0.3,
    ) -> List[Context]:
        """
        Hybrid retrieval with dense, sparse, and temporal signals.
        
        Args:
            query: Query string
            k: Number of results
            temporal_weight: Weight for temporal proximity
            
        Returns:
            List of relevant contexts
        """
        # Generate query embedding
        query_embedding = await self.embedding_provider.embed(query)
        
        # Dense vector similarity search
        dense_results = await self.vector_store.search(
            query_embedding=query_embedding,
            limit=k * 2,
        )
        
        # Sparse keyword matching (BM25-style)
        sparse_results = await self._sparse_search(query, k * 2)
        
        # Fusion ranking with temporal weighting
        contexts = await self._fusion_rank(
            query=query,
            dense_results=dense_results,
            sparse_results=sparse_results,
            temporal_weight=temporal_weight,
            k=k,
        )
        
        return contexts
    
    async def compress_conversation(self, messages: List[MemoryItem]) -> Summary:
        """
        Semantic compression of conversation history.
        
        Args:
            messages: Messages to compress
            
        Returns:
            Compressed summary
        """
        if not messages:
            return Summary(
                content="",
                entities=[],
                relationships={},
                key_decisions=[],
                compression_ratio=0.0,
                original_count=0,
            )
        
        # Extract entities and relationships
        entities = await self._extract_entities(messages)
        relationships = await self._build_knowledge_graph(entities, messages)
        
        # Identify key decisions and outcomes
        key_decisions = await self._extract_key_decisions(messages)
        
        # Generate compressed summary
        summary_content = await self._generate_summary(
            messages=messages,
            entities=entities,
            relationships=relationships,
            key_decisions=key_decisions,
        )
        
        # Calculate compression ratio
        original_length = sum(len(m.content) for m in messages)
        compressed_length = len(summary_content)
        ratio = compressed_length / original_length if original_length > 0 else 0
        
        summary = Summary(
            content=summary_content,
            entities=entities,
            relationships=relationships,
            key_decisions=key_decisions,
            compression_ratio=ratio,
            original_count=len(messages),
        )
        
        logger.info(f"Compressed {len(messages)} messages to {len(summary_content)} chars (ratio: {ratio:.2%})")
        return summary
    
    async def _compress_and_archive(self):
        """Compress pending messages and archive to episodic memory."""
        if not self._pending_compression:
            return
        
        # Compress messages
        summary = await self.compress_conversation(self._pending_compression)
        
        # Create summary memory item
        summary_item = MemoryItem(
            content=summary.content,
            memory_type=MemoryType.LONG_TERM,
            metadata={
                "type": "summary",
                "entities": summary.entities,
                "relationships": summary.relationships,
                "key_decisions": summary.key_decisions,
                "original_count": summary.original_count,
                "compression_ratio": summary.compression_ratio,
            },
        )
        
        # Add to episodic memory
        summary_item.embedding = await self.embedding_provider.embed(summary_item.content)
        await self.vector_store.add([summary_item])
        self.episodic_memory.append(summary_item)
        
        # Clear pending
        self._pending_compression.clear()
        
        # Cleanup old episodic memories if needed
        if len(self.episodic_memory) > self.episodic_capacity:
            removed = self.episodic_memory[:len(self.episodic_memory) - self.episodic_capacity]
            self.episodic_memory = self.episodic_memory[-self.episodic_capacity:]
            logger.debug(f"Archived {len(removed)} old episodic memories")
    
    async def _extract_entities(self, messages: List[MemoryItem]) -> List[str]:
        """Extract key entities from messages."""
        # Simplified entity extraction - in production, use NER
        entities = set()
        for message in messages:
            # Extract capitalized words as potential entities
            words = message.content.split()
            entities.update(word for word in words if word and word[0].isupper())
        return list(entities)[:50]  # Limit to top 50
    
    async def _build_knowledge_graph(
        self,
        entities: List[str],
        messages: List[MemoryItem]
    ) -> Dict[str, List[str]]:
        """Build knowledge graph from entities and messages."""
        # Simplified relationship extraction
        relationships = {entity: [] for entity in entities}
        
        for message in messages:
            content_lower = message.content.lower()
            for entity in entities:
                if entity.lower() in content_lower:
                    # Find related entities in same message
                    for other_entity in entities:
                        if other_entity != entity and other_entity.lower() in content_lower:
                            if other_entity not in relationships[entity]:
                                relationships[entity].append(other_entity)
        
        return relationships
    
    async def _extract_key_decisions(self, messages: List[MemoryItem]) -> List[str]:
        """Extract key decisions and outcomes from messages."""
        # Simplified decision extraction
        decisions = []
        decision_keywords = ["decided", "chose", "selected", "determined", "concluded"]
        
        for message in messages:
            content_lower = message.content.lower()
            if any(keyword in content_lower for keyword in decision_keywords):
                decisions.append(message.content[:200])  # First 200 chars
        
        return decisions[:10]  # Top 10 decisions
    
    async def _generate_summary(
        self,
        messages: List[MemoryItem],
        entities: List[str],
        relationships: Dict[str, List[str]],
        key_decisions: List[str],
    ) -> str:
        """Generate compressed summary from messages and extracted information."""
        # Simplified summary generation
        summary_parts = []
        
        if entities:
            summary_parts.append(f"Key entities: {', '.join(entities[:10])}")
        
        if key_decisions:
            summary_parts.append(f"Key decisions: {'; '.join(key_decisions[:3])}")
        
        # Add message count and timespan
        if messages:
            first_time = messages[0].timestamp
            last_time = messages[-1].timestamp
            duration = last_time - first_time
            summary_parts.append(f"Conversation span: {duration.total_seconds() / 60:.1f} minutes, {len(messages)} messages")
        
        return " | ".join(summary_parts)
    
    async def _sparse_search(self, query: str, limit: int) -> List[MemoryResult]:
        """BM25-style sparse keyword search."""
        # Simplified sparse search - in production, use proper BM25
        query_terms = set(query.lower().split())
        results = []
        
        # Search working memory
        for item in self.working_memory:
            content_terms = set(item.content.lower().split())
            overlap = len(query_terms & content_terms)
            if overlap > 0:
                score = overlap / len(query_terms)
                results.append(MemoryResult(item=item, relevance_score=score))
        
        # Sort by score
        results.sort(key=lambda x: x.relevance_score, reverse=True)
        return results[:limit]
    
    async def _fusion_rank(
        self,
        query: str,
        dense_results: List[MemoryResult],
        sparse_results: List[MemoryResult],
        temporal_weight: float,
        k: int,
    ) -> List[Context]:
        """Fusion ranking combining dense, sparse, and temporal signals."""
        # Combine results
        all_results = {}
        
        # Add dense results
        for i, result in enumerate(dense_results):
            item_id = result.item.id or str(id(result.item))
            all_results[item_id] = {
                "item": result.item,
                "dense_score": result.relevance_score,
                "dense_rank": i,
                "sparse_score": 0.0,
                "sparse_rank": len(sparse_results),
            }
        
        # Add sparse results
        for i, result in enumerate(sparse_results):
            item_id = result.item.id or str(id(result.item))
            if item_id in all_results:
                all_results[item_id]["sparse_score"] = result.relevance_score
                all_results[item_id]["sparse_rank"] = i
            else:
                all_results[item_id] = {
                    "item": result.item,
                    "dense_score": 0.0,
                    "dense_rank": len(dense_results),
                    "sparse_score": result.relevance_score,
                    "sparse_rank": i,
                }
        
        # Calculate fusion scores
        contexts = []
        now = datetime.utcnow()
        
        for item_id, data in all_results.items():
            item = data["item"]
            
            # Reciprocal rank fusion
            dense_rrf = 1.0 / (60 + data["dense_rank"])
            sparse_rrf = 1.0 / (60 + data["sparse_rank"])
            
            # Temporal decay
            age = (now - item.timestamp).total_seconds() / 3600  # hours
            temporal_score = 1.0 / (1.0 + age)
            
            # Combined score
            relevance_score = (
                0.4 * dense_rrf +
                0.3 * sparse_rrf +
                temporal_weight * temporal_score
            )
            
            contexts.append(Context(
                content=item.content,
                relevance_score=relevance_score,
                temporal_weight=temporal_score,
                source_type=item.memory_type.value,
                metadata=item.metadata,
            ))
        
        # Sort and return top k
        contexts.sort(key=lambda x: x.relevance_score, reverse=True)
        return contexts[:k]
    
    async def get(self, item_id: str) -> Optional[MemoryItem]:
        """Get memory item by ID."""
        # Check working memory first
        for item in self.working_memory:
            if item.id == item_id:
                return item
        
        # Check vector store
        return await self.vector_store.get(item_id)
    
    async def search(self, query: MemoryQuery) -> List[MemoryResult]:
        """Search memories."""
        contexts = await self.retrieve_relevant_context(
            query=query.text,
            k=query.limit,
        )
        
        # Convert contexts to memory results
        results = []
        for ctx in contexts:
            # Find corresponding memory item
            item = MemoryItem(
                content=ctx.content,
                memory_type=MemoryType.LONG_TERM,
                metadata=ctx.metadata,
            )
            results.append(MemoryResult(
                item=item,
                relevance_score=ctx.relevance_score,
            ))
        
        return results
    
    async def update(self, item_id: str, updates: Dict[str, Any]) -> bool:
        """Update memory item."""
        item = await self.get(item_id)
        if not item:
            return False
        
        for key, value in updates.items():
            if hasattr(item, key):
                setattr(item, key, value)
        
        return True
    
    async def delete(self, item_id: str) -> bool:
        """Delete memory item."""
        # Remove from working memory
        self.working_memory = deque(
            (item for item in self.working_memory if item.id != item_id),
            maxlen=self.working_capacity
        )
        
        # Remove from vector store
        return await self.vector_store.delete(item_id)
    
    async def clear(self, memory_type: Optional[MemoryType] = None) -> int:
        """Clear memories."""
        if memory_type is None:
            count = len(self.working_memory) + len(self.episodic_memory)
            self.working_memory.clear()
            self.episodic_memory.clear()
            self.procedural_memory.clear()
            await self.vector_store.clear()
            return count
        
        return 0
    
    async def count(self, memory_type: Optional[MemoryType] = None) -> int:
        """Count memory items."""
        if memory_type == MemoryType.WORKING:
            return len(self.working_memory)
        elif memory_type == MemoryType.LONG_TERM:
            return len(self.episodic_memory)
        
        return len(self.working_memory) + len(self.episodic_memory)
