"""
Pydantic models for tool system.
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from datetime import datetime


class ToolDefinition(BaseModel):
    """Definition of a tool."""
    
    name: str
    description: str
    parameters: Dict[str, Any]
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ToolCall(BaseModel):
    """A call to a tool."""
    
    id: str
    tool_name: str
    parameters: Dict[str, Any]
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class ToolOutput(BaseModel):
    """Output from a tool execution."""
    
    call_id: str
    tool_name: str
    success: bool
    output: Any
    error: Optional[str] = None
    execution_time_ms: float = 0.0
    timestamp: datetime = Field(default_factory=datetime.utcnow)
