"""Task model for storing user tasks and AI metadata."""
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, Enum, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base
import enum


class TaskPriority(str, enum.Enum):
    """Task priority levels."""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class TaskStatus(str, enum.Enum):
    """Task status states."""
    PENDING = "pending"
    SCHEDULED = "scheduled"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class Task(Base):
    """Task model storing user tasks with AI-extracted metadata."""
    
    __tablename__ = "tasks"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    # Core task information
    title = Column(String(500), nullable=False)
    description = Column(Text, nullable=True)
    
    # Task attributes
    priority = Column(Enum(TaskPriority), default=TaskPriority.MEDIUM, nullable=False)
    deadline = Column(DateTime(timezone=True), nullable=True)
    estimated_duration = Column(Integer, nullable=True)  # in minutes
    is_flexible = Column(Boolean, default=True)  # can be moved/rescheduled
    status = Column(Enum(TaskStatus), default=TaskStatus.PENDING, nullable=False)
    
    # AI metadata and dependencies
    ai_metadata = Column(JSON, nullable=True)  # Store AI analysis results
    dependencies = Column(JSON, nullable=True)  # List of task IDs this depends on
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="tasks")
    schedules = relationship("Schedule", back_populates="task", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Task(id={self.id}, title={self.title}, status={self.status}, priority={self.priority})>"
    
    def to_dict(self):
        """Convert task to dictionary for API responses."""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "title": self.title,
            "description": self.description,
            "priority": self.priority.value if self.priority else None,
            "deadline": self.deadline.isoformat() if self.deadline else None,
            "estimated_duration": self.estimated_duration,
            "is_flexible": self.is_flexible,
            "status": self.status.value if self.status else None,
            "ai_metadata": self.ai_metadata,
            "dependencies": self.dependencies,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
        }
