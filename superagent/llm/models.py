"""
Pydantic models for LLM requests and responses.
"""

from typing import Any, Dict, List, Literal, Optional, Union
from pydantic import BaseModel, Field, field_validator
from datetime import datetime


class Message(BaseModel):
    """A single message in a conversation."""
    
    role: Literal["system", "user", "assistant", "function", "tool"]
    content: Union[str, List[Dict[str, Any]]]
    name: Optional[str] = None
    function_call: Optional[Dict[str, Any]] = None
    tool_calls: Optional[List[Dict[str, Any]]] = None


class FunctionDefinition(BaseModel):
    """Definition of a function that can be called by the LLM."""
    
    name: str
    description: str
    parameters: Dict[str, Any]


class ToolDefinition(BaseModel):
    """Definition of a tool that can be used by the LLM."""
    
    type: Literal["function"] = "function"
    function: FunctionDefinition


class LLMRequest(BaseModel):
    """Request to an LLM provider."""
    
    model: str
    messages: List[Message]
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    max_tokens: Optional[int] = Field(default=None, gt=0)
    top_p: float = Field(default=1.0, ge=0.0, le=1.0)
    frequency_penalty: float = Field(default=0.0, ge=-2.0, le=2.0)
    presence_penalty: float = Field(default=0.0, ge=-2.0, le=2.0)
    stop: Optional[Union[str, List[str]]] = None
    stream: bool = False
    functions: Optional[List[FunctionDefinition]] = None
    tools: Optional[List[ToolDefinition]] = None
    tool_choice: Optional[Union[str, Dict[str, Any]]] = None
    response_format: Optional[Dict[str, str]] = None
    seed: Optional[int] = None
    user: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    @field_validator("stop")
    @classmethod
    def validate_stop(cls, v):
        """Ensure stop is a list if provided."""
        if v is not None and isinstance(v, str):
            return [v]
        return v


class Usage(BaseModel):
    """Token usage information."""
    
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int


class LLMResponse(BaseModel):
    """Response from an LLM provider."""
    
    id: str
    model: str
    content: str
    role: Literal["assistant"] = "assistant"
    finish_reason: Optional[str] = None
    function_call: Optional[Dict[str, Any]] = None
    tool_calls: Optional[List[Dict[str, Any]]] = None
    usage: Optional[Usage] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    provider: str
    latency_ms: float = 0.0
    cost: float = 0.0
    metadata: Dict[str, Any] = Field(default_factory=dict)


class LLMStreamChunk(BaseModel):
    """A chunk of streamed response from an LLM."""
    
    id: str
    model: str
    delta: str
    role: Optional[Literal["assistant"]] = None
    finish_reason: Optional[str] = None
    function_call: Optional[Dict[str, Any]] = None
    tool_calls: Optional[List[Dict[str, Any]]] = None
    provider: str
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ModelInfo(BaseModel):
    """Information about an LLM model."""
    
    id: str
    provider: str
    context_window: int
    max_output_tokens: int
    supports_streaming: bool = True
    supports_functions: bool = False
    supports_vision: bool = False
    supports_json_mode: bool = False
    input_cost_per_1k: float = 0.0
    output_cost_per_1k: float = 0.0
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ProviderConfig(BaseModel):
    """Configuration for an LLM provider."""
    
    name: str
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    models: List[str] = Field(default_factory=list)
    priority: int = 0
    enabled: bool = True
    timeout: int = 60
    max_retries: int = 3
    rate_limit: Optional[int] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
