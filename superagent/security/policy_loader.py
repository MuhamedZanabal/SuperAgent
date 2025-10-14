"""
Policy loader and validator for RBAC and security policies.
"""

from pathlib import Path
from typing import Dict, Any, Optional
import yaml
import json
import jsonschema

from superagent.core.logger import get_logger

logger = get_logger(__name__)


class PolicyLoader:
    """
    Loads and validates security policies.
    
    Supports YAML policy files with JSON Schema validation.
    """
    
    def __init__(self, schema_path: Optional[Path] = None):
        """
        Initialize policy loader.
        
        Args:
            schema_path: Path to JSON Schema for validation
        """
        self.schema_path = schema_path
        self.schema: Optional[Dict[str, Any]] = None
        
        if schema_path and schema_path.exists():
            with open(schema_path) as f:
                self.schema = json.load(f)
            logger.info(f"Loaded policy schema from {schema_path}")
    
    def load_policy(self, policy_path: Path) -> Dict[str, Any]:
        """
        Load and validate a policy file.
        
        Args:
            policy_path: Path to policy YAML file
            
        Returns:
            Validated policy dictionary
            
        Raises:
            ValueError: If policy is invalid
        """
        if not policy_path.exists():
            raise ValueError(f"Policy file not found: {policy_path}")
        
        # Load YAML
        with open(policy_path) as f:
            policy = yaml.safe_load(f)
        
        # Validate against schema
        if self.schema:
            try:
                jsonschema.validate(policy, self.schema)
                logger.info(f"Policy validated: {policy_path}")
            except jsonschema.ValidationError as e:
                raise ValueError(f"Policy validation failed: {e.message}")
        
        return policy
    
    def merge_policies(
        self,
        base_policy: Dict[str, Any],
        override_policy: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Merge two policies with override precedence.
        
        Args:
            base_policy: Base policy
            override_policy: Override policy
            
        Returns:
            Merged policy
        """
        merged = base_policy.copy()
        
        for key, value in override_policy.items():
            if isinstance(value, dict) and key in merged:
                merged[key] = self.merge_policies(merged[key], value)
            else:
                merged[key] = value
        
        return merged
