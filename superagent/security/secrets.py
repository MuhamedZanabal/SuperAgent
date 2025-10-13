"""
Secrets management system.

Provides secure storage and rotation of API keys and sensitive data.
"""

import os
from datetime import datetime, timedelta
from typing import Dict, Optional

from cryptography.fernet import Fernet

from superagent.core.logger import get_logger

logger = get_logger(__name__)


class SecretsManager:
    """
    Manages secrets and API keys securely.

    Provides encryption, rotation, and secure access to sensitive data.
    """

    def __init__(self, encryption_key: Optional[bytes] = None):
        if encryption_key is None:
            # Generate or load encryption key
            key_file = os.path.expanduser("~/.superagent/encryption.key")
            if os.path.exists(key_file):
                with open(key_file, "rb") as f:
                    encryption_key = f.read()
            else:
                encryption_key = Fernet.generate_key()
                os.makedirs(os.path.dirname(key_file), exist_ok=True)
                with open(key_file, "wb") as f:
                    f.write(encryption_key)

        self._cipher = Fernet(encryption_key)
        self._secrets: Dict[str, bytes] = {}
        self._rotation_dates: Dict[str, datetime] = {}

    def set_secret(self, name: str, value: str) -> None:
        """Store a secret securely."""
        encrypted = self._cipher.encrypt(value.encode())
        self._secrets[name] = encrypted
        self._rotation_dates[name] = datetime.utcnow()
        logger.info(f"Secret stored: {name}")

    def get_secret(self, name: str) -> Optional[str]:
        """Retrieve a secret."""
        encrypted = self._secrets.get(name)
        if encrypted is None:
            return None

        try:
            decrypted = self._cipher.decrypt(encrypted)
            return decrypted.decode()
        except Exception as e:
            logger.error(f"Failed to decrypt secret: {name}", exc_info=e)
            return None

    def delete_secret(self, name: str) -> None:
        """Delete a secret."""
        if name in self._secrets:
            del self._secrets[name]
            del self._rotation_dates[name]
            logger.info(f"Secret deleted: {name}")

    def rotate_secret(self, name: str, new_value: str) -> None:
        """Rotate a secret to a new value."""
        self.set_secret(name, new_value)
        logger.info(f"Secret rotated: {name}")

    def needs_rotation(self, name: str, max_age_days: int = 90) -> bool:
        """Check if a secret needs rotation."""
        rotation_date = self._rotation_dates.get(name)
        if rotation_date is None:
            return False

        age = datetime.utcnow() - rotation_date
        return age > timedelta(days=max_age_days)

    def list_secrets(self) -> list:
        """List all secret names (not values)."""
        return list(self._secrets.keys())
