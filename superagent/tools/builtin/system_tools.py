"""
System operation tools.
"""

from typing import List
import subprocess

from superagent.tools.base import BaseTool, ToolParameter, ToolParameterType, ToolResult
from superagent.core.logger import get_logger

logger = get_logger(__name__)


class ShellCommandTool(BaseTool):
    """Tool for executing shell commands (use with caution)."""
    
    def __init__(self, allowed_commands: List[str] = None):
        """
        Initialize shell command tool.
        
        Args:
            allowed_commands: List of allowed command prefixes
        """
        self.allowed_commands = allowed_commands or []
        super().__init__()
    
    @property
    def name(self) -> str:
        return "shell_command"
    
    @property
    def description(self) -> str:
        return "Execute a shell command"
    
    @property
    def parameters(self) -> List[ToolParameter]:
        return [
            ToolParameter(
                name="command",
                type=ToolParameterType.STRING,
                description="Shell command to execute",
                required=True,
            ),
        ]
    
    async def execute(self, command: str) -> ToolResult:
        """Execute shell command."""
        try:
            # Check if command is allowed
            if self.allowed_commands:
                allowed = any(command.startswith(cmd) for cmd in self.allowed_commands)
                if not allowed:
                    return ToolResult(
                        success=False,
                        output=None,
                        error=f"Command not allowed: {command}",
                    )
            
            # Execute command
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=30,
            )
            
            output = result.stdout if result.returncode == 0 else result.stderr
            
            return ToolResult(
                success=result.returncode == 0,
                output=output,
                metadata={
                    "return_code": result.returncode,
                    "command": command,
                },
            )
            
        except subprocess.TimeoutExpired:
            return ToolResult(
                success=False,
                output=None,
                error="Command execution timeout",
            )
        except Exception as e:
            return ToolResult(
                success=False,
                output=None,
                error=str(e),
            )
