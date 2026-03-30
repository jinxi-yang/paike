import sqlite3
import os

db_path = os.path.join(os.path.dirname(__file__), 'scheduler.db')
conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

teachers_to_check = [
    "黄洁", "易正"
]

out = []
for t in teachers_to_check:
    cursor.execute("SELECT id FROM teacher WHERE name = ?", (t,))
    res = cursor.fetchone()
    if res:
        out.append(f"Found: {t}")
    else:
        out.append(f"MISSING: {t}")

with open('teacher_check_5.txt', 'w', encoding='utf-8') as f:
    f.write('\n'.join(out))

classes = ['155', '156']
out_dates = []

for c in classes:
    cursor.execute("SELECT id, name FROM class WHERE name LIKE ?", (f'%{c}%',))
    cls_recs = cursor.fetchall()
    for cls_rec in cls_recs:
        out_dates.append(f"--- {cls_rec['name']} ---")
        cursor.execute("SELECT scheduled_date FROM class_schedule WHERE class_id = ? ORDER BY scheduled_date", (cls_rec['id'],))
        dates = [r['scheduled_date'] for r in cursor.fetchall()]
        out_dates.append(', '.join(dates))
        
with open('class_dates_5.txt', 'w', encoding='utf-8') as f:
    f.write('\n'.join(out_dates))

conn.close()
