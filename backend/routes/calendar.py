"""Calendar integration routes."""
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from database import get_db
from models.schedule import Schedule
from models.task import Task
from services.calendar_service import calendar_service
from pydantic import BaseModel
from typing import Optional
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/calendar", tags=["calendar"])


class SyncRequest(BaseModel):
    schedule_ids: Optional[list[int]] = None  # If None, sync all


def get_current_user_id(request: Request) -> int:
    """Get current user ID from session."""
    user_id = request.session.get("user_id")
    if not user_id:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return user_id


def get_oauth_credentials(request: Request) -> dict:
    """Get OAuth credentials from session."""
    credentials = request.session.get("oauth_credentials")
    if not credentials:
        raise HTTPException(status_code=401, detail="Not authenticated with Google Calendar")
    return credentials


@router.get("/events")
async def get_calendar_events(
    request: Request,
    days: int = 7,
):
    """
    Fetch Google Calendar events.
    
    Args:
        days: Number of days to fetch (default: 7)
        
    Returns:
        List of calendar events
    """
    try:
        user_id = get_current_user_id(request)
        credentials = get_oauth_credentials(request)
        
        # Calculate date range
        start_date = datetime.utcnow()
        end_date = start_date + timedelta(days=days)
        
        # Fetch events
        events = await calendar_service.get_calendar_events(
            credentials,
            start_date,
            end_date
        )
        
        return events
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching calendar events: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch calendar events")


@router.post("/sync")
async def sync_to_calendar(
    data: SyncRequest,
    request: Request,
    db: Session = Depends(get_db),
):
    """
    Sync schedules to Google Calendar.
    
    Args:
        data: Optional list of schedule IDs to sync
        
    Returns:
        Sync results
    """
    try:
        user_id = get_current_user_id(request)
        credentials = get_oauth_credentials(request)
        
        # Get schedules to sync
        query = db.query(Schedule).filter(Schedule.user_id == user_id)
        
        if data.schedule_ids:
            query = query.filter(Schedule.id.in_(data.schedule_ids))
        else:
            # Sync all unsynced schedules
            query = query.filter(Schedule.is_synced == False)
        
        schedules = query.all()
        
        if not schedules:
            return {"message": "No schedules to sync", "synced": 0}
        
        # Sync each schedule
        synced_count = 0
        errors = []
        
        for schedule in schedules:
            try:
                # Get task details
                task = db.query(Task).filter(Task.id == schedule.task_id).first()
                if not task:
                    continue
                
                if schedule.calendar_event_id:
                    # Update existing event
                    success = await calendar_service.update_event(
                        credentials,
                        schedule.calendar_event_id,
                        schedule.start_time,
                        schedule.end_time
                    )
                else:
                    # Create new event
                    event_id = await calendar_service.create_event(
                        credentials,
                        task.title,
                        task.description or "",
                        schedule.start_time,
                        schedule.end_time
                    )
                    
                    if event_id:
                        schedule.calendar_event_id = event_id
                        success = True
                    else:
                        success = False
                
                if success:
                    schedule.is_synced = True
                    # Safeguard: Ensure task status is also updated to SCHEDULED
                    from models.task import TaskStatus
                    task.status = TaskStatus.SCHEDULED
                    synced_count += 1
                else:
                    errors.append(f"Failed to sync schedule {schedule.id}")
            
            except Exception as e:
                logger.error(f"Error syncing schedule {schedule.id}: {str(e)}")
                errors.append(f"Error syncing schedule {schedule.id}: {str(e)}")
        
        db.commit()
        
        return {
            "message": f"Synced {synced_count} schedules",
            "synced": synced_count,
            "errors": errors
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error syncing to calendar: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to sync to calendar")


@router.get("/availability")
async def get_availability(
    request: Request,
    date: str,
    duration: int = 60,
):
    """
    Get available time slots for a specific date.
    
    Args:
        date: Date in ISO format
        duration: Required duration in minutes
        
    Returns:
        List of available time slots
    """
    try:
        user_id = get_current_user_id(request)
        credentials = get_oauth_credentials(request)
        
        # Parse date
        from dateutil import parser as date_parser
        target_date = date_parser.parse(date)
        
        # Get user preferences
        from models.preferences import UserPreferences
        preferences = db.query(UserPreferences).filter(
            UserPreferences.user_id == user_id
        ).first()
        
        if not preferences:
            raise HTTPException(status_code=400, detail="User preferences not found")
        
        # Get calendar events for the day
        start_of_day = target_date.replace(hour=0, minute=0, second=0, microsecond=0)
        end_of_day = start_of_day + timedelta(days=1)
        
        events = await calendar_service.get_calendar_events(
            credentials,
            start_of_day,
            end_of_day
        )
        
        # Find available slots
        working_hours_start = preferences.working_hours_start.strftime("%H:%M")
        working_hours_end = preferences.working_hours_end.strftime("%H:%M")
        
        available_slots = await calendar_service.find_available_slots(
            events,
            working_hours_start,
            working_hours_end,
            duration,
            target_date
        )
        
        return available_slots
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting availability: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get availability")
