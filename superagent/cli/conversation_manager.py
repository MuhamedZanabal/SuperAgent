"""
Conversation management for save, load, branch, search, and export.
"""
import json
from typing import List, Dict, Any, Optional
from pathlib import Path
from datetime import datetime
import re

from superagent.core.logger import get_logger

logger = get_logger(__name__)


class ConversationManager:
    """Manages conversation persistence, branching, and search."""
    
    def __init__(self, conversations_dir: Optional[Path] = None):
        self.conversations_dir = conversations_dir or Path.home() / ".superagent" / "conversations"
        self.conversations_dir.mkdir(parents=True, exist_ok=True)
    
    def save(
        self,
        session_id: str,
        history: List[Dict[str, Any]],
        metadata: Dict[str, Any],
        filename: Optional[str] = None
    ) -> Path:
        """Save conversation to file."""
        if not filename:
            filename = f"conversation_{session_id}.json"
        
        filepath = self.conversations_dir / filename
        
        data = {
            "session_id": session_id,
            "history": history,
            "metadata": metadata,
            "saved_at": datetime.now().isoformat()
        }
        
        with open(filepath, "w") as f:
            json.dump(data, f, indent=2)
        
        logger.info(f"Saved conversation to {filepath}")
        return filepath
    
    def load(self, filename: str) -> Dict[str, Any]:
        """Load conversation from file."""
        filepath = self.conversations_dir / filename
        
        if not filepath.exists():
            raise FileNotFoundError(f"Conversation not found: {filename}")
        
        with open(filepath) as f:
            data = json.load(f)
        
        logger.info(f"Loaded conversation from {filepath}")
        return data
    
    def list_conversations(self) -> List[Dict[str, Any]]:
        """List all saved conversations."""
        conversations = []
        
        for filepath in self.conversations_dir.glob("*.json"):
            try:
                with open(filepath) as f:
                    data = json.load(f)
                
                conversations.append({
                    "filename": filepath.name,
                    "session_id": data.get("session_id"),
                    "message_count": len(data.get("history", [])),
                    "saved_at": data.get("saved_at"),
                    "metadata": data.get("metadata", {})
                })
            except Exception as e:
                logger.error(f"Error reading {filepath}: {e}")
        
        return sorted(conversations, key=lambda x: x["saved_at"], reverse=True)
    
    def search(self, query: str, history: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Search conversation history for query."""
        results = []
        query_lower = query.lower()
        
        for i, msg in enumerate(history):
            content = msg.get("content", "")
            if query_lower in content.lower():
                results.append({
                    "index": i,
                    "role": msg.get("role"),
                    "content": content,
                    "timestamp": msg.get("timestamp"),
                    "match_context": self._get_match_context(content, query_lower)
                })
        
        return results
    
    def _get_match_context(self, content: str, query: str, context_chars: int = 100) -> str:
        """Get context around match."""
        content_lower = content.lower()
        match_pos = content_lower.find(query)
        
        if match_pos == -1:
            return content[:context_chars]
        
        start = max(0, match_pos - context_chars // 2)
        end = min(len(content), match_pos + len(query) + context_chars // 2)
        
        context = content[start:end]
        if start > 0:
            context = "..." + context
        if end < len(content):
            context = context + "..."
        
        return context
    
    def branch(
        self,
        history: List[Dict[str, Any]],
        branch_point: int,
        new_session_id: str
    ) -> List[Dict[str, Any]]:
        """Create a new conversation branch from a specific point."""
        if branch_point < 0 or branch_point >= len(history):
            raise ValueError(f"Invalid branch point: {branch_point}")
        
        branched_history = history[:branch_point + 1].copy()
        
        logger.info(f"Created branch at message {branch_point}")
        return branched_history
    
    def export_conversation(
        self,
        history: List[Dict[str, Any]],
        filepath: Path,
        format_type: str = "txt"
    ):
        """Export conversation in specified format."""
        if format_type == "txt":
            content = self.export_text(history)
            filepath.write_text(content, encoding="utf-8")
        elif format_type == "md":
            content = self.export_markdown(history)
            filepath.write_text(content, encoding="utf-8")
        elif format_type == "html":
            content = self.export_html(history)
            filepath.write_text(content, encoding="utf-8")
        elif format_type == "json":
            data = {
                "export_date": datetime.now().isoformat(),
                "format_version": "2.0.0",
                "messages": history
            }
            filepath.write_text(json.dumps(data, indent=2), encoding="utf-8")
        elif format_type == "pdf":
            self._export_pdf(history, filepath)
        else:
            raise ValueError(f"Unsupported format: {format_type}")
    
    def _export_pdf(self, history: List[Dict[str, Any]], filepath: Path):
        """Export as PDF using reportlab."""
        try:
            from reportlab.lib.pagesizes import letter
            from reportlab.lib.styles import getSampleStyleSheet
            from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
            
            doc = SimpleDocTemplate(str(filepath), pagesize=letter)
            styles = getSampleStyleSheet()
            story = []
            
            # Title
            title = Paragraph("SuperAgent Conversation Export", styles['Title'])
            story.append(title)
            story.append(Spacer(1, 12))
            
            # Messages
            for msg in history:
                role = msg["role"].upper()
                content = msg["content"]
                timestamp = msg.get("timestamp", "")
                
                # Role and timestamp
                header = Paragraph(f"<b>{role}</b> ({timestamp})", styles['Heading2'])
                story.append(header)
                
                # Content
                text = Paragraph(content.replace("\n", "<br/>"), styles['Normal'])
                story.append(text)
                story.append(Spacer(1, 12))
            
            doc.build(story)
            
        except ImportError:
            raise ImportError("PDF export requires reportlab: pip install reportlab")
    
    def export_text(self, history: List[Dict[str, Any]]) -> str:
        """Export conversation as plain text."""
        lines = []
        
        for msg in history:
            role = msg.get("role", "").upper()
            content = msg.get("content", "")
            timestamp = msg.get("timestamp", "")
            
            lines.append(f"{role} ({timestamp}):")
            lines.append(content)
            lines.append("")
        
        return "\n".join(lines)
    
    def export_markdown(self, history: List[Dict[str, Any]], title: str = "Conversation") -> str:
        """Export conversation as Markdown."""
        lines = [f"# {title}\n"]
        
        for msg in history:
            role = msg.get("role", "")
            content = msg.get("content", "")
            timestamp = msg.get("timestamp", "")
            
            if role == "user":
                lines.append(f"## User ({timestamp})\n")
            else:
                lines.append(f"## Assistant ({timestamp})\n")
            
            lines.append(content)
            lines.append("")
        
        return "\n".join(lines)
    
    def export_html(self, history: List[Dict[str, Any]], title: str = "Conversation") -> str:
        """Export conversation as HTML."""
        html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>{title}</title>
    <style>
        body {{ font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }}
        .message {{ margin: 20px 0; padding: 15px; border-radius: 8px; }}
        .user {{ background-color: #e3f2fd; }}
        .assistant {{ background-color: #f5f5f5; }}
        .role {{ font-weight: bold; color: #1976d2; }}
        .timestamp {{ color: #666; font-size: 0.9em; }}
        .content {{ margin-top: 10px; white-space: pre-wrap; }}
    </style>
</head>
<body>
    <h1>{title}</h1>
"""
        
        for msg in history:
            role = msg.get("role", "")
            content = msg.get("content", "")
            timestamp = msg.get("timestamp", "")
            
            html += f"""
    <div class="message {role}">
        <div class="role">{role.upper()}</div>
        <div class="timestamp">{timestamp}</div>
        <div class="content">{self._escape_html(content)}</div>
    </div>
"""
        
        html += """
</body>
</html>
"""
        return html
    
    def _escape_html(self, text: str) -> str:
        """Escape HTML special characters."""
        return (text
                .replace("&", "&amp;")
                .replace("<", "&lt;")
                .replace(">", "&gt;")
                .replace('"', "&quot;")
                .replace("'", "&#39;"))


class CostTracker:
    """Track token usage and costs."""
    
    # Pricing per 1M tokens (as of 2025)
    PRICING = {
        "claude-sonnet-4-20250514": {"input": 3.00, "output": 15.00},
        "claude-opus-4-20250514": {"input": 15.00, "output": 75.00},
        "claude-3-5-haiku-20241022": {"input": 0.80, "output": 4.00},
    }
    
    def __init__(self):
        self.total_input_tokens = 0
        self.total_output_tokens = 0
        self.total_cost = 0.0
        self.model_usage = {}
    
    def track(self, model: str, input_tokens: int, output_tokens: int) -> float:
        """Track token usage and calculate cost."""
        pricing = self.PRICING.get(model, {"input": 3.00, "output": 15.00})
        
        input_cost = (input_tokens / 1_000_000) * pricing["input"]
        output_cost = (output_tokens / 1_000_000) * pricing["output"]
        cost = input_cost + output_cost
        
        self.total_input_tokens += input_tokens
        self.total_output_tokens += output_tokens
        self.total_cost += cost
        
        if model not in self.model_usage:
            self.model_usage[model] = {
                "input_tokens": 0,
                "output_tokens": 0,
                "cost": 0.0
            }
        
        self.model_usage[model]["input_tokens"] += input_tokens
        self.model_usage[model]["output_tokens"] += output_tokens
        self.model_usage[model]["cost"] += cost
        
        return cost
    
    def get_stats(self) -> Dict[str, Any]:
        """Get usage statistics."""
        return {
            "total_input_tokens": self.total_input_tokens,
            "total_output_tokens": self.total_output_tokens,
            "total_tokens": self.total_input_tokens + self.total_output_tokens,
            "total_cost": self.total_cost,
            "model_usage": self.model_usage
        }
