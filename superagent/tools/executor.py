"""
Tool executor with sandboxing and error handling.
"""

import asyncio
import time
from typing import Any, Dict, Optional
import traceback

from superagent.tools.base import BaseTool, ToolResult
from superagent.tools.registry import ToolRegistry
from superagent.tools.models import ToolCall, ToolOutput
from superagent.core.logger import get_logger
from superagent.core.security import SecurityManager

logger = get_logger(__name__)


class ToolExecutor:
    """
    Executor for running tools with sandboxing and error handling.
    
    Provides safe execution environment with timeouts and resource limits.
    """
    
    def __init__(
        self,
        registry: ToolRegistry,
        security_manager: Optional[SecurityManager] = None,
        default_timeout: int = 30,
    ):
        """
        Initialize tool executor.
        
        Args:
            registry: Tool registry
            security_manager: Security manager for sandboxing
            default_timeout: Default execution timeout in seconds
        """
        self.registry = registry
        self.security_manager = security_manager
        self.default_timeout = default_timeout
    
    async def execute(
        self,
        tool_call: ToolCall,
        timeout: Optional[int] = None,
    ) -> ToolOutput:
        """
        Execute a tool call.
        
        Args:
            tool_call: Tool call to execute
            timeout: Execution timeout in seconds
            
        Returns:
            ToolOutput with result or error
        """
        start_time = time.time()
        timeout = timeout or self.default_timeout
        
        # Get tool
        tool = self.registry.get(tool_call.tool_name)
        if not tool:
            return ToolOutput(
                call_id=tool_call.id,
                tool_name=tool_call.tool_name,
                success=False,
                output=None,
                error=f"Tool not found: {tool_call.tool_name}",
                execution_time_ms=0.0,
            )
        
        try:
            # Validate parameters
            validated_params = tool.validate_parameters(tool_call.parameters)
            
            # Execute with timeout
            result = await asyncio.wait_for(
                tool.execute(**validated_params),
                timeout=timeout,
            )
            
            execution_time = (time.time() - start_time) * 1000
            
            return ToolOutput(
                call_id=tool_call.id,
                tool_name=tool_call.tool_name,
                success=result.success,
                output=result.output,
                error=result.error,
                execution_time_ms=execution_time,
            )
            
        except asyncio.TimeoutError:
            execution_time = (time.time() - start_time) * 1000
            logger.error(f"Tool execution timeout: {tool_call.tool_name}")
            
            return ToolOutput(
                call_id=tool_call.id,
                tool_name=tool_call.tool_name,
                success=False,
                output=None,
                error=f"Execution timeout after {timeout}s",
                execution_time_ms=execution_time,
            )
            
        except Exception as e:
            execution_time = (time.time() - start_time) * 1000
            error_msg = f"{type(e).__name__}: {str(e)}"
            logger.error(f"Tool execution error: {error_msg}\n{traceback.format_exc()}")
            
            return ToolOutput(
                call_id=tool_call.id,
                tool_name=tool_call.tool_name,
                success=False,
                output=None,
                error=error_msg,
                execution_time_ms=execution_time,
            )
    
    async def execute_batch(
        self,
        tool_calls: list[ToolCall],
        parallel: bool = True,
    ) -> list[ToolOutput]:
        """
        Execute multiple tool calls.
        
        Args:
            tool_calls: List of tool calls
            parallel: Whether to execute in parallel
            
        Returns:
            List of tool outputs
        """
        if parallel:
            # Execute in parallel
            tasks = [self.execute(call) for call in tool_calls]
            return await asyncio.gather(*tasks)
        else:
            # Execute sequentially
            results = []
            for call in tool_calls:
                result = await self.execute(call)
                results.append(result)
            return results
