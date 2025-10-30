"""
Clipboard integration for copying responses.
"""
import subprocess
import platform
from typing import Optional

from superagent.core.logger import get_logger

logger = get_logger(__name__)


class ClipboardManager:
    """Manage clipboard operations."""
    
    def __init__(self):
        self.system = platform.system()
    
    def copy(self, text: str) -> bool:
        """Copy text to clipboard."""
        try:
            if self.system == "Darwin":  # macOS
                process = subprocess.Popen(
                    ["pbcopy"],
                    stdin=subprocess.PIPE,
                    close_fds=True
                )
                process.communicate(text.encode("utf-8"))
                return process.returncode == 0
            
            elif self.system == "Linux":
                # Try xclip first
                try:
                    process = subprocess.Popen(
                        ["xclip", "-selection", "clipboard"],
                        stdin=subprocess.PIPE,
                        close_fds=True
                    )
                    process.communicate(text.encode("utf-8"))
                    return process.returncode == 0
                except FileNotFoundError:
                    # Try xsel as fallback
                    process = subprocess.Popen(
                        ["xsel", "--clipboard", "--input"],
                        stdin=subprocess.PIPE,
                        close_fds=True
                    )
                    process.communicate(text.encode("utf-8"))
                    return process.returncode == 0
            
            elif self.system == "Windows":
                process = subprocess.Popen(
                    ["clip"],
                    stdin=subprocess.PIPE,
                    close_fds=True,
                    shell=True
                )
                process.communicate(text.encode("utf-16le"))
                return process.returncode == 0
            
            else:
                logger.warning(f"Clipboard not supported on {self.system}")
                return False
        
        except Exception as e:
            logger.error(f"Failed to copy to clipboard: {e}")
            return False
    
    def paste(self) -> Optional[str]:
        """Paste text from clipboard."""
        try:
            if self.system == "Darwin":  # macOS
                result = subprocess.run(
                    ["pbpaste"],
                    capture_output=True,
                    text=True
                )
                return result.stdout if result.returncode == 0 else None
            
            elif self.system == "Linux":
                # Try xclip first
                try:
                    result = subprocess.run(
                        ["xclip", "-selection", "clipboard", "-o"],
                        capture_output=True,
                        text=True
                    )
                    return result.stdout if result.returncode == 0 else None
                except FileNotFoundError:
                    # Try xsel as fallback
                    result = subprocess.run(
                        ["xsel", "--clipboard", "--output"],
                        capture_output=True,
                        text=True
                    )
                    return result.stdout if result.returncode == 0 else None
            
            elif self.system == "Windows":
                # Windows doesn't have a simple paste command
                logger.warning("Paste not implemented for Windows")
                return None
            
            else:
                logger.warning(f"Clipboard not supported on {self.system}")
                return None
        
        except Exception as e:
            logger.error(f"Failed to paste from clipboard: {e}")
            return None
