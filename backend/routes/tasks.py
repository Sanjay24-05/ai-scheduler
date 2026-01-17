"""Task management routes."""
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from database import get_db
from models.task import Task, TaskStatus, TaskPriority
from models.user import User
from services.ai_service import ai_service
from utils.validators import validate_task_input, sanitize_input
from utils.rate_limiter import api_rate_limiter
from config import settings
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/tasks", tags=["tasks"])


# Pydantic models for request/response
class TaskCreate(BaseModel):
    title: str
    description: Optional[str] = None
    priority: Optional[str] = "medium"
    deadline: Optional[str] = None
    estimated_duration: Optional[int] = None
    is_flexible: Optional[bool] = True
    dependencies: Optional[List[int]] = None


class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    priority: Optional[str] = None
    deadline: Optional[str] = None
    estimated_duration: Optional[int] = None
    is_flexible: Optional[bool] = None
    status: Optional[str] = None
    dependencies: Optional[List[int]] = None


def get_current_user_id(request: Request) -> int:
    """Get current user ID from session."""
    user_id = request.session.get("user_id")
    if not user_id:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return user_id


@router.get("")
async def list_tasks(
    request: Request,
    db: Session = Depends(get_db),
    status: Optional[str] = None,
    priority: Optional[str] = None,
):
    """
    List all tasks for the current user.
    
    Args:
        status: Filter by status (optional)
        priority: Filter by priority (optional)
        
    Returns:
        List of tasks
    """
    try:
        user_id = get_current_user_id(request)
        
        # Check rate limit
        allowed, remaining = api_rate_limiter.is_allowed(str(user_id), settings.api_rate_limit)
        if not allowed:
            raise HTTPException(status_code=429, detail="Rate limit exceeded")
        
        # Build query
        query = db.query(Task).filter(Task.user_id == user_id)
        
        if status:
            query = query.filter(Task.status == TaskStatus(status))
        
        if priority:
            query = query.filter(Task.priority == TaskPriority(priority))
        
        tasks = query.order_by(Task.created_at.desc()).all()
        
        return [task.to_dict() for task in tasks]
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing tasks: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to list tasks")


@router.post("")
async def create_task(
    task_data: TaskCreate,
    request: Request,
    db: Session = Depends(get_db),
):
    """
    Create a new task.
    
    Args:
        task_data: Task creation data
        
    Returns:
        Created task
    """
    try:
        user_id = get_current_user_id(request)
        
        # Check rate limit
        allowed, remaining = api_rate_limiter.is_allowed(str(user_id), settings.api_rate_limit)
        if not allowed:
            raise HTTPException(status_code=429, detail="Rate limit exceeded")
        
        # Validate input
        task_dict = task_data.dict()
        is_valid, error = validate_task_input(task_dict)
        if not is_valid:
            raise HTTPException(status_code=400, detail=error)
        
        # Sanitize inputs
        title = sanitize_input(task_data.title, max_length=500)
        description = sanitize_input(task_data.description or "", max_length=5000)
        
        # Parse deadline if provided
        deadline = None
        if task_data.deadline:
            from dateutil import parser
            deadline = parser.parse(task_data.deadline)
        
        # Create task
        task = Task(
            user_id=user_id,
            title=title,
            description=description if description else None,
            priority=TaskPriority(task_data.priority),
            deadline=deadline,
            estimated_duration=task_data.estimated_duration,
            is_flexible=task_data.is_flexible,
            dependencies=task_data.dependencies,
            status=TaskStatus.PENDING,
        )
        
        db.add(task)
        db.commit()
        db.refresh(task)
        
        return task.to_dict()
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating task: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to create task")


@router.get("/{task_id}")
async def get_task(
    task_id: int,
    request: Request,
    db: Session = Depends(get_db),
):
    """
    Get a specific task.
    
    Args:
        task_id: Task ID
        
    Returns:
        Task details
    """
    try:
        user_id = get_current_user_id(request)
        
        task = db.query(Task).filter(
            Task.id == task_id,
            Task.user_id == user_id
        ).first()
        
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")
        
        return task.to_dict()
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting task: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get task")


@router.put("/{task_id}")
async def update_task(
    task_id: int,
    task_data: TaskUpdate,
    request: Request,
    db: Session = Depends(get_db),
):
    """
    Update a task.
    
    Args:
        task_id: Task ID
        task_data: Task update data
        
    Returns:
        Updated task
    """
    try:
        user_id = get_current_user_id(request)
        
        task = db.query(Task).filter(
            Task.id == task_id,
            Task.user_id == user_id
        ).first()
        
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")
        
        # Update fields
        if task_data.title is not None:
            task.title = sanitize_input(task_data.title, max_length=500)
        
        if task_data.description is not None:
            task.description = sanitize_input(task_data.description, max_length=5000)
        
        if task_data.priority is not None:
            task.priority = TaskPriority(task_data.priority)
        
        if task_data.deadline is not None:
            from dateutil import parser
            task.deadline = parser.parse(task_data.deadline)
        
        if task_data.estimated_duration is not None:
            task.estimated_duration = task_data.estimated_duration
        
        if task_data.is_flexible is not None:
            task.is_flexible = task_data.is_flexible
        
        if task_data.status is not None:
            task.status = TaskStatus(task_data.status)
            if task.status == TaskStatus.COMPLETED:
                task.completed_at = datetime.utcnow()
        
        if task_data.dependencies is not None:
            task.dependencies = task_data.dependencies
        
        db.commit()
        db.refresh(task)
        
        return task.to_dict()
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating task: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to update task")


@router.delete("/{task_id}")
async def delete_task(
    task_id: int,
    request: Request,
    db: Session = Depends(get_db),
):
    """
    Delete a task.
    
    Args:
        task_id: Task ID
        
    Returns:
        Success message
    """
    try:
        user_id = get_current_user_id(request)
        
        task = db.query(Task).filter(
            Task.id == task_id,
            Task.user_id == user_id
        ).first()
        
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")
        
        db.delete(task)
        db.commit()
        
        return {"message": "Task deleted successfully"}
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting task: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to delete task")


@router.post("/{task_id}/complete")
async def complete_task(
    task_id: int,
    request: Request,
    db: Session = Depends(get_db),
):
    """
    Mark a task as complete.
    
    Args:
        task_id: Task ID
        
    Returns:
        Updated task
    """
    try:
        user_id = get_current_user_id(request)
        
        task = db.query(Task).filter(
            Task.id == task_id,
            Task.user_id == user_id
        ).first()
        
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")
        
        task.status = TaskStatus.COMPLETED
        task.completed_at = datetime.utcnow()
        
        db.commit()
        db.refresh(task)
        
        return task.to_dict()
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error completing task: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to complete task")
