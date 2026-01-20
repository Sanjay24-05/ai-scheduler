"""Time Guideline model for scheduling presets."""
from sqlalchemy import Column, Integer, String, Time, Boolean, ForeignKey, JSON, Date
from sqlalchemy.orm import relationship
from database import Base


class TimeGuideline(Base):
    """
    Model for storing user-defined scheduling presets (Time Guidelines).
    Users can have multiple presets for different day ranges or weeks.
    """
    
    __tablename__ = "time_guidelines"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    # Preset Information
    name = Column(String(200), nullable=False)  # e.g., "Standard Work Week", "Intensive Project Week"
    is_active = Column(Boolean, default=True)
    
    # Time Constraints (Optional)
    working_hours_start = Column(Time, nullable=True)
    working_hours_end = Column(Time, nullable=True)
    
    lunch_time = Column(Time, nullable=True)
    lunch_duration = Column(Integer, default=60)  # in minutes
    
    # Auto-breaks (Frequent periodic breaks)
    break_frequency = Column(Integer, default=90)  # in minutes
    break_duration = Column(Integer, default=15)   # in minutes
    
    # Custom buffer between tasks (minutes)
    buffer_time = Column(Integer, default=5)  # in minutes
    
    # Custom / Misc Fixed Breaks (JSON list of {"start_time": "HH:MM", "duration": int})
    misc_breaks = Column(JSON, nullable=True, default=[])

    # Applicability Rules (JSON list of integers 0-6, e.g., [0,1,2,3,4])
    days_of_week = Column(JSON, nullable=False, default=[0,1,2,3,4])
    
    # Optional Date Range (YYYY-MM-DD)
    start_date = Column(Date, nullable=True)
    end_date = Column(Date, nullable=True)
    
    # Relationship
    user = relationship("User", back_populates="time_guidelines")

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "is_active": self.is_active,
            "working_hours_start": self.working_hours_start.isoformat() if self.working_hours_start else None,
            "working_hours_end": self.working_hours_end.isoformat() if self.working_hours_end else None,
            "lunch_time": self.lunch_time.isoformat() if self.lunch_time else None,
            "lunch_duration": self.lunch_duration,
            "break_frequency": self.break_frequency,
            "break_duration": self.break_duration,
            "buffer_time": self.buffer_time,
            "misc_breaks": self.misc_breaks or [],
            "days_of_week": self.days_of_week,
            "start_date": self.start_date.isoformat() if self.start_date else None,
            "end_date": self.end_date.isoformat() if self.end_date else None,
        }
