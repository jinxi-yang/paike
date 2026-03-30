import sqlite3
import os

db_path = os.path.join(os.path.dirname(__file__), 'scheduler.db')
bak_path = os.path.join(os.path.dirname(__file__), 'scheduler.db.bak_before_course_removal')

def get_april_classes(db_file):
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT cs.id, c.name, t.name as topic_name, cs.scheduled_date, cs.status, cs.topic_id
        FROM class_schedule cs
        JOIN class c ON cs.class_id = c.id
        LEFT JOIN topic t ON cs.topic_id = t.id
        WHERE cs.scheduled_date >= '2026-04-01' AND cs.scheduled_date < '2026-05-01'
    """)
    rows = cursor.fetchall()
    conn.close()
    return rows

curr = get_april_classes(db_path)
bak = get_april_classes(bak_path)

print(f"Current DB April classes: {len(curr)}")
for r in curr:
    print(f"  ID={r[0]} | Class={r[1]} | Date={r[3]} | Status={r[4]} | Topic={r[2]} (ID={r[5]})")

print(f"\nBackup DB April classes: {len(bak)}")
for r in bak:
    status_str = r[4] if r[4] else 'None'
    print(f"  ID={r[0]} | Class={r[1]} | Date={r[3]} | Status={status_str} | Topic={r[2]} (ID={r[5]})")

# Find missing class IDs (by comparing class_id, not pk)
conn = sqlite3.connect(db_path)
curr_class_names = [r[1] for r in curr]
bak_class_names = [r[1] for r in bak]
missing = [c for c in bak_class_names if c not in curr_class_names]

print(f"\nMissing from current DB: {missing}")
