"""
Secret redaction for logs and events.
"""

import re
from typing import Any, Dict

# Patterns for common secrets
SECRET_PATTERNS = [
    (r'(api[_-]?key|apikey)[\s:=]+(["\']?)([a-zA-Z0-9_\-]{20,})(\2)', r'\1\2***REDACTED***\4'),
    (r'(token|auth|secret|password)[\s:=]+(["\']?)([^\s"\']{8,})(\2)', r'\1\2***REDACTED***\4'),
    (r'(sk-[a-zA-Z0-9]{20,})', r'***REDACTED***'),  # OpenAI keys
    (r'(ghp_[a-zA-Z0-9]{36})', r'***REDACTED***'),  # GitHub tokens
    (r'(Bearer\s+[a-zA-Z0-9_\-\.]{20,})', r'Bearer ***REDACTED***'),  # Bearer tokens
]


def redact_secrets(text: str) -> str:
    """
    Redact secrets from text.
    
    Args:
        text: Text to redact
    
    Returns:
        Redacted text
    """
    for pattern, replacement in SECRET_PATTERNS:
        text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)
    return text


def redact_dict(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Redact secrets from dictionary.
    
    Args:
        data: Dictionary to redact
    
    Returns:
        Redacted dictionary
    """
    result = {}
    
    for key, value in data.items():
        # Check if key suggests secret
        if any(secret in key.lower() for secret in ['key', 'token', 'secret', 'password', 'auth']):
            result[key] = "***REDACTED***"
        elif isinstance(value, str):
            result[key] = redact_secrets(value)
        elif isinstance(value, dict):
            result[key] = redact_dict(value)
        elif isinstance(value, list):
            result[key] = [redact_dict(item) if isinstance(item, dict) else item for item in value]
        else:
            result[key] = value
    
    return result
