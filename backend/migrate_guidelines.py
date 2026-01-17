
import sqlite3

def migrate():
    conn = sqlite3.connect('scheduler.db')
    cursor = conn.cursor()
    
    # 1. Rename old table if it exists
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='time_guidelines';")
    if cursor.fetchone():
        cursor.execute("DROP TABLE IF EXISTS time_guidelines_old;")
        cursor.execute("ALTER TABLE time_guidelines RENAME TO time_guidelines_old;")
        print("Renamed existing table.")
    else:
        print("time_guidelines table not found, assuming already renamed.")
    
    # 2. Create new table with correct nullability
    # Based on the current model in models/time_guideline.py
    cursor.execute("""
        CREATE TABLE time_guidelines (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            name VARCHAR(200) NOT NULL,
            is_active BOOLEAN DEFAULT 1,
            working_hours_start TIME NULL,
            working_hours_end TIME NULL,
            lunch_time TIME NULL,
            lunch_duration INTEGER DEFAULT 60,
            break_frequency INTEGER DEFAULT 90,
            break_duration INTEGER DEFAULT 15,
            misc_breaks JSON NULL DEFAULT '[]',
            days_of_week JSON NOT NULL DEFAULT '[0,1,2,3,4]',
            start_date DATE NULL,
            end_date DATE NULL,
            FOREIGN KEY (user_id) REFERENCES users (id)
        );
    """)
    
    # 3. Copy data
    cursor.execute("""
        INSERT INTO time_guidelines (
            id, user_id, name, is_active, working_hours_start, working_hours_end,
            lunch_time, lunch_duration, break_frequency, break_duration,
            misc_breaks, days_of_week, start_date, end_date
        )
        SELECT 
            id, user_id, name, is_active, working_hours_start, working_hours_end,
            lunch_time, lunch_duration, break_frequency, break_duration,
            misc_breaks, days_of_week, start_date, end_date
        FROM time_guidelines_old;
    """)
    
    # 4. Create indexes
    cursor.execute("DROP INDEX IF EXISTS ix_time_guidelines_user_id;")
    cursor.execute("DROP INDEX IF EXISTS ix_time_guidelines_id;")
    cursor.execute("CREATE INDEX ix_time_guidelines_user_id ON time_guidelines (user_id);")
    cursor.execute("CREATE INDEX ix_time_guidelines_id ON time_guidelines (id);")
    
    # 5. Drop old table
    cursor.execute("DROP TABLE IF EXISTS time_guidelines_old;")
    
    conn.commit()
    conn.close()
    print("Migration completed successfully!")

if __name__ == "__main__":
    migrate()
