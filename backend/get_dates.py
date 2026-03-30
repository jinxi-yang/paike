import sqlite3
import os

db_path = os.path.join(os.path.dirname(__file__), 'scheduler.db')
conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

classes = ['123', '126', '127', '128']
out = []

for c in classes:
    cursor.execute("SELECT id, name FROM class WHERE name LIKE ?", (f'%{c}%',))
    cls_rec = cursor.fetchone()
    if cls_rec:
        out.append(f"--- {cls_rec['name']} ---")
        cursor.execute("SELECT scheduled_date FROM class_schedule WHERE class_id = ? ORDER BY scheduled_date", (cls_rec['id'],))
        dates = [r['scheduled_date'] for r in cursor.fetchall()]
        out.append(', '.join(dates))
        
with open('class_dates.txt', 'w', encoding='utf-8') as f:
    f.write('\n'.join(out))

conn.close()
