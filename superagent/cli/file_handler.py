"""
File attachment and processing for CLI.
"""
import mimetypes
from pathlib import Path
from typing import Optional, Dict, Any
import base64

from superagent.core.logger import get_logger

logger = get_logger(__name__)


class FileHandler:
    """Handle file attachments and processing."""
    
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
    
    SUPPORTED_TEXT_EXTENSIONS = {
        ".txt", ".md", ".py", ".js", ".ts", ".jsx", ".tsx",
        ".json", ".yaml", ".yml", ".toml", ".ini", ".cfg",
        ".sh", ".bash", ".zsh", ".fish", ".html", ".css",
        ".xml", ".sql", ".rs", ".go", ".java", ".c", ".cpp",
        ".h", ".hpp", ".cs", ".rb", ".php", ".swift", ".kt"
    }
    
    SUPPORTED_IMAGE_EXTENSIONS = {
        ".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp"
    }
    
    def read_file(self, filepath: str) -> Dict[str, Any]:
        """Read file and return content with metadata."""
        path = Path(filepath).expanduser()
        
        if not path.exists():
            raise FileNotFoundError(f"File not found: {filepath}")
        
        if path.stat().st_size > self.MAX_FILE_SIZE:
            raise ValueError(f"File too large: {path.stat().st_size} bytes (max: {self.MAX_FILE_SIZE})")
        
        extension = path.suffix.lower()
        mime_type, _ = mimetypes.guess_type(str(path))
        
        result = {
            "filename": path.name,
            "path": str(path),
            "size": path.stat().st_size,
            "mime_type": mime_type,
            "extension": extension
        }
        
        # Handle text files
        if extension in self.SUPPORTED_TEXT_EXTENSIONS:
            with open(path, "r", encoding="utf-8") as f:
                result["content"] = f.read()
                result["type"] = "text"
        
        # Handle image files
        elif extension in self.SUPPORTED_IMAGE_EXTENSIONS:
            with open(path, "rb") as f:
                result["content"] = base64.b64encode(f.read()).decode("utf-8")
                result["type"] = "image"
        
        else:
            raise ValueError(f"Unsupported file type: {extension}")
        
        logger.info(f"Read file: {filepath} ({result['size']} bytes)")
        return result
    
    def format_for_prompt(self, file_data: Dict[str, Any]) -> str:
        """Format file data for inclusion in prompt."""
        if file_data["type"] == "text":
            return f"""File: {file_data['filename']}
