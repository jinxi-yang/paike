import sqlite3
import os

db_path = os.path.join(os.path.dirname(__file__), 'scheduler.db')
conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

def get_or_create_teacher(name):
    if not name: return None
    cursor.execute("SELECT id FROM teacher WHERE name = ?", (name,))
    t = cursor.fetchone()
    if t: return t['id']
    cursor.execute("INSERT INTO teacher (name) VALUES (?)", (name,))
    return cursor.lastrowid

def get_or_create_combo(teacher_id, course_name, topic_id):
    if not teacher_id or not course_name: return None
    cursor.execute("SELECT id FROM teacher_course_combo WHERE teacher_id = ? AND course_name = ?", (teacher_id, course_name))
    combo = cursor.fetchone()
    if combo: return combo['id']
    cursor.execute("INSERT INTO teacher_course_combo (topic_id, teacher_id, course_name, priority) VALUES (?, ?, ?, 0)", (topic_id, teacher_id, course_name))
    return cursor.lastrowid

# Give EMBA126 topic_id = 8 (which it has NOT completed)
topic_id = 8

cursor.execute("SELECT id FROM class WHERE name LIKE '%126%'")
cls_id = cursor.fetchone()['id']

c1 = get_or_create_combo(get_or_create_teacher('董俊豪'), '企业AI Deepseek战略课', topic_id)
c2 = get_or_create_combo(get_or_create_teacher('易正'), '易经智慧', topic_id)

cursor.execute("SELECT id FROM class_schedule WHERE class_id = ? AND scheduled_date = '2026-04-18'", (cls_id,))
if cursor.fetchone():
    cursor.execute("UPDATE class_schedule SET topic_id = ?, combo_id = ?, combo_id_2 = ?, status='scheduled' WHERE class_id = ? AND scheduled_date = '2026-04-18'", (topic_id, c1, c2, cls_id))
else:
    cursor.execute("INSERT INTO class_schedule (class_id, scheduled_date, topic_id, combo_id, combo_id_2, status) VALUES (?, '2026-04-18', ?, ?, ?, 'scheduled')", (cls_id, topic_id, c1, c2))

conn.commit()
conn.close()
print("Fixed EMBA126 with an uncompleted topic ID!")
