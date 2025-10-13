"""
Vector store implementations for semantic search.
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from pathlib import Path
import uuid

import chromadb
from chromadb.config import Settings

from superagent.memory.models import MemoryItem, MemoryQuery, MemoryResult
from superagent.memory.base import MemoryType
from superagent.memory.embeddings import EmbeddingProvider
from superagent.core.logger import get_logger

logger = get_logger(__name__)


class VectorStore(ABC):
    """Abstract base class for vector stores."""
    
    @abstractmethod
    async def add(self, items: List[MemoryItem]) -> List[str]:
        """Add items to the vector store."""
        pass
    
    @abstractmethod
    async def search(
        self,
        query_embedding: List[float],
        limit: int = 10,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[MemoryResult]:
        """Search for similar items."""
        pass
    
    @abstractmethod
    async def get(self, item_id: str) -> Optional[MemoryItem]:
        """Get an item by ID."""
        pass
    
    @abstractmethod
    async def delete(self, item_id: str) -> bool:
        """Delete an item."""
        pass
    
    @abstractmethod
    async def clear(self) -> int:
        """Clear all items."""
        pass


class ChromaDBStore(VectorStore):
    """
    Vector store implementation using ChromaDB.
    
    Provides persistent vector storage with semantic search.
    """
    
    def __init__(
        self,
        collection_name: str = "superagent_memory",
        persist_directory: Optional[Path] = None,
        embedding_provider: Optional[EmbeddingProvider] = None,
    ):
        """
        Initialize ChromaDB store.
        
        Args:
            collection_name: Name of the collection
            persist_directory: Directory for persistent storage
            embedding_provider: Provider for generating embeddings
        """
        self.collection_name = collection_name
        self.persist_directory = persist_directory
        self.embedding_provider = embedding_provider
        
        # Initialize ChromaDB client
        if persist_directory:
            persist_directory.mkdir(parents=True, exist_ok=True)
            self.client = chromadb.PersistentClient(
                path=str(persist_directory),
                settings=Settings(anonymized_telemetry=False),
            )
        else:
            self.client = chromadb.Client(
                settings=Settings(anonymized_telemetry=False),
            )
        
        # Get or create collection
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            metadata={"description": "SuperAgent memory storage"},
        )
        
        logger.info(f"Initialized ChromaDB store: {collection_name}")
    
    async def add(self, items: List[MemoryItem]) -> List[str]:
        """
        Add items to ChromaDB.
        
        Args:
            items: List of memory items
            
        Returns:
            List of item IDs
        """
        if not items:
            return []
        
        ids = []
        documents = []
        embeddings = []
        metadatas = []
        
        for item in items:
            # Generate ID if not provided
            if not item.id:
                item.id = str(uuid.uuid4())
            
            ids.append(item.id)
            documents.append(item.content)
            
            # Use provided embedding or generate new one
            if item.embedding:
                embeddings.append(item.embedding)
            elif self.embedding_provider:
                embedding = await self.embedding_provider.embed(item.content)
                embeddings.append(embedding)
                item.embedding = embedding
            else:
                # ChromaDB will generate embedding
                embeddings = None
                break
            
            # Prepare metadata
            metadata = {
                "memory_type": item.memory_type.value,
                "timestamp": item.timestamp.isoformat(),
                "importance": item.importance,
                "access_count": item.access_count,
                **item.metadata,
            }
            metadatas.append(metadata)
        
        # Add to collection
        if embeddings:
            self.collection.add(
                ids=ids,
                documents=documents,
                embeddings=embeddings,
                metadatas=metadatas,
            )
        else:
            self.collection.add(
                ids=ids,
                documents=documents,
                metadatas=metadatas,
            )
        
        logger.debug(f"Added {len(ids)} items to ChromaDB")
        return ids
    
    async def search(
        self,
        query_embedding: List[float],
        limit: int = 10,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[MemoryResult]:
        """
        Search for similar items in ChromaDB.
        
        Args:
            query_embedding: Query embedding vector
            limit: Maximum number of results
            filters: Metadata filters
            
        Returns:
            List of memory results
        """
        # Build where clause from filters
        where = None
        if filters:
            where = {}
            for key, value in filters.items():
                if key == "memory_types" and isinstance(value, list):
                    where["memory_type"] = {"$in": [t.value for t in value]}
                else:
                    where[key] = value
        
        # Query collection
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=limit,
            where=where,
        )
        
        # Parse results
        memory_results = []
        if results["ids"] and results["ids"][0]:
            for i, item_id in enumerate(results["ids"][0]):
                # Reconstruct memory item
                metadata = results["metadatas"][0][i]
                
                memory_item = MemoryItem(
                    id=item_id,
                    content=results["documents"][0][i],
                    memory_type=MemoryType(metadata.pop("memory_type")),
                    timestamp=metadata.pop("timestamp"),
                    importance=metadata.pop("importance", 0.5),
                    access_count=metadata.pop("access_count", 0),
                    metadata=metadata,
                )
                
                # Calculate relevance score (1 - normalized distance)
                distance = results["distances"][0][i] if results["distances"] else 0.0
                relevance_score = 1.0 / (1.0 + distance)
                
                memory_results.append(MemoryResult(
                    item=memory_item,
                    relevance_score=relevance_score,
                    distance=distance,
                ))
        
        return memory_results
    
    async def get(self, item_id: str) -> Optional[MemoryItem]:
        """
        Get an item by ID.
        
        Args:
            item_id: Item ID
            
        Returns:
            MemoryItem if found, None otherwise
        """
        try:
            result = self.collection.get(ids=[item_id])
            
            if not result["ids"]:
                return None
            
            metadata = result["metadatas"][0]
            
            return MemoryItem(
                id=item_id,
                content=result["documents"][0],
                memory_type=MemoryType(metadata.pop("memory_type")),
                timestamp=metadata.pop("timestamp"),
                importance=metadata.pop("importance", 0.5),
                access_count=metadata.pop("access_count", 0),
                metadata=metadata,
            )
        except Exception as e:
            logger.error(f"Error getting item {item_id}: {e}")
            return None
    
    async def delete(self, item_id: str) -> bool:
        """
        Delete an item.
        
        Args:
            item_id: Item ID
            
        Returns:
            True if successful
        """
        try:
            self.collection.delete(ids=[item_id])
            return True
        except Exception as e:
            logger.error(f"Error deleting item {item_id}: {e}")
            return False
    
    async def clear(self) -> int:
        """
        Clear all items.
        
        Returns:
            Number of items cleared
        """
        count = self.collection.count()
        self.client.delete_collection(self.collection_name)
        self.collection = self.client.create_collection(
            name=self.collection_name,
            metadata={"description": "SuperAgent memory storage"},
        )
        return count
