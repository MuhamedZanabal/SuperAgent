"""
Main CLI application entry point.
"""

import typer
from typing import Optional
from pathlib import Path

from superagent.core.config import get_config, set_config, SuperAgentConfig
from superagent.core.logger import get_logger
from superagent.cli.chat import chat_command
from superagent.cli.config import config_command
from superagent.cli.models import models_command
from superagent.cli.providers import providers_command
from superagent.cli.run import run_command
from superagent.cli.ui import console, print_banner, print_error

logger = get_logger(__name__)

# Create main app
app = typer.Typer(
    name="superagent",
    help="SuperAgent - Production-grade AI automation platform",
    add_completion=False,
    rich_markup_mode="rich",
)


@app.callback()
def main(
    config_file: Optional[Path] = typer.Option(
        None,
        "--config",
        "-c",
        help="Path to configuration file",
    ),
    debug: bool = typer.Option(
        False,
        "--debug",
        "-d",
        help="Enable debug mode",
    ),
    verbose: bool = typer.Option(
        False,
        "--verbose",
        "-v",
        help="Enable verbose output",
    ),
):
    """
    SuperAgent - AI automation platform.
    
    Configure providers, run agents, and orchestrate AI workflows.
    """
    try:
        # Load configuration
        if config_file and config_file.exists():
            config = SuperAgentConfig.from_yaml(config_file)
            set_config(config)
        else:
            config = get_config()
        
        # Update debug mode
        if debug:
            config.debug = True
            config.log_level = "DEBUG"
        
        # Update config
        set_config(config)
        
    except Exception as e:
        print_error(f"Configuration error: {e}")
        raise typer.Exit(1)


@app.command()
def version():
    """Show version information."""
    config = get_config()
    console.print(f"[bold cyan]SuperAgent[/bold cyan] v{config.version}")
    console.print(f"Environment: [yellow]{config.environment}[/yellow]")


@app.command()
def init(
    output: Path = typer.Option(
        Path.home() / ".superagent" / "config.yaml",
        "--output",
        "-o",
        help="Output path for configuration file",
    ),
):
    """Initialize SuperAgent configuration."""
    try:
        config = get_config()
        
        # Ensure directory exists
        output.parent.mkdir(parents=True, exist_ok=True)
        
        # Save configuration
        config.to_yaml(output)
        
        console.print(f"[green]✓[/green] Configuration initialized at: {output}")
        console.print("\n[yellow]Next steps:[/yellow]")
        console.print("1. Edit the configuration file to add your API keys")
        console.print("2. Run [cyan]superagent providers[/cyan] to check provider status")
        console.print("3. Start chatting with [cyan]superagent chat[/cyan]")
        
    except Exception as e:
        print_error(f"Initialization failed: {e}")
        raise typer.Exit(1)


# Register subcommands
app.command(name="chat")(chat_command)
app.command(name="run")(run_command)
app.command(name="config")(config_command)
app.command(name="models")(models_command)
app.command(name="providers")(providers_command)


def cli_main():
    """Entry point for CLI."""
    try:
        print_banner()
        app()
    except KeyboardInterrupt:
        console.print("\n[yellow]Interrupted by user[/yellow]")
        raise typer.Exit(0)
    except Exception as e:
        print_error(f"Unexpected error: {e}")
        raise typer.Exit(1)


if __name__ == "__main__":
    cli_main()
