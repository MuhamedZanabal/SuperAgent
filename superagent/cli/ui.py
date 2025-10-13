"""
UI utilities for rich terminal output.
"""

from typing import Optional, Any, Dict, List
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
from rich.markdown import Markdown
from rich.syntax import Syntax
from rich.live import Live
from rich.text import Text
import time

# Global console instance
console = Console()


def print_banner():
    """Print SuperAgent banner."""
    banner = """
    ╔═══════════════════════════════════════╗
    ║                                       ║
    ║         [bold cyan]S U P E R A G E N T[/bold cyan]         ║
    ║                                       ║
    ║   [dim]AI Automation Platform[/dim]            ║
    ║                                       ║
    ╚═══════════════════════════════════════╝
    """
    console.print(banner)


def print_error(message: str):
    """Print error message."""
    console.print(f"[bold red]✗ Error:[/bold red] {message}")


def print_success(message: str):
    """Print success message."""
    console.print(f"[bold green]✓[/bold green] {message}")


def print_warning(message: str):
    """Print warning message."""
    console.print(f"[bold yellow]⚠[/bold yellow] {message}")


def print_info(message: str):
    """Print info message."""
    console.print(f"[bold blue]ℹ[/bold blue] {message}")


def create_table(
    title: str,
    columns: List[str],
    rows: List[List[Any]],
    show_header: bool = True,
) -> Table:
    """
    Create a rich table.
    
    Args:
        title: Table title
        columns: Column names
        rows: Row data
        show_header: Whether to show header
        
    Returns:
        Rich Table object
    """
    table = Table(title=title, show_header=show_header)
    
    # Add columns
    for col in columns:
        table.add_column(col, style="cyan")
    
    # Add rows
    for row in rows:
        table.add_row(*[str(cell) for cell in row])
    
    return table


def print_panel(
    content: str,
    title: Optional[str] = None,
    style: str = "cyan",
):
    """Print content in a panel."""
    console.print(Panel(content, title=title, border_style=style))


def print_markdown(content: str):
    """Print markdown content."""
    md = Markdown(content)
    console.print(md)


def print_code(
    code: str,
    language: str = "python",
    theme: str = "monokai",
):
    """Print syntax-highlighted code."""
    syntax = Syntax(code, language, theme=theme, line_numbers=True)
    console.print(syntax)


class StreamingDisplay:
    """
    Display for streaming LLM responses.
    
    Shows content as it arrives with typing effect.
    """
    
    def __init__(self, prefix: str = ""):
        """
        Initialize streaming display.
        
        Args:
            prefix: Prefix to show before content
        """
        self.prefix = prefix
        self.content = ""
        self.live = None
    
    def __enter__(self):
        """Start live display."""
        self.live = Live(
            self._render(),
            console=console,
            refresh_per_second=10,
        )
        self.live.__enter__()
        return self
    
    def __exit__(self, *args):
        """Stop live display."""
        if self.live:
            self.live.__exit__(*args)
    
    def _render(self) -> Panel:
        """Render current content."""
        text = Text()
        if self.prefix:
            text.append(self.prefix, style="bold cyan")
            text.append("\n\n")
        text.append(self.content)
        
        return Panel(
            text,
            border_style="cyan",
            title="[bold]Response[/bold]",
        )
    
    def update(self, delta: str):
        """
        Update display with new content.
        
        Args:
            delta: New content to append
        """
        self.content += delta
        if self.live:
            self.live.update(self._render())
    
    def finish(self):
        """Finish streaming and show final content."""
        if self.live:
            self.live.update(self._render())


class ProgressDisplay:
    """Display for long-running operations with progress bar."""
    
    def __init__(self, description: str = "Processing..."):
        """
        Initialize progress display.
        
        Args:
            description: Description of the operation
        """
        self.description = description
        self.progress = None
        self.task_id = None
    
    def __enter__(self):
        """Start progress display."""
        self.progress = Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            console=console,
        )
        self.progress.__enter__()
        self.task_id = self.progress.add_task(self.description, total=None)
        return self
    
    def __exit__(self, *args):
        """Stop progress display."""
        if self.progress:
            self.progress.__exit__(*args)
    
    def update(self, description: Optional[str] = None, advance: float = 1):
        """
        Update progress.
        
        Args:
            description: New description
            advance: Amount to advance progress
        """
        if self.progress and self.task_id is not None:
            if description:
                self.progress.update(self.task_id, description=description)
            self.progress.advance(self.task_id, advance)


def prompt_user(message: str, default: Optional[str] = None) -> str:
    """
    Prompt user for input.
    
    Args:
        message: Prompt message
        default: Default value
        
    Returns:
        User input
    """
    if default:
        message = f"{message} [{default}]"
    
    console.print(f"[bold cyan]?[/bold cyan] {message}: ", end="")
    response = input().strip()
    
    return response if response else (default or "")


def confirm(message: str, default: bool = False) -> bool:
    """
    Ask user for confirmation.
    
    Args:
        message: Confirmation message
        default: Default value
        
    Returns:
        True if confirmed, False otherwise
    """
    default_str = "Y/n" if default else "y/N"
    console.print(f"[bold cyan]?[/bold cyan] {message} [{default_str}]: ", end="")
    response = input().strip().lower()
    
    if not response:
        return default
    
    return response in ("y", "yes")
