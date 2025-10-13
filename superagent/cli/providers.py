"""
Providers status command.
"""

import asyncio
import typer

from superagent.llm import create_default_provider
from superagent.core.config import get_config
from superagent.cli.ui import console, create_table, print_error


def providers_command():
    """
    Show provider status and metrics.
    
    Examples:
        superagent providers
    """
    asyncio.run(show_providers())


async def show_providers():
    """Display provider status and metrics."""
    config = get_config()
    
    try:
        provider = create_default_provider(config)
    except Exception as e:
        print_error(f"Failed to initialize provider: {e}")
        return
    
    console.print("\n[bold cyan]Provider Status[/bold cyan]\n")
    
    # Get all providers
    providers = provider.list_providers()
    
    if not providers:
        console.print("[yellow]No providers configured[/yellow]")
        return
    
    # Get metrics for each provider
    all_metrics = provider.get_all_metrics()
    
    # Create status table
    rows = []
    for prov_name in sorted(providers):
        metrics = all_metrics.get(prov_name, {})
        
        status = "✓ Active" if metrics.get("total_requests", 0) > 0 else "○ Ready"
        success_rate = metrics.get("success_rate", 0.0) * 100
        total_requests = metrics.get("total_requests", 0)
        avg_latency = metrics.get("avg_latency_ms", 0.0)
        
        rows.append([
            prov_name,
            status,
            f"{success_rate:.1f}%",
            str(total_requests),
            f"{avg_latency:.0f}ms",
        ])
    
    table = create_table(
        "Providers",
        ["Provider", "Status", "Success Rate", "Requests", "Avg Latency"],
        rows,
    )
    console.print(table)
    console.print()
    
    # Show detailed metrics if any provider has been used
    if any(m.get("total_requests", 0) > 0 for m in all_metrics.values()):
        console.print("[bold cyan]Detailed Metrics[/bold cyan]\n")
        
        for prov_name in sorted(providers):
            metrics = all_metrics.get(prov_name, {})
            
            if metrics.get("total_requests", 0) == 0:
                continue
            
            detail_rows = [
                ["Total Requests", str(metrics.get("total_requests", 0))],
                ["Successful", str(metrics.get("successful_requests", 0))],
                ["Failed", str(metrics.get("failed_requests", 0))],
                ["Total Tokens", str(metrics.get("total_tokens", 0))],
                ["Total Cost", f"${metrics.get('total_cost', 0.0):.4f}"],
                ["Avg Latency", f"{metrics.get('avg_latency_ms', 0.0):.0f}ms"],
            ]
            
            if metrics.get("last_error"):
                detail_rows.append(["Last Error", metrics["last_error"]])
            
            detail_table = create_table(
                f"{prov_name.title()} Metrics",
                ["Metric", "Value"],
                detail_rows,
            )
            console.print(detail_table)
            console.print()
