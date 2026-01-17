
import sqlite3
import json

def check_db():
    conn = sqlite3.connect('scheduler.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM time_guidelines;")
    rows = cursor.fetchall()
    columns = [description[0] for description in cursor.description]
    
    results = []
    for row in rows:
        results.append(dict(zip(columns, row)))
    
    print(json.dumps(results, indent=2))
    conn.close()

if __name__ == "__main__":
    check_db()
