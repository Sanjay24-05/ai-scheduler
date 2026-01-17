"""User settings and preferences routes."""
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from database import get_db
from models.preferences import UserPreferences
from pydantic import BaseModel
from typing import Optional
from datetime import time
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
