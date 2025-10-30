"""
Enhanced interactive shell with GeminiCLI/Codex-style features.
Implements comprehensive slash commands, rich rendering, and conversation management.
"""
import asyncio
from typing import Optional, List, Dict, Any
from pathlib import Path
from datetime import datetime
import json

from rich.console import Console
from rich.markdown import Markdown
from rich.syntax import Syntax
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich import box
from prompt_toolkit import PromptSession
from prompt_toolkit.completion import WordCompleter
from prompt_toolkit.history import FileHistory
from prompt_toolkit.key_binding import KeyBindings

from superagent.core.runtime import SuperAgentRuntime
from superagent.core.logger import get_logger
from superagent.ux.orchestrator import UXOrchestrator
from superagent.protocol.events import EventEmitter, EventType

logger = get_logger(__name__)
console = Console()


class EnhancedShell:
    """Enhanced interactive shell with comprehensive features."""
    
    def __init__(self, runtime: SuperAgentRuntime):
        self.runtime = runtime
        self.orchestrator = UXOrchestrator(runtime)
        self.event_emitter = EventEmitter()
        
        # Conversation state
        self.conversation_history: List[Dict[str, Any]] = []
        self.current_profile = "default"
        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.conversation_dir = Path.home() / ".superagent" / "conversations"
        self.conversation_dir.mkdir(parents=True, exist_ok=True)
        
        # Statistics
        self.stats = {
            "messages": 0,
            "tokens_used": 0,
            "cost": 0.0,
            "start_time": datetime.now()
        }
        
        # Setup prompt session
        self.setup_prompt_session()
        
        # Slash commands
        self.commands = {
            "/help": self.cmd_help,
            "/clear": self.cmd_clear,
            "/new": self.cmd_new,
            "/reset": self.cmd_new,
            "/history": self.cmd_history,
            "/save": self.cmd_save,
            "/load": self.cmd_load,
            "/export": self.cmd_export,
            "/model": self.cmd_model,
            "/temp": self.cmd_temperature,
            "/tokens": self.cmd_max_tokens,
            "/system": self.cmd_system_prompt,
            "/profile": self.cmd_profile,
            "/search": self.cmd_search,
            "/undo": self.cmd_undo,
            "/redo": self.cmd_redo,
            "/copy": self.cmd_copy,
            "/stats": self.cmd_stats,
            "/config": self.cmd_config,
            "/edit": self.cmd_edit,
            "/branch": self.cmd_branch,
            "/streaming": self.cmd_streaming,
            "/multiline": self.cmd_multiline,
            "/file": self.cmd_file,
            "/image": self.cmd_image,
            "/code": self.cmd_code,
            "/web": self.cmd_web,
            "/summarize": self.cmd_summarize,
            "/continue": self.cmd_continue,
            "/regenerate": self.cmd_regenerate,
            "/quit": self.cmd_quit,
            "/exit": self.cmd_quit
        }
    
    def setup_prompt_session(self):
        """Setup prompt_toolkit session with history and completion."""
        history_file = Path.home() / ".superagent" / "history"
        history_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Command completer
        command_completer = WordCompleter(
            list(self.commands.keys()),
            ignore_case=True,
            sentence=True
        )
        
        # Key bindings
        kb = KeyBindings()
        
        @kb.add('c-c')
        def _(event):
            """Handle Ctrl+C to interrupt."""
            event.app.exit(exception=KeyboardInterrupt)
        
        self.session = PromptSession(
            history=FileHistory(str(history_file)),
            completer=command_completer,
            key_bindings=kb,
            multiline=False
        )
    
    async def run(self):
        """Run the interactive shell."""
        console.print(Panel.fit(
            "[bold cyan]SuperAgent Interactive Shell[/bold cyan]\n\n"
            "Type your message or use slash commands (type /help for list)\n"
            "Press Ctrl+C to interrupt, /quit to exit",
            border_style="cyan",
            box=box.DOUBLE
        ))
        console.print()
        
        # Auto-load last conversation if exists
        await self.auto_load_last_conversation()
        
        while True:
            try:
                # Get user input
                user_input = await asyncio.to_thread(
                    self.session.prompt,
                    f"[{self.current_profile}] > "
                )
                
                if not user_input.strip():
                    continue
                
                # Handle slash commands
                if user_input.startswith("/"):
                    await self.handle_command(user_input)
                else:
                    # Regular message
                    await self.handle_message(user_input)
                
            except KeyboardInterrupt:
                console.print("\n[yellow]Interrupted. Type /quit to exit.[/yellow]")
            except EOFError:
                break
            except Exception as e:
                logger.error(f"Error in shell: {e}", exc_info=True)
                console.print(f"[red]Error: {e}[/red]")
        
        # Save conversation on exit
        await self.auto_save_conversation()
    
    async def handle_command(self, command_line: str):
        """Handle slash command."""
        parts = command_line.split(maxsplit=1)
        command = parts[0].lower()
        args = parts[1] if len(parts) > 1 else ""
        
        if command in self.commands:
            await self.commands[command](args)
        else:
            console.print(f"[red]Unknown command: {command}[/red]")
            console.print("[dim]Type /help for available commands[/dim]")
    
    async def handle_message(self, message: str):
        """Handle regular user message."""
        # Add to history
        self.conversation_history.append({
            "role": "user",
            "content": message,
            "timestamp": datetime.now().isoformat()
        })
        
        # Show thinking indicator
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task("Thinking...", total=None)
            
            try:
                # Get response from orchestrator
                response = await self.orchestrator.process_input(message)
                
                progress.update(task, completed=True)
                
                # Add response to history
                self.conversation_history.append({
                    "role": "assistant",
                    "content": response.get("content", ""),
                    "timestamp": datetime.now().isoformat(),
                    "tokens": response.get("tokens", 0),
                    "cost": response.get("cost", 0.0)
                })
                
                # Update stats
                self.stats["messages"] += 2
                self.stats["tokens_used"] += response.get("tokens", 0)
                self.stats["cost"] += response.get("cost", 0.0)
                
                # Display response
                self.display_response(response.get("content", ""))
                
                # Auto-save
                if self.runtime.config.features.get("auto_save", True):
                    await self.auto_save_conversation()
                
            except Exception as e:
                progress.update(task, completed=True)
                logger.error(f"Error processing message: {e}", exc_info=True)
                console.print(f"[red]Error: {e}[/red]")
    
    def display_response(self, content: str):
        """Display assistant response with rich formatting."""
        console.print()
        console.print(Panel(
            Markdown(content),
            title="[bold cyan]Assistant[/bold cyan]",
            border_style="cyan",
            box=box.ROUNDED
        ))
        console.print()
    
    # Command implementations
    async def cmd_help(self, args: str):
        """Display help for all commands."""
        table = Table(title="Available Commands", box=box.ROUNDED)
        table.add_column("Command", style="cyan")
        table.add_column("Description")
        
        help_text = {
            "/help": "Display this help message",
            "/clear": "Clear conversation history",
            "/new, /reset": "Start new conversation",
            "/history [n]": "Show last n messages",
            "/save <file>": "Save conversation to file",
            "/load <file>": "Load conversation from file",
            "/export <format>": "Export as txt, md, html, pdf",
            "/model [name]": "Switch model",
            "/temp <value>": "Set temperature (0.0-1.0)",
            "/tokens <num>": "Set max tokens",
            "/system <prompt>": "Set system prompt",
            "/profile <name>": "Switch profile",
            "/search <query>": "Search conversation",
            "/undo": "Remove last message",
            "/redo": "Resend last message",
            "/copy [n]": "Copy response to clipboard",
            "/stats": "Show statistics",
            "/config": "Show configuration",
            "/streaming [on|off]": "Toggle streaming",
            "/multiline": "Enter multiline mode",
            "/file <path>": "Attach file",
            "/image <path>": "Analyze image",
            "/summarize": "Summarize conversation",
            "/continue": "Continue from last response",
            "/regenerate": "Regenerate last response",
            "/quit, /exit": "Exit shell"
        }
        
        for cmd, desc in help_text.items():
            table.add_row(cmd, desc)
        
        console.print(table)
    
    async def cmd_clear(self, args: str):
        """Clear conversation history."""
        self.conversation_history.clear()
        self.stats = {
            "messages": 0,
            "tokens_used": 0,
            "cost": 0.0,
            "start_time": datetime.now()
        }
        console.print("[green]✓ Conversation cleared[/green]")
    
    async def cmd_new(self, args: str):
        """Start new conversation."""
        await self.auto_save_conversation()
        await self.cmd_clear(args)
        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        console.print("[green]✓ New conversation started[/green]")
    
    async def cmd_history(self, args: str):
        """Show conversation history."""
        n = int(args) if args.isdigit() else len(self.conversation_history)
        
        for msg in self.conversation_history[-n:]:
            role = msg["role"]
            content = msg["content"]
            timestamp = msg.get("timestamp", "")
            
            style = "cyan" if role == "user" else "green"
            console.print(f"[{style}]{role.upper()}[/{style}] ({timestamp}):")
            console.print(content)
            console.print()
    
    async def cmd_save(self, args: str):
        """Save conversation to file."""
        filename = args or f"conversation_{self.session_id}.json"
        filepath = self.conversation_dir / filename
        
        data = {
            "session_id": self.session_id,
            "profile": self.current_profile,
            "history": self.conversation_history,
            "stats": self.stats,
            "timestamp": datetime.now().isoformat()
        }
        
        with open(filepath, "w") as f:
            json.dump(data, f, indent=2)
        
        console.print(f"[green]✓ Saved to {filepath}[/green]")
    
    async def cmd_load(self, args: str):
        """Load conversation from file."""
        if not args:
            console.print("[red]Usage: /load <filename>[/red]")
            return
        
        filepath = self.conversation_dir / args
        if not filepath.exists():
            console.print(f"[red]File not found: {filepath}[/red]")
            return
        
        with open(filepath) as f:
            data = json.load(f)
        
        self.conversation_history = data.get("history", [])
        self.stats = data.get("stats", self.stats)
        self.session_id = data.get("session_id", self.session_id)
        
        console.print(f"[green]✓ Loaded {len(self.conversation_history)} messages[/green]")
    
    async def cmd_stats(self, args: str):
        """Show conversation statistics."""
        duration = datetime.now() - self.stats["start_time"]
        
        table = Table(title="Conversation Statistics", box=box.ROUNDED)
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="bold")
        
        table.add_row("Messages", str(self.stats["messages"]))
        table.add_row("Tokens Used", f"{self.stats['tokens_used']:,}")
        table.add_row("Estimated Cost", f"${self.stats['cost']:.4f}")
        table.add_row("Duration", str(duration).split('.')[0])
        table.add_row("Session ID", self.session_id)
        table.add_row("Profile", self.current_profile)
        
        console.print(table)
    
    async def cmd_config(self, args: str):
        """Show current configuration."""
        config = self.runtime.config
        
        table = Table(title="Current Configuration", box=box.ROUNDED)
        table.add_column("Setting", style="cyan")
        table.add_column("Value", style="bold")
        
        table.add_row("Provider", config.default_provider)
        table.add_row("Model", config.llm_providers[0].default_model)
        table.add_row("Temperature", str(config.llm_providers[0].temperature))
        table.add_row("Max Tokens", str(config.llm_providers[0].max_tokens))
        table.add_row("Streaming", str(config.ui_preferences.get("streaming", True)))
        
        console.print(table)
    
    async def cmd_quit(self, args: str):
        """Exit the shell."""
        await self.auto_save_conversation()
        console.print("[cyan]Goodbye![/cyan]")
        raise EOFError
    
    async def cmd_export(self, args: str):
        """Export conversation in various formats."""
        from superagent.cli.conversation_manager import ConversationManager
        
        format_type = args.lower() if args else "txt"
        if format_type not in ["txt", "md", "html", "pdf", "json"]:
            console.print(f"[red]Unsupported format: {format_type}[/red]")
            console.print("[dim]Supported: txt, md, html, pdf, json[/dim]")
            return
        
        manager = ConversationManager(self.conversation_dir)
        filename = f"export_{self.session_id}.{format_type}"
        filepath = self.conversation_dir / filename
        
        try:
            manager.export_conversation(
                self.conversation_history,
                filepath,
                format_type
            )
            console.print(f"[green]✓ Exported to {filepath}[/green]")
        except Exception as e:
            console.print(f"[red]Export failed: {e}[/red]")
    
    async def cmd_model(self, args: str):
        """Switch LLM model."""
        if not args:
            # Show current model
            current = self.runtime.config.llm_providers[0].default_model
            console.print(f"[cyan]Current model: {current}[/cyan]")
            console.print("\n[dim]Available models:[/dim]")
            models = [
                "claude-3-5-sonnet-20241022",
                "claude-3-5-haiku-20241022",
                "claude-3-opus-20240229",
                "gpt-4-turbo-preview",
                "gpt-4",
                "gpt-3.5-turbo"
            ]
            for model in models:
                console.print(f"  • {model}")
            return
        
        # Switch model
        self.runtime.config.llm_providers[0].default_model = args
        console.print(f"[green]✓ Switched to model: {args}[/green]")
    
    async def cmd_temperature(self, args: str):
        """Set temperature for generation."""
        if not args:
            current = self.runtime.config.llm_providers[0].temperature
            console.print(f"[cyan]Current temperature: {current}[/cyan]")
            return
        
        try:
            temp = float(args)
            if not 0.0 <= temp <= 2.0:
                console.print("[red]Temperature must be between 0.0 and 2.0[/red]")
                return
            
            self.runtime.config.llm_providers[0].temperature = temp
            console.print(f"[green]✓ Temperature set to {temp}[/green]")
        except ValueError:
            console.print("[red]Invalid temperature value[/red]")
    
    async def cmd_max_tokens(self, args: str):
        """Set max tokens for generation."""
        if not args:
            current = self.runtime.config.llm_providers[0].max_tokens
            console.print(f"[cyan]Current max tokens: {current}[/cyan]")
            return
        
        try:
            tokens = int(args)
            if tokens < 1:
                console.print("[red]Max tokens must be positive[/red]")
                return
            
            self.runtime.config.llm_providers[0].max_tokens = tokens
            console.print(f"[green]✓ Max tokens set to {tokens}[/green]")
        except ValueError:
            console.print("[red]Invalid token value[/red]")
    
    async def cmd_system_prompt(self, args: str):
        """Set system prompt."""
        if not args:
            current = getattr(self.runtime.config, "system_prompt", "")
            if current:
                console.print(Panel(current, title="Current System Prompt", border_style="cyan"))
            else:
                console.print("[dim]No system prompt set[/dim]")
            return
        
        self.runtime.config.system_prompt = args
        console.print("[green]✓ System prompt updated[/green]")
    
    async def cmd_profile(self, args: str):
        """Switch profile."""
        if not args:
            console.print(f"[cyan]Current profile: {self.current_profile}[/cyan]")
            # List available profiles
            profiles_dir = Path.home() / ".superagent" / "profiles"
            if profiles_dir.exists():
                profiles = [p.stem for p in profiles_dir.glob("*.json")]
                if profiles:
                    console.print("\n[dim]Available profiles:[/dim]")
                    for profile in profiles:
                        console.print(f"  • {profile}")
            return
        
        # Load profile
        profiles_dir = Path.home() / ".superagent" / "profiles"
        profile_file = profiles_dir / f"{args}.json"
        
        if not profile_file.exists():
            console.print(f"[red]Profile not found: {args}[/red]")
            return
        
        try:
            with open(profile_file) as f:
                profile_data = json.load(f)
            
            # Apply profile settings
            if "model" in profile_data:
                self.runtime.config.llm_providers[0].default_model = profile_data["model"]
            if "temperature" in profile_data:
                self.runtime.config.llm_providers[0].temperature = profile_data["temperature"]
            if "max_tokens" in profile_data:
                self.runtime.config.llm_providers[0].max_tokens = profile_data["max_tokens"]
            if "system_prompt" in profile_data:
                self.runtime.config.system_prompt = profile_data["system_prompt"]
            
            self.current_profile = args
            console.print(f"[green]✓ Switched to profile: {args}[/green]")
        except Exception as e:
            console.print(f"[red]Failed to load profile: {e}[/red]")
    
    async def cmd_search(self, args: str):
        """Search conversation history."""
        if not args:
            console.print("[red]Usage: /search <query>[/red]")
            return
        
        query = args.lower()
        results = []
        
        for i, msg in enumerate(self.conversation_history):
            if query in msg["content"].lower():
                results.append((i, msg))
        
        if not results:
            console.print(f"[yellow]No results found for: {query}[/yellow]")
            return
        
        console.print(f"[cyan]Found {len(results)} result(s):[/cyan]\n")
        for i, msg in results[:10]:  # Show first 10
            role = msg["role"]
            content = msg["content"][:200]  # Truncate
            console.print(f"[dim]#{i}[/dim] [{role}]: {content}...")
            console.print()
    
    async def cmd_redo(self, args: str):
        """Resend last user message."""
        # Find last user message
        user_messages = [msg for msg in self.conversation_history if msg["role"] == "user"]
        if not user_messages:
            console.print("[yellow]No messages to redo[/yellow]")
            return
        
        last_message = user_messages[-1]["content"]
        console.print(f"[dim]Resending: {last_message}[/dim]\n")
        await self.handle_message(last_message)
    
    async def cmd_copy(self, args: str):
        """Copy response to clipboard."""
        from superagent.cli.clipboard import copy_to_clipboard
        
        n = int(args) if args.isdigit() else 1
        
        # Get last n assistant messages
        assistant_messages = [msg for msg in self.conversation_history if msg["role"] == "assistant"]
        if not assistant_messages:
            console.print("[yellow]No responses to copy[/yellow]")
            return
        
        content = assistant_messages[-n]["content"]
        
        try:
            copy_to_clipboard(content)
            console.print("[green]✓ Copied to clipboard[/green]")
        except Exception as e:
            console.print(f"[red]Failed to copy: {e}[/red]")
    
    async def cmd_edit(self, args: str):
        """Edit last message."""
        if not args:
            console.print("[red]Usage: /edit <new message>[/red]")
            return
        
        # Remove last exchange
        if len(self.conversation_history) >= 2:
            self.conversation_history = self.conversation_history[:-2]
        
        # Send new message
        await self.handle_message(args)
    
    async def cmd_branch(self, args: str):
        """Create conversation branch."""
        if not args:
            console.print("[red]Usage: /branch <name>[/red]")
            return
        
        # Save current conversation as branch
        branch_name = f"branch_{args}_{self.session_id}"
        await self.cmd_save(f"{branch_name}.json")
        console.print(f"[green]✓ Created branch: {args}[/green]")
    
    async def cmd_streaming(self, args: str):
        """Toggle streaming mode."""
        current = self.runtime.config.ui_preferences.get("streaming", True)
        
        if not args:
            status = "enabled" if current else "disabled"
            console.print(f"[cyan]Streaming is currently {status}[/cyan]")
            return
        
        if args.lower() in ["on", "true", "1"]:
            self.runtime.config.ui_preferences["streaming"] = True
            console.print("[green]✓ Streaming enabled[/green]")
        elif args.lower() in ["off", "false", "0"]:
            self.runtime.config.ui_preferences["streaming"] = False
            console.print("[green]✓ Streaming disabled[/green]")
        else:
            console.print("[red]Usage: /streaming [on|off][/red]")
    
    async def cmd_multiline(self, args: str):
        """Enter multiline input mode."""
        console.print("[cyan]Multiline mode (Ctrl+D or empty line to finish):[/cyan]")
        lines = []
        
        while True:
            try:
                line = await asyncio.to_thread(input)
                if not line:
                    break
                lines.append(line)
            except EOFError:
                break
        
        if lines:
            message = "\n".join(lines)
            await self.handle_message(message)
    
    async def cmd_file(self, args: str):
        """Attach file to message."""
        from superagent.cli.file_handler import FileHandler
        
        if not args:
            console.print("[red]Usage: /file <path> [message][/red]")
            return
        
        parts = args.split(maxsplit=1)
        filepath = Path(parts[0])
        message = parts[1] if len(parts) > 1 else ""
        
        handler = FileHandler()
        
        try:
            content = handler.read_file(filepath)
            full_message = f"{message}\n\nFile: {filepath.name}\n\`\`\`\n{content}\n\`\`\`"
            await self.handle_message(full_message)
        except Exception as e:
            console.print(f"[red]Failed to read file: {e}[/red]")
    
    async def cmd_image(self, args: str):
        """Analyze image."""
        from superagent.cli.file_handler import FileHandler
        
        if not args:
            console.print("[red]Usage: /image <path> [question][/red]")
            return
        
        parts = args.split(maxsplit=1)
        filepath = Path(parts[0])
        question = parts[1] if len(parts) > 1 else "What's in this image?"
        
        handler = FileHandler()
        
        try:
            image_data = handler.read_image(filepath)
            # TODO: Implement vision model integration
            console.print("[yellow]Image analysis requires vision model support[/yellow]")
        except Exception as e:
            console.print(f"[red]Failed to read image: {e}[/red]")
    
    async def cmd_code(self, args: str):
        """Generate code."""
        if not args:
            console.print("[red]Usage: /code <description>[/red]")
            return
        
        prompt = f"Generate code for: {args}\n\nProvide complete, production-ready code with comments."
        await self.handle_message(prompt)
    
    async def cmd_web(self, args: str):
        """Fetch content from URL."""
        if not args:
            console.print("[red]Usage: /web <url>[/red]")
            return
        
        try:
            import httpx
            
            async with httpx.AsyncClient() as client:
                response = await client.get(args, timeout=10.0)
                response.raise_for_status()
                
                content = response.text[:5000]  # Limit content
                message = f"Content from {args}:\n\n{content}"
                await self.handle_message(message)
        except Exception as e:
            console.print(f"[red]Failed to fetch URL: {e}[/red]")
    
    async def cmd_summarize(self, args: str):
        """Summarize conversation."""
        if not self.conversation_history:
            console.print("[yellow]No conversation to summarize[/yellow]")
            return
        
        # Create summary prompt
        history_text = "\n\n".join([
            f"{msg['role'].upper()}: {msg['content']}"
            for msg in self.conversation_history
        ])
        
        prompt = f"Summarize this conversation:\n\n{history_text}"
        await self.handle_message(prompt)
    
    async def cmd_continue(self, args: str):
        """Continue from last response."""
        if not self.conversation_history:
            console.print("[yellow]No conversation to continue[/yellow]")
            return
        
        await self.handle_message("Please continue from where you left off.")
    
    async def cmd_regenerate(self, args: str):
        """Regenerate last response."""
        # Remove last assistant message
        if self.conversation_history and self.conversation_history[-1]["role"] == "assistant":
            self.conversation_history.pop()
        
        # Resend last user message
        await self.cmd_redo("")
    
    # Helper methods
    async def auto_save_conversation(self):
        """Auto-save conversation if enabled."""
        if self.conversation_history and self.runtime.config.features.get("auto_save", True):
            await self.cmd_save(f"autosave_{self.session_id}.json")
    
    async def auto_load_last_conversation(self):
        """Auto-load last conversation if exists."""
        autosave_files = sorted(self.conversation_dir.glob("autosave_*.json"))
        if autosave_files:
            latest = autosave_files[-1]
            console.print(f"[dim]Loading last conversation: {latest.name}[/dim]")
            await self.cmd_load(latest.name)
