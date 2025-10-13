"""Tests for security systems."""

import pytest

from superagent.security.rbac import RBACManager, Role, Permission
from superagent.security.audit import AuditLogger
from superagent.security.secrets import SecretsManager


def test_rbac_manager():
    """Test RBAC system."""
    rbac = RBACManager()

    # Assign role to user
    rbac.assign_role("user123", "user")

    # Check permissions
    assert rbac.has_permission("user123", Permission.LLM_READ)
    assert rbac.has_permission("user123", Permission.TOOL_EXECUTE)
    assert not rbac.has_permission("user123", Permission.SYSTEM_ADMIN)

    # Get user permissions
    permissions = rbac.get_user_permissions("user123")
    assert Permission.LLM_READ in permissions

    # Revoke role
    rbac.revoke_role("user123", "user")
    assert not rbac.has_permission("user123", Permission.LLM_READ)


def test_audit_logger():
    """Test audit logging."""
    audit = AuditLogger()

    # Log authentication
    audit.log_authentication("user123", True, "192.168.1.1")

    # Log authorization
    audit.log_authorization("user123", "llm:read", "gpt-4", True)

    # Log data access
    audit.log_data_access("user123", "memory", "read")

    # Query events
    events = audit.get_events(user_id="user123")
    assert len(events) == 3

    auth_events = audit.get_events(event_type="authentication")
    assert len(auth_events) == 1


def test_secrets_manager():
    """Test secrets management."""
    manager = SecretsManager()

    # Store secret
    manager.set_secret("api_key", "sk-test123")

    # Retrieve secret
    value = manager.get_secret("api_key")
    assert value == "sk-test123"

    # Rotate secret
    manager.rotate_secret("api_key", "sk-test456")
    value = manager.get_secret("api_key")
    assert value == "sk-test456"

    # Delete secret
    manager.delete_secret("api_key")
    value = manager.get_secret("api_key")
    assert value is None

    # List secrets
    manager.set_secret("key1", "value1")
    manager.set_secret("key2", "value2")
    secrets = manager.list_secrets()
    assert len(secrets) == 2
