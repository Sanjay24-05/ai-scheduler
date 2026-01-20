"""Intelligent scheduling algorithm service."""
from datetime import datetime, timedelta, time as dt_time
from typing import List, Dict, Optional, Any, Tuple
from dateutil import parser
from sqlalchemy.orm import Session
from models.task import Task, TaskPriority, TaskStatus
from models.schedule import Schedule
from models.preferences import UserPreferences
import logging
import pytz

logger = logging.getLogger(__name__)


class SchedulerService:
    """Service for intelligent task scheduling."""
    
    def __init__(self):
        """Initialize scheduler service."""
        pass
    
    def prioritize_tasks(self, tasks: List[Task]) -> List[Task]:
        """
        Sort tasks by priority, deadline urgency, and dependencies.
        
        Args:
            tasks: List of tasks to prioritize
            
        Returns:
            Sorted list of tasks
        """
        def task_score(task: Task) -> Tuple[int, float, int]:
            """Calculate priority score for a task."""
            # Priority weight (high=3, medium=2, low=1)
            priority_weight = {
                TaskPriority.HIGH: 3,
                TaskPriority.MEDIUM: 2,
                TaskPriority.LOW: 1
            }.get(task.priority, 2)
            
            # Deadline urgency (days until deadline)
            if task.deadline:
                now = datetime.now(task.deadline.tzinfo) if task.deadline.tzinfo else datetime.now()
                days_until = (task.deadline - now).days
                # Closer deadlines get higher urgency (inverse)
                urgency = 1.0 / max(days_until, 0.1)
            else:
                urgency = 0.0
            
            # Task ID for stable sorting
            task_id = task.id or 0
            
            # Return tuple for sorting (higher priority first, then urgency, then ID)
            return (-priority_weight, -urgency, task_id)
        
        return sorted(tasks, key=task_score)
    
    def _combine_datetime(self, date: datetime, time: dt_time) -> datetime:
        """Combine date and time objects, preserving timezone from date."""
        combined = datetime.combine(date.date(), time)
        if date.tzinfo:
            # Handle both pytz and native timezones
            if hasattr(date.tzinfo, 'localize'):
                return date.tzinfo.localize(combined.replace(tzinfo=None))
            return combined.replace(tzinfo=date.tzinfo)
        return combined
    
    def _add_break_if_needed(
        self,
        current_time: datetime,
        last_break: datetime,
        guideline: Dict[str, Any]
    ) -> Tuple[datetime, datetime]:
        """Check if a break is needed."""
        break_freq = guideline.get("break_frequency", 90)
        break_dur = guideline.get("break_duration", 15)
        
        time_since_break = (current_time - last_break).total_seconds() / 60
        
        if time_since_break >= break_freq:
            break_end = current_time + timedelta(minutes=break_dur)
            return break_end, break_end
        
        return current_time, last_break
    
    def _is_lunch_time(
        self,
        current_time: datetime,
        guideline: Dict[str, Any],
        lunch_taken: bool
    ) -> Tuple[bool, datetime]:
        """Check if it's lunch time and return lunch end time."""
        if lunch_taken or not guideline.get("lunch_time"):
            return False, current_time
        
        lunch_start = self._combine_datetime(current_time, guideline["lunch_time"])
        lunch_end = lunch_start + timedelta(minutes=guideline.get("lunch_duration", 60))
        
        # If current_time has reached lunch_start
        if current_time >= lunch_start and current_time < lunch_end:
            return True, lunch_end
            
        return False, current_time

    def _get_effective_guideline(self, date: datetime, guidelines: List[Any], preferences: Any) -> Dict[str, Any]:
        """Find the active guideline for a specific date, fallback to preferences."""
        target_date = date.date()
        day_of_week = date.isoweekday() % 7 # 0=Sunday, 1=Monday, ..., 6=Saturday
        
        # Filter guidelines that apply to this day and optionally date range
        candidates = []
        for g in guidelines:
            # Check day of week
            if day_of_week not in (g.days_of_week or []):
                continue
                
            # Check date range
            if g.start_date and target_date < g.start_date:
                continue
            if g.end_date and target_date > g.end_date:
                continue
                
            candidates.append(g)
            
        if candidates:
            # Take the first one (could be refined to find "most specific")
            g = candidates[0]
            # If working hours are not set, fallback to preferences
            return {
                "working_hours_start": g.working_hours_start or preferences.working_hours_start,
                "working_hours_end": g.working_hours_end or preferences.working_hours_end,
                "lunch_time": g.lunch_time,
                "lunch_duration": g.lunch_duration,
                "break_frequency": g.break_frequency,
                "break_duration": g.break_duration,
                "misc_breaks": g.misc_breaks or [],
                "buffer_time": g.buffer_time if g.buffer_time is not None else (preferences.buffer_time or 5)
            }
            
        # Fallback to default preferences
        return {
            "working_hours_start": preferences.working_hours_start,
            "working_hours_end": preferences.working_hours_end,
            "lunch_time": preferences.lunch_time,
            "lunch_duration": preferences.lunch_duration,
            "break_frequency": preferences.break_frequency,
            "break_duration": preferences.break_duration,
            "misc_breaks": [],
            "buffer_time": preferences.buffer_time or 5
        }
    
    async def generate_schedule(
        self,
        db: Session,
        user_id: int,
        task_ids: List[int],
        calendar_events: List[Dict],
        preferences: UserPreferences,
        start_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Generate optimal schedule for tasks.
        
        Args:
            db: Database session
            user_id: User ID
            task_ids: List of task IDs to schedule
            calendar_events: Existing calendar events
            preferences: Default user preferences (fallback)
            start_date: Start date for scheduling (default: tomorrow)
            
        Returns:
            Dictionary with schedule and conflicts
        """
        # Get tasks (including pending and flexible scheduled ones if needed)
        tasks = db.query(Task).filter(
            Task.id.in_(task_ids),
            Task.user_id == user_id
        ).all()
        
        # If we want to be truly adaptive, we should also consider 
        # already scheduled tasks that are flexible and can be moved.
        moving_tasks = tasks
        
        if not moving_tasks:
            return {"schedule": [], "conflicts": [], "message": "No tasks to schedule"}
            
        # Get active guidelines
        from models.time_guideline import TimeGuideline
        guidelines = db.query(TimeGuideline).filter(
            TimeGuideline.user_id == user_id,
            TimeGuideline.is_active == True
        ).all()
        
        # Prioritize tasks
        sorted_tasks = self.prioritize_tasks(tasks)
        
        # Set start date (tomorrow if not specified)
        if not start_date:
            start_date = datetime.now() + timedelta(days=1)
        start_date = start_date.replace(hour=0, minute=0, second=0, microsecond=0)
        
        # Initialize scheduling
        schedule = []
        conflicts = []
        current_date = start_date
        max_days = 30  # Don't schedule more than 30 days out
        
        # Track breaks and lunch
        last_break = None
        lunch_taken = False
        
        # Ensure start_date is timezone-aware if tasks/events are
        if current_date.tzinfo is None:
            current_date = pytz.UTC.localize(current_date)
        
        for task in sorted_tasks:
            scheduled = False
            days_tried = 0
            
            # Reset current_time for each task if we want to pack them
            # or keep it for sequential scheduling.
            # Here we keep current_time across tasks to avoid overlapping each other.
            
            while not scheduled and days_tried < max_days:
                # Get effective guideline for this date
                effective = self._get_effective_guideline(current_date, guidelines, preferences)
                
                # Get working hours for current date
                work_start = self._combine_datetime(current_date, effective["working_hours_start"])
                work_end = self._combine_datetime(current_date, effective["working_hours_end"])
                
                # Ensure work hours are timezone aware
                if work_start.tzinfo is None:
                    work_start = pytz.UTC.localize(work_start)
                    work_end = pytz.UTC.localize(work_end)
                
                # Initialize current time if needed
                if last_break is None:
                    current_time = work_start
                    last_break = work_start
                else:
                    # Continue from last scheduled time or start of day
                    if current_time.date() != current_date.date():
                        current_time = work_start
                        last_break = work_start
                        lunch_taken = False
                    elif current_time < work_start:
                        current_time = work_start
                
                # Get busy periods for this day
                busy_periods = self._get_busy_periods(calendar_events, schedule, current_date, effective)
                
                # Try to find a slot
                task_duration = task.estimated_duration or 60  # Default 60 minutes
                logger.debug(f"Attempting to schedule task {task.id} on {current_date.date()} starting from {current_time.time()}")
                
                while not scheduled and current_time + timedelta(minutes=task_duration) <= work_end:
                    # Check for lunch time
                    is_lunch, lunch_end = self._is_lunch_time(current_time, effective, lunch_taken)
                    if is_lunch:
                        logger.debug(f"Encountered lunch, moving to {lunch_end.time()}")
                        current_time = lunch_end
                        lunch_taken = True
                        continue
                    
                    # Check for break
                    new_curr, new_last = self._add_break_if_needed(current_time, last_break, effective)
                    if new_curr != current_time:
                        logger.debug(f"Encountered break, moving to {new_curr.time()}")
                        current_time = new_curr
                        last_break = new_last
                        continue
                    
                    # Try to schedule task
                    slot_start = current_time
                    slot_end = slot_start + timedelta(minutes=task_duration)
                    
                    # Check for conflicts
                    has_conflict = self._check_slot_conflict(slot_start, slot_end, busy_periods)
                    
                    if not has_conflict:
                        # Schedule the task
                        schedule.append({
                            "task_id": task.id,
                            "task_title": task.title,
                            "start_time": slot_start,
                            "end_time": slot_end,
                            "reasoning": self._generate_simple_reasoning(task, slot_start),
                        })
                        
                        # Update current time with buffer
                        buffer = max(effective.get("buffer_time", 5), 1)
                        current_time = slot_end + timedelta(minutes=buffer)
                        last_break = current_time # Reset last_break
                        scheduled = True
                        logger.debug(f"Successfully scheduled task {task.id} at {slot_start}")
                    else:
                        # Move to next available slot after the conflict
                        next_slot = self._find_next_available_slot(current_time, busy_periods, task_duration, work_end)
                        if next_slot and next_slot > current_time:
                            logger.debug(f"Conflict found, moving current_time to {next_slot.time()}")
                            current_time = next_slot
                        else:
                            # No more slots today
                            logger.debug(f"No more slots for today on {current_date.date()}")
                            break
                
                if not scheduled:
                    # Try next day
                    current_date += timedelta(days=1)
                    days_tried += 1
                    current_time = self._combine_datetime(current_date, preferences.working_hours_start)
                    if current_time.tzinfo is None:
                        current_time = pytz.UTC.localize(current_time)
                    last_break = current_time
                    lunch_taken = False
                    logger.debug(f"Moving to next day: {current_date.date()}")
            
            if not scheduled:
                conflicts.append({
                    "task_id": task.id,
                    "task_title": task.title,
                    "reason": "Could not find available slot within 30 days"
                })
        
        return {
            "schedule": schedule,
            "conflicts": conflicts,
            "message": f"Scheduled {len(schedule)} tasks, {len(conflicts)} conflicts"
        }
    
    def _get_busy_periods(
        self,
        calendar_events: List[Dict],
        schedule: List[Dict],
        date: datetime,
        guideline: Dict[str, Any] = None
    ) -> List[Tuple[datetime, datetime]]:
        """Get all busy periods for a specific date, including misc breaks."""
        busy_periods = []
        
        # Add calendar events
        for event in calendar_events:
            event_start = parser.parse(event['start'])
            event_end = parser.parse(event['end'])
            
            if event_start.date() == date.date():
                busy_periods.append((event_start, event_end))
        
        # Add already scheduled tasks
        for item in schedule:
            if item['start_time'].date() == date.date():
                busy_periods.append((item['start_time'], item['end_time']))
                
        # Add misc breaks from guideline
        if guideline and guideline.get("misc_breaks"):
            for brk in guideline["misc_breaks"]:
                try:
                    # Parse HH:MM
                    h, m = map(int, brk["start_time"].split(':'))
                    brk_start = self._combine_datetime(date, dt_time(h, m))
                    brk_end = brk_start + timedelta(minutes=brk.get("duration", 15))
                    busy_periods.append((brk_start, brk_end))
                except Exception as e:
                    logger.error(f"Error parsing misc break: {str(e)}")
                
        # Handle timezone awareness for all busy periods
        normalized_busy = []
        for start, end in busy_periods:
            if start.tzinfo and not date.tzinfo:
                start = start.replace(tzinfo=None)
                end = end.replace(tzinfo=None)
            elif start.tzinfo is None and date.tzinfo is not None:
                start = pytz.UTC.localize(start)
                end = pytz.UTC.localize(end)
            normalized_busy.append((start, end))
        
        # Sort by start time
        normalized_busy.sort(key=lambda x: x[0])
        
        return normalized_busy
    
    def _check_slot_conflict(
        self,
        slot_start: datetime,
        slot_end: datetime,
        busy_periods: List[Tuple[datetime, datetime]]
    ) -> bool:
        """Check if a time slot conflicts with busy periods."""
        for busy_start, busy_end in busy_periods:
            # Check for overlap
            if slot_start < busy_end and slot_end > busy_start:
                return True
        return False
    
    def _find_next_available_slot(
        self,
        current_time: datetime,
        busy_periods: List[Tuple[datetime, datetime]],
        duration_minutes: int,
        work_end: datetime
    ) -> Optional[datetime]:
        """Find the next available time slot after a conflict."""
        temp_time = current_time
        
        for busy_start, busy_end in busy_periods:
            # If there's an overlap
            if temp_time < busy_end and (temp_time + timedelta(minutes=duration_minutes)) > busy_start:
                # Move to the end of this busy period
                temp_time = busy_end
                
        # After skipping all overlapping busy periods, check if we still fit in today
        if temp_time + timedelta(minutes=duration_minutes) <= work_end:
            return temp_time
        
        return None
    
    def _generate_simple_reasoning(self, task: Task, start_time: datetime) -> str:
        """Generate simple reasoning for scheduling decision."""
        reasons = []
        
        if task.priority == TaskPriority.HIGH:
            reasons.append("high priority")
        
        if task.deadline:
            now = datetime.now(task.deadline.tzinfo) if task.deadline.tzinfo else datetime.now()
            days_until = (task.deadline - now).days
            if days_until <= 0:
                reasons.append("deadline today")
            elif days_until <= 2:
                reasons.append("urgent deadline")
            elif days_until <= 7:
                reasons.append("approaching deadline")
        
        if start_time.hour < 11:
            reasons.append("peak morning productivity")
        elif start_time.hour > 16:
            reasons.append("end of day wrap-up")
            
        if not reasons:
            reasons.append("optimal availability")
        
        primary = reasons[0]
        secondary = f", {reasons[1]}" if len(reasons) > 1 else ""
        
        return f"Scheduled for {primary}{secondary}."


# Global scheduler service instance
scheduler_service = SchedulerService()
