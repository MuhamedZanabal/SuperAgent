"""
Compatibility shims for Python 3.10+.
"""

from enum import Enum

try:
    from enum import StrEnum  # Python 3.11+
except ImportError:
    # Python 3.10 shim
    class StrEnum(str, Enum):
        """String enumeration for Python 3.10 compatibility."""
        
        def __str__(self) -> str:
            return str(self.value)
        
        def __repr__(self) -> str:
            return f"{self.__class__.__name__}.{self.name}"


__all__ = ["StrEnum"]
