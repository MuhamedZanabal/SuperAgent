"""
Checkpoint Manager - Session state persistence and rollback.
"""

import json
import pickle
from typing import Optional, Dict, Any, List
from pathlib import Path
from datetime import datetime
from dataclasses import asdict

from superagent.core.logger import get_logger
from superagent.core.utils import generate_id

logger = get_logger(__name__)


class CheckpointManager:
    """
    Manage session checkpoints for rollback and recovery.
    
    Provides:
    - Automatic checkpointing before risky operations
    - Manual checkpoint creation
    - Rollback to previous states
    - Checkpoint listing and cleanup
    """
    
    def __init__(self, checkpoint_dir: Optional[Path] = None):
        """
        Initialize checkpoint manager.
        
        Args:
            checkpoint_dir: Directory for storing checkpoints
        """
        self.checkpoint_dir = checkpoint_dir or Path.home() / ".superagent" / "checkpoints"
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Checkpoint manager initialized: {self.checkpoint_dir}")
    
    async def create_checkpoint(
        self,
        session_id: str,
        state: Any,
        description: Optional[str] = None,
    ) -> str:
        """
        Create a checkpoint.
        
        Args:
            session_id: Session identifier
            state: State to checkpoint
            description: Optional description
        
        Returns:
            Checkpoint ID
        """
        checkpoint_id = generate_id("ckpt")
        
        checkpoint_data = {
            "checkpoint_id": checkpoint_id,
            "session_id": session_id,
            "created_at": datetime.now().isoformat(),
            "description": description or "Auto checkpoint",
            "state": self._serialize_state(state),
        }
        
        # Save checkpoint
        checkpoint_file = self.checkpoint_dir / f"{checkpoint_id}.json"
        
        try:
            with open(checkpoint_file, 'w') as f:
                json.dump(checkpoint_data, f, indent=2)
            
            logger.info(f"Created checkpoint: {checkpoint_id}")
            return checkpoint_id
            
        except Exception as e:
            logger.error(f"Failed to create checkpoint: {e}")
            raise
    
    async def restore_checkpoint(self, checkpoint_id: str) -> Any:
        """
        Restore state from checkpoint.
        
        Args:
            checkpoint_id: Checkpoint to restore
        
        Returns:
            Restored state
        """
        checkpoint_file = self.checkpoint_dir / f"{checkpoint_id}.json"
        
        if not checkpoint_file.exists():
            raise ValueError(f"Checkpoint not found: {checkpoint_id}")
        
        try:
            with open(checkpoint_file, 'r') as f:
                checkpoint_data = json.load(f)
            
            state = self._deserialize_state(checkpoint_data["state"])
            
            logger.info(f"Restored checkpoint: {checkpoint_id}")
            return state
            
        except Exception as e:
            logger.error(f"Failed to restore checkpoint: {e}")
            raise
    
    async def list_checkpoints(
        self,
        session_id: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        List available checkpoints.
        
        Args:
            session_id: Optional filter by session
        
        Returns:
            List of checkpoint metadata
        """
        checkpoints = []
        
        for checkpoint_file in self.checkpoint_dir.glob("*.json"):
            try:
                with open(checkpoint_file, 'r') as f:
                    data = json.load(f)
                
                # Filter by session if specified
                if session_id and data["session_id"] != session_id:
                    continue
                
                checkpoints.append({
                    "checkpoint_id": data["checkpoint_id"],
                    "session_id": data["session_id"],
                    "created_at": data["created_at"],
                    "description": data["description"],
                })
                
            except Exception as e:
                logger.warning(f"Could not read checkpoint {checkpoint_file}: {e}")
        
        # Sort by creation time (newest first)
        checkpoints.sort(key=lambda x: x["created_at"], reverse=True)
        
        return checkpoints
    
    async def delete_checkpoint(self, checkpoint_id: str) -> bool:
        """Delete a checkpoint."""
        checkpoint_file = self.checkpoint_dir / f"{checkpoint_id}.json"
        
        try:
            checkpoint_file.unlink()
            logger.info(f"Deleted checkpoint: {checkpoint_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete checkpoint: {e}")
            return False
    
    def _serialize_state(self, state: Any) -> Dict[str, Any]:
        """Serialize state for storage."""
        if hasattr(state, '__dict__'):
            return {
                "__type__": type(state).__name__,
                "__data__": asdict(state) if hasattr(state, '__dataclass_fields__') else state.__dict__,
            }
        return {"__data__": state}
    
    def _deserialize_state(self, data: Dict[str, Any]) -> Any:
        """Deserialize state from storage."""
        # Simple deserialization - can be enhanced with type reconstruction
        return data.get("__data__", data)
