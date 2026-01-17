"""User settings and preferences routes."""
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from database import get_db
from models.time_guideline import TimeGuideline
from pydantic import BaseModel
from typing import Optional, List
from datetime import time, date as dt_date
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/settings", tags=["settings"])


class PreferencesUpdate(BaseModel):
    working_hours_start: Optional[str] = None  # HH:MM format
    working_hours_end: Optional[str] = None
    lunch_time: Optional[str] = None
    lunch_duration: Optional[int] = None
    break_frequency: Optional[int] = None
    break_duration: Optional[int] = None
    buffer_time: Optional[int] = None
    timezone: Optional[str] = None


class TimeGuidelineCreate(BaseModel):
    name: str
    working_hours_start: str  # HH:MM
    working_hours_end: str    # HH:MM
    lunch_time: Optional[str] = None
    lunch_duration: int = 60
    break_frequency: int = 90
    break_duration: int = 15
    days_of_week: List[int]
    start_date: Optional[str] = None  # YYYY-MM-DD
    end_date: Optional[str] = None
    is_active: bool = True


class TimeGuidelineUpdate(BaseModel):
    name: Optional[str] = None
    working_hours_start: Optional[str] = None
    working_hours_end: Optional[str] = None
    lunch_time: Optional[str] = None
    lunch_duration: Optional[int] = None
    break_frequency: Optional[int] = None
    break_duration: Optional[int] = None
    days_of_week: Optional[List[int]] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    is_active: Optional[bool] = None


def get_current_user_id(request: Request) -> int:
    """Get current user ID from session."""
    user_id = request.session.get("user_id")
    if not user_id:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return user_id


@router.get("")
async def get_preferences(
    request: Request,
    db: Session = Depends(get_db),
):
    """
    Get user preferences.
    
    Returns:
        User preferences
    """
    try:
        user_id = get_current_user_id(request)
        
        preferences = db.query(UserPreferences).filter(
            UserPreferences.user_id == user_id
        ).first()
        
        if not preferences:
            raise HTTPException(status_code=404, detail="Preferences not found")
        
        return preferences.to_dict()
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting preferences: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get preferences")


@router.put("")
async def update_preferences(
    data: PreferencesUpdate,
    request: Request,
    db: Session = Depends(get_db),
):
    """
    Update user preferences.
    
    Args:
        data: Preferences update data
        
    Returns:
        Updated preferences
    """
    try:
        user_id = get_current_user_id(request)
        
        preferences = db.query(UserPreferences).filter(
            UserPreferences.user_id == user_id
        ).first()
        
        if not preferences:
            raise HTTPException(status_code=404, detail="Preferences not found")
        
        # Update fields
        if data.working_hours_start:
            hour, minute = map(int, data.working_hours_start.split(':'))
            preferences.working_hours_start = time(hour, minute)
        
        if data.working_hours_end:
            hour, minute = map(int, data.working_hours_end.split(':'))
            preferences.working_hours_end = time(hour, minute)
        
        if data.lunch_time:
            hour, minute = map(int, data.lunch_time.split(':'))
            preferences.lunch_time = time(hour, minute)
        
        if data.lunch_duration is not None:
            preferences.lunch_duration = data.lunch_duration
        
        if data.break_frequency is not None:
            preferences.break_frequency = data.break_frequency
        
        if data.break_duration is not None:
            preferences.break_duration = data.break_duration
        
        if data.buffer_time is not None:
            preferences.buffer_time = data.buffer_time
        
        if data.timezone:
            preferences.timezone = data.timezone
        
        db.commit()
        db.refresh(preferences)
        
        return preferences.to_dict()
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating preferences: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to update preferences")


@router.post("/reset")
async def reset_preferences(
    request: Request,
    db: Session = Depends(get_db),
):
    """
    Reset preferences to defaults.
    
    Returns:
        Reset preferences
    """
    try:
        user_id = get_current_user_id(request)
        
        preferences = db.query(UserPreferences).filter(
            UserPreferences.user_id == user_id
        ).first()
        
        if not preferences:
            raise HTTPException(status_code=404, detail="Preferences not found")
        
        # Reset to defaults
        preferences.working_hours_start = time(9, 0)
        preferences.working_hours_end = time(17, 0)
        preferences.lunch_time = time(12, 0)
        preferences.lunch_duration = 60
        preferences.break_frequency = 120
        preferences.break_duration = 15
        preferences.buffer_time = 5
        preferences.timezone = "UTC"
        
        db.commit()
        db.refresh(preferences)
        
        return preferences.to_dict()
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error resetting preferences: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to reset preferences")
# Time Guidelines (Presets) Routes

@router.get("/guidelines")
async def get_time_guidelines(
    request: Request,
    db: Session = Depends(get_db),
):
    """Get all user time guidelines."""
    try:
        user_id = get_current_user_id(request)
        guidelines = db.query(TimeGuideline).filter(
            TimeGuideline.user_id == user_id
        ).all()
        return [g.to_dict() for g in guidelines]
    except Exception as e:
        logger.error(f"Error getting guidelines: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get guidelines")


@router.post("/guidelines")
async def create_time_guideline(
    data: TimeGuidelineCreate,
    request: Request,
    db: Session = Depends(get_db),
):
    """Create a new time guideline."""
    try:
        user_id = get_current_user_id(request)
        
        # Parse times
        wh_start = time(*map(int, data.working_hours_start.split(':')))
        wh_end = time(*map(int, data.working_hours_end.split(':')))
        l_time = time(*map(int, data.lunch_time.split(':'))) if data.lunch_time else None
        
        # Parse dates
        from datetime import datetime
        s_date = datetime.strptime(data.start_date, "%Y-%m-%d").date() if data.start_date else None
        e_date = datetime.strptime(data.end_date, "%Y-%m-%d").date() if data.end_date else None
        
        guideline = TimeGuideline(
            user_id=user_id,
            name=data.name,
            working_hours_start=wh_start,
            working_hours_end=wh_end,
            lunch_time=l_time,
            lunch_duration=data.lunch_duration,
            break_frequency=data.break_frequency,
            break_duration=data.break_duration,
            days_of_week=data.days_of_week,
            start_date=s_date,
            end_date=e_date,
            is_active=data.is_active
        )
        
        db.add(guideline)
        db.commit()
        db.refresh(guideline)
        return guideline.to_dict()
    except Exception as e:
        logger.error(f"Error creating guideline: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to create guideline")


@router.put("/guidelines/{id}")
async def update_time_guideline(
    id: int,
    data: TimeGuidelineUpdate,
    request: Request,
    db: Session = Depends(get_db),
):
    """Update a time guideline."""
    try:
        user_id = get_current_user_id(request)
        guideline = db.query(TimeGuideline).filter(
            TimeGuideline.id == id,
            TimeGuideline.user_id == user_id
        ).first()
        
        if not guideline:
            raise HTTPException(status_code=404, detail="Guideline not found")
        
        if data.name: guideline.name = data.name
        if data.working_hours_start:
            guideline.working_hours_start = time(*map(int, data.working_hours_start.split(':')))
        if data.working_hours_end:
            guideline.working_hours_end = time(*map(int, data.working_hours_end.split(':')))
        if data.lunch_time:
            guideline.lunch_time = time(*map(int, data.lunch_time.split(':')))
        if data.lunch_duration is not None: guideline.lunch_duration = data.lunch_duration
        if data.break_frequency is not None: guideline.break_frequency = data.break_frequency
        if data.break_duration is not None: guideline.break_duration = data.break_duration
        if data.days_of_week is not None: guideline.days_of_week = data.days_of_week
        if data.is_active is not None: guideline.is_active = data.is_active
        
        from datetime import datetime
        if data.start_date is not None:
            guideline.start_date = datetime.strptime(data.start_date, "%Y-%m-%d").date() if data.start_date else None
        if data.end_date is not None:
            guideline.end_date = datetime.strptime(data.end_date, "%Y-%m-%d").date() if data.end_date else None
            
        db.commit()
        db.refresh(guideline)
        return guideline.to_dict()
    except Exception as e:
        logger.error(f"Error updating guideline: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to update guideline")


@router.delete("/guidelines/{id}")
async def delete_time_guideline(
    id: int,
    request: Request,
    db: Session = Depends(get_db),
):
    """Delete a time guideline."""
    try:
        user_id = get_current_user_id(request)
        guideline = db.query(TimeGuideline).filter(
            TimeGuideline.id == id,
            TimeGuideline.user_id == user_id
        ).first()
        
        if not guideline:
            raise HTTPException(status_code=404, detail="Guideline not found")
            
        db.delete(guideline)
        db.commit()
        return {"message": "Guideline deleted"}
    except Exception as e:
        logger.error(f"Error deleting guideline: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to delete guideline")
