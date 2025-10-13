"""
Session management for persistent conversations.
"""

import json
from pathlib import Path
from typing import Any, Dict, Optional
from datetime import datetime
import uuid


class SessionManager:
    """
    Manages persistent conversation sessions.
    
    Features:
    - Save and load conversation history
    - Session metadata tracking
    - Session listing and cleanup
    """
    
    def __init__(self, sessions_dir: Path):
        self.sessions_dir = sessions_dir
        self.sessions_dir.mkdir(parents=True, exist_ok=True)
    
    def create_session(self) -> str:
        """
        Create a new session.
        
        Returns:
            Session ID
        """
        session_id = str(uuid.uuid4())
        return session_id
    
    def save_session(self, session_id: str, data: Dict[str, Any]) -> None:
        """
        Save session data.
        
        Args:
            session_id: Session identifier
            data: Session data to save
        """
        session_file = self.sessions_dir / f"{session_id}.json"
        
        with open(session_file, "w") as f:
            json.dump(data, f, indent=2)
    
    def load_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Load session data.
        
        Args:
            session_id: Session identifier
            
        Returns:
            Session data if exists, None otherwise
        """
        session_file = self.sessions_dir / f"{session_id}.json"
        
        if not session_file.exists():
            return None
        
        try:
            with open(session_file, "r") as f:
                return json.load(f)
        except Exception:
            return None
    
    def list_sessions(self) -> list[Dict[str, Any]]:
        """
        List all sessions.
        
        Returns:
            List of session metadata
        """
        sessions = []
        
        for session_file in self.sessions_dir.glob("*.json"):
            try:
                with open(session_file, "r") as f:
                    data = json.load(f)
                    sessions.append({
                        "session_id": session_file.stem,
                        "timestamp": data.get("timestamp"),
                        "model": data.get("model"),
                        "message_count": len(data.get("messages", [])),
                    })
            except Exception:
                continue
        
        return sorted(sessions, key=lambda s: s.get("timestamp", ""), reverse=True)
    
    def delete_session(self, session_id: str) -> bool:
        """
        Delete a session.
        
        Args:
            session_id: Session identifier
            
        Returns:
            True if deleted, False otherwise
        """
        session_file = self.sessions_dir / f"{session_id}.json"
        
        if session_file.exists():
            session_file.unlink()
            return True
        
        return False
