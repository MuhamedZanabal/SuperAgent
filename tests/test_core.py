"""Tests for core systems."""

import pytest
from pathlib import Path
from superagent.core.config import SuperAgentConfig, get_config
from superagent.core.security import SecurityManager, Permission
from superagent.core.logger import get_logger
from superagent.core.utils import retry, safe_json_loads, generate_id


def test_config_initialization():
    """Test configuration initialization."""
    config = SuperAgentConfig()
    assert config.version == "0.1.0"
    assert config.data_dir.exists()
    assert config.cache_dir.exists()
    assert config.plugins_path.exists()


def test_config_from_env(monkeypatch):
    """Test configuration from environment variables."""
    monkeypatch.setenv("SUPERAGENT_DEFAULT_MODEL", "gpt-4")
    monkeypatch.setenv("SUPERAGENT_TEMPERATURE", "0.5")
    
    config = SuperAgentConfig()
    assert config.default_model == "gpt-4"
    assert config.temperature == 0.5


def test_security_manager_file_access():
    """Test security manager file access validation."""
    security = SecurityManager()
    
    # Test allowed path
    allowed_path = security.config.data_dir / "test.txt"
    assert security.validate_file_access(allowed_path, Permission.READ)
    
    # Test blocked path
    blocked_path = Path("/etc/passwd")
    with pytest.raises(PermissionError):
        security.validate_file_access(blocked_path, Permission.READ)


def test_security_manager_encryption():
    """Test encryption and decryption."""
    security = SecurityManager()
    
    original = "sensitive data"
    encrypted = security.encrypt(original)
    decrypted = security.decrypt(encrypted)
    
    assert encrypted != original
    assert decrypted == original


def test_security_manager_hashing():
    """Test sensitive data hashing."""
    security = SecurityManager()
    
    data = "password123"
    hash1 = security.hash_sensitive_data(data)
    hash2 = security.hash_sensitive_data(data)
    
    assert hash1 == hash2
    assert len(hash1) == 64  # SHA256 hex digest


@pytest.mark.asyncio
async def test_retry_decorator():
    """Test retry decorator."""
    call_count = 0
    
    @retry(max_attempts=3, delay=0.1)
    async def failing_function():
        nonlocal call_count
        call_count += 1
        if call_count < 3:
            raise ValueError("Temporary failure")
        return "success"
    
    result = await failing_function()
    assert result == "success"
    assert call_count == 3


def test_safe_json_loads():
    """Test safe JSON parsing."""
    valid_json = '{"key": "value"}'
    result = safe_json_loads(valid_json)
    assert result == {"key": "value"}
    
    invalid_json = '{invalid}'
    result = safe_json_loads(invalid_json, default={})
    assert result == {}


def test_generate_id():
    """Test ID generation."""
    id1 = generate_id()
    id2 = generate_id()
    
    assert len(id1) > 0
    assert id1 != id2
