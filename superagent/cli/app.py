"""
Main CLI application entry point.
"""

import typer
from typing import Optional
from pathlib import Path
import asyncio

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


@app.callback(invoke_without_command=True)
def main(
    ctx: typer.Context,
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
        config_path = config_file or Path.home() / ".superagent" / "config.yaml"
        
        # If no subcommand and no config exists, run wizard
        if ctx.invoked_subcommand is None:
            if not config_path.exists():
                console.print("[yellow]No configuration found. Running setup wizard...[/yellow]\n")
                from superagent.cli.wizard import run_wizard
                config = asyncio.run(run_wizard())
                set_config(config)
            else:
                # Load existing config
                config = SuperAgentConfig.from_yaml(config_path)
                set_config(config)
            
            # Launch interactive shell
            from superagent.cli.interactive.enhanced_shell import EnhancedShell
            from superagent.core.runtime import SuperAgentRuntime
            
            runtime = SuperAgentRuntime(config)
            shell = EnhancedShell(runtime)
            asyncio.run(shell.run())
            return
        
        # Load configuration for subcommands
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
    """Initialize SuperAgent configuration with wizard."""
    from superagent.cli.wizard import run_wizard
    
    try:
        config = asyncio.run(run_wizard())
        
        console.print(f"\n[green]✓[/green] Configuration initialized at: {output}")
        console.print("\n[yellow]Next steps:[/yellow]")
        console.print("1. Run [cyan]superagent[/cyan] to start the interactive shell")
        console.print("2. Or use [cyan]superagent chat[/cyan] for quick conversations")
        console.print("3. Check [cyan]superagent --help[/cyan] for all commands")
        
    except Exception as e:
        print_error(f"Initialization failed: {e}")
        raise typer.Exit(1)


@app.command()
def interactive():
    """Launch interactive shell (GeminiCLI-style experience)."""
    try:
        config_path = Path.home() / ".superagent" / "config.yaml"
        
        if not config_path.exists():
            console.print("[yellow]No configuration found. Running setup wizard...[/yellow]\n")
            from superagent.cli.wizard import run_wizard
            config = asyncio.run(run_wizard())
        else:
            config = SuperAgentConfig.from_yaml(config_path)
        
        set_config(config)
        
        from superagent.cli.interactive.enhanced_shell import EnhancedShell
        from superagent.core.runtime import SuperAgentRuntime
        
        runtime = SuperAgentRuntime(config)
        shell = EnhancedShell(runtime)
        asyncio.run(shell.run())
        
    except Exception as e:
        print_error(f"Interactive shell error: {e}")
        raise typer.Exit(1)


@app.command()
def wizard():
    """Run configuration wizard to set up or reconfigure SuperAgent."""
    from superagent.cli.wizard import run_wizard
    
    try:
        config = asyncio.run(run_wizard())
        console.print("\n[green]✓ Configuration complete![/green]")
        console.print("Run [cyan]superagent[/cyan] to start using SuperAgent")
    except Exception as e:
        print_error(f"Wizard failed: {e}")
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
