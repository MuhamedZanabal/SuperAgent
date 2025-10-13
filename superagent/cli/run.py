"""
One-shot execution command.
"""

import asyncio
from typing import Optional
import typer

from superagent.llm import create_default_provider
from superagent.llm.models import LLMRequest, Message
from superagent.core.config import get_config
from superagent.core.logger import get_logger
from superagent.cli.ui import (
    console,
    print_error,
    StreamingDisplay,
    ProgressDisplay,
)

logger = get_logger(__name__)


def run_command(
    prompt: str = typer.Argument(..., help="Prompt to execute"),
    model: Optional[str] = typer.Option(
        None,
        "--model",
        "-m",
        help="Model to use",
    ),
    system: Optional[str] = typer.Option(
        None,
        "--system",
        "-s",
        help="System prompt",
    ),
    temperature: Optional[float] = typer.Option(
        None,
        "--temperature",
        "-t",
        help="Temperature (0.0-2.0)",
    ),
    max_tokens: Optional[int] = typer.Option(
        None,
        "--max-tokens",
        help="Maximum tokens to generate",
    ),
    stream: bool = typer.Option(
        True,
        "--stream/--no-stream",
        help="Enable streaming responses",
    ),
    output: Optional[str] = typer.Option(
        None,
        "--output",
        "-o",
        help="Save output to file",
    ),
):
    """
    Execute a single prompt and exit.
    
    Examples:
        superagent run "Explain quantum computing"
        superagent run "Write a Python function" --model gpt-4
        superagent run "Analyze this" --system "You are a data analyst"
    """
    asyncio.run(execute_prompt(
        prompt,
        model,
        system,
        temperature,
        max_tokens,
        stream,
        output,
    ))


async def execute_prompt(
    prompt: str,
    model: Optional[str],
    system_prompt: Optional[str],
    temperature: Optional[float],
    max_tokens: Optional[int],
    stream: bool,
    output_file: Optional[str],
):
    """Execute a single prompt."""
    config = get_config()
    
    # Use provided values or defaults
    model = model or config.default_model
    temperature = temperature if temperature is not None else config.temperature
    max_tokens = max_tokens or config.max_tokens
    
    # Initialize provider
    try:
        with ProgressDisplay("Initializing provider..."):
            provider = create_default_provider(config)
    except Exception as e:
        print_error(f"Failed to initialize provider: {e}")
        return
    
    # Build messages
    messages = []
    if system_prompt:
        messages.append(Message(role="system", content=system_prompt))
    messages.append(Message(role="user", content=prompt))
    
    # Create request
    request = LLMRequest(
        model=model,
        messages=messages,
        temperature=temperature,
        max_tokens=max_tokens,
        stream=stream,
    )
    
    # Generate response
    response_content = ""
    
    try:
        if stream:
            # Stream response
            with StreamingDisplay() as display:
                async for chunk in provider.stream(request):
                    response_content += chunk.delta
                    display.update(chunk.delta)
            
            console.print()  # New line after streaming
            
        else:
            # Non-streaming response
            with ProgressDisplay("Generating response..."):
                response = await provider.generate(request)
                response_content = response.content
            
            console.print(f"\n{response_content}\n")
            
            # Show metrics
            if response.usage:
                console.print(
                    f"[dim]Tokens: {response.usage.total_tokens} | "
                    f"Cost: ${response.cost:.4f} | "
                    f"Latency: {response.latency_ms:.0f}ms[/dim]"
                )
        
        # Save to file if requested
        if output_file:
            with open(output_file, "w") as f:
                f.write(response_content)
            console.print(f"\n[green]✓[/green] Output saved to: {output_file}")
        
    except Exception as e:
        print_error(f"Execution failed: {e}")
        raise typer.Exit(1)
