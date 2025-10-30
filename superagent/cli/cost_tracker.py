# File: superagent/cli/cost_tracker.py
# Version: 2.0.0 - Complete cost tracking implementation

"""
Cost Tracker for SuperAgent v2.0.0

Tracks token usage and costs across different LLM providers and models.
Provides detailed analytics and cost optimization insights.
"""

from datetime import datetime
from typing import Dict, List, Optional
from dataclasses import dataclass, field
import json
from pathlib import Path


@dataclass
class RequestRecord:
    """Record of a single API request."""
    timestamp: datetime
    model: str
    input_tokens: int
    output_tokens: int
    cost: float
    metadata: Dict = field(default_factory=dict)


class CostTracker:
    """Track costs and token usage for LLM requests."""
    
    # Pricing per 1M tokens (as of 2024)
    PRICING = {
        "claude-3-5-sonnet-20241022": {"input": 3.00, "output": 15.00},
        "claude-3-5-haiku-20241022": {"input": 0.80, "output": 4.00},
        "claude-3-opus-20240229": {"input": 15.00, "output": 75.00},
        "gpt-4-turbo-preview": {"input": 10.00, "output": 30.00},
        "gpt-4": {"input": 30.00, "output": 60.00},
        "gpt-3.5-turbo": {"input": 0.50, "output": 1.50},
    }
    
    def __init__(self, storage_path: Optional[Path] = None):
        self.storage_path = storage_path or Path.home() / ".superagent" / "cost_tracking.json"
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        
        self.records: List[RequestRecord] = []
        self._load_records()
    
    def _load_records(self):
        """Load records from storage."""
        if self.storage_path.exists():
            try:
                with open(self.storage_path) as f:
                    data = json.load(f)
                    self.records = [
                        RequestRecord(
                            timestamp=datetime.fromisoformat(r["timestamp"]),
                            model=r["model"],
                            input_tokens=r["input_tokens"],
                            output_tokens=r["output_tokens"],
                            cost=r["cost"],
                            metadata=r.get("metadata", {})
                        )
                        for r in data
                    ]
            except Exception:
                self.records = []
    
    def _save_records(self):
        """Save records to storage."""
        data = [
            {
                "timestamp": r.timestamp.isoformat(),
                "model": r.model,
                "input_tokens": r.input_tokens,
                "output_tokens": r.output_tokens,
                "cost": r.cost,
                "metadata": r.metadata
            }
            for r in self.records
        ]
        
        with open(self.storage_path, "w") as f:
            json.dump(data, f, indent=2)
    
    def calculate_cost(self, model: str, input_tokens: int, output_tokens: int) -> float:
        """Calculate cost for a request."""
        pricing = self.PRICING.get(model, {"input": 1.0, "output": 2.0})
        
        input_cost = (input_tokens / 1_000_000) * pricing["input"]
        output_cost = (output_tokens / 1_000_000) * pricing["output"]
        
        return input_cost + output_cost
    
    def track_request(
        self,
        model: str,
        input_tokens: int,
        output_tokens: int,
        metadata: Optional[Dict] = None
    ):
        """Track a request."""
        cost = self.calculate_cost(model, input_tokens, output_tokens)
        
        record = RequestRecord(
            timestamp=datetime.now(),
            model=model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cost=cost,
            metadata=metadata or {}
        )
        
        self.records.append(record)
        self._save_records()
    
    def get_stats(self) -> Dict:
        """Get cost statistics."""
        if not self.records:
            return {
                "total_requests": 0,
                "total_input_tokens": 0,
                "total_output_tokens": 0,
                "total_cost": 0.0,
                "by_model": {}
            }
        
        total_input = sum(r.input_tokens for r in self.records)
        total_output = sum(r.output_tokens for r in self.records)
        total_cost = sum(r.cost for r in self.records)
        
        by_model = {}
        for record in self.records:
            if record.model not in by_model:
                by_model[record.model] = 0.0
            by_model[record.model] += record.cost
        
        return {
            "total_requests": len(self.records),
            "total_input_tokens": total_input,
            "total_output_tokens": total_output,
            "total_cost": total_cost,
            "by_model": by_model
        }
    
    def get_recent_records(self, limit: int = 10) -> List[RequestRecord]:
        """Get recent records."""
        return sorted(self.records, key=lambda r: r.timestamp, reverse=True)[:limit]
    
    def clear(self):
        """Clear all records."""
        self.records = []
        self._save_records()
