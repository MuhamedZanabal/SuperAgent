"""
Interactive chat command.
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
    print_info,
    print_warning,
    StreamingDisplay,
)

logger = get_logger(__name__)


def chat_command(
    model: Optional[str] = typer.Option(
        None,
        "--model",
        "-m",
        help="Model to use for chat",
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
    stream: bool = typer.Option(
        True,
        "--stream/--no-stream",
        help="Enable streaming responses",
    ),
):
    """
    Start interactive chat session.
    
    Examples:
        superagent chat
        superagent chat --model gpt-4-turbo-preview
        superagent chat --system "You are a helpful coding assistant"
    """
    asyncio.run(chat_session(model, system, temperature, stream))


async def chat_session(
    model: Optional[str],
    system_prompt: Optional[str],
    temperature: Optional[float],
    stream: bool,
):
    """Run interactive chat session."""
    config = get_config()
    
    # Use provided model or default
    model = model or config.default_model
    temperature = temperature if temperature is not None else config.temperature
    
    # Initialize provider
    try:
        provider = create_default_provider(config)
    except Exception as e:
        print_error(f"Failed to initialize provider: {e}")
        return
    
    # Initialize conversation
    messages = []
    if system_prompt:
        messages.append(Message(role="system", content=system_prompt))
    
    # Print welcome message
    console.print("\n[bold cyan]SuperAgent Chat[/bold cyan]")
    console.print(f"Model: [yellow]{model}[/yellow]")
    console.print(f"Temperature: [yellow]{temperature}[/yellow]")
    console.print(f"Streaming: [yellow]{'enabled' if stream else 'disabled'}[/yellow]")
    console.print("\n[dim]Type 'exit' or 'quit' to end the session[/dim]")
    console.print("[dim]Type 'clear' to clear conversation history[/dim]")
    console.print("[dim]Type 'save' to save conversation[/dim]\n")
    
    # Chat loop
    while True:
        try:
            # Get user input
            console.print("[bold green]You:[/bold green] ", end="")
            user_input = input().strip()
            
            # Handle commands
            if user_input.lower() in ("exit", "quit"):
                console.print("\n[yellow]Goodbye![/yellow]")
                break
            
            if user_input.lower() == "clear":
                messages = []
                if system_prompt:
                    messages.append(Message(role="system", content=system_prompt))
                print_info("Conversation cleared")
                continue
            
            if user_input.lower() == "save":
                save_conversation(messages)
                continue
            
            if not user_input:
                continue
            
            # Add user message
            messages.append(Message(role="user", content=user_input))
            
            # Create request
            request = LLMRequest(
                model=model,
                messages=messages,
                temperature=temperature,
                stream=stream,
            )
            
            # Generate response
            console.print("\n[bold cyan]Assistant:[/bold cyan]")
            
            if stream:
                # Stream response
                assistant_content = ""
                with StreamingDisplay() as display:
                    try:
                        async for chunk in provider.stream(request):
                            assistant_content += chunk.delta
                            display.update(chunk.delta)
                    except Exception as e:
                        print_error(f"Streaming failed: {e}")
                        continue
                
                console.print()  # New line after streaming
                
                # Add assistant message to history
                messages.append(Message(role="assistant", content=assistant_content))
                
            else:
                # Non-streaming response
                try:
                    response = await provider.generate(request)
                    console.print(response.content)
                    console.print()
                    
                    # Add assistant message to history
                    messages.append(Message(role="assistant", content=response.content))
                    
                    # Show metrics
                    if response.usage:
                        console.print(
                            f"[dim]Tokens: {response.usage.total_tokens} | "
                            f"Cost: ${response.cost:.4f} | "
                            f"Latency: {response.latency_ms:.0f}ms[/dim]"
                        )
                    
                except Exception as e:
                    print_error(f"Generation failed: {e}")
                    continue
            
            console.print()  # Extra spacing
            
        except KeyboardInterrupt:
            console.print("\n[yellow]Interrupted[/yellow]")
            break
        except Exception as e:
            print_error(f"Error: {e}")
            continue


def save_conversation(messages: list):
    """Save conversation to file."""
    import json
    from datetime import datetime
    from pathlib import Path
    
    config = get_config()
    save_dir = config.data_dir / "conversations"
    save_dir.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = save_dir / f"conversation_{timestamp}.json"
    
    conversation_data = {
        "timestamp": datetime.now().isoformat(),
        "messages": [
            {
                "role": msg.role,
                "content": msg.content,
            }
            for msg in messages
        ],
    }
    
    with open(filename, "w") as f:
        json.dump(conversation_data, f, indent=2)
    
    print_info(f"Conversation saved to: {filename}")
