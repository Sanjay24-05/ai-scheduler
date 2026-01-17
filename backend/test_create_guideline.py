
import json
from datetime import time
from database import SessionLocal
from models.time_guideline import TimeGuideline
from routes.settings import TimeGuidelineCreate

def test_create():
    db = SessionLocal()
    try:
        # Simulate what the API does
        wh_start = time(9, 0)
        wh_end = time(17, 0)
        l_time = time(12, 0)
        
        guideline = TimeGuideline(
            user_id=1,
            name="Test Guideline",
            working_hours_start=wh_start,
            working_hours_end=wh_end,
            lunch_time=l_time,
            lunch_duration=60,
            break_frequency=90,
            break_duration=15,
            misc_breaks=[{"start_time": "10:30", "duration": 15}],
            days_of_week=[1, 2, 3, 4, 5],
            is_active=True
        )
        
        db.add(guideline)
        db.commit()
        db.refresh(guideline)
        print("Successfully created guideline!")
        print(guideline.to_dict())
        
        # Now try with NULL working hours
        guideline2 = TimeGuideline(
            user_id=1,
            name="Break Only Guideline",
            working_hours_start=None,
            working_hours_end=None,
            lunch_time=None,
            misc_breaks=[{"start_time": "14:00", "duration": 30}],
            days_of_week=[6],
            is_active=True
        )
        db.add(guideline2)
        db.commit()
        db.refresh(guideline2)
        print("Successfully created null hours guideline!")
        print(guideline2.to_dict())
        
    except Exception as e:
        print(f"Error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    test_create()
