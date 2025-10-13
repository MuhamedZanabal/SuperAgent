"""
Configuration management system with environment variable support,
validation, and secure secret handling.
"""

import os
from pathlib import Path
from typing import Any, Dict, Optional
from enum import StrEnum

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
import yaml


class LogLevel(StrEnum):
    """Supported logging levels."""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class ProviderType(StrEnum):
    """Supported LLM providers."""
    OPENROUTER = "openrouter"
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    AZURE = "azure"
    OLLAMA = "ollama"
    TOGETHER = "together"
    GROQ = "groq"


class SuperAgentConfig(BaseSettings):
    """
    Main configuration class for SuperAgent.
    
    Loads configuration from environment variables, .env files, and YAML config files.
    Validates all settings and provides secure defaults.
    """
    
    model_config = SettingsConfigDict(
        env_prefix="SUPERAGENT_",
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="allow",
    )
    
    # Core Settings
    app_name: str = Field(default="SuperAgent", description="Application name")
    version: str = Field(default="0.1.0", description="Application version")
    environment: str = Field(default="development", description="Runtime environment")
    debug: bool = Field(default=False, description="Enable debug mode")
    log_level: LogLevel = Field(default=LogLevel.INFO, description="Logging level")
    
    # Runtime Settings
    max_workers: int = Field(default=4, description="Maximum concurrent workers")
    timeout: int = Field(default=300, description="Default operation timeout in seconds")
    retry_attempts: int = Field(default=3, description="Default retry attempts")
    retry_delay: float = Field(default=1.0, description="Delay between retries in seconds")
    
    # LLM Provider Settings
    default_provider: ProviderType = Field(
        default=ProviderType.OPENAI,
        description="Default LLM provider"
    )
    default_model: str = Field(default="gpt-4-turbo-preview", description="Default model")
    max_tokens: int = Field(default=4096, description="Maximum tokens per request")
    temperature: float = Field(default=0.7, description="Default temperature")
    streaming_enabled: bool = Field(default=True, description="Enable streaming responses")
    
    # API Keys (loaded from environment)
    openai_api_key: Optional[str] = Field(default=None, description="OpenAI API key")
    anthropic_api_key: Optional[str] = Field(default=None, description="Anthropic API key")
    azure_api_key: Optional[str] = Field(default=None, description="Azure API key")
    groq_api_key: Optional[str] = Field(default=None, description="Groq API key")
    together_api_key: Optional[str] = Field(default=None, description="Together API key")
    openrouter_api_key: Optional[str] = Field(default=None, description="OpenRouter API key")
    
    # Memory Settings
    memory_enabled: bool = Field(default=True, description="Enable memory system")
    vector_store_type: str = Field(default="chromadb", description="Vector store backend")
    vector_store_path: Path = Field(
        default=Path.home() / ".superagent" / "vector_store",
        description="Vector store data path"
    )
    embedding_model: str = Field(
        default="sentence-transformers/all-MiniLM-L6-v2",
        description="Embedding model"
    )
    max_memory_items: int = Field(default=1000, description="Maximum memory items")
    
    # Security Settings
    sandbox_enabled: bool = Field(default=True, description="Enable sandboxed execution")
    max_file_size_mb: int = Field(default=100, description="Maximum file size in MB")
    allowed_domains: list[str] = Field(
        default_factory=lambda: ["*"],
        description="Allowed domains for network access"
    )
    encryption_enabled: bool = Field(default=True, description="Enable encryption")
    
    # Plugin Settings
    plugins_enabled: bool = Field(default=True, description="Enable plugin system")
    plugins_path: Path = Field(
        default=Path.home() / ".superagent" / "plugins",
        description="Plugins directory"
    )
    auto_load_plugins: bool = Field(default=True, description="Auto-load plugins on startup")
    
    # Monitoring Settings
    metrics_enabled: bool = Field(default=True, description="Enable metrics collection")
    analytics_enabled: bool = Field(default=True, description="Enable analytics")
    cost_tracking_enabled: bool = Field(default=True, description="Enable cost tracking")
    
    # Storage Settings
    data_dir: Path = Field(
        default=Path.home() / ".superagent" / "data",
        description="Data directory"
    )
    cache_dir: Path = Field(
        default=Path.home() / ".superagent" / "cache",
        description="Cache directory"
    )
    logs_dir: Path = Field(
        default=Path.home() / ".superagent" / "logs",
        description="Logs directory"
    )
    
    @field_validator("data_dir", "cache_dir", "logs_dir", "vector_store_path", "plugins_path")
    @classmethod
    def ensure_directory_exists(cls, v: Path) -> Path:
        """Ensure directory exists, create if necessary."""
        v.mkdir(parents=True, exist_ok=True)
        return v
    
    @field_validator("temperature")
    @classmethod
    def validate_temperature(cls, v: float) -> float:
        """Validate temperature is in valid range."""
        if not 0.0 <= v <= 2.0:
            raise ValueError("Temperature must be between 0.0 and 2.0")
        return v
    
    @classmethod
    def from_yaml(cls, path: Path) -> "SuperAgentConfig":
        """
        Load configuration from YAML file.
        
        Args:
            path: Path to YAML configuration file
            
        Returns:
            SuperAgentConfig instance
        """
        with open(path, "r") as f:
            config_dict = yaml.safe_load(f)
        return cls(**config_dict)
    
    def to_yaml(self, path: Path) -> None:
        """
        Save configuration to YAML file.
        
        Args:
            path: Path to save YAML configuration
        """
        with open(path, "w") as f:
            yaml.dump(self.model_dump(), f, default_flow_style=False)
    
    def get_provider_api_key(self, provider: ProviderType) -> Optional[str]:
        """
        Get API key for specified provider.
        
        Args:
            provider: Provider type
            
        Returns:
            API key if available, None otherwise
        """
        key_mapping = {
            ProviderType.OPENAI: self.openai_api_key,
            ProviderType.ANTHROPIC: self.anthropic_api_key,
            ProviderType.AZURE: self.azure_api_key,
            ProviderType.GROQ: self.groq_api_key,
            ProviderType.TOGETHER: self.together_api_key,
            ProviderType.OPENROUTER: self.openrouter_api_key,
        }
        return key_mapping.get(provider)
    
    def validate_provider_config(self, provider: ProviderType) -> bool:
        """
        Validate that provider has necessary configuration.
        
        Args:
            provider: Provider to validate
            
        Returns:
            True if provider is properly configured
        """
        api_key = self.get_provider_api_key(provider)
        if provider == ProviderType.OLLAMA:
            return True  # Ollama doesn't require API key
        return api_key is not None and len(api_key) > 0


# Global config instance
_config: Optional[SuperAgentConfig] = None


def get_config() -> SuperAgentConfig:
    """
    Get global configuration instance.
    
    Returns:
        SuperAgentConfig singleton instance
    """
    global _config
    if _config is None:
        _config = SuperAgentConfig()
    return _config


def set_config(config: SuperAgentConfig) -> None:
    """
    Set global configuration instance.
    
    Args:
        config: Configuration instance to set
    """
    global _config
    _config = config
