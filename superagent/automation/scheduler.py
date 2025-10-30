"""
Task scheduler for automated execution.
"""
import asyncio
from typing import Dict, Any, Optional, Callable, List
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum

from superagent.core.logger import get_logger

logger = get_logger(__name__)


class ScheduleType(str, Enum):
    """Schedule types."""
    ONCE = "once"
    INTERVAL = "interval"
    CRON = "cron"
    DAILY = "daily"
    WEEKLY = "weekly"


@dataclass
class Schedule:
    """Schedule configuration."""
    id: str
    type: ScheduleType
    task: Callable
    args: Dict[str, Any]
    interval: Optional[timedelta] = None
    cron_expression: Optional[str] = None
    next_run: Optional[datetime] = None
    enabled: bool = True


class Scheduler:
    """Task scheduler."""
    
    def __init__(self):
        self.schedules: Dict[str, Schedule] = {}
        self._running = False
        self._task: Optional[asyncio.Task] = None
    
    def add_schedule(self, schedule: Schedule) -> None:
        """Add a schedule."""
        self.schedules[schedule.id] = schedule
        logger.info(f"Added schedule: {schedule.id}")
    
    def remove_schedule(self, schedule_id: str) -> None:
        """Remove a schedule."""
        if schedule_id in self.schedules:
            del self.schedules[schedule_id]
            logger.info(f"Removed schedule: {schedule_id}")
    
    def get_schedule(self, schedule_id: str) -> Optional[Schedule]:
        """Get schedule by ID."""
        return self.schedules.get(schedule_id)
    
    def list_schedules(self) -> List[Schedule]:
        """List all schedules."""
        return list(self.schedules.values())
    
    async def start(self) -> None:
        """Start the scheduler."""
        if self._running:
            logger.warning("Scheduler already running")
            return
        
        self._running = True
        self._task = asyncio.create_task(self._run_loop())
        logger.info("Scheduler started")
    
    async def stop(self) -> None:
        """Stop the scheduler."""
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("Scheduler stopped")
    
    async def _run_loop(self) -> None:
        """Main scheduler loop."""
        while self._running:
            try:
                await self._check_schedules()
                await asyncio.sleep(1)  # Check every second
            except Exception as e:
                logger.error(f"Error in scheduler loop: {e}")
    
    async def _check_schedules(self) -> None:
        """Check and execute due schedules."""
        now = datetime.now()
        
        for schedule in self.schedules.values():
            if not schedule.enabled:
                continue
            
            if schedule.next_run and now >= schedule.next_run:
                await self._execute_schedule(schedule)
                self._update_next_run(schedule)
    
    async def _execute_schedule(self, schedule: Schedule) -> None:
        """Execute a scheduled task."""
        try:
            logger.info(f"Executing schedule: {schedule.id}")
            await schedule.task(**schedule.args)
        except Exception as e:
            logger.error(f"Error executing schedule {schedule.id}: {e}")
    
    def _update_next_run(self, schedule: Schedule) -> None:
        """Update next run time for schedule."""
        if schedule.type == ScheduleType.ONCE:
            schedule.enabled = False
        elif schedule.type == ScheduleType.INTERVAL and schedule.interval:
            schedule.next_run = datetime.now() + schedule.interval
        elif schedule.type == ScheduleType.DAILY:
            schedule.next_run = datetime.now() + timedelta(days=1)
        elif schedule.type == ScheduleType.WEEKLY:
            schedule.next_run = datetime.now() + timedelta(weeks=1)
