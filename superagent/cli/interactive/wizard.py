"""
Interactive configuration wizard.
"""

from typing import Optional
from rich.console import Console
from rich.prompt import Prompt, Confirm
from rich.panel import Panel
from rich.table import Table

from superagent.core.config import SuperAgentConfig, ProviderType


class ConfigWizard:
    """
    Interactive configuration wizard for first-time setup.
    
    Guides users through:
    - LLM provider selection and API key entry
    - Memory backend configuration
    - Security settings
    - Plugin configuration
    """
    
    def __init__(self, config: SuperAgentConfig):
        self.config = config
        self.console = Console()
    
    async def run(self) -> None:
        """Run the configuration wizard."""
        self.console.print(Panel.fit(
            "[bold cyan]SuperAgent Configuration Wizard[/bold cyan]\n"
            "Let's set up your SuperAgent installation.",
            border_style="cyan",
        ))
        
        # Provider configuration
        await self.configure_providers()
        
        # Memory configuration
        await self.configure_memory()
        
        # Security configuration
        await self.configure_security()
        
        # Save configuration
        self.save_config()
        
        self.console.print("\n[bold green]✓[/bold green] Configuration complete!")
    
    async def configure_providers(self) -> None:
        """Configure LLM providers."""
        self.console.print("\n[bold]LLM Provider Configuration[/bold]")
        
        # Show available providers
        table = Table(title="Available Providers")
        table.add_column("Provider", style="cyan")
        table.add_column("Status", style="yellow")
        
        for provider in ProviderType:
            api_key = self.config.get_provider_api_key(provider)
            status = "✓ Configured" if api_key else "✗ Not configured"
            table.add_row(provider.value, status)
        
        self.console.print(table)
        
        # Ask to configure providers
        if Confirm.ask("\nWould you like to configure providers?", default=True):
            for provider in ProviderType:
                if provider == ProviderType.OLLAMA:
                    continue  # Skip Ollama (no API key needed)
                
                current_key = self.config.get_provider_api_key(provider)
                if current_key:
                    if not Confirm.ask(f"Update {provider.value} API key?", default=False):
                        continue
                
                api_key = Prompt.ask(
                    f"Enter {provider.value} API key (or press Enter to skip)",
                    password=True,
                    default="",
                )
                
                if api_key:
                    setattr(self.config, f"{provider.value}_api_key", api_key)
        
        # Select default provider
        default_provider = Prompt.ask(
            "Select default provider",
            choices=[p.value for p in ProviderType],
            default=self.config.default_provider.value,
        )
        self.config.default_provider = ProviderType(default_provider)
        
        # Select default model
        default_model = Prompt.ask(
            "Enter default model",
            default=self.config.default_model,
        )
        self.config.default_model = default_model
    
    async def configure_memory(self) -> None:
        """Configure memory settings."""
        self.console.print("\n[bold]Memory Configuration[/bold]")
        
        enable_memory = Confirm.ask(
            "Enable memory system?",
            default=self.config.memory_enabled,
        )
        self.config.memory_enabled = enable_memory
        
        if enable_memory:
            vector_store = Prompt.ask(
                "Vector store backend",
                choices=["chromadb", "faiss", "qdrant"],
                default=self.config.vector_store_type,
            )
            self.config.vector_store_type = vector_store
    
    async def configure_security(self) -> None:
        """Configure security settings."""
        self.console.print("\n[bold]Security Configuration[/bold]")
        
        sandbox_enabled = Confirm.ask(
            "Enable sandboxed execution?",
            default=self.config.sandbox_enabled,
        )
        self.config.sandbox_enabled = sandbox_enabled
        
        encryption_enabled = Confirm.ask(
            "Enable encryption?",
            default=self.config.encryption_enabled,
        )
        self.config.encryption_enabled = encryption_enabled
    
    def save_config(self) -> None:
        """Save configuration to file."""
        config_path = self.config.data_dir.parent / "config.yaml"
        self.config.to_yaml(config_path)
        self.console.print(f"\n[green]✓[/green] Configuration saved to: {config_path}")
