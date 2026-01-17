"""User preferences model for scheduling configuration."""
from sqlalchemy import Column, Integer, String, Time, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base
from datetime import time


class UserPreferences(Base):
    """User preferences for scheduling algorithm."""
    
    __tablename__ = "user_preferences"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False, index=True)
    
    # Working hours
    working_hours_start = Column(Time, default=time(9, 0), nullable=False)  # 9:00 AM
    working_hours_end = Column(Time, default=time(17, 0), nullable=False)  # 5:00 PM
    
    # Lunch configuration
    lunch_time = Column(Time, default=time(12, 0), nullable=False)  # 12:00 PM
    lunch_duration = Column(Integer, default=60, nullable=False)  # minutes
    
    # Break configuration
    break_frequency = Column(Integer, default=120, nullable=False)  # every 120 minutes
    break_duration = Column(Integer, default=15, nullable=False)  # 15 minutes
    
    # Buffer time
    buffer_time = Column(Integer, default=5, nullable=False)  # minutes between tasks
    
    # Timezone
    timezone = Column(String, default="UTC", nullable=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="preferences")
    
    def __repr__(self):
        return f"<UserPreferences(user_id={self.user_id}, working_hours={self.working_hours_start}-{self.working_hours_end})>"
    
    def to_dict(self):
        """Convert preferences to dictionary for API responses."""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "working_hours_start": self.working_hours_start.isoformat() if self.working_hours_start else None,
            "working_hours_end": self.working_hours_end.isoformat() if self.working_hours_end else None,
            "lunch_time": self.lunch_time.isoformat() if self.lunch_time else None,
            "lunch_duration": self.lunch_duration,
            "break_frequency": self.break_frequency,
            "break_duration": self.break_duration,
            "buffer_time": self.buffer_time,
            "timezone": self.timezone,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
