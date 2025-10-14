"""
Security manager for sandboxing, permission control, encryption,
and secure execution isolation.
"""

import os
import sys
from pathlib import Path
from typing import Any, Optional, Set
from enum import Flag, auto
import hashlib
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2

from superagent.core.logger import get_logger
from superagent.core.config import get_config

logger = get_logger(__name__)


class Permission(Flag):
    """Permission flags for sandboxed operations."""
    NONE = 0
    READ = auto()
    WRITE = auto()
    EXECUTE = auto()
    NETWORK = auto()
    SYSTEM = auto()
    ALL = READ | WRITE | EXECUTE | NETWORK | SYSTEM


class SecurityManager:
    """
    Manages security policies, sandboxing, and encryption.
    
    Enforces permission boundaries, validates operations,
    and provides encryption utilities.
    """
    
    def __init__(self):
        """Initialize security manager."""
        self.config = get_config()
        self._encryption_key: Optional[bytes] = None
        self._allowed_paths: Set[Path] = set()
        self._blocked_paths: Set[Path] = {
            Path("/etc"),
            Path("/sys"),
            Path("/proc"),
            Path(sys.prefix),  # Python installation
        }
        
        # Initialize allowed paths
        self._allowed_paths.add(self.config.data_dir)
        self._allowed_paths.add(self.config.cache_dir)
        self._allowed_paths.add(self.config.plugins_path)
        
        logger.info("Security manager initialized", extra={
            "sandbox_enabled": self.config.sandbox_enabled,
            "encryption_enabled": self.config.encryption_enabled,
        })
    
    def validate_file_access(
        self,
        path: Path,
        permission: Permission = Permission.READ
    ) -> bool:
        """
        Validate file access permission.
        
        Args:
            path: File path to validate
            permission: Required permission level
            
        Returns:
            True if access is allowed
            
        Raises:
            PermissionError: If access is denied
        """
        if not self.config.sandbox_enabled:
            return True
        
        # Resolve to absolute path
        abs_path = path.resolve()
        
        # Check blocked paths
        for blocked in self._blocked_paths:
            if abs_path.is_relative_to(blocked):
                logger.warning(
                    f"Access denied to blocked path: {abs_path}",
                    extra={"path": str(abs_path), "permission": permission.name}
                )
                raise PermissionError(f"Access denied to protected path: {abs_path}")
        
        # Check allowed paths for write/execute
        if permission & (Permission.WRITE | Permission.EXECUTE):
            allowed = any(abs_path.is_relative_to(allowed_path) 
                         for allowed_path in self._allowed_paths)
            if not allowed:
                logger.warning(
                    f"Write/execute access denied: {abs_path}",
                    extra={"path": str(abs_path), "permission": permission.name}
                )
                raise PermissionError(f"Write/execute access denied: {abs_path}")
        
        # Check file size for reads
        if permission & Permission.READ and abs_path.exists():
            size_mb = abs_path.stat().st_size / (1024 * 1024)
            if size_mb > self.config.max_file_size_mb:
                logger.warning(
                    f"File too large: {size_mb:.2f}MB > {self.config.max_file_size_mb}MB",
                    extra={"path": str(abs_path), "size_mb": size_mb}
                )
                raise PermissionError(
                    f"File exceeds maximum size: {size_mb:.2f}MB > "
                    f"{self.config.max_file_size_mb}MB"
                )
        
        return True
    
    def validate_network_access(self, domain: str) -> bool:
        """
        Validate network access to domain.
        
        Args:
            domain: Domain to validate
            
        Returns:
            True if access is allowed
            
        Raises:
            PermissionError: If access is denied
        """
        if not self.config.sandbox_enabled:
            return True
        
        # Check allowed domains
        if "*" in self.config.allowed_domains:
            return True
        
        allowed = any(
            domain.endswith(allowed_domain) 
            for allowed_domain in self.config.allowed_domains
        )
        
        if not allowed:
            logger.warning(
                f"Network access denied to domain: {domain}",
                extra={"domain": domain}
            )
            raise PermissionError(f"Network access denied to domain: {domain}")
        
        return True
    
    def get_encryption_key(self, password: Optional[str] = None) -> bytes:
        """
        Get or generate encryption key.
        
        Args:
            password: Optional password for key derivation
            
        Returns:
            Encryption key bytes
        """
        if self._encryption_key is not None:
            return self._encryption_key
        
        if password:
            # Load or generate salt from secure storage
            salt_file = self.config.data_dir / ".salt"
            if salt_file.exists():
                salt = salt_file.read_bytes()
            else:
                salt = os.urandom(16)
                salt_file.parent.mkdir(parents=True, exist_ok=True)
                salt_file.write_bytes(salt)
                # Secure the salt file
                os.chmod(salt_file, 0o600)
            
            # Derive key from password
            kdf = PBKDF2(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt,
                iterations=100000,
            )
            key = kdf.derive(password.encode())
        else:
            # Generate random key
            key = Fernet.generate_key()
        
        self._encryption_key = key
        return key
    
    def encrypt(self, data: str, password: Optional[str] = None) -> str:
        """
        Encrypt string data.
        
        Args:
            data: Data to encrypt
            password: Optional password for encryption
            
        Returns:
            Encrypted data as base64 string
        """
        if not self.config.encryption_enabled:
            return data
        
        key = self.get_encryption_key(password)
        fernet = Fernet(key)
        encrypted = fernet.encrypt(data.encode())
        return encrypted.decode()
    
    def decrypt(self, encrypted_data: str, password: Optional[str] = None) -> str:
        """
        Decrypt string data.
        
        Args:
            encrypted_data: Encrypted data as base64 string
            password: Optional password for decryption
            
        Returns:
            Decrypted data
        """
        if not self.config.encryption_enabled:
            return encrypted_data
        
        key = self.get_encryption_key(password)
        fernet = Fernet(key)
        decrypted = fernet.decrypt(encrypted_data.encode())
        return decrypted.decode()
    
    def hash_sensitive_data(self, data: str) -> str:
        """
        Hash sensitive data for storage.
        
        Args:
            data: Data to hash
            
        Returns:
            Hex digest of hash
        """
        return hashlib.sha256(data.encode()).hexdigest()
    
    def add_allowed_path(self, path: Path) -> None:
        """
        Add path to allowed paths.
        
        Args:
            path: Path to allow
        """
        self._allowed_paths.add(path.resolve())
        logger.debug(f"Added allowed path: {path}")
    
    def remove_allowed_path(self, path: Path) -> None:
        """
        Remove path from allowed paths.
        
        Args:
            path: Path to remove
        """
        self._allowed_paths.discard(path.resolve())
        logger.debug(f"Removed allowed path: {path}")
