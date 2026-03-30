import sqlite3

def check_db(db_path, name):
    print(f"\n--- Checking {name} ({db_path}) ---")
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Count classes in April
        cursor.execute("SELECT id, class_id, topic_id, scheduled_date, status, notes FROM class_schedule WHERE scheduled_date >= '2026-04-01' AND scheduled_date < '2026-05-01'")
        rows = cursor.fetchall()
        print(f"Total April Schedule Records: {len(rows)}")
        
        for row in rows:
            print(row)
            
        conn.close()
    except Exception as e:
        print(f"Error checking {name}: {e}")

check_db('scheduler.db', 'Current DB')
check_db('scheduler.db.bak_before_course_removal', 'Backup (Before Course Removal)')
check_db('scheduler.db.bak_status_migration', 'Backup (Status Migration)')
