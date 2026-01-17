"""Google Calendar service for calendar integration."""
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any
import logging

logger = logging.getLogger(__name__)


class CalendarService:
    """Service for interacting with Google Calendar API."""
    
    def __init__(self):
        """Initialize calendar service."""
        self.service_name = "calendar"
        self.service_version = "v3"
    
    def _get_service(self, credentials_dict: Dict):
        """
        Create Google Calendar service instance.
        
        Args:
            credentials_dict: Dictionary with OAuth credentials
            
        Returns:
            Google Calendar service instance
        """
        credentials = Credentials(
            token=credentials_dict.get("access_token"),
            refresh_token=credentials_dict.get("refresh_token"),
            token_uri=credentials_dict.get("token_uri"),
            client_id=credentials_dict.get("client_id"),
            client_secret=credentials_dict.get("client_secret"),
            scopes=credentials_dict.get("scopes"),
        )
        
        return build(self.service_name, self.service_version, credentials=credentials)
    
    async def get_calendar_events(
        self,
        credentials_dict: Dict,
        start_date: datetime,
        end_date: datetime,
        calendar_id: str = "primary"
    ) -> List[Dict[str, Any]]:
        """
        Fetch calendar events within a date range.
        
        Args:
            credentials_dict: OAuth credentials
            start_date: Start of date range
            end_date: End of date range
            calendar_id: Calendar ID (default: primary)
            
        Returns:
            List of calendar events
        """
        try:
            service = self._get_service(credentials_dict)
            
            # Format dates for API
            time_min = start_date.isoformat() + 'Z'
            time_max = end_date.isoformat() + 'Z'
            
            # Fetch events
            events_result = service.events().list(
                calendarId=calendar_id,
                timeMin=time_min,
                timeMax=time_max,
                singleEvents=True,
                orderBy='startTime'
            ).execute()
            
            events = events_result.get('items', [])
            
            # Parse and return events
            parsed_events = []
            for event in events:
                start = event['start'].get('dateTime', event['start'].get('date'))
                end = event['end'].get('dateTime', event['end'].get('date'))
                
                parsed_events.append({
                    "id": event.get("id"),
                    "summary": event.get("summary", "No title"),
                    "start": start,
                    "end": end,
                    "status": event.get("status"),
                    "description": event.get("description"),
                })
            
            return parsed_events
        
        except HttpError as e:
            logger.error(f"Google Calendar API error: {str(e)}")
            return []
        except Exception as e:
            logger.error(f"Error fetching calendar events: {str(e)}")
            return []
    
    async def find_available_slots(
        self,
        events: List[Dict],
        working_hours_start: str,
        working_hours_end: str,
        duration_minutes: int,
        date: datetime
    ) -> List[Dict[str, str]]:
        """
        Find available time slots in a day.
        
        Args:
            events: List of existing calendar events
            working_hours_start: Start of working hours (HH:MM format)
            working_hours_end: End of working hours (HH:MM format)
            duration_minutes: Required duration in minutes
            date: Date to find slots for
            
        Returns:
            List of available time slots
        """
        from dateutil import parser
        
        # Parse working hours
        start_hour, start_min = map(int, working_hours_start.split(':'))
        end_hour, end_min = map(int, working_hours_end.split(':'))
        
        # Create working hours datetime
        work_start = date.replace(hour=start_hour, minute=start_min, second=0, microsecond=0)
        work_end = date.replace(hour=end_hour, minute=end_min, second=0, microsecond=0)
        
        # Get busy periods from events
        busy_periods = []
        for event in events:
            event_start = parser.parse(event['start'])
            event_end = parser.parse(event['end'])
            
            # Only consider events on the same day
            if event_start.date() == date.date():
                busy_periods.append((event_start, event_end))
        
        # Sort busy periods
        busy_periods.sort(key=lambda x: x[0])
        
        # Find available slots
        available_slots = []
        current_time = work_start
        
        for busy_start, busy_end in busy_periods:
            # Check if there's a gap before this busy period
            if current_time < busy_start:
                gap_duration = (busy_start - current_time).total_seconds() / 60
                if gap_duration >= duration_minutes:
                    available_slots.append({
                        "start": current_time.isoformat(),
                        "end": (current_time + timedelta(minutes=duration_minutes)).isoformat(),
                    })
            
            # Move current time to end of busy period
            current_time = max(current_time, busy_end)
        
        # Check if there's time after the last busy period
        if current_time < work_end:
            gap_duration = (work_end - current_time).total_seconds() / 60
            if gap_duration >= duration_minutes:
                available_slots.append({
                    "start": current_time.isoformat(),
                    "end": (current_time + timedelta(minutes=duration_minutes)).isoformat(),
                })
        
        return available_slots
    
    async def create_event(
        self,
        credentials_dict: Dict,
        summary: str,
        description: str,
        start_time: datetime,
        end_time: datetime,
        calendar_id: str = "primary"
    ) -> Optional[str]:
        """
        Create a calendar event.
        
        Args:
            credentials_dict: OAuth credentials
            summary: Event title
            description: Event description
            start_time: Event start time
            end_time: Event end time
            calendar_id: Calendar ID (default: primary)
            
        Returns:
            Event ID or None if error
        """
        try:
            service = self._get_service(credentials_dict)
            
            # Ensure times are timezone-aware
            if not start_time.tzinfo:
                import pytz
                start_time = pytz.UTC.localize(start_time)
            if not end_time.tzinfo:
                import pytz
                end_time = pytz.UTC.localize(end_time)
                
            event = {
                'summary': summary,
                'description': description,
                'start': {
                    'dateTime': start_time.isoformat(),
                },
                'end': {
                    'dateTime': end_time.isoformat(),
                },
            }
            
            created_event = service.events().insert(
                calendarId=calendar_id,
                body=event
            ).execute()
            
            return created_event.get('id')
        
        except HttpError as e:
            logger.error(f"Error creating calendar event: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error creating event: {str(e)}")
            return None
    
    async def update_event(
        self,
        credentials_dict: Dict,
        event_id: str,
        start_time: datetime,
        end_time: datetime,
        calendar_id: str = "primary"
    ) -> bool:
        """
        Update a calendar event.
        
        Args:
            credentials_dict: OAuth credentials
            event_id: Event ID to update
            start_time: New start time
            end_time: New end time
            calendar_id: Calendar ID (default: primary)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            service = self._get_service(credentials_dict)
            
            # Get existing event
            event = service.events().get(
                calendarId=calendar_id,
                eventId=event_id
            ).execute()
            
            # Ensure times are timezone-aware
            if not start_time.tzinfo:
                import pytz
                start_time = pytz.UTC.localize(start_time)
            if not end_time.tzinfo:
                import pytz
                end_time = pytz.UTC.localize(end_time)
                
            # Update times
            event['start'] = {
                'dateTime': start_time.isoformat(),
            }
            event['end'] = {
                'dateTime': end_time.isoformat(),
            }
            
            # Update event
            service.events().update(
                calendarId=calendar_id,
                eventId=event_id,
                body=event
            ).execute()
            
            return True
        
        except HttpError as e:
            logger.error(f"Error updating calendar event: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error updating event: {str(e)}")
            return False
    
    async def delete_event(
        self,
        credentials_dict: Dict,
        event_id: str,
        calendar_id: str = "primary"
    ) -> bool:
        """
        Delete a calendar event.
        
        Args:
            credentials_dict: OAuth credentials
            event_id: Event ID to delete
            calendar_id: Calendar ID (default: primary)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            service = self._get_service(credentials_dict)
            
            service.events().delete(
                calendarId=calendar_id,
                eventId=event_id
            ).execute()
            
            return True
        
        except HttpError as e:
            logger.error(f"Error deleting calendar event: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error deleting event: {str(e)}")
            return False
    
    async def check_conflicts(
        self,
        credentials_dict: Dict,
        start_time: datetime,
        end_time: datetime,
        calendar_id: str = "primary"
    ) -> bool:
        """
        Check if a time slot conflicts with existing events.
        
        Args:
            credentials_dict: OAuth credentials
            start_time: Slot start time
            end_time: Slot end time
            calendar_id: Calendar ID (default: primary)
            
        Returns:
            True if conflict exists, False otherwise
        """
        try:
            events = await self.get_calendar_events(
                credentials_dict,
                start_time,
                end_time,
                calendar_id
            )
            
            return len(events) > 0
        
        except Exception as e:
            logger.error(f"Error checking conflicts: {str(e)}")
            return True  # Assume conflict on error to be safe


# Global calendar service instance
calendar_service = CalendarService()
