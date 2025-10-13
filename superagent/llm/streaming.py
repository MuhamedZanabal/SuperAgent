"""
Streaming utilities for LLM responses.
"""

import asyncio
from typing import AsyncIterator, Callable, Optional, List
from dataclasses import dataclass, field

from superagent.llm.models import LLMStreamChunk, LLMResponse, Usage
from superagent.core.logger import get_logger

logger = get_logger(__name__)


@dataclass
class StreamBuffer:
    """Buffer for accumulating streamed chunks into a complete response."""
    
    id: str
    model: str
    provider: str
    content: str = ""
    role: str = "assistant"
    finish_reason: Optional[str] = None
    function_call: Optional[dict] = None
    tool_calls: Optional[List[dict]] = None
    chunks_received: int = 0
    metadata: dict = field(default_factory=dict)
    
    def add_chunk(self, chunk: LLMStreamChunk) -> None:
        """Add a chunk to the buffer."""
        self.content += chunk.delta
        self.chunks_received += 1
        
        if chunk.role:
            self.role = chunk.role
        if chunk.finish_reason:
            self.finish_reason = chunk.finish_reason
        if chunk.function_call:
            self.function_call = chunk.function_call
        if chunk.tool_calls:
            self.tool_calls = chunk.tool_calls
    
    def to_response(
        self,
        usage: Optional[Usage] = None,
        latency_ms: float = 0.0,
        cost: float = 0.0,
    ) -> LLMResponse:
        """Convert the buffer to a complete LLMResponse."""
        return LLMResponse(
            id=self.id,
            model=self.model,
            content=self.content,
            role=self.role,
            finish_reason=self.finish_reason,
            function_call=self.function_call,
            tool_calls=self.tool_calls,
            usage=usage,
            provider=self.provider,
            latency_ms=latency_ms,
            cost=cost,
            metadata={
                **self.metadata,
                "chunks_received": self.chunks_received,
            },
        )


class StreamHandler:
    """
    Handler for processing LLM stream chunks with callbacks.
    
    Allows registering callbacks for different stream events.
    """
    
    def __init__(self):
        self._on_chunk_callbacks: List[Callable[[LLMStreamChunk], None]] = []
        self._on_complete_callbacks: List[Callable[[LLMResponse], None]] = []
        self._on_error_callbacks: List[Callable[[Exception], None]] = []
    
    def on_chunk(self, callback: Callable[[LLMStreamChunk], None]) -> None:
        """Register a callback for each chunk received."""
        self._on_chunk_callbacks.append(callback)
    
    def on_complete(self, callback: Callable[[LLMResponse], None]) -> None:
        """Register a callback for when streaming completes."""
        self._on_complete_callbacks.append(callback)
    
    def on_error(self, callback: Callable[[Exception], None]) -> None:
        """Register a callback for errors during streaming."""
        self._on_error_callbacks.append(callback)
    
    async def handle_stream(
        self,
        stream: AsyncIterator[LLMStreamChunk],
        buffer: Optional[StreamBuffer] = None,
    ) -> LLMResponse:
        """
        Process a stream with registered callbacks.
        
        Args:
            stream: AsyncIterator of LLMStreamChunk objects
            buffer: Optional StreamBuffer to accumulate chunks
            
        Returns:
            Complete LLMResponse after stream finishes
            
        Raises:
            Exception: If an error occurs during streaming
        """
        if buffer is None:
            # Create buffer from first chunk
            first_chunk = await anext(stream)
            buffer = StreamBuffer(
                id=first_chunk.id,
                model=first_chunk.model,
                provider=first_chunk.provider,
            )
            buffer.add_chunk(first_chunk)
            
            # Trigger callbacks for first chunk
            for callback in self._on_chunk_callbacks:
                try:
                    callback(first_chunk)
                except Exception as e:
                    logger.error(f"Error in chunk callback: {e}")
        
        try:
            async for chunk in stream:
                buffer.add_chunk(chunk)
                
                # Trigger chunk callbacks
                for callback in self._on_chunk_callbacks:
                    try:
                        callback(chunk)
                    except Exception as e:
                        logger.error(f"Error in chunk callback: {e}")
            
            # Stream completed successfully
            response = buffer.to_response()
            
            # Trigger completion callbacks
            for callback in self._on_complete_callbacks:
                try:
                    callback(response)
                except Exception as e:
                    logger.error(f"Error in complete callback: {e}")
            
            return response
            
        except Exception as e:
            # Trigger error callbacks
            for callback in self._on_error_callbacks:
                try:
                    callback(e)
                except Exception as err:
                    logger.error(f"Error in error callback: {err}")
            raise


async def merge_streams(
    *streams: AsyncIterator[LLMStreamChunk],
) -> AsyncIterator[LLMStreamChunk]:
    """
    Merge multiple streams into a single stream.
    
    Useful for parallel generation or fallback scenarios.
    
    Args:
        *streams: Variable number of stream iterators
        
    Yields:
        LLMStreamChunk objects from all streams
    """
    queues = [asyncio.Queue() for _ in streams]
    
    async def consume_stream(stream: AsyncIterator[LLMStreamChunk], queue: asyncio.Queue):
        """Consume a stream and put chunks into a queue."""
        try:
            async for chunk in stream:
                await queue.put(chunk)
        except Exception as e:
            await queue.put(e)
        finally:
            await queue.put(None)  # Signal completion
    
    # Start consuming all streams
    tasks = [
        asyncio.create_task(consume_stream(stream, queue))
        for stream, queue in zip(streams, queues)
    ]
    
    active_queues = set(queues)
    
    try:
        while active_queues:
            # Wait for any queue to have an item
            done, pending = await asyncio.wait(
                [asyncio.create_task(q.get()) for q in active_queues],
                return_when=asyncio.FIRST_COMPLETED,
            )
            
            for task in done:
                item = task.result()
                
                if item is None:
                    # Stream completed
                    continue
                elif isinstance(item, Exception):
                    # Stream errored
                    logger.error(f"Stream error: {item}")
                    continue
                else:
                    # Valid chunk
                    yield item
    finally:
        # Cancel any remaining tasks
        for task in tasks:
            if not task.done():
                task.cancel()
