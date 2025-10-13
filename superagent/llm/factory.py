"""
Provider factory for creating and managing LLM provider instances.
"""

from typing import Dict, List, Optional
from superagent.llm.base import BaseLLMProvider
from superagent.llm.litellm_provider import LiteLLMProvider
from superagent.llm.models import ProviderConfig
from superagent.llm.provider import UnifiedLLMProvider
from superagent.core.config import SuperAgentConfig, ProviderType
from superagent.core.logger import get_logger

logger = get_logger(__name__)


class ProviderFactory:
    """
    Factory for creating LLM provider instances.
    
    Handles provider instantiation, configuration, and registration.
    """
    
    @staticmethod
    def create_provider(
        provider_type: str,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        **kwargs,
    ) -> BaseLLMProvider:
        """
        Create a provider instance.
        
        Args:
            provider_type: Type of provider (e.g., "openai", "anthropic")
            api_key: API key for authentication
            base_url: Base URL for API endpoint
            **kwargs: Additional provider configuration
            
        Returns:
            BaseLLMProvider instance
        """
        return LiteLLMProvider(
            provider_name=provider_type,
            api_key=api_key,
            base_url=base_url,
            **kwargs,
        )
    
    @staticmethod
    def create_from_config(
        config: ProviderConfig,
    ) -> BaseLLMProvider:
        """
        Create a provider from a ProviderConfig.
        
        Args:
            config: Provider configuration
            
        Returns:
            BaseLLMProvider instance
        """
        return ProviderFactory.create_provider(
            provider_type=config.name,
            api_key=config.api_key,
            base_url=config.base_url,
            timeout=config.timeout,
            max_retries=config.max_retries,
            **config.metadata,
        )
    
    @staticmethod
    def create_unified_provider(
        app_config: SuperAgentConfig,
    ) -> UnifiedLLMProvider:
        """
        Create a unified provider with all configured providers.
        
        Args:
            app_config: Application configuration
            
        Returns:
            UnifiedLLMProvider with all providers registered
        """
        unified = UnifiedLLMProvider()
        
        # Define provider configurations based on app config
        provider_configs = []
        
        # OpenAI
        if app_config.openai_api_key:
            provider_configs.append(ProviderConfig(
                name="openai",
                api_key=app_config.openai_api_key,
                models=[
                    "gpt-4-turbo-preview",
                    "gpt-4",
                    "gpt-3.5-turbo",
                    "gpt-4o",
                    "gpt-4o-mini",
                ],
                priority=100,
                enabled=True,
                timeout=app_config.timeout,
                max_retries=app_config.retry_attempts,
            ))
        
        # Anthropic
        if app_config.anthropic_api_key:
            provider_configs.append(ProviderConfig(
                name="anthropic",
                api_key=app_config.anthropic_api_key,
                models=[
                    "claude-3-opus-20240229",
                    "claude-3-sonnet-20240229",
                    "claude-3-haiku-20240307",
                    "claude-3-5-sonnet-20240620",
                ],
                priority=90,
                enabled=True,
                timeout=app_config.timeout,
                max_retries=app_config.retry_attempts,
            ))
        
        # Groq
        if app_config.groq_api_key:
            provider_configs.append(ProviderConfig(
                name="groq",
                api_key=app_config.groq_api_key,
                models=[
                    "llama-3.1-70b-versatile",
                    "llama-3.1-8b-instant",
                    "mixtral-8x7b-32768",
                ],
                priority=80,
                enabled=True,
                timeout=app_config.timeout,
                max_retries=app_config.retry_attempts,
            ))
        
        # Together
        if app_config.together_api_key:
            provider_configs.append(ProviderConfig(
                name="together",
                api_key=app_config.together_api_key,
                models=[
                    "meta-llama/Meta-Llama-3.1-70B-Instruct-Turbo",
                    "meta-llama/Meta-Llama-3.1-8B-Instruct-Turbo",
                    "mistralai/Mixtral-8x7B-Instruct-v0.1",
                ],
                priority=70,
                enabled=True,
                timeout=app_config.timeout,
                max_retries=app_config.retry_attempts,
            ))
        
        # OpenRouter
        if app_config.openrouter_api_key:
            provider_configs.append(ProviderConfig(
                name="openrouter",
                api_key=app_config.openrouter_api_key,
                models=[
                    "openai/gpt-4-turbo-preview",
                    "anthropic/claude-3-opus",
                    "meta-llama/llama-3.1-70b-instruct",
                ],
                priority=60,
                enabled=True,
                timeout=app_config.timeout,
                max_retries=app_config.retry_attempts,
            ))
        
        # Ollama (local, no API key needed)
        provider_configs.append(ProviderConfig(
            name="ollama",
            models=[
                "llama3.1",
                "llama3.1:70b",
                "mistral",
                "codellama",
            ],
            priority=50,
            enabled=True,
            base_url="http://localhost:11434",
            timeout=app_config.timeout,
            max_retries=app_config.retry_attempts,
        ))
        
        # Register all provider configs
        for config in provider_configs:
            unified.register_provider_config(config)
            
            # Create and register provider instance
            try:
                provider = ProviderFactory.create_from_config(config)
                unified.register_provider(config.name, provider)
                logger.info(f"Registered provider: {config.name}")
            except Exception as e:
                logger.error(f"Failed to register provider {config.name}: {e}")
        
        return unified


def create_default_provider(config: Optional[SuperAgentConfig] = None) -> UnifiedLLMProvider:
    """
    Create a default unified provider with standard configuration.
    
    Args:
        config: Optional application configuration
        
    Returns:
        UnifiedLLMProvider instance
    """
    if config is None:
        from superagent.core.config import get_config
        config = get_config()
    
    return ProviderFactory.create_unified_provider(config)
