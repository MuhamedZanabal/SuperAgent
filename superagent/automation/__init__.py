"""
Automation layer for SuperAgent v2.0.0

Provides scheduling, chaining, and reactive triggers.
"""
from .scheduler import Scheduler, Schedule
from .chain import Chain, ChainStep
from .triggers import Trigger, TriggerManager

__all__ = ["Scheduler", "Schedule", "Chain", "ChainStep", "Trigger", "TriggerManager"]
