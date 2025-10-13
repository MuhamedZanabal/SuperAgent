"""
Embedding providers for semantic search.
"""

from abc import ABC, abstractmethod
from typing import List, Union
import numpy as np

from sentence_transformers import SentenceTransformer

from superagent.core.logger import get_logger

logger = get_logger(__name__)


class EmbeddingProvider(ABC):
    """Abstract base class for embedding providers."""
    
    @abstractmethod
    async def embed(self, texts: Union[str, List[str]]) -> Union[List[float], List[List[float]]]:
        """
        Generate embeddings for text(s).
        
        Args:
            texts: Single text or list of texts
            
        Returns:
            Embedding vector(s)
        """
        pass
    
    @property
    @abstractmethod
    def dimension(self) -> int:
        """Return embedding dimension."""
        pass


class SentenceTransformerEmbeddings(EmbeddingProvider):
    """
    Embedding provider using Sentence Transformers.
    
    Provides high-quality embeddings for semantic search.
    """
    
    def __init__(self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2"):
        """
        Initialize sentence transformer.
        
        Args:
            model_name: Name of the sentence transformer model
        """
        self.model_name = model_name
        self._model = None
        self._dimension = None
    
    def _load_model(self):
        """Lazy load the model."""
        if self._model is None:
            logger.info(f"Loading embedding model: {self.model_name}")
            self._model = SentenceTransformer(self.model_name)
            # Get dimension from model
            self._dimension = self._model.get_sentence_embedding_dimension()
    
    async def embed(self, texts: Union[str, List[str]]) -> Union[List[float], List[List[float]]]:
        """
        Generate embeddings using sentence transformers.
        
        Args:
            texts: Single text or list of texts
            
        Returns:
            Embedding vector(s)
        """
        self._load_model()
        
        # Handle single text
        if isinstance(texts, str):
            embedding = self._model.encode(texts, convert_to_numpy=True)
            return embedding.tolist()
        
        # Handle list of texts
        embeddings = self._model.encode(texts, convert_to_numpy=True)
        return embeddings.tolist()
    
    @property
    def dimension(self) -> int:
        """Return embedding dimension."""
        if self._dimension is None:
            self._load_model()
        return self._dimension


class OpenAIEmbeddings(EmbeddingProvider):
    """
    Embedding provider using OpenAI's embedding API.
    
    Requires OpenAI API key.
    """
    
    def __init__(self, api_key: str, model: str = "text-embedding-3-small"):
        """
        Initialize OpenAI embeddings.
        
        Args:
            api_key: OpenAI API key
            model: Embedding model name
        """
        self.api_key = api_key
        self.model = model
        self._dimension = 1536 if "3-small" in model else 3072
    
    async def embed(self, texts: Union[str, List[str]]) -> Union[List[float], List[List[float]]]:
        """
        Generate embeddings using OpenAI API.
        
        Args:
            texts: Single text or list of texts
            
        Returns:
            Embedding vector(s)
        """
        import openai
        
        client = openai.AsyncOpenAI(api_key=self.api_key)
        
        # Handle single text
        if isinstance(texts, str):
            response = await client.embeddings.create(
                model=self.model,
                input=texts,
            )
            return response.data[0].embedding
        
        # Handle list of texts
        response = await client.embeddings.create(
            model=self.model,
            input=texts,
        )
        return [item.embedding for item in response.data]
    
    @property
    def dimension(self) -> int:
        """Return embedding dimension."""
        return self._dimension
