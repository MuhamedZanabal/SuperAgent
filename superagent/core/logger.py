"""
Unified structured logging system with JSON output, color console formatting,
and contextual metadata support.
"""

import logging
import sys
from pathlib import Path
from typing import Any, Dict, Optional
from datetime import datetime
import json

from rich.console import Console
from rich.logging import RichHandler
from rich.theme import Theme

from superagent.core.config import get_config, LogLevel


# Custom theme for rich console
SUPERAGENT_THEME = Theme({
    "info": "cyan",
    "warning": "yellow",
    "error": "red bold",
    "critical": "red bold reverse",
    "success": "green bold",
    "debug": "dim",
})

console = Console(theme=SUPERAGENT_THEME)


class StructuredFormatter(logging.Formatter):
    """JSON formatter for structured logging."""
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON."""
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        
        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        
        # Add extra fields
        if hasattr(record, "extra_fields"):
            log_data.update(record.extra_fields)
        
        return json.dumps(log_data)


class SuperAgentLogger(logging.LoggerAdapter):
    """
    Enhanced logger with contextual metadata support.
    
    Allows adding persistent context to all log messages from this logger instance.
    """
    
    def __init__(self, logger: logging.Logger, extra: Optional[Dict[str, Any]] = None):
        """
        Initialize logger adapter.
        
        Args:
            logger: Base logger instance
            extra: Additional context to include in all log messages
        """
        super().__init__(logger, extra or {})
    
    def process(self, msg: str, kwargs: Dict[str, Any]) -> tuple[str, Dict[str, Any]]:
        """
        Process log message and add context.
        
        Args:
            msg: Log message
            kwargs: Additional keyword arguments
            
        Returns:
            Tuple of (message, kwargs) with context added
        """
        # Merge extra context
        extra_fields = {**self.extra}
        if "extra" in kwargs:
            extra_fields.update(kwargs["extra"])
        
        # Create new record with extra fields
        if extra_fields:
            kwargs["extra"] = {"extra_fields": extra_fields}
        
        return msg, kwargs
    
    def with_context(self, **context: Any) -> "SuperAgentLogger":
        """
        Create new logger with additional context.
        
        Args:
            **context: Additional context fields
            
        Returns:
            New logger instance with merged context
        """
        merged_context = {**self.extra, **context}
        return SuperAgentLogger(self.logger, merged_context)


def setup_logging(
    log_level: Optional[LogLevel] = None,
    log_file: Optional[Path] = None,
    json_output: bool = False,
) -> None:
    """
    Configure logging system.
    
    Args:
        log_level: Logging level (defaults to config value)
        log_file: Optional file path for log output
        json_output: Use JSON formatting instead of rich console
    """
    config = get_config()
    level = log_level or config.log_level
    
    # Clear existing handlers
    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    root_logger.setLevel(level.value)
    
    # Console handler
    if json_output:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(StructuredFormatter())
    else:
        console_handler = RichHandler(
            console=console,
            rich_tracebacks=True,
            tracebacks_show_locals=config.debug,
            show_time=True,
            show_path=config.debug,
        )
    
    console_handler.setLevel(level.value)
    root_logger.addHandler(console_handler)
    
    # File handler (JSON format)
    if log_file:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(StructuredFormatter())
        file_handler.setLevel(level.value)
        root_logger.addHandler(file_handler)
    elif config.logs_dir:
        # Default log file
        log_file = config.logs_dir / f"superagent_{datetime.now().strftime('%Y%m%d')}.log"
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(StructuredFormatter())
        file_handler.setLevel(level.value)
        root_logger.addHandler(file_handler)


def get_logger(name: str, **context: Any) -> SuperAgentLogger:
    """
    Get logger instance with optional context.
    
    Args:
        name: Logger name (typically __name__)
        **context: Additional context fields
        
    Returns:
        SuperAgentLogger instance
    """
    base_logger = logging.getLogger(name)
    return SuperAgentLogger(base_logger, context)
