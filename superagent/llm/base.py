"""
Base classes and interfaces for LLM providers.
"""

from abc import ABC, abstractmethod
from enum import Enum
from typing import AsyncIterator, Dict, List, Optional, Any
from dataclasses import dataclass

from superagent.llm.models import (
    LLMRequest,
    LLMResponse,
    LLMStreamChunk,
    ModelInfo,
)


class LLMCapability(str, Enum):
    """Capabilities that an LLM provider may support."""
    
    CHAT = "chat"
    COMPLETION = "completion"
    STREAMING = "streaming"
    FUNCTION_CALLING = "function_calling"
    VISION = "vision"
    JSON_MODE = "json_mode"
    EMBEDDINGS = "embeddings"
    FINE_TUNING = "fine_tuning"


@dataclass
class ProviderMetrics:
    """Metrics for provider performance tracking."""
    
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    total_tokens: int = 0
    total_cost: float = 0.0
    avg_latency_ms: float = 0.0
    last_error: Optional[str] = None


class BaseLLMProvider(ABC):
    """
    Abstract base class for all LLM providers.
    
    Defines the interface that all provider implementations must follow.
    """
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        timeout: int = 60,
        max_retries: int = 3,
        **kwargs: Any,
    ):
        """
        Initialize the LLM provider.
        
        Args:
            api_key: API key for authentication
            base_url: Base URL for API endpoint (for custom deployments)
            timeout: Request timeout in seconds
            max_retries: Maximum number of retry attempts
            **kwargs: Additional provider-specific configuration
        """
        self.api_key = api_key
        self.base_url = base_url
        self.timeout = timeout
        self.max_retries = max_retries
        self.config = kwargs
        self.metrics = ProviderMetrics()
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Return the provider name."""
        pass
    
    @property
    @abstractmethod
    def supported_capabilities(self) -> List[LLMCapability]:
        """Return list of capabilities this provider supports."""
        pass
    
    @abstractmethod
    async def generate(
        self,
        request: LLMRequest,
    ) -> LLMResponse:
        """
        Generate a completion for the given request.
        
        Args:
            request: The LLM request containing messages and parameters
            
        Returns:
            LLMResponse containing the generated text and metadata
            
        Raises:
            ProviderError: If the request fails
        """
        pass
    
    @abstractmethod
    async def stream(
        self,
        request: LLMRequest,
    ) -> AsyncIterator[LLMStreamChunk]:
        """
        Stream a completion for the given request.
        
        Args:
            request: The LLM request containing messages and parameters
            
        Yields:
            LLMStreamChunk objects as they are generated
            
        Raises:
            ProviderError: If the request fails
        """
        pass
    
    @abstractmethod
    async def get_model_info(self, model: str) -> ModelInfo:
        """
        Get information about a specific model.
        
        Args:
            model: Model identifier
            
        Returns:
            ModelInfo containing model capabilities and limits
        """
        pass
    
    @abstractmethod
    def count_tokens(self, text: str, model: str) -> int:
        """
        Count tokens in the given text for the specified model.
        
        Args:
            text: Text to count tokens for
            model: Model identifier for tokenization
            
        Returns:
            Number of tokens
        """
        pass
    
    def supports_capability(self, capability: LLMCapability) -> bool:
        """Check if this provider supports a specific capability."""
        return capability in self.supported_capabilities
    
    def update_metrics(
        self,
        success: bool,
        tokens: int = 0,
        cost: float = 0.0,
        latency_ms: float = 0.0,
        error: Optional[str] = None,
    ) -> None:
        """Update provider metrics after a request."""
        self.metrics.total_requests += 1
        if success:
            self.metrics.successful_requests += 1
        else:
            self.metrics.failed_requests += 1
            self.metrics.last_error = error
        
        self.metrics.total_tokens += tokens
        self.metrics.total_cost += cost
        
        # Update rolling average latency
        total = self.metrics.total_requests
        self.metrics.avg_latency_ms = (
            (self.metrics.avg_latency_ms * (total - 1) + latency_ms) / total
        )
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get current provider metrics."""
        return {
            "provider": self.name,
            "total_requests": self.metrics.total_requests,
            "successful_requests": self.metrics.successful_requests,
            "failed_requests": self.metrics.failed_requests,
            "success_rate": (
                self.metrics.successful_requests / self.metrics.total_requests
                if self.metrics.total_requests > 0
                else 0.0
            ),
            "total_tokens": self.metrics.total_tokens,
            "total_cost": self.metrics.total_cost,
            "avg_latency_ms": self.metrics.avg_latency_ms,
            "last_error": self.metrics.last_error,
        }


class ProviderError(Exception):
    """Base exception for provider errors."""
    
    def __init__(
        self,
        message: str,
        provider: str,
        retryable: bool = False,
        original_error: Optional[Exception] = None,
    ):
        super().__init__(message)
        self.provider = provider
        self.retryable = retryable
        self.original_error = original_error
