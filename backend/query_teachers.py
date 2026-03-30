import sqlite3
import os

db_path = os.path.join(os.path.dirname(__file__), 'scheduler.db')
conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

teachers = ['钟彩民', '王晓耕', '张庆安', '岳庆平', '刘春华', '蔡毅臣', '李继延', '吴子敬', '杨波', '程国辉']
placeholders = ','.join(['?']*len(teachers))

cursor.execute(f"""
    SELECT t.id as teacher_id, t.name as teacher_name, 
           c.id as course_id, c.name as course_name, c.duration_days,
           tc.id as combo_id
    FROM teacher t
    JOIN teacher_course_combo tc ON t.id = tc.teacher_id
    JOIN course c ON tc.course_id = c.id
    WHERE t.name IN ({placeholders})
""", teachers)

results = cursor.fetchall()
out = []
for r in results:
    out.append(f"Teacher: {r['teacher_name']}, Course: {r['course_name']} (Duration: {r['duration_days']} days), Combo ID: {r['combo_id']}")

with open('output_teachers.txt', 'w', encoding='utf-8') as f:
    f.write('\n'.join(out))

conn.close()
