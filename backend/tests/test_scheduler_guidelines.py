
import pytest
from datetime import datetime, time, timedelta
import pytz
from services.scheduler import SchedulerService
from unittest.mock import MagicMock

@pytest.fixture
def scheduler():
    return SchedulerService()

@pytest.fixture
def mock_preferences():
    pref = MagicMock()
    pref.working_hours_start = time(9, 0)
    pref.working_hours_end = time(17, 0)
    pref.lunch_time = time(12, 0)
    pref.lunch_duration = 60
    pref.break_frequency = 90
    pref.break_duration = 15
    pref.buffer_time = 5
    return pref

def test_get_effective_guideline_with_optional_hours(scheduler, mock_preferences):
    # Guideline with no working hours should fallback to preferences
    guideline = MagicMock()
    guideline.days_of_week = [1, 2, 3, 4, 5]
    guideline.working_hours_start = None
    guideline.working_hours_end = None
    guideline.lunch_time = time(13, 0)
    guideline.lunch_duration = 45
    guideline.break_frequency = 60
    guideline.break_duration = 10
    guideline.misc_breaks = [{"start_time": "10:30", "duration": 15}]
    guideline.start_date = None
    guideline.end_date = None
    
    date = datetime(2024, 5, 20)  # Monday
    effective = scheduler._get_effective_guideline(date, [guideline], mock_preferences)
    
    assert effective["working_hours_start"] == mock_preferences.working_hours_start
    assert effective["working_hours_end"] == mock_preferences.working_hours_end
    assert effective["lunch_time"] == time(13, 0)
    assert effective["misc_breaks"] == [{"start_time": "10:30", "duration": 15}]

def test_get_busy_periods_with_misc_breaks(scheduler):
    date = datetime(2024, 5, 20)
    guideline = {
        "misc_breaks": [
            {"start_time": "10:00", "duration": 15},
            {"start_time": "14:30", "duration": 30}
        ]
    }
    
    busy_periods = scheduler._get_busy_periods([], [], date, guideline)
    
    # We expect 2 busy periods from misc breaks
    assert len(busy_periods) == 2
    
    # Check first break (10:00 - 10:15)
    # Note: _get_busy_periods might add UTC localization
    brk1_start = busy_periods[0][0]
    brk1_end = busy_periods[0][1]
    assert brk1_start.hour == 10
    assert brk1_start.minute == 0
    assert (brk1_end - brk1_start).total_seconds() / 60 == 15
    
    # Check second break (14:30 - 15:00)
    brk2_start = busy_periods[1][0]
    brk2_end = busy_periods[1][1]
    assert brk2_start.hour == 14
    assert brk2_start.minute == 30
    assert (brk2_end - brk2_start).total_seconds() / 60 == 30

def test_scheduler_respects_misc_breaks(scheduler, mock_preferences):
    # This is a more complex test that requires mocking Task and DB
    pass 
