"""
Example plugin demonstrating tool creation.
"""

from typing import Dict, Any
from superagent.tools.base import BaseTool, ToolParameter, ToolResult


class GreetingTool(BaseTool):
    """Example tool that generates greetings."""
    
    name = "greeting"
    description = "Generate a personalized greeting message"
    parameters = [
        ToolParameter(
            name="name",
            type="string",
            description="Name of the person to greet",
            required=True,
        ),
        ToolParameter(
            name="style",
            type="string",
            description="Greeting style: formal, casual, or friendly",
            required=False,
        ),
    ]
    
    async def execute(self, **kwargs: Any) -> ToolResult:
        """Execute the greeting tool."""
        name = kwargs.get("name", "there")
        style = kwargs.get("style", "casual")
        
        greetings = {
            "formal": f"Good day, {name}. It is a pleasure to meet you.",
            "casual": f"Hey {name}!",
            "friendly": f"Hello {name}! How are you doing today?",
        }
        
        message = greetings.get(style, greetings["casual"])
        
        return ToolResult(
            success=True,
            output=message,
            metadata={"style": style, "name": name},
        )


class CalculatorTool(BaseTool):
    """Example calculator tool."""
    
    name = "calculator"
    description = "Perform basic arithmetic operations"
    parameters = [
        ToolParameter(
            name="operation",
            type="string",
            description="Operation: add, subtract, multiply, divide",
            required=True,
        ),
        ToolParameter(
            name="a",
            type="number",
            description="First number",
            required=True,
        ),
        ToolParameter(
            name="b",
            type="number",
            description="Second number",
            required=True,
        ),
    ]
    
    async def execute(self, **kwargs: Any) -> ToolResult:
        """Execute the calculator tool."""
        operation = kwargs.get("operation")
        a = float(kwargs.get("a", 0))
        b = float(kwargs.get("b", 0))
        
        operations = {
            "add": a + b,
            "subtract": a - b,
            "multiply": a * b,
            "divide": a / b if b != 0 else None,
        }
        
        result = operations.get(operation)
        
        if result is None:
            return ToolResult(
                success=False,
                error="Invalid operation or division by zero",
            )
        
        return ToolResult(
            success=True,
            output=str(result),
            metadata={"operation": operation, "a": a, "b": b, "result": result},
        )
