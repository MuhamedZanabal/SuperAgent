"""
Tests for LLM provider system.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from superagent.llm.models import LLMRequest, Message, LLMResponse
from superagent.llm.litellm_provider import LiteLLMProvider
from superagent.llm.provider import UnifiedLLMProvider
from superagent.llm.factory import create_default_provider
from superagent.core.config import SuperAgentConfig


@pytest.fixture
def mock_config():
    """Create a mock configuration."""
    return SuperAgentConfig(
        openai_api_key="test-key",
        anthropic_api_key="test-key",
        default_model="gpt-4-turbo-preview",
    )


@pytest.fixture
def sample_request():
    """Create a sample LLM request."""
    return LLMRequest(
        model="gpt-4-turbo-preview",
        messages=[
            Message(role="user", content="Hello, how are you?")
        ],
        temperature=0.7,
        max_tokens=100,
    )


@pytest.mark.asyncio
async def test_litellm_provider_generate(sample_request):
    """Test LiteLLM provider generation."""
    provider = LiteLLMProvider(
        provider_name="openai",
        api_key="test-key",
    )
    
    # Mock the acompletion call
    with patch("superagent.llm.litellm_provider.acompletion") as mock_completion:
        mock_response = MagicMock()
        mock_response.id = "test-id"
        mock_response.model = "gpt-4-turbo-preview"
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "I'm doing well, thank you!"
        mock_response.choices[0].finish_reason = "stop"
        mock_response.usage.prompt_tokens = 10
        mock_response.usage.completion_tokens = 8
        mock_response.usage.total_tokens = 18
        
        mock_completion.return_value = mock_response
        
        response = await provider.generate(sample_request)
        
        assert isinstance(response, LLMResponse)
        assert response.content == "I'm doing well, thank you!"
        assert response.provider == "openai"


@pytest.mark.asyncio
async def test_unified_provider_fallback(sample_request):
    """Test unified provider fallback logic."""
    unified = UnifiedLLMProvider()
    
    # Create mock providers
    primary_provider = MagicMock(spec=LiteLLMProvider)
    primary_provider.name = "openai"
    primary_provider.generate = AsyncMock(side_effect=Exception("API Error"))
    
    fallback_provider = MagicMock(spec=LiteLLMProvider)
    fallback_provider.name = "anthropic"
    fallback_provider.generate = AsyncMock(return_value=LLMResponse(
        id="test-id",
        model="claude-3-sonnet-20240229",
        content="Fallback response",
        provider="anthropic",
    ))
    fallback_provider.supports_capability = MagicMock(return_value=True)
    fallback_provider.update_metrics = MagicMock()
    
    # Register providers
    unified.register_provider("openai", primary_provider)
    unified.register_provider("anthropic", fallback_provider)
    
    # Configure fallback
    from superagent.llm.models import ProviderConfig
    unified.register_provider_config(ProviderConfig(
        name="openai",
        models=["gpt-4-turbo-preview"],
        priority=100,
    ))
    unified.register_provider_config(ProviderConfig(
        name="anthropic",
        models=["claude-3-sonnet-20240229"],
        priority=90,
    ))
    
    # Test fallback
    response = await unified.generate(sample_request, provider_name="openai")
    
    assert response.content == "Fallback response"
    assert response.provider == "anthropic"


def test_provider_factory(mock_config):
    """Test provider factory creation."""
    unified = create_default_provider(mock_config)
    
    assert isinstance(unified, UnifiedLLMProvider)
    assert len(unified.list_providers()) > 0
    assert "openai" in unified.list_providers()


@pytest.mark.asyncio
async def test_token_counting():
    """Test token counting functionality."""
    provider = LiteLLMProvider(provider_name="openai")
    
    text = "Hello, how are you today?"
    tokens = provider.count_tokens(text, "gpt-4-turbo-preview")
    
    assert tokens > 0
    assert isinstance(tokens, int)
