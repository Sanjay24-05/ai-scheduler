"""AI interaction routes."""
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from database import get_db
from models.task import Task
from services.ai_service import ai_service
from utils.rate_limiter import ai_rate_limiter
from config import settings
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/ai", tags=["ai"])


class TaskAnalysisRequest(BaseModel):
    description: str
    history: Optional[List[Dict[str, str]]] = None


class ClarificationRequest(BaseModel):
    task_id: int


class ScheduleSuggestionRequest(BaseModel):
    task_ids: List[int]


def get_current_user_id(request: Request) -> int:
    """Get current user ID from session."""
    user_id = request.session.get("user_id")
    if not user_id:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return user_id


@router.post("/analyze-task")
async def analyze_task(
    data: TaskAnalysisRequest,
    request: Request,
    db: Session = Depends(get_db),
):
    """
    Analyze a task description using AI.
    
    Args:
        data: Task description
        
    Returns:
        Extracted task metadata
    """
    try:
        user_id = get_current_user_id(request)
        
        # Check AI rate limit
        allowed, remaining = ai_rate_limiter.is_allowed(str(user_id), settings.ai_rate_limit)
        if not allowed:
            raise HTTPException(status_code=429, detail="AI rate limit exceeded. Please try again later.")
        
        # Analyze task
        analysis = await ai_service.analyze_task(data.description, data.history)
        
        return {
            "analysis": analysis,
            "remaining_requests": remaining
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error analyzing task: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to analyze task")


@router.post("/ask-clarification")
async def ask_clarification(
    data: ClarificationRequest,
    request: Request,
    db: Session = Depends(get_db),
):
    """
    Get clarifying questions for a task.
    
    Args:
        data: Task ID
        
    Returns:
        List of clarifying questions
    """
    try:
        user_id = get_current_user_id(request)
        
        # Check AI rate limit
        allowed, remaining = ai_rate_limiter.is_allowed(str(user_id), settings.ai_rate_limit)
        if not allowed:
            raise HTTPException(status_code=429, detail="AI rate limit exceeded")
        
        # Get task
        task = db.query(Task).filter(
            Task.id == data.task_id,
            Task.user_id == user_id
        ).first()
        
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")
        
        # Generate clarifications
        task_data = task.to_dict()
        questions = await ai_service.generate_clarifications(task_data)
        
        return {
            "questions": questions,
            "remaining_requests": remaining
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating clarifications: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to generate clarifications")


@router.post("/suggest-schedule")
async def suggest_schedule(
    data: ScheduleSuggestionRequest,
    request: Request,
    db: Session = Depends(get_db),
):
    """
    Get AI suggestions for scheduling tasks.
    
    Args:
        data: List of task IDs
        
    Returns:
        Scheduling suggestions
    """
    try:
        user_id = get_current_user_id(request)
        
        # Check AI rate limit
        allowed, remaining = ai_rate_limiter.is_allowed(str(user_id), settings.ai_rate_limit)
        if not allowed:
            raise HTTPException(status_code=429, detail="AI rate limit exceeded")
        
        # Get tasks
        tasks = db.query(Task).filter(
            Task.id.in_(data.task_ids),
            Task.user_id == user_id
        ).all()
        
        if not tasks:
            raise HTTPException(status_code=404, detail="No tasks found")
        
        # Get user preferences
        from models.preferences import UserPreferences
        preferences = db.query(UserPreferences).filter(
            UserPreferences.user_id == user_id
        ).first()
        
        # Prepare data for AI
        tasks_data = [task.to_dict() for task in tasks]
        preferences_data = preferences.to_dict() if preferences else {}
        
        # Get calendar events (placeholder - will be implemented with calendar service)
        calendar_events = []
        
        # Get AI suggestions
        suggestions = await ai_service.suggest_schedule(
            tasks_data,
            calendar_events,
            preferences_data
        )
        
        return {
            "suggestions": suggestions,
            "remaining_requests": remaining
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting schedule suggestions: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get suggestions")
