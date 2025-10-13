"""
Base classes for tools and plugins.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Callable
from enum import Enum
from pydantic import BaseModel, Field


class ToolParameterType(str, Enum):
    """Types of tool parameters."""
    
    STRING = "string"
    INTEGER = "integer"
    NUMBER = "number"
    BOOLEAN = "boolean"
    ARRAY = "array"
    OBJECT = "object"


class ToolParameter(BaseModel):
    """Definition of a tool parameter."""
    
    name: str
    type: ToolParameterType
    description: str
    required: bool = True
    default: Optional[Any] = None
    enum: Optional[List[Any]] = None
    items: Optional[Dict[str, Any]] = None  # For array types
    properties: Optional[Dict[str, Any]] = None  # For object types


class ToolResult(BaseModel):
    """Result from tool execution."""
    
    success: bool
    output: Any
    error: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class BaseTool(ABC):
    """
    Abstract base class for tools.
    
    All tools must inherit from this class and implement the execute method.
    """
    
    def __init__(self):
        """Initialize the tool."""
        self._validate_definition()
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Return the tool name."""
        pass
    
    @property
    @abstractmethod
    def description(self) -> str:
        """Return the tool description."""
        pass
    
    @property
    @abstractmethod
    def parameters(self) -> List[ToolParameter]:
        """Return the tool parameters."""
        pass
    
    @abstractmethod
    async def execute(self, **kwargs: Any) -> ToolResult:
        """
        Execute the tool with given parameters.
        
        Args:
            **kwargs: Tool parameters
            
        Returns:
            ToolResult with output or error
        """
        pass
    
    def _validate_definition(self) -> None:
        """Validate tool definition."""
        if not self.name:
            raise ValueError("Tool name cannot be empty")
        if not self.description:
            raise ValueError("Tool description cannot be empty")
    
    def validate_parameters(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate and coerce parameters.
        
        Args:
            params: Parameters to validate
            
        Returns:
            Validated parameters
            
        Raises:
            ValueError: If validation fails
        """
        validated = {}
        
        for param_def in self.parameters:
            value = params.get(param_def.name)
            
            # Check required parameters
            if param_def.required and value is None:
                if param_def.default is not None:
                    value = param_def.default
                else:
                    raise ValueError(f"Required parameter missing: {param_def.name}")
            
            # Skip validation if value is None and not required
            if value is None:
                continue
            
            # Type validation
            if param_def.type == ToolParameterType.STRING:
                value = str(value)
            elif param_def.type == ToolParameterType.INTEGER:
                value = int(value)
            elif param_def.type == ToolParameterType.NUMBER:
                value = float(value)
            elif param_def.type == ToolParameterType.BOOLEAN:
                value = bool(value)
            elif param_def.type == ToolParameterType.ARRAY:
                if not isinstance(value, list):
                    raise ValueError(f"Parameter {param_def.name} must be an array")
            elif param_def.type == ToolParameterType.OBJECT:
                if not isinstance(value, dict):
                    raise ValueError(f"Parameter {param_def.name} must be an object")
            
            # Enum validation
            if param_def.enum and value not in param_def.enum:
                raise ValueError(
                    f"Parameter {param_def.name} must be one of {param_def.enum}"
                )
            
            validated[param_def.name] = value
        
        return validated
    
    def to_function_definition(self) -> Dict[str, Any]:
        """
        Convert tool to OpenAI function definition format.
        
        Returns:
            Function definition dictionary
        """
        properties = {}
        required = []
        
        for param in self.parameters:
            properties[param.name] = {
                "type": param.type.value,
                "description": param.description,
            }
            
            if param.enum:
                properties[param.name]["enum"] = param.enum
            if param.items:
                properties[param.name]["items"] = param.items
            if param.properties:
                properties[param.name]["properties"] = param.properties
            
            if param.required:
                required.append(param.name)
        
        return {
            "name": self.name,
            "description": self.description,
            "parameters": {
                "type": "object",
                "properties": properties,
                "required": required,
            },
        }
