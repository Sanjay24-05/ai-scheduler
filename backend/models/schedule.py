"""Schedule model for storing scheduled task entries."""
from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base


class Schedule(Base):
    """Schedule entry model linking tasks to calendar time slots."""
    
    __tablename__ = "schedules"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    task_id = Column(Integer, ForeignKey("tasks.id"), nullable=False, index=True)
    
    # Time slot information
    start_time = Column(DateTime(timezone=True), nullable=False)
    end_time = Column(DateTime(timezone=True), nullable=False)
    
    # Google Calendar integration
    calendar_event_id = Column(String, nullable=True)  # Google Calendar event ID
    is_synced = Column(Boolean, default=False)  # Whether synced to Google Calendar
    
    # AI reasoning
    reasoning = Column(Text, nullable=True)  # AI explanation for this scheduling decision
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="schedules")
    task = relationship("Task", back_populates="schedules")
    
    def __repr__(self):
        return f"<Schedule(id={self.id}, task_id={self.task_id}, start={self.start_time}, end={self.end_time})>"
    
    def to_dict(self):
        """Convert schedule to dictionary for API responses."""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "task_id": self.task_id,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "calendar_event_id": self.calendar_event_id,
            "is_synced": self.is_synced,
            "reasoning": self.reasoning,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
