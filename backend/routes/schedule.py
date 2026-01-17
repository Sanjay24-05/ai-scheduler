"""Schedule management routes."""
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from database import get_db
from models.task import Task, TaskStatus
from models.schedule import Schedule
from models.preferences import UserPreferences
from services.scheduler import scheduler_service
from services.calendar_service import calendar_service
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/schedule", tags=["schedule"])


class GenerateScheduleRequest(BaseModel):
    task_ids: List[int]
    start_date: Optional[str] = None


def get_current_user_id(request: Request) -> int:
    """Get current user ID from session."""
    user_id = request.session.get("user_id")
    if not user_id:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return user_id


@router.post("/generate")
async def generate_schedule(
    data: GenerateScheduleRequest,
    request: Request,
    db: Session = Depends(get_db),
):
    """
    Generate schedule for tasks.
    
    Args:
        data: Task IDs and optional start date
        
    Returns:
        Generated schedule
    """
    try:
        user_id = get_current_user_id(request)
        
        # Get user preferences
        preferences = db.query(UserPreferences).filter(
            UserPreferences.user_id == user_id
        ).first()
        
        if not preferences:
            raise HTTPException(status_code=400, detail="User preferences not found")
        
        # Parse start date
        start_date = None
        if data.start_date:
            from dateutil import parser
            start_date = parser.parse(data.start_date)
        
        # Get calendar events (placeholder - will integrate with Google Calendar)
        calendar_events = []
        
        # Generate schedule
        result = await scheduler_service.generate_schedule(
            db=db,
            user_id=user_id,
            task_ids=data.task_ids,
            calendar_events=calendar_events,
            preferences=preferences,
            start_date=start_date
        )
        
        # Save schedule to database
        for item in result["schedule"]:
            # Check if schedule already exists for this task
            existing = db.query(Schedule).filter(
                Schedule.task_id == item["task_id"],
                Schedule.user_id == user_id
            ).first()
            
            if existing:
                # Update existing schedule
                existing.start_time = item["start_time"]
                existing.end_time = item["end_time"]
                existing.reasoning = item["reasoning"]
            else:
                # Create new schedule
                schedule = Schedule(
                    user_id=user_id,
                    task_id=item["task_id"],
                    start_time=item["start_time"],
                    end_time=item["end_time"],
                    reasoning=item["reasoning"],
                    is_synced=False
                )
                db.add(schedule)
            
            # Update task status
            task = db.query(Task).filter(Task.id == item["task_id"]).first()
            if task:
                task.status = TaskStatus.SCHEDULED
        
        db.commit()
        
        return result
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating schedule: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to generate schedule")


@router.get("/current")
async def get_current_schedule(
    request: Request,
    db: Session = Depends(get_db),
    days: int = 7,
):
    """
    Get current schedule for the user.
    
    Args:
        days: Number of days to fetch (default: 7)
        
    Returns:
        Current schedule
    """
    try:
        user_id = get_current_user_id(request)
        
        # Get schedules for next N days
        start_date = datetime.utcnow()
        end_date = start_date + timedelta(days=days)
        
        schedules = db.query(Schedule).filter(
            Schedule.user_id == user_id,
            Schedule.start_time >= start_date,
            Schedule.start_time <= end_date
        ).order_by(Schedule.start_time).all()
        
        # Include task details
        result = []
        for schedule in schedules:
            task = db.query(Task).filter(Task.id == schedule.task_id).first()
            schedule_dict = schedule.to_dict()
            if task:
                schedule_dict["task"] = task.to_dict()
            result.append(schedule_dict)
        
        return result
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting current schedule: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get schedule")


@router.get("/daily/{date}")
async def get_daily_schedule(
    date: str,
    request: Request,
    db: Session = Depends(get_db),
):
    """
    Get schedule for a specific day.
    
    Args:
        date: Date in ISO format (YYYY-MM-DD)
        
    Returns:
        Daily schedule
    """
    try:
        user_id = get_current_user_id(request)
        
        # Parse date
        from dateutil import parser
        target_date = parser.parse(date)
        start_of_day = target_date.replace(hour=0, minute=0, second=0, microsecond=0)
        end_of_day = start_of_day + timedelta(days=1)
        
        # Get schedules for the day
        schedules = db.query(Schedule).filter(
            Schedule.user_id == user_id,
            Schedule.start_time >= start_of_day,
            Schedule.start_time < end_of_day
        ).order_by(Schedule.start_time).all()
        
        # Include task details
        result = []
        for schedule in schedules:
            task = db.query(Task).filter(Task.id == schedule.task_id).first()
            schedule_dict = schedule.to_dict()
            if task:
                schedule_dict["task"] = task.to_dict()
            result.append(schedule_dict)
        
        return result
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting daily schedule: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get daily schedule")


@router.get("/explain/{task_id}")
async def explain_scheduling(
    task_id: int,
    request: Request,
    db: Session = Depends(get_db),
):
    """
    Get explanation for why a task was scheduled at its time.
    
    Args:
        task_id: Task ID
        
    Returns:
        Scheduling explanation
    """
    try:
        user_id = get_current_user_id(request)
        
        # Get schedule for task
        schedule = db.query(Schedule).filter(
            Schedule.task_id == task_id,
            Schedule.user_id == user_id
        ).first()
        
        if not schedule:
            raise HTTPException(status_code=404, detail="Schedule not found for this task")
        
        return {
            "task_id": task_id,
            "reasoning": schedule.reasoning,
            "start_time": schedule.start_time.isoformat(),
            "end_time": schedule.end_time.isoformat()
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error explaining scheduling: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to explain scheduling")
