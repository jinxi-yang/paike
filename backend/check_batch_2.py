import sqlite3
import os

db_path = os.path.join(os.path.dirname(__file__), 'scheduler.db')
conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

teachers_to_check = [
    "郑翔洲", "严小云", "郝军龙", "刘勇", "张涛", "张晓丽", "张益铭", "史璐", "张华光", "万力"
]

out = []
for t in teachers_to_check:
    cursor.execute("SELECT id FROM teacher WHERE name = ?", (t,))
    res = cursor.fetchone()
    if res:
        out.append(f"Found: {t}")
    else:
        out.append(f"MISSING: {t}")

with open('teacher_check_2.txt', 'w', encoding='utf-8') as f:
    f.write('\n'.join(out))

classes = ['125', '129', '130', '131']
out_dates = []

for c in classes:
    cursor.execute("SELECT id, name FROM class WHERE name LIKE ?", (f'%{c}%',))
    cls_rec = cursor.fetchone()
    if cls_rec:
        out_dates.append(f"--- {cls_rec['name']} ---")
        cursor.execute("SELECT scheduled_date FROM class_schedule WHERE class_id = ? ORDER BY scheduled_date", (cls_rec['id'],))
        dates = [r['scheduled_date'] for r in cursor.fetchall()]
        out_dates.append(', '.join(dates))
        
with open('class_dates_2.txt', 'w', encoding='utf-8') as f:
    f.write('\n'.join(out_dates))

conn.close()
