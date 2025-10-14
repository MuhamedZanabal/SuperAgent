"""
Diff Engine - Generate and apply code diffs with preview.
"""

import difflib
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from pathlib import Path

from superagent.core.logger import get_logger

logger = get_logger(__name__)


@dataclass
class FileDiff:
    """Diff for a single file."""
    file_path: str
    old_content: str
    new_content: str
    diff_lines: List[str]
    additions: int
    deletions: int


@dataclass
class DiffPreview:
    """Preview of all planned changes."""
    file_diffs: List[FileDiff]
    total_additions: int
    total_deletions: int
    total_files: int
    summary: str


class DiffEngine:
    """
    Generate and apply code diffs with preview.
    
    Provides diff-first workflow with partial application support.
    """
    
    def __init__(self):
        """Initialize diff engine."""
        logger.info("Diff engine initialized")
    
    async def generate_preview(
        self,
        plan: Dict[str, Any],
        context: Dict[str, Any],
    ) -> DiffPreview:
        """
        Generate preview of planned changes.
        
        Args:
            plan: Execution plan with file changes
            context: Context with current file states
        
        Returns:
            DiffPreview with all changes
        """
        file_diffs = []
        total_additions = 0
        total_deletions = 0
        
        # Extract file changes from plan
        changes = plan.get("file_changes", {})
        
        for file_path, new_content in changes.items():
            # Get current content
            old_content = self._read_file(file_path)
            
            # Generate diff
            diff = self._generate_diff(
                file_path=file_path,
                old_content=old_content,
                new_content=new_content,
            )
            
            file_diffs.append(diff)
            total_additions += diff.additions
            total_deletions += diff.deletions
        
        # Generate summary
        summary = self._generate_summary(file_diffs)
        
        return DiffPreview(
            file_diffs=file_diffs,
            total_additions=total_additions,
            total_deletions=total_deletions,
            total_files=len(file_diffs),
            summary=summary,
        )
    
    def _read_file(self, file_path: str) -> str:
        """Read file content safely."""
        try:
            with open(file_path, 'r') as f:
                return f.read()
        except FileNotFoundError:
            return ""  # New file
        except Exception as e:
            logger.warning(f"Could not read {file_path}: {e}")
            return ""
    
    def _generate_diff(
        self,
        file_path: str,
        old_content: str,
        new_content: str,
    ) -> FileDiff:
        """Generate diff for a single file."""
        old_lines = old_content.splitlines(keepends=True)
        new_lines = new_content.splitlines(keepends=True)
        
        # Generate unified diff
        diff_lines = list(difflib.unified_diff(
            old_lines,
            new_lines,
            fromfile=f"a/{file_path}",
            tofile=f"b/{file_path}",
            lineterm='',
        ))
        
        # Count additions and deletions
        additions = sum(1 for line in diff_lines if line.startswith('+') and not line.startswith('+++'))
        deletions = sum(1 for line in diff_lines if line.startswith('-') and not line.startswith('---'))
        
        return FileDiff(
            file_path=file_path,
            old_content=old_content,
            new_content=new_content,
            diff_lines=diff_lines,
            additions=additions,
            deletions=deletions,
        )
    
    def _generate_summary(self, file_diffs: List[FileDiff]) -> str:
        """Generate human-readable summary."""
        if not file_diffs:
            return "No changes"
        
        lines = [f"Changes to {len(file_diffs)} file(s):"]
        
        for diff in file_diffs:
            status = "modified"
            if not diff.old_content:
                status = "created"
            elif not diff.new_content:
                status = "deleted"
            
            lines.append(
                f"  {diff.file_path}: {status} "
                f"(+{diff.additions}, -{diff.deletions})"
            )
        
        return "\n".join(lines)
    
    async def apply_changes(
        self,
        preview: DiffPreview,
        selected_files: Optional[List[str]] = None,
    ) -> Dict[str, bool]:
        """
        Apply changes from preview.
        
        Args:
            preview: DiffPreview to apply
            selected_files: Optional list of files to apply (partial application)
        
        Returns:
            Dict mapping file paths to success status
        """
        results = {}
        
        for diff in preview.file_diffs:
            # Skip if not selected (partial application)
            if selected_files and diff.file_path not in selected_files:
                continue
            
            try:
                # Write new content
                file_path = Path(diff.file_path)
                file_path.parent.mkdir(parents=True, exist_ok=True)
                
                with open(file_path, 'w') as f:
                    f.write(diff.new_content)
                
                results[diff.file_path] = True
                logger.info(f"Applied changes to {diff.file_path}")
                
            except Exception as e:
                logger.error(f"Failed to apply changes to {diff.file_path}: {e}")
                results[diff.file_path] = False
        
        return results
