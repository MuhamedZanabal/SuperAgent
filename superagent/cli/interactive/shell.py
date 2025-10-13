"""
Main interactive shell using Textual for modern terminal UI.
"""

import asyncio
from pathlib import Path
from typing import Optional
from datetime import datetime

from textual.app import App, ComposeResult
from textual.containers import Container, Vertical, Horizontal
from textual.widgets import Header, Footer, Input, RichLog, Static
from textual.binding import Binding
from textual import events
from rich.markdown import Markdown
from rich.panel import Panel
from rich.text import Text

from superagent.core.config import get_config, SuperAgentConfig
from superagent.core.logger import get_logger
from superagent.llm import create_default_provider
from superagent.llm.models import LLMRequest, Message
from superagent.cli.interactive.commands import CommandRegistry, CommandContext
from superagent.cli.interactive.autocomplete import AutocompleteEngine
from superagent.cli.interactive.session import SessionManager

logger = get_logger(__name__)


class InteractiveShell(App):
    """
    Interactive SuperAgent shell with slash commands and @mention support.
    
    Features:
    - Slash commands (/plan, /exec, /settings, etc.)
    - @mention file inclusion with autocomplete
    - Persistent sessions
    - Real-time streaming responses
    - Modern terminal UI
    """
    
    CSS = """
    Screen {
        background: $surface;
    }
    
    #chat-container {
        height: 1fr;
        border: solid $primary;
        background: $panel;
    }
    
    #chat-log {
        height: 1fr;
        padding: 1;
        background: $panel;
    }
    
    #input-container {
        height: auto;
        padding: 1;
        background: $surface;
    }
    
    #user-input {
        width: 100%;
    }
    
    #status-bar {
        height: 1;
        background: $primary;
        color: $text;
        padding: 0 1;
    }
    
    .user-message {
        color: $success;
    }
    
    .assistant-message {
        color: $accent;
    }
    
    .system-message {
        color: $warning;
    }
    
    .error-message {
        color: $error;
    }
    """
    
    BINDINGS = [
        Binding("ctrl+c", "quit", "Quit", show=True),
        Binding("ctrl+l", "clear", "Clear", show=True),
        Binding("ctrl+s", "save", "Save", show=True),
        Binding("ctrl+k", "command_palette", "Commands", show=True),
    ]
    
    def __init__(
        self,
        config: Optional[SuperAgentConfig] = None,
        session_id: Optional[str] = None,
    ):
        super().__init__()
        self.config = config or get_config()
        self.command_registry = CommandRegistry()
        self.autocomplete_engine = AutocompleteEngine()
        self.session_manager = SessionManager(self.config.data_dir / "sessions")
        self.session_id = session_id or self.session_manager.create_session()
        self.messages: list[Message] = []
        self.provider = None
        self.current_model = self.config.default_model
        
    def compose(self) -> ComposeResult:
        """Create child widgets."""
        yield Header(show_clock=True)
        
        with Container(id="chat-container"):
            yield RichLog(id="chat-log", highlight=True, markup=True, wrap=True)
        
        with Vertical(id="input-container"):
            yield Static(id="status-bar")
            yield Input(
                placeholder="Type a message or /command...",
                id="user-input",
            )
        
        yield Footer()
    
    async def on_mount(self) -> None:
        """Initialize shell on mount."""
        # Initialize provider
        try:
            self.provider = create_default_provider(self.config)
        except Exception as e:
            logger.error(f"Failed to initialize provider: {e}")
            self.show_error(f"Provider initialization failed: {e}")
        
        # Load session if exists
        session_data = self.session_manager.load_session(self.session_id)
        if session_data:
            self.messages = [
                Message(role=msg["role"], content=msg["content"])
                for msg in session_data.get("messages", [])
            ]
            self.current_model = session_data.get("model", self.current_model)
        
        # Show welcome message
        self.show_welcome()
        
        # Update status bar
        self.update_status()
        
        # Focus input
        self.query_one("#user-input", Input).focus()
    
    def show_welcome(self) -> None:
        """Display welcome message."""
        chat_log = self.query_one("#chat-log", RichLog)
        
        welcome_text = f"""
# Welcome to SuperAgent Interactive Shell

**Version:** {self.config.version}
**Model:** {self.current_model}
**Session:** {self.session_id[:8]}

## Available Commands:
- `/help` - Show help and available commands
- `/settings` - Open configuration wizard
- `/plan <goal>` - Create execution plan
- `/exec <command>` - Execute command or code
- `/memory` - View memory and context
- `/tools` - List available tools
- `/clear` - Clear conversation
- `/save` - Save session
- `/exit` - Exit shell

## Tips:
- Type `@` to include files in your message
- Use `Ctrl+K` for command palette
- Use `Ctrl+L` to clear screen
- Use `Ctrl+S` to save session

Start chatting or type a command!
"""
        chat_log.write(Markdown(welcome_text))
    
    def update_status(self) -> None:
        """Update status bar."""
        status_bar = self.query_one("#status-bar", Static)
        status_text = (
            f"Model: {self.current_model} | "
            f"Messages: {len(self.messages)} | "
            f"Session: {self.session_id[:8]}"
        )
        status_bar.update(status_text)
    
    async def on_input_submitted(self, event: Input.Submitted) -> None:
        """Handle user input submission."""
        user_input = event.value.strip()
        
        if not user_input:
            return
        
        # Clear input
        event.input.value = ""
        
        # Check if it's a slash command
        if user_input.startswith("/"):
            await self.handle_command(user_input)
        else:
            await self.handle_message(user_input)
    
    async def handle_command(self, command_text: str) -> None:
        """Handle slash command."""
        chat_log = self.query_one("#chat-log", RichLog)
        
        # Parse command
        parts = command_text[1:].split(maxsplit=1)
        command_name = parts[0].lower()
        command_args = parts[1] if len(parts) > 1 else ""
        
        # Show command in log
        chat_log.write(f"[bold cyan]> {command_text}[/bold cyan]")
        
        # Create command context
        context = CommandContext(
            shell=self,
            config=self.config,
            messages=self.messages,
            provider=self.provider,
            session_manager=self.session_manager,
        )
        
        # Execute command
        try:
            result = await self.command_registry.execute(
                command_name,
                command_args,
                context,
            )
            
            if result:
                chat_log.write(result)
        
        except Exception as e:
            self.show_error(f"Command failed: {e}")
    
    async def handle_message(self, user_input: str) -> None:
        """Handle regular chat message."""
        chat_log = self.query_one("#chat-log", RichLog)
        
        # Process @mentions (file inclusion)
        processed_input = await self.process_mentions(user_input)
        
        # Show user message
        chat_log.write(Panel(
            processed_input,
            title="[bold green]You[/bold green]",
            border_style="green",
        ))
        
        # Add to messages
        self.messages.append(Message(role="user", content=processed_input))
        
        # Generate response
        if not self.provider:
            self.show_error("Provider not initialized")
            return
        
        try:
            request = LLMRequest(
                model=self.current_model,
                messages=self.messages,
                temperature=self.config.temperature,
                stream=True,
            )
            
            # Show assistant header
            chat_log.write("[bold cyan]Assistant:[/bold cyan]")
            
            # Stream response
            assistant_content = ""
            async for chunk in self.provider.stream(request):
                assistant_content += chunk.delta
                # Update last line with accumulated content
                chat_log.write(chunk.delta, end="")
            
            chat_log.write("")  # New line
            
            # Add assistant message
            self.messages.append(Message(role="assistant", content=assistant_content))
            
            # Update status
            self.update_status()
            
            # Auto-save session
            await self.save_session()
        
        except Exception as e:
            self.show_error(f"Generation failed: {e}")
    
    async def process_mentions(self, text: str) -> str:
        """
        Process @mentions in text and include file contents.
        
        Args:
            text: Input text with @mentions
            
        Returns:
            Processed text with file contents included
        """
        import re
        
        # Find all @mentions
        mentions = re.findall(r'@([\w\-./]+)', text)
        
        if not mentions:
            return text
        
        # Process each mention
        processed_text = text
        for mention in mentions:
            file_path = Path(mention)
            
            if file_path.exists() and file_path.is_file():
                try:
                    # Read file content
                    content = file_path.read_text()
                    
                    # Replace mention with file content
                    file_block = f"\n\n```{file_path.suffix[1:]}\n# File: {mention}\n{content}\n```\n\n"
                    processed_text = processed_text.replace(f"@{mention}", file_block)
                
                except Exception as e:
                    logger.warning(f"Failed to read file {mention}: {e}")
        
        return processed_text
    
    def show_error(self, message: str) -> None:
        """Display error message."""
        chat_log = self.query_one("#chat-log", RichLog)
        chat_log.write(f"[bold red]Error:[/bold red] {message}")
    
    def show_info(self, message: str) -> None:
        """Display info message."""
        chat_log = self.query_one("#chat-log", RichLog)
        chat_log.write(f"[bold yellow]Info:[/bold yellow] {message}")
    
    async def save_session(self) -> None:
        """Save current session."""
        session_data = {
            "session_id": self.session_id,
            "timestamp": datetime.now().isoformat(),
            "model": self.current_model,
            "messages": [
                {"role": msg.role, "content": msg.content}
                for msg in self.messages
            ],
        }
        self.session_manager.save_session(self.session_id, session_data)
    
    def action_quit(self) -> None:
        """Quit the application."""
        asyncio.create_task(self.save_session())
        self.exit()
    
    def action_clear(self) -> None:
        """Clear chat log."""
        chat_log = self.query_one("#chat-log", RichLog)
        chat_log.clear()
        self.show_info("Chat cleared")
    
    async def action_save(self) -> None:
        """Save session."""
        await self.save_session()
        self.show_info(f"Session saved: {self.session_id}")
    
    def action_command_palette(self) -> None:
        """Show command palette."""
        # TODO: Implement command palette
        self.show_info("Command palette (coming soon)")


async def launch_interactive_shell(
    config: Optional[SuperAgentConfig] = None,
    session_id: Optional[str] = None,
) -> None:
    """
    Launch interactive shell.
    
    Args:
        config: Configuration instance
        session_id: Optional session ID to resume
    """
    app = InteractiveShell(config=config, session_id=session_id)
    await app.run_async()
