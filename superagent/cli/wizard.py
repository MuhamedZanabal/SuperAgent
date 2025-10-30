"""
Configuration wizard for first-run setup.
Guides users through API key setup, model selection, and profile creation.
"""
from typing import Optional, Dict, Any
import asyncio
from pathlib import Path

from rich.console import Console
from rich.prompt import Prompt, Confirm
from rich.panel import Panel
from rich.table import Table
from rich import box

from superagent.core.config import SuperAgentConfig, LLMProviderConfig
from superagent.core.security import SecurityManager
from superagent.core.logger import get_logger

logger = get_logger(__name__)
console = Console()


class ConfigurationWizard:
    """Interactive configuration wizard for first-run setup."""
    
    def __init__(self, config_path: Optional[Path] = None):
        self.config_path = config_path or Path.home() / ".superagent" / "config.yaml"
        self.security = SecurityManager()
        
    async def run(self) -> SuperAgentConfig:
        """Run the configuration wizard."""
        console.clear()
        console.print(Panel.fit(
            "[bold cyan]Welcome to SuperAgent![/bold cyan]\n\n"
            "Let's set up your AI assistant. This will only take a minute.",
            border_style="cyan",
            box=box.DOUBLE
        ))
        console.print()
        
        # Step 1: API Key Setup
        api_key = await self._setup_api_key()
        
        # Step 2: Model Selection
        model = await self._select_model()
        
        # Step 3: Default Parameters
        params = await self._configure_parameters()
        
        # Step 4: System Prompt
        system_prompt = await self._configure_system_prompt()
        
        # Step 5: Profile Setup
        profiles = await self._setup_profiles(params, system_prompt)
        
        # Step 6: UI Preferences
        ui_prefs = await self._configure_ui()
        
        # Step 7: Feature Flags
        features = await self._configure_features()
        
        # Create configuration
        config = SuperAgentConfig(
            llm_providers=[
                LLMProviderConfig(
                    name="anthropic",
                    api_key=api_key,
                    default_model=model,
                    **params
                )
            ],
            default_provider="anthropic",
            profiles=profiles,
            ui_preferences=ui_prefs,
            features=features
        )
        
        # Save configuration
        await self._save_config(config)
        
        console.print()
        console.print(Panel.fit(
            "[bold green]✓ Configuration complete![/bold green]\n\n"
            f"Your settings have been saved to:\n{self.config_path}\n\n"
            "Run [bold cyan]superagent[/bold cyan] to start chatting!",
            border_style="green",
            box=box.DOUBLE
        ))
        
        return config
    
    async def _setup_api_key(self) -> str:
        """Setup API key with validation."""
        console.print("[bold]Step 1: API Key Setup[/bold]")
        console.print("Enter your Anthropic API key (starts with 'sk-ant-'):")
        console.print("[dim]You can get one at: https://console.anthropic.com/[/dim]\n")
        
        while True:
            api_key = Prompt.ask("API Key", password=True)
            
            if not api_key:
                console.print("[red]API key is required[/red]")
                continue
            
            if not api_key.startswith("sk-ant-"):
                console.print("[yellow]Warning: API key should start with 'sk-ant-'[/yellow]")
                if not Confirm.ask("Continue anyway?"):
                    continue
            
            # Validate API key
            console.print("\n[dim]Validating API key...[/dim]")
            if await self._validate_api_key(api_key):
                console.print("[green]✓ API key validated successfully![/green]\n")
                return api_key
            else:
                console.print("[red]✗ Invalid API key. Please try again.[/red]\n")
    
    async def _validate_api_key(self, api_key: str) -> bool:
        """Validate API key by making a test request."""
        try:
            from anthropic import Anthropic
            client = Anthropic(api_key=api_key)
            # Make a minimal test request
            await asyncio.to_thread(
                client.messages.create,
                model="claude-3-5-haiku-20241022",
                max_tokens=10,
                messages=[{"role": "user", "content": "Hi"}]
            )
            return True
        except Exception as e:
            logger.error(f"API key validation failed: {e}")
            return False
    
    async def _select_model(self) -> str:
        """Select default model."""
        console.print("[bold]Step 2: Model Selection[/bold]")
        console.print("Choose your default Claude model:\n")
        
        models = {
            "1": {
                "name": "claude-sonnet-4-20250514",
                "display": "Claude Sonnet 4",
                "description": "Best balance of intelligence and speed"
            },
            "2": {
                "name": "claude-opus-4-20250514",
                "display": "Claude Opus 4",
                "description": "Most capable model for complex tasks"
            },
            "3": {
                "name": "claude-3-5-haiku-20241022",
                "display": "Claude 3.5 Haiku",
                "description": "Fastest model for simple tasks"
            }
        }
        
        table = Table(show_header=True, box=box.ROUNDED)
        table.add_column("#", style="cyan")
        table.add_column("Model", style="bold")
        table.add_column("Description")
        
        for key, model in models.items():
            table.add_row(key, model["display"], model["description"])
        
        console.print(table)
        console.print()
        
        choice = Prompt.ask("Select model", choices=list(models.keys()), default="1")
        selected = models[choice]
        
        console.print(f"[green]✓ Selected: {selected['display']}[/green]\n")
        return selected["name"]
    
    async def _configure_parameters(self) -> Dict[str, Any]:
        """Configure default parameters."""
        console.print("[bold]Step 3: Default Parameters[/bold]")
        console.print("Configure default generation parameters:\n")
        
        use_defaults = Confirm.ask("Use recommended defaults?", default=True)
        
        if use_defaults:
            params = {
                "temperature": 1.0,
                "max_tokens": 4096,
                "top_p": 0.9,
                "top_k": 40
            }
            console.print("[green]✓ Using recommended defaults[/green]\n")
        else:
            params = {
                "temperature": float(Prompt.ask("Temperature (0.0-1.0)", default="1.0")),
                "max_tokens": int(Prompt.ask("Max tokens", default="4096")),
                "top_p": float(Prompt.ask("Top P (0.0-1.0)", default="0.9")),
                "top_k": int(Prompt.ask("Top K", default="40"))
            }
            console.print("[green]✓ Parameters configured[/green]\n")
        
        return params
    
    async def _configure_system_prompt(self) -> Optional[str]:
        """Configure default system prompt."""
        console.print("[bold]Step 4: System Prompt[/bold]")
        console.print("Set a default system prompt (optional):\n")
        
        use_prompt = Confirm.ask("Set a custom system prompt?", default=False)
        
        if use_prompt:
            console.print("\n[dim]Enter your system prompt (press Ctrl+D when done):[/dim]")
            lines = []
            try:
                while True:
                    line = input()
                    lines.append(line)
            except EOFError:
                pass
            
            prompt = "\n".join(lines).strip()
            if prompt:
                console.print(f"\n[green]✓ System prompt set ({len(prompt)} characters)[/green]\n")
                return prompt
        
        console.print("[dim]No system prompt set[/dim]\n")
        return None
    
    async def _setup_profiles(self, default_params: Dict[str, Any], default_prompt: Optional[str]) -> Dict[str, Dict[str, Any]]:
        """Setup user profiles."""
        console.print("[bold]Step 5: Profile Setup[/bold]")
        console.print("Create profiles for different use cases:\n")
        
        profiles = {
            "default": {
                **default_params,
                "system_prompt": default_prompt,
                "streaming": True
            }
        }
        
        create_more = Confirm.ask("Create additional profiles? (e.g., coding, creative)", default=False)
        
        if create_more:
            presets = {
                "coding": {
                    "temperature": 0.7,
                    "max_tokens": 8000,
                    "system_prompt": "You are an expert programmer. Provide clear, well-documented code with explanations.",
                    "streaming": True
                },
                "creative": {
                    "temperature": 1.2,
                    "max_tokens": 4096,
                    "system_prompt": "You are a creative writing assistant. Be imaginative and expressive.",
                    "streaming": True
                },
                "analysis": {
                    "temperature": 0.5,
                    "max_tokens": 6000,
                    "system_prompt": "You are an analytical assistant. Provide detailed, structured analysis.",
                    "streaming": True
                }
            }
            
            console.print("\nAvailable presets:")
            for name, config in presets.items():
                console.print(f"  • [cyan]{name}[/cyan]: {config['system_prompt'][:60]}...")
            
            console.print()
            for name in presets:
                if Confirm.ask(f"Add '{name}' profile?", default=True):
                    profiles[name] = presets[name]
                    console.print(f"[green]✓ Added '{name}' profile[/green]")
        
        console.print()
        return profiles
    
    async def _configure_ui(self) -> Dict[str, Any]:
        """Configure UI preferences."""
        console.print("[bold]Step 6: UI Preferences[/bold]\n")
        
        return {
            "color_scheme": Prompt.ask("Color scheme", choices=["dark", "light"], default="dark"),
            "syntax_highlighting": Confirm.ask("Enable syntax highlighting?", default=True),
            "streaming": Confirm.ask("Enable streaming responses?", default=True),
            "show_tokens": Confirm.ask("Show token counts?", default=True),
            "show_cost": Confirm.ask("Show cost estimates?", default=True)
        }
    
    async def _configure_features(self) -> Dict[str, Any]:
        """Configure feature flags."""
        console.print("\n[bold]Step 7: Features[/bold]\n")
        
        return {
            "auto_save": Confirm.ask("Auto-save conversations?", default=True),
            "cost_tracking": Confirm.ask("Enable cost tracking?", default=True),
            "web_search": Confirm.ask("Enable web search? (experimental)", default=False),
            "code_execution": Confirm.ask("Enable code execution? (requires sandbox)", default=False)
        }
    
    async def _save_config(self, config: SuperAgentConfig):
        """Save configuration to file."""
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Encrypt API keys before saving
        config_dict = config.model_dump()
        for provider in config_dict.get("llm_providers", []):
            if "api_key" in provider:
                provider["api_key"] = self.security.encrypt(provider["api_key"])
        
        # Save to YAML
        import yaml
        with open(self.config_path, "w") as f:
            yaml.dump(config_dict, f, default_flow_style=False)
        
        # Set restrictive permissions
        self.config_path.chmod(0o600)
        
        logger.info(f"Configuration saved to {self.config_path}")


async def run_wizard() -> SuperAgentConfig:
    """Run the configuration wizard."""
    wizard = ConfigurationWizard()
    return await wizard.run()
