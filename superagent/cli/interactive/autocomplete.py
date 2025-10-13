"""
Autocomplete engine for files and commands.
"""

from pathlib import Path
from typing import List, Optional
import os


class AutocompleteEngine:
    """
    Autocomplete engine for file paths and commands.
    
    Provides intelligent autocomplete suggestions for:
    - File paths when typing @
    - Slash commands when typing /
    """
    
    def __init__(self, base_path: Optional[Path] = None):
        self.base_path = base_path or Path.cwd()
    
    def get_file_suggestions(self, partial: str, max_results: int = 10) -> List[str]:
        """
        Get file path suggestions for partial input.
        
        Args:
            partial: Partial file path
            max_results: Maximum number of results
            
        Returns:
            List of matching file paths
        """
        try:
            # Handle absolute vs relative paths
            if partial.startswith("/"):
                search_path = Path(partial)
            else:
                search_path = self.base_path / partial
            
            # Get parent directory and filename pattern
            if search_path.is_dir():
                parent_dir = search_path
                pattern = "*"
            else:
                parent_dir = search_path.parent
                pattern = f"{search_path.name}*"
            
            # Find matching files
            matches = []
            if parent_dir.exists():
                for item in parent_dir.glob(pattern):
                    # Skip hidden files unless explicitly requested
                    if not partial.startswith(".") and item.name.startswith("."):
                        continue
                    
                    # Get relative path
                    try:
                        rel_path = item.relative_to(self.base_path)
                    except ValueError:
                        rel_path = item
                    
                    matches.append(str(rel_path))
                    
                    if len(matches) >= max_results:
                        break
            
            return sorted(matches)
        
        except Exception:
            return []
    
    def get_command_suggestions(self, partial: str, commands: List[str]) -> List[str]:
        """
        Get command suggestions for partial input.
        
        Args:
            partial: Partial command name
            commands: List of available commands
            
        Returns:
            List of matching commands
        """
        partial_lower = partial.lower()
        return [
            cmd for cmd in commands
            if cmd.lower().startswith(partial_lower)
        ]
