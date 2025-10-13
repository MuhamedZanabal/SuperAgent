"""
Models listing command.
"""

import asyncio
import typer

from superagent.llm import create_default_provider
from superagent.core.config import get_config
from superagent.cli.ui import console, create_table, print_error


def models_command(
    provider: str = typer.Option(
        None,
        "--provider",
        "-p",
        help="Filter by provider",
    ),
):
    """
    List available models.
    
    Examples:
        superagent models
        superagent models --provider openai
    """
    asyncio.run(list_models(provider))


async def list_models(provider_filter: str = None):
    """List available models."""
    config = get_config()
    
    try:
        llm_provider = create_default_provider(config)
    except Exception as e:
        print_error(f"Failed to initialize provider: {e}")
        return
    
    console.print("\n[bold cyan]Available Models[/bold cyan]\n")
    
    # Get all models
    models = llm_provider.list_available_models()
    
    # Filter by provider if specified
    if provider_filter:
        models = [m for m in models if provider_filter.lower() in m.lower()]
    
    if not models:
        console.print("[yellow]No models found[/yellow]")
        return
    
    # Group by provider
    provider_models = {}
    for model in models:
        # Extract provider from model name
        if "/" in model:
            prov, _ = model.split("/", 1)
        else:
            prov = llm_provider.get_provider_for_model(model) or "unknown"
        
        if prov not in provider_models:
            provider_models[prov] = []
        provider_models[prov].append(model)
    
    # Display by provider
    for prov, prov_models in sorted(provider_models.items()):
        table = create_table(
            f"{prov.title()} Models",
            ["Model"],
            [[model] for model in sorted(prov_models)],
        )
        console.print(table)
        console.print()
