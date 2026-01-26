"""Scheduler Engine - Automated Remediation Scheduling.

This module provides cron-like scheduling for automated remediation,
event-triggered fixes, and background task management.

Features:
    - Cron-style scheduling (daily, weekly, monthly, custom)
    - Event-triggered remediation (on PR merge, on issue, on commit)
    - Background task execution with async support
    - Task queue management
    - Task history and status tracking
    
Example:
    >>> from ollama.pmo.scheduler import SchedulerEngine
    >>> scheduler = SchedulerEngine()
    >>> scheduler.schedule_daily(hour=2, minute=0)  # 2am daily
    >>> scheduler.start()
"""

from typing import Dict, List, Optional, Any, Callable
from pathlib import Path
from datetime import datetime, timedelta, time
from dataclasses import dataclass, field
from enum import Enum
import logging
import json
import asyncio
import threading
import time as time_module
from queue import Queue, Empty

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class TaskStatus(Enum):
    """Task execution status."""
    
    PENDING = 'pending'
    RUNNING = 'running'
    COMPLETED = 'completed'
    FAILED = 'failed'
    CANCELLED = 'cancelled'


class TriggerType(Enum):
    """Task trigger type."""
    
    CRON = 'cron'  # Time-based schedule
    EVENT = 'event'  # Event-driven
    MANUAL = 'manual'  # Manually triggered


@dataclass
class ScheduledTask:
    """Represents a scheduled remediation task."""
    
    task_id: str
    name: str
    trigger_type: TriggerType
    schedule: str  # Cron expression or event name
    function: Callable
    args: tuple = field(default_factory=tuple)
    kwargs: Dict[str, Any] = field(default_factory=dict)
    enabled: bool = True
    last_run: Optional[datetime] = None
    next_run: Optional[datetime] = None
    run_count: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'task_id': self.task_id,
            'name': self.name,
            'trigger_type': self.trigger_type.value,
            'schedule': self.schedule,
            'enabled': self.enabled,
            'last_run': self.last_run.isoformat() if self.last_run else None,
            'next_run': self.next_run.isoformat() if self.next_run else None,
            'run_count': self.run_count,
        }


@dataclass
class TaskResult:
    """Result of a task execution."""
    
    task_id: str
    status: TaskStatus
    start_time: datetime
    end_time: Optional[datetime] = None
    duration_ms: int = 0
    result: Any = None
    error: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'task_id': self.task_id,
            'status': self.status.value,
            'start_time': self.start_time.isoformat(),
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'duration_ms': self.duration_ms,
            'error': self.error,
        }


class SchedulerEngine:
    """Automated remediation scheduling engine.
    
    Provides cron-like scheduling, event triggering, and background
    task management for automated compliance remediation.
    
    Attributes:
        repo_path: Local repository path
        history_file: Path to task history file
        running: Whether scheduler is running
        tasks: Registered scheduled tasks
        
    Example:
        >>> scheduler = SchedulerEngine()
        >>> scheduler.schedule_daily(hour=2, minute=0)
        >>> scheduler.on_event('pr_merged', remediate_pr)
        >>> scheduler.start()  # Run in background
    """
    
    def __init__(
        self,
        repo_path: Optional[Path] = None,
    ) -> None:
        """Initialize scheduler engine.
        
        Args:
            repo_path: Local path to repository
        """
        self.repo_path = Path(repo_path) if repo_path else Path.cwd()
        
        # History file
        self.history_file = self.repo_path / '.pmo' / 'schedule_history.jsonl'
        self.history_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Scheduler state
        self.running = False
        self.tasks: Dict[str, ScheduledTask] = {}
        self.task_queue: Queue = Queue()
        self.worker_thread: Optional[threading.Thread] = None
        
        # Task results
        self.results: List[TaskResult] = []
    
    def schedule_daily(
        self,
        hour: int = 0,
        minute: int = 0,
        function: Optional[Callable] = None,
        task_name: str = "Daily Remediation",
    ) -> str:
        """Schedule daily remediation task.
        
        Args:
            hour: Hour to run (0-23)
            minute: Minute to run (0-59)
            function: Function to call (default: basic remediation)
            task_name: Human-readable task name
            
        Returns:
            Task ID
            
        Example:
            >>> task_id = scheduler.schedule_daily(hour=2, minute=30)
        """
        task_id = f"daily_{hour:02d}{minute:02d}"
        schedule = f"0 {minute} {hour} * * *"  # Cron: daily at HH:MM
        
        # Calculate next run
        now = datetime.now()
        next_run = datetime.combine(now.date(), time(hour=hour, minute=minute))
        if next_run <= now:
            next_run += timedelta(days=1)
        
        task = ScheduledTask(
            task_id=task_id,
            name=task_name,
            trigger_type=TriggerType.CRON,
            schedule=schedule,
            function=function or self._default_remediation,
            next_run=next_run,
        )
        
        self.tasks[task_id] = task
        logger.info(f"Scheduled daily task: {task_name} at {hour:02d}:{minute:02d}")
        
        return task_id
    
    def schedule_weekly(
        self,
        day_of_week: int = 0,  # 0=Monday
        hour: int = 0,
        minute: int = 0,
        function: Optional[Callable] = None,
        task_name: str = "Weekly Remediation",
    ) -> str:
        """Schedule weekly remediation task.
        
        Args:
            day_of_week: Day (0=Monday, 6=Sunday)
            hour: Hour to run (0-23)
            minute: Minute to run (0-59)
            function: Function to call
            task_name: Human-readable task name
            
        Returns:
            Task ID
            
        Example:
            >>> task_id = scheduler.schedule_weekly(day_of_week=0, hour=3)
        """
        task_id = f"weekly_{day_of_week}_{hour:02d}{minute:02d}"
        schedule = f"0 {minute} {hour} * * {day_of_week}"
        
        # Calculate next run
        now = datetime.now()
        days_ahead = day_of_week - now.weekday()
        if days_ahead < 0 or (days_ahead == 0 and now.time() >= time(hour, minute)):
            days_ahead += 7
        
        next_run = datetime.combine(now.date(), time(hour=hour, minute=minute))
        next_run += timedelta(days=days_ahead)
        
        task = ScheduledTask(
            task_id=task_id,
            name=task_name,
            trigger_type=TriggerType.CRON,
            schedule=schedule,
            function=function or self._default_remediation,
            next_run=next_run,
        )
        
        self.tasks[task_id] = task
        logger.info(f"Scheduled weekly task: {task_name}")
        
        return task_id
    
    def schedule_monthly(
        self,
        day: int = 1,
        hour: int = 0,
        minute: int = 0,
        function: Optional[Callable] = None,
        task_name: str = "Monthly Remediation",
    ) -> str:
        """Schedule monthly remediation task.
        
        Args:
            day: Day of month (1-31)
            hour: Hour to run (0-23)
            minute: Minute to run (0-59)
            function: Function to call
            task_name: Human-readable task name
            
        Returns:
            Task ID
        """
        task_id = f"monthly_{day:02d}_{hour:02d}{minute:02d}"
        schedule = f"0 {minute} {hour} {day} * *"
        
        # Calculate next run
        now = datetime.now()
        if now.day < day:
            # This month
            next_run = datetime.combine(
                now.replace(day=day).date(),
                time(hour=hour, minute=minute)
            )
        else:
            # Next month
            if now.month == 12:
                next_month = now.replace(year=now.year + 1, month=1, day=day)
            else:
                next_month = now.replace(month=now.month + 1, day=day)
            next_run = datetime.combine(next_month.date(), time(hour=hour, minute=minute))
        
        task = ScheduledTask(
            task_id=task_id,
            name=task_name,
            trigger_type=TriggerType.CRON,
            schedule=schedule,
            function=function or self._default_remediation,
            next_run=next_run,
        )
        
        self.tasks[task_id] = task
        logger.info(f"Scheduled monthly task: {task_name}")
        
        return task_id
    
    def on_event(
        self,
        event_name: str,
        function: Callable,
        task_name: Optional[str] = None,
    ) -> str:
        """Register event-triggered remediation.
        
        Args:
            event_name: Name of triggering event (pr_merged, issue_created, etc.)
            function: Function to call when event occurs
            task_name: Human-readable task name
            
        Returns:
            Task ID
            
        Example:
            >>> scheduler.on_event('pr_merged', lambda: print("PR merged!"))
        """
        task_id = f"event_{event_name}"
        
        task = ScheduledTask(
            task_id=task_id,
            name=task_name or f"On {event_name}",
            trigger_type=TriggerType.EVENT,
            schedule=event_name,
            function=function,
        )
        
        self.tasks[task_id] = task
        logger.info(f"Registered event trigger: {event_name}")
        
        return task_id
    
    def trigger_event(self, event_name: str, **kwargs: Any) -> None:
        """Manually trigger an event.
        
        Args:
            event_name: Name of event to trigger
            **kwargs: Arguments to pass to event handlers
            
        Example:
            >>> scheduler.trigger_event('pr_merged', pr_number=123)
        """
        for task_id, task in self.tasks.items():
            if task.trigger_type == TriggerType.EVENT and task.schedule == event_name:
                if task.enabled:
                    logger.info(f"Triggering event task: {task.name}")
                    self.task_queue.put((task, kwargs))
    
    def start(self) -> None:
        """Start scheduler in background thread.
        
        Example:
            >>> scheduler.start()  # Runs in background
            >>> # ... do other work ...
            >>> scheduler.stop()
        """
        if self.running:
            logger.warning("Scheduler already running")
            return
        
        self.running = True
        self.worker_thread = threading.Thread(target=self._scheduler_loop, daemon=True)
        self.worker_thread.start()
        logger.info("Scheduler started")
    
    def stop(self) -> None:
        """Stop scheduler.
        
        Example:
            >>> scheduler.stop()
        """
        if not self.running:
            logger.warning("Scheduler not running")
            return
        
        self.running = False
        if self.worker_thread:
            self.worker_thread.join(timeout=5)
        logger.info("Scheduler stopped")
    
    def run_task(self, task_id: str, **kwargs: Any) -> Optional[TaskResult]:
        """Manually run a task immediately.
        
        Args:
            task_id: ID of task to run
            **kwargs: Arguments to pass to task function
            
        Returns:
            Task result
            
        Example:
            >>> result = scheduler.run_task('daily_0200')
        """
        if task_id not in self.tasks:
            logger.error(f"Task not found: {task_id}")
            return None
        
        task = self.tasks[task_id]
        return self._execute_task(task, kwargs)
    
    def get_tasks(self) -> List[Dict[str, Any]]:
        """Get all registered tasks.
        
        Returns:
            List of task information
        """
        return [task.to_dict() for task in self.tasks.values()]
    
    def get_task_history(
        self,
        task_id: Optional[str] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """Get task execution history.
        
        Args:
            task_id: Filter by specific task ID
            limit: Maximum results to return
            
        Returns:
            List of task results
        """
        history: List[Dict[str, Any]] = []
        
        if not self.history_file.exists():
            return history
        
        try:
            with open(self.history_file, 'r') as f:
                for line in f:
                    try:
                        entry = json.loads(line)
                        
                        if task_id and entry.get('task_id') != task_id:
                            continue
                        
                        history.append(entry)
                        
                        if len(history) >= limit:
                            break
                            
                    except json.JSONDecodeError:
                        continue
        except Exception as e:
            logger.error(f"Failed to read history: {e}")
        
        return list(reversed(history))  # Most recent first
    
    def _scheduler_loop(self) -> None:
        """Main scheduler loop (runs in background thread)."""
        logger.info("Scheduler loop started")
        
        while self.running:
            try:
                # Check for queued tasks
                try:
                    task, kwargs = self.task_queue.get(timeout=1)
                    self._execute_task(task, kwargs)
                except Empty:
                    pass
                
                # Check scheduled tasks
                now = datetime.now()
                for task in self.tasks.values():
                    if (
                        task.enabled
                        and task.trigger_type == TriggerType.CRON
                        and task.next_run
                        and now >= task.next_run
                    ):
                        self._execute_task(task, {})
                        self._schedule_next_run(task)
                
                # Sleep briefly
                time_module.sleep(10)  # Check every 10 seconds
                
            except Exception as e:
                logger.error(f"Scheduler loop error: {e}")
        
        logger.info("Scheduler loop stopped")
    
    def _execute_task(self, task: ScheduledTask, kwargs: Dict[str, Any]) -> TaskResult:
        """Execute a task.
        
        Args:
            task: Task to execute
            kwargs: Keyword arguments for task function
            
        Returns:
            Task result
        """
        start_time = datetime.now()
        
        try:
            logger.info(f"Executing task: {task.name}")
            
            # Call function
            result = task.function(*task.args, **{**task.kwargs, **kwargs})
            
            # Update task
            task.last_run = start_time
            task.run_count += 1
            
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds() * 1000
            
            task_result = TaskResult(
                task_id=task.task_id,
                status=TaskStatus.COMPLETED,
                start_time=start_time,
                end_time=end_time,
                duration_ms=int(duration),
                result=result,
            )
            
            logger.info(f"Task completed: {task.name} ({duration:.0f}ms)")
            
        except Exception as e:
            logger.error(f"Task failed: {task.name} - {e}")
            
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds() * 1000
            
            task_result = TaskResult(
                task_id=task.task_id,
                status=TaskStatus.FAILED,
                start_time=start_time,
                end_time=end_time,
                duration_ms=int(duration),
                error=str(e),
            )
        
        # Log to history
        self._log_to_history(task_result)
        self.results.append(task_result)
        
        return task_result
    
    def _schedule_next_run(self, task: ScheduledTask) -> None:
        """Calculate next run time for a task.
        
        Args:
            task: Task to schedule
        """
        if not task.next_run:
            return
        
        # Parse schedule (simplified - only handles specific patterns)
        if task.schedule.startswith("0 ") and task.schedule.count(" ") == 5:
            parts = task.schedule.split()
            minute = int(parts[1])
            hour = int(parts[2])
            day = parts[3]
            month = parts[4]
            dow = parts[5]
            
            # Daily
            if day == "*" and month == "*" and dow == "*":
                task.next_run += timedelta(days=1)
            
            # Weekly
            elif day == "*" and month == "*" and dow != "*":
                task.next_run += timedelta(days=7)
            
            # Monthly
            elif day != "*" and month == "*":
                # Next month
                if task.next_run.month == 12:
                    task.next_run = task.next_run.replace(year=task.next_run.year + 1, month=1)
                else:
                    task.next_run = task.next_run.replace(month=task.next_run.month + 1)
    
    def _log_to_history(self, result: TaskResult) -> None:
        """Log task result to history file.
        
        Args:
            result: Task result to log
        """
        try:
            with open(self.history_file, 'a') as f:
                f.write(json.dumps(result.to_dict()) + '\n')
        except Exception as e:
            logger.error(f"Failed to log to history: {e}")
    
    def _default_remediation(self) -> Dict[str, Any]:
        """Default remediation function.
        
        Returns:
            Remediation result
        """
        logger.info("Running default remediation")
        # Placeholder - would call PMOAgent.auto_remediate_drift()
        return {'status': 'completed', 'fixes_applied': 0}
