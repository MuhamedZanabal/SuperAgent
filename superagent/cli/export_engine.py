# File: superagent/cli/export_engine.py
# Version: 2.0.0 - Complete export engine implementation

"""
Export Engine for SuperAgent v2.0.0

Exports conversations in multiple formats: TXT, MD, HTML, PDF, JSON.
"""

from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime
import json


class ExportEngine:
    """Export conversations in various formats."""
    
    @staticmethod
    def export_txt(history: List[Dict[str, Any]], filepath: Path):
        """Export as plain text."""
        with open(filepath, "w", encoding="utf-8") as f:
            f.write("SuperAgent Conversation Export\n")
            f.write("=" * 50 + "\n\n")
            
            for msg in history:
                role = msg["role"].upper()
                content = msg["content"]
                timestamp = msg.get("timestamp", "")
                
                f.write(f"{role} ({timestamp}):\n")
                f.write(f"{content}\n\n")
                f.write("-" * 50 + "\n\n")
    
    @staticmethod
    def export_markdown(history: List[Dict[str, Any]], filepath: Path):
        """Export as Markdown."""
        with open(filepath, "w", encoding="utf-8") as f:
            f.write("# SuperAgent Conversation Export\n\n")
            
            for msg in history:
                role = msg["role"].capitalize()
                content = msg["content"]
                timestamp = msg.get("timestamp", "")
                
                f.write(f"## {role} ({timestamp})\n\n")
                f.write(f"{content}\n\n")
                f.write("---\n\n")
    
    @staticmethod
    def export_html(history: List[Dict[str, Any]], filepath: Path):
        """Export as HTML."""
        html = """<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>SuperAgent Conversation</title>
    <style>
        body { font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }
        .message { margin: 20px 0; padding: 15px; border-radius: 8px; }
        .user { background: #e3f2fd; }
        .assistant { background: #f1f8e9; }
        .role { font-weight: bold; color: #1976d2; }
        .timestamp { color: #666; font-size: 0.9em; }
        .content { margin-top: 10px; line-height: 1.6; }
    </style>
</head>
<body>
    <h1>SuperAgent Conversation Export</h1>
"""
        
        for msg in history:
            role = msg["role"]
            content = msg["content"].replace("\n", "<br>")
            timestamp = msg.get("timestamp", "")
            
            html += f"""
    <div class="message {role}">
        <div class="role">{role.upper()}</div>
        <div class="timestamp">{timestamp}</div>
        <div class="content">{content}</div>
    </div>
"""
        
        html += """
</body>
</html>
"""
        
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(html)
    
    @staticmethod
    def export_json(history: List[Dict[str, Any]], filepath: Path):
        """Export as JSON."""
        data = {
            "export_date": datetime.now().isoformat(),
            "format_version": "2.0.0",
            "messages": history
        }
        
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    @staticmethod
    def export_pdf(history: List[Dict[str, Any]], filepath: Path):
        """Export as PDF (requires reportlab)."""
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
