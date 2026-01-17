
from database import SessionLocal
from models.time_guideline import TimeGuideline

def test_retrieval():
    db = SessionLocal()
    guideline = db.query(TimeGuideline).first()
    if guideline:
        print(f"Name: {guideline.name}")
        print(f"Misc Breaks type: {type(guideline.misc_breaks)}")
        print(f"Misc Breaks: {guideline.misc_breaks}")
        print(f"To dict: {guideline.to_dict()}")
    else:
        print("No guideline found")
    db.close()

if __name__ == "__main__":
    test_retrieval()
