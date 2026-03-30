import sqlite3
import os
import sys
import codecs

if sys.platform == "win32":
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.detach())

db_path = os.path.join(os.path.dirname(__file__), 'scheduler.db')
conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

classes_to_check = ['151', '152', '153', '155', '156']

query = """
    SELECT c.name as class_name, cs.scheduled_date, 
           t1.name as teacher_1, tc1.course_name as course_1,
           t2.name as teacher_2, tc2.course_name as course_2
    FROM class_schedule cs
    JOIN class c ON cs.class_id = c.id
    LEFT JOIN teacher_course_combo tc1 ON cs.combo_id = tc1.id
    LEFT JOIN teacher t1 ON tc1.teacher_id = t1.id
    LEFT JOIN teacher_course_combo tc2 ON cs.combo_id_2 = tc2.id
    LEFT JOIN teacher t2 ON tc2.teacher_id = t2.id
    WHERE cs.scheduled_date >= '2026-01-01' AND cs.scheduled_date <= '2026-12-31'
    AND ({})
    ORDER BY c.name, cs.scheduled_date
"""
like_clauses = " OR ".join([f"c.name LIKE '%{cls}%'" for cls in classes_to_check])

cursor.execute(query.format(like_clauses))
rows = cursor.fetchall()
conn.close()

data = {}
for r in rows:
    cname = r['class_name']
    if cname not in data:
        data[cname] = []
    
    t1 = r['teacher_1'] or ''
    c1 = r['course_1'] or ''
    t2 = r['teacher_2'] or ''
    c2 = r['course_2'] or ''
    
    c1_str = f"[{t1}] {c1}" if t1 or c1 else ""
    c2_str = f"[{t2}] {c2}" if t2 or c2 else ""
    combos = f"{c1_str} | {c2_str}" if c2_str else c1_str
    
    data[cname].append(f"{r['scheduled_date']} -> {combos}")

for cname, schedules in sorted(data.items()):
    print(f"\n=== {cname} ===")
    for s in schedules:
        print("  " + s)
