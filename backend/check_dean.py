import sqlite3
import os

db_path = os.path.join(os.path.dirname(__file__), 'scheduler.db')
conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

cursor.execute("SELECT id, name FROM course WHERE id IN (50, 61)")
res = cursor.fetchall()
for r in res:
    print(f"Course: {r['id']} -> {r['name']}")

conn.close()
