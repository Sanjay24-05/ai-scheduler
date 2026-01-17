"""Rate limiting utility for API and AI requests."""
from datetime import datetime, timedelta
from typing import Dict, Tuple
from collections import defaultdict
import threading


class RateLimiter:
    """
    In-memory rate limiter for API and AI requests.
    Tracks requests per user and enforces limits.
    """
    
    def __init__(self):
        """Initialize rate limiter with empty tracking dictionaries."""
        self.requests: Dict[str, list] = defaultdict(list)
        self.lock = threading.Lock()
    
    def is_allowed(self, user_id: str, limit: int, window_minutes: int = 60) -> Tuple[bool, int]:
        """
        Check if a request is allowed based on rate limits.
        
        Args:
            user_id: User identifier
            limit: Maximum number of requests allowed
            window_minutes: Time window in minutes (default: 60)
            
        Returns:
            Tuple of (is_allowed, remaining_requests)
        """
        with self.lock:
            now = datetime.utcnow()
            window_start = now - timedelta(minutes=window_minutes)
            
            # Get user's request history
            user_requests = self.requests[user_id]
            
            # Filter out requests outside the time window
            user_requests = [req_time for req_time in user_requests if req_time > window_start]
            
            # Update the request history
            self.requests[user_id] = user_requests
            
            # Check if limit is exceeded
            if len(user_requests) >= limit:
                return False, 0
            
            # Add current request
            user_requests.append(now)
            
            # Calculate remaining requests
            remaining = limit - len(user_requests)
            
            return True, remaining
    
    def reset_user(self, user_id: str):
        """
        Reset rate limit for a specific user.
        
        Args:
            user_id: User identifier
        """
        with self.lock:
            if user_id in self.requests:
                del self.requests[user_id]
    
    def cleanup_old_requests(self, window_minutes: int = 60):
        """
        Clean up old requests from memory to prevent memory leaks.
        
        Args:
            window_minutes: Time window in minutes
        """
        with self.lock:
            now = datetime.utcnow()
            window_start = now - timedelta(minutes=window_minutes)
            
            for user_id in list(self.requests.keys()):
                # Filter out old requests
                self.requests[user_id] = [
                    req_time for req_time in self.requests[user_id]
                    if req_time > window_start
                ]
                
                # Remove user if no requests in window
                if not self.requests[user_id]:
                    del self.requests[user_id]


# Global rate limiter instances
api_rate_limiter = RateLimiter()
ai_rate_limiter = RateLimiter()
