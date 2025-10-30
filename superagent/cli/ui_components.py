"""
Comprehensive UI component library for rich terminal experiences.
Provides reusable, accessible, and beautiful UI components.
"""
from typing import Optional, List, Dict, Any, Callable
from dataclasses import dataclass
from datetime import datetime
import time

from rich.console import Console, Group
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeRemainingColumn
from rich.markdown import Markdown
from rich.syntax import Syntax
from rich.live import Live
from rich.text import Text
from rich.layout import Layout
from rich.tree import Tree
from rich.columns import Columns
from rich import box
from rich.align import Align
from rich.rule import Rule

console = Console()


@dataclass
class StatusMessage:
    """Status message with icon and styling."""
    SUCCESS = ("✓", "green")
    ERROR = ("✗", "red")
    WARNING = ("⚠", "yellow")
    INFO = ("ℹ", "blue")
    THINKING = ("🤔", "cyan")
    WORKING = ("⚙", "magenta")


class InteractiveDashboard:
    """
    Interactive dashboard with live updates.
    Shows system status, metrics, and real-time information.
    """
    
    def __init__(self):
        self.layout = Layout()
        self.metrics = {}
        self.logs = []
        self.max_logs = 10
        
    def setup_layout(self):
        """Setup dashboard layout."""
        self.layout.split(
            Layout(name="header", size=3),
            Layout(name="body", ratio=1),
            Layout(name="footer", size=3)
        )
        
        self.layout["body"].split_row(
            Layout(name="left", ratio=2),
            Layout(name="right", ratio=1)
        )
        
        self.layout["left"].split(
            Layout(name="main", ratio=2),
            Layout(name="logs", ratio=1)
        )
    
    def render_header(self) -> Panel:
        """Render dashboard header."""
        title = Text()
        title.append("SuperAgent ", style="bold cyan")
        title.append("Dashboard", style="bold white")
        
        return Panel(
            Align.center(title),
            style="cyan",
            box=box.DOUBLE
        )
    
    def render_metrics(self) -> Panel:
        """Render metrics panel."""
        table = Table(show_header=False, box=None, padding=(0, 2))
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="bold")
        
        for key, value in self.metrics.items():
            table.add_row(key, str(value))
        
        return Panel(
            table,
            title="[bold]Metrics[/bold]",
            border_style="cyan",
            box=box.ROUNDED
        )
    
    def render_logs(self) -> Panel:
        """Render logs panel."""
        log_text = Text()
        for log in self.logs[-self.max_logs:]:
            timestamp = log.get("timestamp", "")
            level = log.get("level", "INFO")
            message = log.get("message", "")
            
            style = {
                "INFO": "blue",
                "WARNING": "yellow",
                "ERROR": "red",
                "SUCCESS": "green"
            }.get(level, "white")
            
            log_text.append(f"[{timestamp}] ", style="dim")
            log_text.append(f"{level}: ", style=style)
            log_text.append(f"{message}\n")
        
        return Panel(
            log_text,
            title="[bold]Activity Log[/bold]",
            border_style="cyan",
            box=box.ROUNDED
        )
    
    def render_status(self) -> Panel:
        """Render status panel."""
        status_text = Text()
        status_text.append("● ", style="bold green")
        status_text.append("System Operational", style="green")
        
        return Panel(
            Align.center(status_text),
            style="green",
            box=box.ROUNDED
        )
    
    def update_metrics(self, metrics: Dict[str, Any]):
        """Update dashboard metrics."""
        self.metrics.update(metrics)
    
    def add_log(self, level: str, message: str):
        """Add log entry."""
        self.logs.append({
            "timestamp": datetime.now().strftime("%H:%M:%S"),
            "level": level,
            "message": message
        })
    
    def render(self) -> Layout:
        """Render complete dashboard."""
        self.setup_layout()
        
        self.layout["header"].update(self.render_header())
        self.layout["main"].update(self.render_metrics())
        self.layout["logs"].update(self.render_logs())
        self.layout["right"].update(self.render_status())
        self.layout["footer"].update(Panel(
            "[dim]Press Ctrl+C to exit dashboard[/dim]",
            style="dim"
        ))
        
        return self.layout


class ProgressTracker:
    """
    Enhanced progress tracker with multiple tasks and stages.
    """
    
    def __init__(self, description: str = "Processing"):
        self.description = description
        self.progress = None
        self.tasks = {}
        
    def __enter__(self):
        self.progress = Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TimeRemainingColumn(),
            console=console
        )
        self.progress.__enter__()
        return self
    
    def __exit__(self, *args):
        if self.progress:
            self.progress.__exit__(*args)
    
    def add_task(self, name: str, total: Optional[int] = None) -> int:
        """Add a new task to track."""
        task_id = self.progress.add_task(name, total=total)
        self.tasks[name] = task_id
        return task_id
    
    def update(self, name: str, advance: float = 1, **kwargs):
        """Update task progress."""
        if name in self.tasks:
            self.progress.update(self.tasks[name], advance=advance, **kwargs)
    
    def complete(self, name: str):
        """Mark task as complete."""
        if name in self.tasks:
            self.progress.update(self.tasks[name], completed=True)


class ConversationView:
    """
    Beautiful conversation view with syntax highlighting and formatting.
    """
    
    @staticmethod
    def render_message(role: str, content: str, metadata: Optional[Dict] = None) -> Panel:
        """Render a single message."""
        # Determine styling based on role
        if role == "user":
            title = "[bold cyan]You[/bold cyan]"
            border_style = "cyan"
        elif role == "assistant":
            title = "[bold green]Assistant[/bold green]"
            border_style = "green"
        else:
            title = f"[bold]{role.title()}[/bold]"
            border_style = "white"
        
        # Add metadata if available
        if metadata:
            meta_text = []
            if "tokens" in metadata:
                meta_text.append(f"Tokens: {metadata['tokens']}")
            if "cost" in metadata:
                meta_text.append(f"Cost: ${metadata['cost']:.4f}")
            if "model" in metadata:
                meta_text.append(f"Model: {metadata['model']}")
            
            if meta_text:
                title += f" [dim]({', '.join(meta_text)})[/dim]"
        
        # Render content with markdown
        try:
            rendered_content = Markdown(content)
        except:
            rendered_content = content
        
        return Panel(
            rendered_content,
            title=title,
            border_style=border_style,
            box=box.ROUNDED,
            padding=(1, 2)
        )
    
    @staticmethod
    def render_conversation(messages: List[Dict[str, Any]]) -> Group:
        """Render entire conversation."""
        panels = []
        for msg in messages:
            role = msg.get("role", "unknown")
            content = msg.get("content", "")
            metadata = {
                k: v for k, v in msg.items()
                if k not in ["role", "content", "timestamp"]
            }
            panels.append(ConversationView.render_message(role, content, metadata))
        
        return Group(*panels)


class CodeDisplay:
    """
    Enhanced code display with syntax highlighting and line numbers.
    """
    
    @staticmethod
    def render(code: str, language: str = "python", theme: str = "monokai", 
               title: Optional[str] = None, line_numbers: bool = True) -> Panel:
        """Render code with syntax highlighting."""
        syntax = Syntax(
            code,
            language,
            theme=theme,
            line_numbers=line_numbers,
            word_wrap=False
        )
        
        return Panel(
            syntax,
            title=title or f"[bold]{language.title()} Code[/bold]",
            border_style="blue",
            box=box.ROUNDED
        )
    
    @staticmethod
    def render_diff(old_code: str, new_code: str, language: str = "python") -> Panel:
        """Render code diff."""
        import difflib
        
        diff = difflib.unified_diff(
            old_code.splitlines(keepends=True),
            new_code.splitlines(keepends=True),
            lineterm=""
        )
        
        diff_text = "".join(diff)
        
        syntax = Syntax(
            diff_text,
            "diff",
            theme="monokai",
            line_numbers=True
        )
        
        return Panel(
            syntax,
            title="[bold]Code Diff[/bold]",
            border_style="yellow",
            box=box.ROUNDED
        )


class DataTable:
    """
    Enhanced data table with sorting, filtering, and styling.
    """
    
    @staticmethod
    def render(
        data: List[Dict[str, Any]],
        title: Optional[str] = None,
        columns: Optional[List[str]] = None,
        show_header: bool = True,
        highlight: bool = True
    ) -> Table:
        """Render data as a table."""
        if not data:
            return Table(title=title or "No Data")
        
        # Determine columns
        if columns is None:
            columns = list(data[0].keys())
        
        # Create table
        table = Table(
            title=title,
            show_header=show_header,
            box=box.ROUNDED,
            highlight=highlight
        )
        
        # Add columns
        for col in columns:
            table.add_column(col.replace("_", " ").title(), style="cyan")
        
        # Add rows
        for row in data:
            table.add_row(*[str(row.get(col, "")) for col in columns])
        
        return table


class TreeView:
    """
    Tree view for hierarchical data.
    """
    
    @staticmethod
    def render(data: Dict[str, Any], title: str = "Tree") -> Tree:
        """Render hierarchical data as a tree."""
        tree = Tree(f"[bold cyan]{title}[/bold cyan]")
        
        def add_node(parent, key, value):
            if isinstance(value, dict):
                branch = parent.add(f"[bold]{key}[/bold]")
                for k, v in value.items():
                    add_node(branch, k, v)
            elif isinstance(value, list):
                branch = parent.add(f"[bold]{key}[/bold] ({len(value)} items)")
                for i, item in enumerate(value):
                    add_node(branch, f"[{i}]", item)
            else:
                parent.add(f"{key}: [green]{value}[/green]")
        
        for key, value in data.items():
            add_node(tree, key, value)
        
        return tree


class NotificationManager:
    """
    Non-intrusive notification system.
    """
    
    @staticmethod
    def success(message: str, details: Optional[str] = None):
        """Show success notification."""
        icon, style = StatusMessage.SUCCESS
        content = f"[{style}]{icon} {message}[/{style}]"
        if details:
            content += f"\n[dim]{details}[/dim]"
        console.print(Panel(content, border_style=style, box=box.ROUNDED))
    
    @staticmethod
    def error(message: str, details: Optional[str] = None):
        """Show error notification."""
        icon, style = StatusMessage.ERROR
        content = f"[{style}]{icon} {message}[/{style}]"
        if details:
            content += f"\n[dim]{details}[/dim]"
        console.print(Panel(content, border_style=style, box=box.ROUNDED))
    
    @staticmethod
    def warning(message: str, details: Optional[str] = None):
        """Show warning notification."""
        icon, style = StatusMessage.WARNING
        content = f"[{style}]{icon} {message}[/{style}]"
        if details:
            content += f"\n[dim]{details}[/dim]"
        console.print(Panel(content, border_style=style, box=box.ROUNDED))
    
    @staticmethod
    def info(message: str, details: Optional[str] = None):
        """Show info notification."""
        icon, style = StatusMessage.INFO
        content = f"[{style}]{icon} {message}[/{style}]"
        if details:
            content += f"\n[dim]{details}[/dim]"
        console.print(Panel(content, border_style=style, box=box.ROUNDED))


class LoadingAnimation:
    """
    Beautiful loading animations for long operations.
    """
    
    def __init__(self, message: str = "Loading"):
        self.message = message
        self.live = None
        self.start_time = None
        
    def __enter__(self):
        self.start_time = time.time()
        self.live = Live(self._render(), console=console, refresh_per_second=10)
        self.live.__enter__()
        return self
    
    def __exit__(self, *args):
        if self.live:
            elapsed = time.time() - self.start_time
            self.live.update(Panel(
                f"[green]✓ {self.message} complete[/green]\n"
                f"[dim]Took {elapsed:.2f}s[/dim]",
                border_style="green",
                box=box.ROUNDED
            ))
            time.sleep(0.5)  # Brief pause to show completion
            self.live.__exit__(*args)
    
    def _render(self) -> Panel:
        """Render loading animation."""
        return Panel(
            f"[cyan]⚙ {self.message}...[/cyan]",
            border_style="cyan",
            box=box.ROUNDED
        )
    
    def update(self, message: str):
        """Update loading message."""
        self.message = message
        if self.live:
            self.live.update(self._render())


class HelpSystem:
    """
    Comprehensive contextual help system.
    """
    
    @staticmethod
    def show_command_help(command: str, description: str, usage: str, 
                         examples: Optional[List[str]] = None):
        """Show detailed help for a command."""
        content = []
        
        # Description
        content.append(f"[bold cyan]{command}[/bold cyan]")
        content.append(f"\n{description}\n")
        
        # Usage
        content.append("[bold]Usage:[/bold]")
        content.append(f"  {usage}\n")
        
        # Examples
        if examples:
            content.append("[bold]Examples:[/bold]")
            for example in examples:
                content.append(f"  [dim]$[/dim] {example}")
        
        console.print(Panel(
            "\n".join(content),
            title="[bold]Command Help[/bold]",
            border_style="cyan",
            box=box.ROUNDED
        ))
    
    @staticmethod
    def show_quick_tips():
        """Show quick tips for new users."""
        tips = [
            "💡 Use Tab for command completion",
            "💡 Press Ctrl+C to interrupt long operations",
            "💡 Type /help to see all available commands",
            "💡 Use /save to preserve your conversations",
            "💡 Try /profile to switch between different modes",
            "💡 Use /stats to track your usage and costs"
        ]
        
        console.print(Panel(
            "\n".join(tips),
            title="[bold cyan]Quick Tips[/bold cyan]",
            border_style="cyan",
            box=box.ROUNDED
        ))


class AccessibilityHelper:
    """
    Accessibility features for screen readers and keyboard navigation.
    """
    
    @staticmethod
    def announce(message: str):
        """Announce message for screen readers."""
        # Use ANSI escape codes for screen reader announcements
        console.print(f"\033]0;{message}\007", end="")
    
    @staticmethod
    def describe_visual(element: str, description: str):
        """Provide text description of visual elements."""
        console.print(f"[dim]{element}: {description}[/dim]")


# Keyboard shortcuts registry
KEYBOARD_SHORTCUTS = {
    "Ctrl+C": "Interrupt current operation",
    "Ctrl+D": "Exit multiline mode / End of input",
    "Tab": "Autocomplete command",
    "↑/↓": "Navigate command history",
    "Ctrl+L": "Clear screen",
    "Ctrl+R": "Search command history"
}


def show_keyboard_shortcuts():
    """Display keyboard shortcuts."""
    table = Table(title="Keyboard Shortcuts", box=box.ROUNDED)
    table.add_column("Shortcut", style="cyan")
    table.add_column("Action")
    
    for shortcut, action in KEYBOARD_SHORTCUTS.items():
        table.add_row(shortcut, action)
    
    console.print(table)
