import sqlite3
import os

db_path = os.path.join(os.path.dirname(__file__), 'scheduler.db')
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

cursor.execute("SELECT * FROM class_schedule WHERE scheduled_date = '2026-05-09'")
print("Raw records on 2026-05-09:")
for r in cursor.fetchall():
    print(r)

print("\nAll EMBA125 classes:")
cursor.execute("SELECT * FROM class_schedule cs JOIN class c ON cs.class_id = c.id WHERE c.name LIKE '%125%'")
for r in cursor.fetchall():
    print(r)

print("\nAll EMBA129 classes:")
cursor.execute("SELECT * FROM class_schedule cs JOIN class c ON cs.class_id = c.id WHERE c.name LIKE '%129%'")
for r in cursor.fetchall():
    print(r)

conn.close()
