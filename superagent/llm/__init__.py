"""
LLM Integration Layer

Provides unified interface for multiple LLM providers with automatic fallback,
streaming support, and intelligent routing.
"""

from superagent.llm.base import BaseLLMProvider, LLMCapability, ProviderError
from superagent.llm.models import (
    LLMRequest,
    LLMResponse,
    LLMStreamChunk,
    ModelInfo,
    ProviderConfig,
    Message,
    Usage,
    FunctionDefinition,
    ToolDefinition,
)
from superagent.llm.provider import UnifiedLLMProvider
from superagent.llm.streaming import StreamHandler, StreamBuffer
from superagent.llm.litellm_provider import LiteLLMProvider
from superagent.llm.factory import ProviderFactory, create_default_provider

__all__ = [
    # Base classes
    "BaseLLMProvider",
    "LLMCapability",
    "ProviderError",
    # Models
    "LLMRequest",
    "LLMResponse",
    "LLMStreamChunk",
    "ModelInfo",
    "ProviderConfig",
    "Message",
    "Usage",
    "FunctionDefinition",
    "ToolDefinition",
    # Providers
    "UnifiedLLMProvider",
    "LiteLLMProvider",
    # Streaming
    "StreamHandler",
    "StreamBuffer",
    # Factory
    "ProviderFactory",
    "create_default_provider",
]
