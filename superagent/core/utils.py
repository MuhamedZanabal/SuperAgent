"""
Common utility functions for system operations, serialization,
hashing, and async helpers.
"""

import asyncio
import hashlib
import json
import uuid
from datetime import datetime
from functools import wraps
from typing import Any, Callable, Optional, TypeVar, ParamSpec
from pathlib import Path

from superagent.core.logger import get_logger

logger = get_logger(__name__)

P = ParamSpec("P")
T = TypeVar("T")


def generate_id(prefix: str = "") -> str:
    """
    Generate unique identifier.
    
    Args:
        prefix: Optional prefix for the ID
        
    Returns:
        Unique identifier string
    """
    unique_id = str(uuid.uuid4())
    return f"{prefix}{unique_id}" if prefix else unique_id


def hash_string(text: str, algorithm: str = "sha256") -> str:
    """
    Generate hash of string.
    
    Args:
        text: Text to hash
        algorithm: Hash algorithm (sha256, md5, etc.)
        
    Returns:
        Hex digest of hash
    """
    hasher = hashlib.new(algorithm)
    hasher.update(text.encode("utf-8"))
    return hasher.hexdigest()


def safe_json_loads(text: str, default: Any = None) -> Any:
    """
    Safely parse JSON with fallback.
    
    Args:
        text: JSON string to parse
        default: Default value if parsing fails
        
    Returns:
        Parsed JSON or default value
    """
    try:
        return json.loads(text)
    except (json.JSONDecodeError, TypeError) as e:
        logger.warning(f"Failed to parse JSON: {e}", extra={"text": text[:100]})
        return default


def safe_json_dumps(obj: Any, default: Any = None, **kwargs: Any) -> str:
    """
    Safely serialize object to JSON.
    
    Args:
        obj: Object to serialize
        default: Default serializer for non-serializable objects
        **kwargs: Additional arguments for json.dumps
        
    Returns:
        JSON string
    """
    try:
        return json.dumps(obj, default=default, **kwargs)
    except (TypeError, ValueError) as e:
        logger.warning(f"Failed to serialize to JSON: {e}")
        return "{}"


def timestamp_iso() -> str:
    """
    Get current timestamp in ISO format.
    
    Returns:
        ISO formatted timestamp string
    """
    return datetime.utcnow().isoformat()


def read_file_safe(path: Path, encoding: str = "utf-8") -> Optional[str]:
    """
    Safely read file contents.
    
    Args:
        path: File path
        encoding: File encoding
        
    Returns:
        File contents or None if error
    """
    try:
        return path.read_text(encoding=encoding)
    except Exception as e:
        logger.error(f"Failed to read file {path}: {e}")
        return None


def write_file_safe(path: Path, content: str, encoding: str = "utf-8") -> bool:
    """
    Safely write content to file.
    
    Args:
        path: File path
        content: Content to write
        encoding: File encoding
        
    Returns:
        True if successful, False otherwise
    """
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding=encoding)
        return True
    except Exception as e:
        logger.error(f"Failed to write file {path}: {e}")
        return False


def async_retry(
    max_attempts: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
    exceptions: tuple[type[Exception], ...] = (Exception,),
) -> Callable[[Callable[P, T]], Callable[P, T]]:
    """
    Decorator for async functions with retry logic.
    
    Args:
        max_attempts: Maximum number of retry attempts
        delay: Initial delay between retries in seconds
        backoff: Backoff multiplier for delay
        exceptions: Tuple of exceptions to catch and retry
        
    Returns:
        Decorated function with retry logic
    """
    def decorator(func: Callable[P, T]) -> Callable[P, T]:
        @wraps(func)
        async def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
            current_delay = delay
            last_exception = None
            
            for attempt in range(max_attempts):
                try:
                    return await func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt < max_attempts - 1:
                        logger.warning(
                            f"Attempt {attempt + 1}/{max_attempts} failed: {e}. "
                            f"Retrying in {current_delay}s...",
                            extra={"function": func.__name__, "attempt": attempt + 1}
                        )
                        await asyncio.sleep(current_delay)
                        current_delay *= backoff
                    else:
                        logger.error(
                            f"All {max_attempts} attempts failed for {func.__name__}",
                            extra={"function": func.__name__}
                        )
            
            raise last_exception  # type: ignore
        
        return wrapper  # type: ignore
    
    return decorator


async def run_with_timeout(
    coro: Callable[P, T],
    timeout: float,
    *args: P.args,
    **kwargs: P.kwargs
) -> Optional[T]:
    """
    Run coroutine with timeout.
    
    Args:
        coro: Coroutine function to run
        timeout: Timeout in seconds
        *args: Positional arguments for coroutine
        **kwargs: Keyword arguments for coroutine
        
    Returns:
        Result of coroutine or None if timeout
    """
    try:
        return await asyncio.wait_for(coro(*args, **kwargs), timeout=timeout)
    except asyncio.TimeoutError:
        logger.warning(f"Operation timed out after {timeout}s", extra={"function": coro.__name__})
        return None
