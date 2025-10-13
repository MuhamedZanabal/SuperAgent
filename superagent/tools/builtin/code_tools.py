"""
Code execution tools.
"""

from typing import List
import sys
from io import StringIO
import traceback

from superagent.tools.base import BaseTool, ToolParameter, ToolParameterType, ToolResult
from superagent.core.logger import get_logger

logger = get_logger(__name__)


class PythonExecuteTool(BaseTool):
    """Tool for executing Python code in a sandboxed environment."""
    
    @property
    def name(self) -> str:
        return "python_execute"
    
    @property
    def description(self) -> str:
        return "Execute Python code and return the output"
    
    @property
    def parameters(self) -> List[ToolParameter]:
        return [
            ToolParameter(
                name="code",
                type=ToolParameterType.STRING,
                description="Python code to execute",
                required=True,
            ),
        ]
    
    async def execute(self, code: str) -> ToolResult:
        """Execute Python code."""
        try:
            # Capture stdout
            old_stdout = sys.stdout
            sys.stdout = StringIO()
            
            # Create restricted globals
            restricted_globals = {
                "__builtins__": {
                    "print": print,
                    "len": len,
                    "range": range,
                    "str": str,
                    "int": int,
                    "float": float,
                    "bool": bool,
                    "list": list,
                    "dict": dict,
                    "set": set,
                    "tuple": tuple,
                    "sum": sum,
                    "min": min,
                    "max": max,
                    "abs": abs,
                    "round": round,
                    "sorted": sorted,
                    "enumerate": enumerate,
                    "zip": zip,
                },
            }
            
            # Execute code
            exec(code, restricted_globals)
            
            # Get output
            output = sys.stdout.getvalue()
            sys.stdout = old_stdout
            
            return ToolResult(
                success=True,
                output=output,
                metadata={"code_length": len(code)},
            )
            
        except Exception as e:
            sys.stdout = old_stdout
            error_msg = f"{type(e).__name__}: {str(e)}\n{traceback.format_exc()}"
            
            return ToolResult(
                success=False,
                output=None,
                error=error_msg,
            )
