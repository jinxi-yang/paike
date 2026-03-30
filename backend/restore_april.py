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

def get_or_create_combo(teacher_id, course_name, topic_id=None):
    if not teacher_id or not course_name: return None
    cursor.execute("SELECT id FROM teacher_course_combo WHERE teacher_id = ? AND course_name = ?", (teacher_id, course_name))
    combo = cursor.fetchone()
    if combo: return combo['id']
    cursor.execute("INSERT INTO teacher_course_combo (topic_id, teacher_id, course_name, priority) VALUES (?, ?, ?, 0)", (topic_id or 1, teacher_id, course_name))
    return cursor.lastrowid

def add_schedule_correctly(class_name, date, d1_t, d1_c, d2_t, d2_c, seq):
    cursor.execute("SELECT id, project_id FROM class WHERE name LIKE ?", (f'%{class_name}%',))
    cls = cursor.fetchone()
    if not cls: 
        print(f"Class {class_name} not found")
        return
    cls_id = cls['id']
    proj_id = cls['project_id']
    
    cursor.execute("SELECT id FROM topic WHERE project_id = ? AND sequence = ?", (proj_id, seq))
    topic = cursor.fetchone()
    if not topic:
        # Fall back to max sequence topic
        cursor.execute("SELECT id FROM topic WHERE project_id = ? ORDER BY sequence DESC LIMIT 1", (proj_id,))
        topic = cursor.fetchone()
    topic_id = topic['id'] if topic else 1
    
    c1 = get_or_create_combo(get_or_create_teacher(d1_t), d1_c, topic_id)
    c2 = get_or_create_combo(get_or_create_teacher(d2_t), d2_c, topic_id)
    
    cursor.execute("SELECT id FROM class_schedule WHERE class_id = ? AND scheduled_date = ?", (cls_id, date))
    if cursor.fetchone():
        cursor.execute("UPDATE class_schedule SET topic_id = ?, combo_id = ?, combo_id_2 = ?, status='scheduled' WHERE class_id = ? AND scheduled_date = ?", (topic_id, c1, c2, cls_id, date))
    else:
        cursor.execute("INSERT INTO class_schedule (class_id, scheduled_date, topic_id, combo_id, combo_id_2, status) VALUES (?, ?, ?, ?, ?, 'scheduled')", (cls_id, date, topic_id, c1, c2))
    print(f"Restored {class_name} on {date} with topic_id {topic_id}")

add_schedule_correctly('126', '2026-04-18', '董俊豪', '企业AI Deepseek战略课', '易正', '易经智慧', 7)
add_schedule_correctly('127', '2026-04-18', '董俊豪', 'AI驱动增长：企业家的战略蓝图与实战路径', '尚旭', '易经智慧与经营决策', 7)

conn.commit()
conn.close()
print("Restored 126 and 127 successfully!")
