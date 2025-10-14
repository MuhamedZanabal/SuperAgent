"""
Path trust and validation for secure file operations.
"""

from pathlib import Path
from typing import List, Optional
import os

from superagent.core.logger import get_logger

logger = get_logger(__name__)


class PathTrustManager:
    """
    Manages trusted paths and validates file operations.
    
    Prevents path traversal, symlink escapes, and unauthorized access.
    """
    
    def __init__(self, trusted_roots: Optional[List[str]] = None):
        """
        Initialize path trust manager.
        
        Args:
            trusted_roots: List of trusted root directories
        """
        self.trusted_roots = [Path(r).resolve() for r in (trusted_roots or [])]
        
        # Add current working directory by default
        if not self.trusted_roots:
            self.trusted_roots.append(Path.cwd().resolve())
        
        logger.info(f"Initialized path trust with {len(self.trusted_roots)} roots")
    
    def is_trusted_path(self, target: str) -> bool:
        """
        Check if a path is within trusted roots.
        
        Args:
            target: Path to check
            
        Returns:
            True if path is trusted, False otherwise
        """
        try:
            target_path = Path(target).resolve()
            
            # Check if path is within any trusted root
            for root in self.trusted_roots:
                try:
                    target_path.relative_to(root)
                    return True
                except ValueError:
                    continue
            
            return False
            
        except Exception as e:
            logger.warning(f"Path validation error for {target}: {e}")
            return False
    
    def validate_path(self, target: str, operation: str = "access") -> Path:
        """
        Validate and normalize a path.
        
        Args:
            target: Path to validate
            operation: Operation being performed (for logging)
            
        Returns:
            Resolved Path object
            
        Raises:
            ValueError: If path is not trusted
        """
        if not self.is_trusted_path(target):
            raise ValueError(
                f"Path not trusted for {operation}: {target}. "
                f"Trusted roots: {[str(r) for r in self.trusted_roots]}"
            )
        
        return Path(target).resolve()
    
    def add_trusted_root(self, root: str) -> None:
        """
        Add a trusted root directory.
        
        Args:
            root: Root directory to trust
        """
        root_path = Path(root).resolve()
        if root_path not in self.trusted_roots:
            self.trusted_roots.append(root_path)
            logger.info(f"Added trusted root: {root_path}")
    
    def remove_trusted_root(self, root: str) -> None:
        """
        Remove a trusted root directory.
        
        Args:
            root: Root directory to remove
        """
        root_path = Path(root).resolve()
        if root_path in self.trusted_roots:
            self.trusted_roots.remove(root_path)
            logger.info(f"Removed trusted root: {root_path}")


def is_trusted_path(target: str, roots: List[str]) -> bool:
    """
    Check if a path is within trusted roots (standalone function).
    
    Args:
        target: Path to check
        roots: List of trusted root directories
        
    Returns:
        True if path is trusted, False otherwise
    """
    manager = PathTrustManager(roots)
    return manager.is_trusted_path(target)
