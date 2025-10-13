"""
Configuration management command.
"""

import typer
from pathlib import Path
from typing import Optional

from superagent.core.config import get_config, SuperAgentConfig
from superagent.cli.ui import (
    console,
    print_error,
    print_success,
    print_info,
    create_table,
)


def config_command(
    show: bool = typer.Option(
        False,
        "--show",
        help="Show current configuration",
    ),
    set_key: Optional[str] = typer.Option(
        None,
        "--set",
        help="Set configuration key (format: key=value)",
    ),
    export: Optional[Path] = typer.Option(
        None,
        "--export",
        help="Export configuration to file",
    ),
):
    """
    Manage SuperAgent configuration.
    
    Examples:
        superagent config --show
        superagent config --set default_model=gpt-4
        superagent config --export config.yaml
    """
    config = get_config()
    
    if show:
        show_config(config)
    elif set_key:
        set_config_value(config, set_key)
    elif export:
        export_config(config, export)
    else:
        show_config(config)


def show_config(config: SuperAgentConfig):
    """Display current configuration."""
    console.print("\n[bold cyan]SuperAgent Configuration[/bold cyan]\n")
    
    # Core settings
    core_table = create_table(
        "Core Settings",
        ["Setting", "Value"],
        [
            ["App Name", config.app_name],
            ["Version", config.version],
            ["Environment", config.environment],
            ["Debug", str(config.debug)],
            ["Log Level", config.log_level],
        ],
    )
    console.print(core_table)
    console.print()
    
    # LLM settings
    llm_table = create_table(
        "LLM Settings",
        ["Setting", "Value"],
        [
            ["Default Provider", config.default_provider],
            ["Default Model", config.default_model],
            ["Max Tokens", str(config.max_tokens)],
            ["Temperature", str(config.temperature)],
            ["Streaming", str(config.streaming_enabled)],
        ],
    )
    console.print(llm_table)
    console.print()
    
    # Provider status
    provider_table = create_table(
        "Provider Status",
        ["Provider", "Status"],
        [
            ["OpenAI", "✓ Configured" if config.openai_api_key else "✗ Not configured"],
            ["Anthropic", "✓ Configured" if config.anthropic_api_key else "✗ Not configured"],
            ["Groq", "✓ Configured" if config.groq_api_key else "✗ Not configured"],
            ["Together", "✓ Configured" if config.together_api_key else "✗ Not configured"],
            ["OpenRouter", "✓ Configured" if config.openrouter_api_key else "✗ Not configured"],
            ["Ollama", "✓ Available (local)"],
        ],
    )
    console.print(provider_table)
    console.print()
    
    # Paths
    paths_table = create_table(
        "Paths",
        ["Path", "Location"],
        [
            ["Data Directory", str(config.data_dir)],
            ["Cache Directory", str(config.cache_dir)],
            ["Logs Directory", str(config.logs_dir)],
            ["Plugins Directory", str(config.plugins_path)],
            ["Vector Store", str(config.vector_store_path)],
        ],
    )
    console.print(paths_table)


def set_config_value(config: SuperAgentConfig, key_value: str):
    """Set a configuration value."""
    try:
        key, value = key_value.split("=", 1)
        key = key.strip()
        value = value.strip()
        
        # Update config
        if hasattr(config, key):
            setattr(config, key, value)
            print_success(f"Set {key} = {value}")
        else:
            print_error(f"Unknown configuration key: {key}")
            
    except ValueError:
        print_error("Invalid format. Use: key=value")


def export_config(config: SuperAgentConfig, path: Path):
    """Export configuration to file."""
    try:
        config.to_yaml(path)
        print_success(f"Configuration exported to: {path}")
    except Exception as e:
        print_error(f"Export failed: {e}")
