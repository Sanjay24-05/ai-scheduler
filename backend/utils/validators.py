"""Input validation utilities."""
import re
from datetime import datetime
from typing import Optional, Dict, Any
from dateutil import parser


def sanitize_input(text: str, max_length: int = 5000) -> str:
    """
    Sanitize user input by removing potentially dangerous characters.
    
    Args:
        text: Input text to sanitize
        max_length: Maximum allowed length
        
    Returns:
        Sanitized text
    """
    if not text:
        return ""
    
    # Trim to max length
    text = text[:max_length]
    
    # Remove null bytes and other control characters
    text = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', text)
    
    # Strip leading/trailing whitespace
    text = text.strip()
    
    return text


def validate_task_input(data: Dict[str, Any]) -> tuple[bool, Optional[str]]:
    """
    Validate task input data.
    
    Args:
        data: Task data dictionary
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    # Check required fields
    if not data.get("title"):
        return False, "Task title is required"
    
    # Validate title length
    title = data.get("title", "")
    if len(title) > 500:
        return False, "Task title must be 500 characters or less"
    
    # Validate description length
    description = data.get("description", "")
    if description and len(description) > 5000:
        return False, "Task description must be 5000 characters or less"
    
    # Validate priority
    valid_priorities = ["high", "medium", "low"]
    priority = data.get("priority")
    if priority and priority.lower() not in valid_priorities:
        return False, f"Priority must be one of: {', '.join(valid_priorities)}"
    
    # Validate estimated_duration
    duration = data.get("estimated_duration")
    if duration is not None:
        try:
            duration = int(duration)
            if duration <= 0 or duration > 1440:  # Max 24 hours
                return False, "Estimated duration must be between 1 and 1440 minutes"
        except (ValueError, TypeError):
            return False, "Estimated duration must be a valid number"
    
    # Validate deadline
    deadline = data.get("deadline")
    if deadline:
        is_valid, error = validate_datetime(deadline)
        if not is_valid:
            return False, f"Invalid deadline: {error}"
    
    return True, None


def validate_datetime(dt_string: str) -> tuple[bool, Optional[str]]:
    """
    Validate and parse datetime string.
    
    Args:
        dt_string: Datetime string to validate
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not dt_string:
        return False, "Datetime string is empty"
    
    try:
        # Try to parse the datetime string
        parsed_dt = parser.parse(dt_string)
        
        # Check if it's in the past (optional, can be removed if past dates are allowed)
        # if parsed_dt < datetime.now(parsed_dt.tzinfo):
        #     return False, "Datetime cannot be in the past"
        
        return True, None
    except (ValueError, TypeError) as e:
        return False, f"Invalid datetime format: {str(e)}"


def validate_email(email: str) -> bool:
    """
    Validate email format.
    
    Args:
        email: Email address to validate
        
    Returns:
        True if valid, False otherwise
    """
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def validate_time_range(start_time: str, end_time: str) -> tuple[bool, Optional[str]]:
    """
    Validate that end_time is after start_time.
    
    Args:
        start_time: Start time string
        end_time: End time string
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    try:
        start = parser.parse(start_time)
        end = parser.parse(end_time)
        
        if end <= start:
            return False, "End time must be after start time"
        
        return True, None
    except (ValueError, TypeError) as e:
        return False, f"Invalid time format: {str(e)}"
