"""
File operation tools.
"""

from typing import List
from pathlib import Path
from superagent.core.security import SecurityManager, Permission
from superagent.tools.base import BaseTool, ToolParameter, ToolParameterType, ToolResult
from superagent.core.logger import get_logger

logger = get_logger(__name__)


class ReadFileTool(BaseTool):
    """Tool for reading file contents."""
    
    def __init__(self, security_manager: SecurityManager):
        self.security_manager = security_manager
        super().__init__()
    
    @property
    def name(self) -> str:
        return "read_file"
    
    @property
    def description(self) -> str:
        return "Read contents of a file"
    
    @property
    def parameters(self) -> List[ToolParameter]:
        return [
            ToolParameter(
                name="path",
                type=ToolParameterType.STRING,
                description="Path to the file to read",
                required=True,
            ),
        ]
    
    async def execute(self, path: str) -> ToolResult:
        """Read file contents."""
        try:
            file_path = Path(path)
            
            self.security_manager.validate_file_access(file_path, Permission.READ)
            
            # Read file
            content = file_path.read_text()
            
            return ToolResult(
                success=True,
                output=content,
                metadata={"path": str(file_path), "size": len(content)},
            )
            
        except Exception as e:
            return ToolResult(
                success=False,
                output=None,
                error=str(e),
            )


class WriteFileTool(BaseTool):
    """Tool for writing file contents."""
    
    def __init__(self, security_manager: SecurityManager):
        self.security_manager = security_manager
        super().__init__()
    
    @property
    def name(self) -> str:
        return "write_file"
    
    @property
    def description(self) -> str:
        return "Write contents to a file"
    
    @property
    def parameters(self) -> List[ToolParameter]:
        return [
            ToolParameter(
                name="path",
                type=ToolParameterType.STRING,
                description="Path to the file to write",
                required=True,
            ),
            ToolParameter(
                name="content",
                type=ToolParameterType.STRING,
                description="Content to write to the file",
                required=True,
            ),
        ]
    
    async def execute(self, path: str, content: str) -> ToolResult:
        """Write file contents."""
        try:
            file_path = Path(path)
            
            self.security_manager.validate_file_access(file_path, Permission.WRITE)
            
            # Create parent directories
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Write file
            file_path.write_text(content)
            
            return ToolResult(
                success=True,
                output=f"Successfully wrote {len(content)} characters to {path}",
                metadata={"path": str(file_path), "size": len(content)},
            )
            
        except Exception as e:
            return ToolResult(
                success=False,
                output=None,
                error=str(e),
            )


class ListFilesTool(BaseTool):
    """Tool for listing files in a directory."""
    
    def __init__(self, security_manager: SecurityManager):
        self.security_manager = security_manager
        super().__init__()
    
    @property
    def name(self) -> str:
        return "list_files"
    
    @property
    def description(self) -> str:
        return "List files in a directory"
    
    @property
    def parameters(self) -> List[ToolParameter]:
        return [
            ToolParameter(
                name="path",
                type=ToolParameterType.STRING,
                description="Path to the directory",
                required=True,
            ),
            ToolParameter(
                name="pattern",
                type=ToolParameterType.STRING,
                description="Glob pattern to filter files (e.g., '*.py')",
                required=False,
                default="*",
            ),
        ]
    
    async def execute(self, path: str, pattern: str = "*") -> ToolResult:
        """List files in directory."""
        try:
            dir_path = Path(path)
            
            self.security_manager.validate_file_access(dir_path, Permission.READ)
            
            # List files
            files = [str(f.relative_to(dir_path)) for f in dir_path.glob(pattern)]
            
            return ToolResult(
                success=True,
                output=files,
                metadata={"path": str(dir_path), "count": len(files)},
            )
            
        except Exception as e:
            return ToolResult(
                success=False,
                output=None,
                error=str(e),
            )
