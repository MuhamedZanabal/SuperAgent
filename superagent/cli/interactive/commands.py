"""
Slash command registry and handlers.
"""

from dataclasses import dataclass
from typing import Any, Callable, Dict, Optional, TYPE_CHECKING
import inspect

if TYPE_CHECKING:
    from superagent.cli.interactive.shell import InteractiveShell
    from superagent.core.config import SuperAgentConfig
    from superagent.llm.models import Message
    from superagent.llm.base import BaseLLMProvider
    from superagent.cli.interactive.session import SessionManager


@dataclass
class CommandContext:
    """Context passed to command handlers."""
    shell: "InteractiveShell"
    config: "SuperAgentConfig"
    messages: list["Message"]
    provider: Optional["BaseLLMProvider"]
    session_manager: "SessionManager"


class Command:
    """Slash command definition."""
    
    def __init__(
        self,
        name: str,
        handler: Callable,
        description: str,
        aliases: Optional[list[str]] = None,
    ):
        self.name = name
        self.handler = handler
        self.description = description
        self.aliases = aliases or []
    
    async def execute(self, args: str, context: CommandContext) -> Any:
        """Execute command with arguments."""
        if inspect.iscoroutinefunction(self.handler):
            return await self.handler(args, context)
        return self.handler(args, context)


class CommandRegistry:
    """Registry for slash commands."""
    
    def __init__(self):
        self.commands: Dict[str, Command] = {}
        self._register_builtin_commands()
    
    def register(
        self,
        name: str,
        handler: Callable,
        description: str,
        aliases: Optional[list[str]] = None,
    ) -> None:
        """Register a new command."""
        command = Command(name, handler, description, aliases)
        self.commands[name] = command
        
        # Register aliases
        for alias in command.aliases:
            self.commands[alias] = command
    
    async def execute(
        self,
        command_name: str,
        args: str,
        context: CommandContext,
    ) -> Any:
        """Execute a command by name."""
        command = self.commands.get(command_name)
        
        if not command:
            return f"Unknown command: /{command_name}. Type /help for available commands."
        
        return await command.execute(args, context)
    
    def get_all_commands(self) -> list[Command]:
        """Get all registered commands (excluding aliases)."""
        seen = set()
        commands = []
        
        for command in self.commands.values():
            if command.name not in seen:
                commands.append(command)
                seen.add(command.name)
        
        return sorted(commands, key=lambda c: c.name)
    
    def _register_builtin_commands(self) -> None:
        """Register built-in commands."""
        
        # Help command
        async def cmd_help(args: str, ctx: CommandContext) -> str:
            """Show help and available commands."""
            from rich.table import Table
            from rich.console import Console
            from io import StringIO
            
            table = Table(title="Available Commands", show_header=True)
            table.add_column("Command", style="cyan")
            table.add_column("Description", style="white")
            
            for command in self.get_all_commands():
                aliases_str = f" ({', '.join(command.aliases)})" if command.aliases else ""
                table.add_row(f"/{command.name}{aliases_str}", command.description)
            
            # Render table to string
            console = Console(file=StringIO(), width=80)
            console.print(table)
            return console.file.getvalue()
        
        self.register("help", cmd_help, "Show help and available commands", ["h", "?"])
        
        # Settings command
        async def cmd_settings(args: str, ctx: CommandContext) -> str:
            """Open configuration wizard."""
            from superagent.cli.interactive.wizard import ConfigWizard
            
            wizard = ConfigWizard(ctx.config)
            await wizard.run()
            return "Configuration updated"
        
        self.register("settings", cmd_settings, "Open configuration wizard", ["config"])
        
        # Clear command
        async def cmd_clear(args: str, ctx: CommandContext) -> str:
            """Clear conversation history."""
            ctx.messages.clear()
            ctx.shell.query_one("#chat-log").clear()
            return "Conversation cleared"
        
        self.register("clear", cmd_clear, "Clear conversation history", ["cls"])
        
        # Exit command
        async def cmd_exit(args: str, ctx: CommandContext) -> None:
            """Exit the shell."""
            await ctx.shell.save_session()
            ctx.shell.exit()
        
        self.register("exit", cmd_exit, "Exit the shell", ["quit", "q"])
        
        # Model command
        async def cmd_model(args: str, ctx: CommandContext) -> str:
            """Change current model."""
            if not args:
                return f"Current model: {ctx.shell.current_model}"
            
            ctx.shell.current_model = args.strip()
            ctx.shell.update_status()
            return f"Model changed to: {args.strip()}"
        
        self.register("model", cmd_model, "Change current model", ["m"])
        
        # Memory command
        async def cmd_memory(args: str, ctx: CommandContext) -> str:
            """View memory and context."""
            from rich.table import Table
            from rich.console import Console
            from io import StringIO
            
            table = Table(title="Conversation Memory", show_header=True)
            table.add_column("#", style="cyan", width=4)
            table.add_column("Role", style="yellow", width=10)
            table.add_column("Content", style="white")
            
            for i, msg in enumerate(ctx.messages, 1):
                content_preview = msg.content[:100] + "..." if len(msg.content) > 100 else msg.content
                table.add_row(str(i), msg.role, content_preview)
            
            console = Console(file=StringIO(), width=100)
            console.print(table)
            return console.file.getvalue()
        
        self.register("memory", cmd_memory, "View memory and context", ["mem"])
        
        # Tools command
        async def cmd_tools(args: str, ctx: CommandContext) -> str:
            """List available tools."""
            from superagent.tools.registry import get_global_registry
            
            registry = get_global_registry()
            tools = registry.list_tools()
            
            if not tools:
                return "No tools available"
            
            from rich.table import Table
            from rich.console import Console
            from io import StringIO
            
            table = Table(title="Available Tools", show_header=True)
            table.add_column("Name", style="cyan")
            table.add_column("Description", style="white")
            
            for tool in tools:
                table.add_row(tool.name, tool.description)
            
            console = Console(file=StringIO(), width=100)
            console.print(table)
            return console.file.getvalue()
        
        self.register("tools", cmd_tools, "List available tools", ["t"])
        
        # Save command
        async def cmd_save(args: str, ctx: CommandContext) -> str:
            """Save current session."""
            await ctx.shell.save_session()
            return f"Session saved: {ctx.shell.session_id}"
        
        self.register("save", cmd_save, "Save current session", ["s"])
        
        # Monitoring commands for Phase 6.5
        
        # Plan command
        async def cmd_plan(args: str, ctx: CommandContext) -> str:
            """Create execution plan for a task."""
            if not args:
                return "Usage: /plan <task description>"
            
            from superagent.agents.advanced_planner import UnifiedAdvancedPlanner
            from superagent.agents.models import Task
            
            planner = UnifiedAdvancedPlanner()
            task = Task(
                id=f"task_{hash(args)}",
                description=args,
                type="user_request"
            )
            
            plan = await planner.create_plan(task)
            
            from rich.table import Table
            from rich.console import Console
            from io import StringIO
            
            table = Table(title=f"Execution Plan: {plan.name}", show_header=True)
            table.add_column("#", style="cyan", width=4)
            table.add_column("Step", style="yellow")
            table.add_column("Tool", style="green")
            table.add_column("Probability", style="magenta")
            
            for i, step in enumerate(plan.steps, 1):
                table.add_row(
                    str(i),
                    step.description,
                    step.tool_name or "N/A",
                    f"{step.success_probability:.0%}"
                )
            
            console = Console(file=StringIO(), width=100)
            console.print(table)
            return console.file.getvalue()
        
        self.register("plan", cmd_plan, "Create execution plan for a task", ["p"])
        
        # Execute command
        async def cmd_exec(args: str, ctx: CommandContext) -> str:
            """Execute a task autonomously."""
            if not args:
                return "Usage: /exec <task description>"
            
            from superagent.orchestration.orchestrator import RuntimeOrchestrator
            
            orchestrator = RuntimeOrchestrator()
            await orchestrator.start()
            
            result = await orchestrator.execute_goal(args)
            
            await orchestrator.stop()
            
            if result.success:
                return f"✓ Task completed successfully\n\nResult: {result.output}"
            else:
                return f"✗ Task failed: {result.error}"
        
        self.register("exec", cmd_exec, "Execute a task autonomously", ["execute", "run"])
        
        # Monitor command
        async def cmd_monitor(args: str, ctx: CommandContext) -> str:
            """Show system monitoring dashboard."""
            from superagent.monitoring.profiler import UnifiedProfiler
            from rich.table import Table
            from rich.console import Console
            from io import StringIO
            
            profiler = UnifiedProfiler()
            summary = profiler.get_summary()
            
            if "message" in summary:
                return summary["message"]
            
            console = Console(file=StringIO(), width=100)
            
            # Performance summary
            perf_table = Table(title="Performance Summary", show_header=True)
            perf_table.add_column("Metric", style="cyan")
            perf_table.add_column("Value", style="white")
            
            perf_table.add_row("Total Operations", str(summary["total_operations"]))
            perf_table.add_row("Success Rate", f"{summary['success_rate']:.1f}%")
            perf_table.add_row("Avg Duration", f"{summary['avg_duration_ms']:.0f}ms")
            perf_table.add_row("Avg CPU", f"{summary['avg_cpu_percent']:.1f}%")
            perf_table.add_row("Avg Memory", f"{summary['avg_memory_mb']:.0f}MB")
            
            console.print(perf_table)
            console.print()
            
            # Bottlenecks
            bottlenecks = profiler.get_bottlenecks()
            if bottlenecks:
                bottleneck_table = Table(title="Detected Bottlenecks", show_header=True)
                bottleneck_table.add_column("Severity", style="red")
                bottleneck_table.add_column("Operation", style="yellow")
                bottleneck_table.add_column("Issue", style="white")
                
                for b in bottlenecks[-5:]:  # Show last 5
                    bottleneck_table.add_row(b.severity, b.operation, b.issue)
                
                console.print(bottleneck_table)
            
            return console.file.getvalue()
        
        self.register("monitor", cmd_monitor, "Show system monitoring dashboard", ["mon", "stats"])
        
        # Health command
        async def cmd_health(args: str, ctx: CommandContext) -> str:
            """Check context health."""
            from superagent.orchestration.context_health import ContextHealthMonitor
            from superagent.orchestration.context_fusion import ContextFusionEngine, UnifiedContext
            from rich.table import Table
            from rich.console import Console
            from io import StringIO
            
            # Create context from current messages
            fusion = ContextFusionEngine()
            context = UnifiedContext(
                conversation_history=ctx.messages,
                memory_vectors=[],
                attached_files=[],
                active_plan=None
            )
            
            monitor = ContextHealthMonitor(fusion)
            report = await monitor.check_health(context)
            
            console = Console(file=StringIO(), width=100)
            
            # Health status
            status_color = "green" if report.is_healthy else "red" if report.status.value == "critical" else "yellow"
            console.print(f"[{status_color}]Health Status: {report.status.value.upper()}[/{status_color}]")
            console.print(f"Health Score: {report.score:.1f}/100\n")
            
            # Metrics
            metrics_table = Table(title="Context Metrics", show_header=True)
            metrics_table.add_column("Metric", style="cyan")
            metrics_table.add_column("Value", style="white")
            
            for key, value in report.metrics.items():
                if isinstance(value, float):
                    metrics_table.add_row(key, f"{value:.2f}")
                else:
                    metrics_table.add_row(key, str(value))
            
            console.print(metrics_table)
            console.print()
            
            # Issues
            if report.issues:
                issues_table = Table(title="Health Issues", show_header=True)
                issues_table.add_column("Severity", style="red")
                issues_table.add_column("Category", style="yellow")
                issues_table.add_column("Description", style="white")
                
                for issue in report.issues:
                    issues_table.add_row(issue.severity.value, issue.category, issue.description)
                
                console.print(issues_table)
            
            return console.file.getvalue()
        
        self.register("health", cmd_health, "Check context health", ["status"])
        
        # Reflect command
        async def cmd_reflect(args: str, ctx: CommandContext) -> str:
            """Show reflection insights and learned patterns."""
            from superagent.agents.reflection import AdaptiveReflectionSystem
            from rich.table import Table
            from rich.console import Console
            from io import StringIO
            
            reflection = AdaptiveReflectionSystem()
            stats = reflection.get_statistics()
            
            if "message" in stats:
                return stats["message"]
            
            console = Console(file=StringIO(), width=100)
            
            # Statistics
            stats_table = Table(title="Reflection Statistics", show_header=True)
            stats_table.add_column("Metric", style="cyan")
            stats_table.add_column("Value", style="white")
            
            stats_table.add_row("Total Executions", str(stats["total_executions"]))
            stats_table.add_row("Success Rate", f"{stats['success_rate']:.1f}%")
            stats_table.add_row("Insights Generated", str(stats["insights_generated"]))
            stats_table.add_row("Patterns Learned", str(stats["patterns_learned"]))
            
            console.print(stats_table)
            console.print()
            
            # Top recommendations
            recommendations = reflection.get_recommendations(limit=5)
            if recommendations:
                rec_table = Table(title="Top Recommendations", show_header=True)
                rec_table.add_column("Category", style="yellow")
                rec_table.add_column("Insight", style="white")
                rec_table.add_column("Confidence", style="green")
                
                for rec in recommendations:
                    rec_table.add_row(
                        rec.category,
                        rec.insight[:60] + "..." if len(rec.insight) > 60 else rec.insight,
                        f"{rec.confidence:.0%}"
                    )
                
                console.print(rec_table)
            
            return console.file.getvalue()
        
        self.register("reflect", cmd_reflect, "Show reflection insights", ["insights"])
