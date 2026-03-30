import sqlite3
import os

db_path = os.path.join(os.path.dirname(__file__), 'scheduler.db')
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

cursor.execute("""
    SELECT cs.id, c.name, cs.scheduled_date, cs.status, cs.topic_id
    FROM class_schedule cs
    JOIN class c ON cs.class_id = c.id
    WHERE cs.scheduled_date >= '2026-05-01' AND cs.scheduled_date < '2026-06-01'
    AND (c.name LIKE '%125%' OR c.name LIKE '%129%')
""")

print("EMBA125 and EMBA129 schedules in May (Current DB):")
for r in cursor.fetchall():
    print(f"  ID={r[0]} | Class={r[1]} | Date={r[2]} | Status={r[3]} | TopicID={r[4]}")
conn.close()
