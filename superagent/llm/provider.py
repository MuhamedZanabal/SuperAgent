"""
Unified LLM provider with multi-provider support and automatic fallback.
"""

import time
from typing import AsyncIterator, Dict, List, Optional, Any
from contextlib import asynccontextmanager

from superagent.llm.base import BaseLLMProvider, LLMCapability, ProviderError
from superagent.llm.models import (
    LLMRequest,
    LLMResponse,
    LLMStreamChunk,
    ModelInfo,
    ProviderConfig,
    Usage,
)
from superagent.llm.streaming import StreamBuffer
from superagent.core.logger import get_logger
from superagent.core.utils import async_retry

logger = get_logger(__name__)


class UnifiedLLMProvider:
    """
    Unified interface for multiple LLM providers with automatic fallback.
    
    Features:
    - Multi-provider support with priority-based routing
    - Automatic fallback on provider failure
    - Streaming and non-streaming modes
    - Token counting and cost tracking
    - Rate limiting and retry logic
    - Model capability detection
    """
    
    def __init__(self, configs: Optional[List[ProviderConfig]] = None):
        """
        Initialize the unified provider.
        
        Args:
            configs: List of provider configurations
        """
        self.providers: Dict[str, BaseLLMProvider] = {}
        self.configs: Dict[str, ProviderConfig] = {}
        self.model_to_provider: Dict[str, str] = {}
        
        if configs:
            for config in configs:
                self.register_provider_config(config)
    
    def register_provider_config(self, config: ProviderConfig) -> None:
        """
        Register a provider configuration.
        
        Args:
            config: Provider configuration
        """
        self.configs[config.name] = config
        
        # Map models to provider
        for model in config.models:
            self.model_to_provider[model] = config.name
        
        logger.info(f"Registered provider config: {config.name}")
    
    def register_provider(
        self,
        name: str,
        provider: BaseLLMProvider,
    ) -> None:
        """
        Register a provider instance.
        
        Args:
            name: Provider name
            provider: Provider instance
        """
        self.providers[name] = provider
        logger.info(f"Registered provider instance: {name}")
    
    def get_provider_for_model(self, model: str) -> Optional[str]:
        """
        Get the provider name for a given model.
        
        Args:
            model: Model identifier
            
        Returns:
            Provider name or None if not found
        """
        # Direct mapping
        if model in self.model_to_provider:
            return self.model_to_provider[model]
        
        # Check if model string contains provider prefix
        for provider_name in self.providers.keys():
            if model.startswith(f"{provider_name}/"):
                return provider_name
        
        return None
    
    def get_provider(self, name: str) -> Optional[BaseLLMProvider]:
        """Get a provider instance by name."""
        return self.providers.get(name)
    
    def get_fallback_providers(
        self,
        primary_provider: str,
        capability: Optional[LLMCapability] = None,
    ) -> List[str]:
        """
        Get fallback providers sorted by priority.
        
        Args:
            primary_provider: Primary provider that failed
            capability: Required capability for fallback providers
            
        Returns:
            List of provider names sorted by priority
        """
        fallbacks = []
        
        for name, config in self.configs.items():
            if name == primary_provider or not config.enabled:
                continue
            
            provider = self.providers.get(name)
            if provider is None:
                continue
            
            # Check capability if specified
            if capability and not provider.supports_capability(capability):
                continue
            
            fallbacks.append((name, config.priority))
        
        # Sort by priority (higher is better)
        fallbacks.sort(key=lambda x: x[1], reverse=True)
        return [name for name, _ in fallbacks]
    
    @async_retry(max_attempts=3, delay=1.0, backoff=2.0)
    async def generate(
        self,
        request: LLMRequest,
        provider_name: Optional[str] = None,
        enable_fallback: bool = True,
    ) -> LLMResponse:
        """
        Generate a completion with automatic fallback.
        
        Args:
            request: LLM request
            provider_name: Specific provider to use (optional)
            enable_fallback: Whether to try fallback providers on failure
            
        Returns:
            LLMResponse from the provider
            
        Raises:
            ProviderError: If all providers fail
        """
        start_time = time.time()
        
        # Determine provider
        if provider_name is None:
            provider_name = self.get_provider_for_model(request.model)
            if provider_name is None:
                raise ProviderError(
                    f"No provider found for model: {request.model}",
                    provider="unknown",
                )
        
        # Get provider instance
        provider = self.get_provider(provider_name)
        if provider is None:
            raise ProviderError(
                f"Provider not registered: {provider_name}",
                provider=provider_name,
            )
        
        # Try primary provider
        try:
            logger.info(f"Generating with provider: {provider_name}, model: {request.model}")
            response = await provider.generate(request)
            
            # Update metrics
            latency_ms = (time.time() - start_time) * 1000
            response.latency_ms = latency_ms
            provider.update_metrics(
                success=True,
                tokens=response.usage.total_tokens if response.usage else 0,
                cost=response.cost,
                latency_ms=latency_ms,
            )
            
            return response
            
        except Exception as e:
            logger.error(f"Provider {provider_name} failed: {e}")
            provider.update_metrics(success=False, error=str(e))
            
            # Try fallback providers if enabled
            if enable_fallback:
                fallback_providers = self.get_fallback_providers(
                    provider_name,
                    capability=LLMCapability.CHAT,
                )
                
                for fallback_name in fallback_providers:
                    try:
                        logger.info(f"Trying fallback provider: {fallback_name}")
                        fallback_provider = self.get_provider(fallback_name)
                        
                        # Update request with fallback provider's model
                        fallback_config = self.configs[fallback_name]
                        if fallback_config.models:
                            request.model = fallback_config.models[0]
                        
                        response = await fallback_provider.generate(request)
                        
                        # Update metrics
                        latency_ms = (time.time() - start_time) * 1000
                        response.latency_ms = latency_ms
                        fallback_provider.update_metrics(
                            success=True,
                            tokens=response.usage.total_tokens if response.usage else 0,
                            cost=response.cost,
                            latency_ms=latency_ms,
                        )
                        
                        logger.info(f"Fallback successful with: {fallback_name}")
                        return response
                        
                    except Exception as fallback_error:
                        logger.error(f"Fallback provider {fallback_name} failed: {fallback_error}")
                        fallback_provider.update_metrics(success=False, error=str(fallback_error))
                        continue
            
            # All providers failed
            raise ProviderError(
                f"All providers failed. Last error: {e}",
                provider=provider_name,
                original_error=e,
            )
    
    async def stream(
        self,
        request: LLMRequest,
        provider_name: Optional[str] = None,
    ) -> AsyncIterator[LLMStreamChunk]:
        """
        Stream a completion from the provider.
        
        Args:
            request: LLM request with stream=True
            provider_name: Specific provider to use (optional)
            
        Yields:
            LLMStreamChunk objects
            
        Raises:
            ProviderError: If provider fails
        """
        # Determine provider
        if provider_name is None:
            provider_name = self.get_provider_for_model(request.model)
            if provider_name is None:
                raise ProviderError(
                    f"No provider found for model: {request.model}",
                    provider="unknown",
                )
        
        # Get provider instance
        provider = self.get_provider(provider_name)
        if provider is None:
            raise ProviderError(
                f"Provider not registered: {provider_name}",
                provider=provider_name,
            )
        
        # Check streaming support
        if not provider.supports_capability(LLMCapability.STREAMING):
            raise ProviderError(
                f"Provider {provider_name} does not support streaming",
                provider=provider_name,
            )
        
        # Stream from provider
        request.stream = True
        start_time = time.time()
        buffer = None
        
        try:
            logger.info(f"Streaming with provider: {provider_name}, model: {request.model}")
            
            async for chunk in provider.stream(request):
                if buffer is None:
                    buffer = StreamBuffer(
                        id=chunk.id,
                        model=chunk.model,
                        provider=chunk.provider,
                    )
                buffer.add_chunk(chunk)
                yield chunk
            
            # Update metrics after successful stream
            latency_ms = (time.time() - start_time) * 1000
            provider.update_metrics(
                success=True,
                tokens=len(buffer.content.split()) if buffer else 0,  # Rough estimate
                latency_ms=latency_ms,
            )
            
        except Exception as e:
            logger.error(f"Streaming failed: {e}")
            provider.update_metrics(success=False, error=str(e))
            raise ProviderError(
                f"Streaming failed: {e}",
                provider=provider_name,
                original_error=e,
            )
    
    async def get_model_info(
        self,
        model: str,
        provider_name: Optional[str] = None,
    ) -> ModelInfo:
        """
        Get information about a model.
        
        Args:
            model: Model identifier
            provider_name: Specific provider (optional)
            
        Returns:
            ModelInfo object
        """
        if provider_name is None:
            provider_name = self.get_provider_for_model(model)
            if provider_name is None:
                raise ProviderError(
                    f"No provider found for model: {model}",
                    provider="unknown",
                )
        
        provider = self.get_provider(provider_name)
        if provider is None:
            raise ProviderError(
                f"Provider not registered: {provider_name}",
                provider=provider_name,
            )
        
        return await provider.get_model_info(model)
    
    def get_all_metrics(self) -> Dict[str, Any]:
        """Get metrics from all providers."""
        return {
            name: provider.get_metrics()
            for name, provider in self.providers.items()
        }
    
    def list_available_models(self) -> List[str]:
        """List all available models across all providers."""
        return list(self.model_to_provider.keys())
    
    def list_providers(self) -> List[str]:
        """List all registered providers."""
        return list(self.providers.keys())
