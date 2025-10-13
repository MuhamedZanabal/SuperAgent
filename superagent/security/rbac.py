"""
Role-Based Access Control (RBAC) system.

Provides role and permission management for secure access control.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Set

from superagent.core.logger import get_logger

logger = get_logger(__name__)


class Permission(str, Enum):
    """System permissions."""

    # LLM permissions
    LLM_READ = "llm:read"
    LLM_WRITE = "llm:write"

    # Tool permissions
    TOOL_EXECUTE = "tool:execute"
    TOOL_MANAGE = "tool:manage"

    # Memory permissions
    MEMORY_READ = "memory:read"
    MEMORY_WRITE = "memory:write"

    # Agent permissions
    AGENT_EXECUTE = "agent:execute"
    AGENT_MANAGE = "agent:manage"

    # System permissions
    SYSTEM_ADMIN = "system:admin"
    SYSTEM_CONFIG = "system:config"


@dataclass
class Role:
    """A role with associated permissions."""

    name: str
    permissions: Set[Permission] = field(default_factory=set)
    description: str = ""


class RBACManager:
    """
    Manages roles and permissions for access control.

    Provides role assignment, permission checking, and access control.
    """

    def __init__(self):
        self._roles: Dict[str, Role] = {}
        self._user_roles: Dict[str, Set[str]] = {}
        self._initialize_default_roles()

    def _initialize_default_roles(self) -> None:
        """Initialize default system roles."""
        # Admin role with all permissions
        admin_role = Role(
            name="admin",
            permissions=set(Permission),
            description="Full system access",
        )
        self.create_role(admin_role)

        # User role with basic permissions
        user_role = Role(
            name="user",
            permissions={
                Permission.LLM_READ,
                Permission.LLM_WRITE,
                Permission.TOOL_EXECUTE,
                Permission.MEMORY_READ,
                Permission.MEMORY_WRITE,
                Permission.AGENT_EXECUTE,
            },
            description="Standard user access",
        )
        self.create_role(user_role)

        # Read-only role
        readonly_role = Role(
            name="readonly",
            permissions={
                Permission.LLM_READ,
                Permission.MEMORY_READ,
            },
            description="Read-only access",
        )
        self.create_role(readonly_role)

    def create_role(self, role: Role) -> None:
        """Create a new role."""
        self._roles[role.name] = role
        logger.info(f"Role created: {role.name}")

    def assign_role(self, user_id: str, role_name: str) -> None:
        """Assign a role to a user."""
        if role_name not in self._roles:
            raise ValueError(f"Role not found: {role_name}")

        if user_id not in self._user_roles:
            self._user_roles[user_id] = set()

        self._user_roles[user_id].add(role_name)
        logger.info(f"Role assigned: {role_name} to user {user_id}")

    def revoke_role(self, user_id: str, role_name: str) -> None:
        """Revoke a role from a user."""
        if user_id in self._user_roles:
            self._user_roles[user_id].discard(role_name)
            logger.info(f"Role revoked: {role_name} from user {user_id}")

    def has_permission(self, user_id: str, permission: Permission) -> bool:
        """Check if a user has a specific permission."""
        if user_id not in self._user_roles:
            return False

        for role_name in self._user_roles[user_id]:
            role = self._roles.get(role_name)
            if role and permission in role.permissions:
                return True

        return False

    def get_user_permissions(self, user_id: str) -> Set[Permission]:
        """Get all permissions for a user."""
        permissions = set()

        if user_id in self._user_roles:
            for role_name in self._user_roles[user_id]:
                role = self._roles.get(role_name)
                if role:
                    permissions.update(role.permissions)

        return permissions

    def get_user_roles(self, user_id: str) -> List[str]:
        """Get all roles assigned to a user."""
        return list(self._user_roles.get(user_id, set()))
