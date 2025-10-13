"""
LiteLLM-based provider implementation supporting 100+ models.
"""

import time
from typing import AsyncIterator, List, Optional
import litellm
from litellm import acompletion, completion_cost

from superagent.llm.base import BaseLLMProvider, LLMCapability, ProviderError
from superagent.llm.models import (
    LLMRequest,
    LLMResponse,
    LLMStreamChunk,
    ModelInfo,
    Message,
    Usage,
)
from superagent.core.logger import get_logger

logger = get_logger(__name__)

# Suppress LiteLLM verbose logging
litellm.suppress_debug_info = True


class LiteLLMProvider(BaseLLMProvider):
    """
    Provider implementation using LiteLLM for multi-provider support.
    
    Supports 100+ models from OpenAI, Anthropic, Azure, Groq, Together,
    OpenRouter, Ollama, and many more providers.
    """
    
    def __init__(
        self,
        provider_name: str,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        timeout: int = 60,
        max_retries: int = 3,
        **kwargs,
    ):
        """
        Initialize LiteLLM provider.
        
        Args:
            provider_name: Name of the provider (e.g., "openai", "anthropic")
            api_key: API key for authentication
            base_url: Base URL for API endpoint
            timeout: Request timeout in seconds
            max_retries: Maximum retry attempts
            **kwargs: Additional provider-specific configuration
        """
        super().__init__(api_key, base_url, timeout, max_retries, **kwargs)
        self._provider_name = provider_name
        
        # Configure LiteLLM
        if api_key:
            self._set_api_key(provider_name, api_key)
        
        if base_url:
            litellm.api_base = base_url
    
    def _set_api_key(self, provider: str, api_key: str) -> None:
        """Set API key for the provider in LiteLLM."""
        key_mapping = {
            "openai": "OPENAI_API_KEY",
            "anthropic": "ANTHROPIC_API_KEY",
            "azure": "AZURE_API_KEY",
            "groq": "GROQ_API_KEY",
            "together": "TOGETHER_API_KEY",
            "openrouter": "OPENROUTER_API_KEY",
        }
        
        env_var = key_mapping.get(provider.lower())
        if env_var:
            import os
            os.environ[env_var] = api_key
    
    @property
    def name(self) -> str:
        """Return the provider name."""
        return self._provider_name
    
    @property
    def supported_capabilities(self) -> List[LLMCapability]:
        """Return list of capabilities this provider supports."""
        # Most providers support these core capabilities
        return [
            LLMCapability.CHAT,
            LLMCapability.COMPLETION,
            LLMCapability.STREAMING,
            LLMCapability.FUNCTION_CALLING,
        ]
    
    def _convert_messages(self, messages: List[Message]) -> List[dict]:
        """Convert Message objects to LiteLLM format."""
        return [
            {
                "role": msg.role,
                "content": msg.content,
                **({"name": msg.name} if msg.name else {}),
                **({"function_call": msg.function_call} if msg.function_call else {}),
                **({"tool_calls": msg.tool_calls} if msg.tool_calls else {}),
            }
            for msg in messages
        ]
    
    def _convert_tools(self, request: LLMRequest) -> Optional[List[dict]]:
        """Convert tool definitions to LiteLLM format."""
        if not request.tools:
            return None
        
        return [
            {
                "type": tool.type,
                "function": {
                    "name": tool.function.name,
                    "description": tool.function.description,
                    "parameters": tool.function.parameters,
                },
            }
            for tool in request.tools
        ]
    
    async def generate(self, request: LLMRequest) -> LLMResponse:
        """
        Generate a completion using LiteLLM.
        
        Args:
            request: LLM request
            
        Returns:
            LLMResponse with generated content
            
        Raises:
            ProviderError: If generation fails
        """
        start_time = time.time()
        
        try:
            # Prepare request parameters
            params = {
                "model": request.model,
                "messages": self._convert_messages(request.messages),
                "temperature": request.temperature,
                "max_tokens": request.max_tokens,
                "top_p": request.top_p,
                "frequency_penalty": request.frequency_penalty,
                "presence_penalty": request.presence_penalty,
                "timeout": self.timeout,
            }
            
            # Add optional parameters
            if request.stop:
                params["stop"] = request.stop
            if request.tools:
                params["tools"] = self._convert_tools(request)
            if request.tool_choice:
                params["tool_choice"] = request.tool_choice
            if request.response_format:
                params["response_format"] = request.response_format
            if request.seed:
                params["seed"] = request.seed
            if request.user:
                params["user"] = request.user
            
            # Make API call
            logger.debug(f"Calling LiteLLM with model: {request.model}")
            response = await acompletion(**params)
            
            # Extract response data
            choice = response.choices[0]
            message = choice.message
            
            # Calculate cost
            try:
                cost = completion_cost(completion_response=response)
            except Exception as e:
                logger.warning(f"Could not calculate cost: {e}")
                cost = 0.0
            
            # Build response
            llm_response = LLMResponse(
                id=response.id,
                model=response.model,
                content=message.content or "",
                role="assistant",
                finish_reason=choice.finish_reason,
                function_call=message.function_call if hasattr(message, "function_call") else None,
                tool_calls=message.tool_calls if hasattr(message, "tool_calls") else None,
                usage=Usage(
                    prompt_tokens=response.usage.prompt_tokens,
                    completion_tokens=response.usage.completion_tokens,
                    total_tokens=response.usage.total_tokens,
                ) if response.usage else None,
                provider=self.name,
                latency_ms=(time.time() - start_time) * 1000,
                cost=cost,
                metadata=request.metadata,
            )
            
            return llm_response
            
        except Exception as e:
            logger.error(f"LiteLLM generation failed: {e}")
            raise ProviderError(
                message=f"Generation failed: {str(e)}",
                provider=self.name,
                retryable=True,
                original_error=e,
            )
    
    async def stream(self, request: LLMRequest) -> AsyncIterator[LLMStreamChunk]:
        """
        Stream a completion using LiteLLM.
        
        Args:
            request: LLM request
            
        Yields:
            LLMStreamChunk objects
            
        Raises:
            ProviderError: If streaming fails
        """
        try:
            # Prepare request parameters
            params = {
                "model": request.model,
                "messages": self._convert_messages(request.messages),
                "temperature": request.temperature,
                "max_tokens": request.max_tokens,
                "top_p": request.top_p,
                "frequency_penalty": request.frequency_penalty,
                "presence_penalty": request.presence_penalty,
                "stream": True,
                "timeout": self.timeout,
            }
            
            # Add optional parameters
            if request.stop:
                params["stop"] = request.stop
            if request.tools:
                params["tools"] = self._convert_tools(request)
            if request.tool_choice:
                params["tool_choice"] = request.tool_choice
            if request.seed:
                params["seed"] = request.seed
            if request.user:
                params["user"] = request.user
            
            # Stream response
            logger.debug(f"Streaming from LiteLLM with model: {request.model}")
            response = await acompletion(**params)
            
            async for chunk in response:
                if not chunk.choices:
                    continue
                
                choice = chunk.choices[0]
                delta = choice.delta
                
                # Build stream chunk
                stream_chunk = LLMStreamChunk(
                    id=chunk.id,
                    model=chunk.model,
                    delta=delta.content or "",
                    role=delta.role if hasattr(delta, "role") else None,
                    finish_reason=choice.finish_reason,
                    function_call=delta.function_call if hasattr(delta, "function_call") else None,
                    tool_calls=delta.tool_calls if hasattr(delta, "tool_calls") else None,
                    provider=self.name,
                    metadata=request.metadata,
                )
                
                yield stream_chunk
                
        except Exception as e:
            logger.error(f"LiteLLM streaming failed: {e}")
            raise ProviderError(
                message=f"Streaming failed: {str(e)}",
                provider=self.name,
                retryable=True,
                original_error=e,
            )
    
    async def get_model_info(self, model: str) -> ModelInfo:
        """
        Get information about a model.
        
        Args:
            model: Model identifier
            
        Returns:
            ModelInfo with model capabilities
        """
        # LiteLLM model info (approximate values)
        model_configs = {
            "gpt-4-turbo-preview": {
                "context_window": 128000,
                "max_output": 4096,
                "input_cost": 0.01,
                "output_cost": 0.03,
            },
            "gpt-4": {
                "context_window": 8192,
                "max_output": 4096,
                "input_cost": 0.03,
                "output_cost": 0.06,
            },
            "gpt-3.5-turbo": {
                "context_window": 16385,
                "max_output": 4096,
                "input_cost": 0.0005,
                "output_cost": 0.0015,
            },
            "claude-3-opus-20240229": {
                "context_window": 200000,
                "max_output": 4096,
                "input_cost": 0.015,
                "output_cost": 0.075,
            },
            "claude-3-sonnet-20240229": {
                "context_window": 200000,
                "max_output": 4096,
                "input_cost": 0.003,
                "output_cost": 0.015,
            },
        }
        
        config = model_configs.get(model, {
            "context_window": 4096,
            "max_output": 2048,
            "input_cost": 0.0,
            "output_cost": 0.0,
        })
        
        return ModelInfo(
            id=model,
            provider=self.name,
            context_window=config["context_window"],
            max_output_tokens=config["max_output"],
            supports_streaming=True,
            supports_functions=True,
            supports_vision=False,
            supports_json_mode=True,
            input_cost_per_1k=config["input_cost"],
            output_cost_per_1k=config["output_cost"],
        )
    
    def count_tokens(self, text: str, model: str) -> int:
        """
        Count tokens using LiteLLM's token counter.
        
        Args:
            text: Text to count tokens for
            model: Model identifier
            
        Returns:
            Number of tokens
        """
        try:
            return litellm.token_counter(model=model, text=text)
        except Exception as e:
            logger.warning(f"Token counting failed, using approximation: {e}")
            # Fallback: rough approximation (1 token ≈ 4 characters)
            return len(text) // 4
