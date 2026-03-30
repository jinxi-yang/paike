import sqlite3
import os

db_path = os.path.join(os.path.dirname(__file__), 'scheduler.db')
bak_path = os.path.join(os.path.dirname(__file__), 'scheduler.db.bak_before_course_removal')

def restore_missing_schedules():
    # 1. Connect to backup to read the missing 6 schedules
    conn_bak = sqlite3.connect(bak_path)
    cur_bak = conn_bak.cursor()
    # Missing classes: 123 (6-13), 128 (6-27), 127 (8-01), 136 (9-12), 135 (10-24), 136 (11-14)
    # They have status=None
    cur_bak.execute("""
        SELECT cs.class_id, cs.scheduled_date, cs.topic_id, cs.combo_id, cs.combo_id_2,
               c.name as class_name,
               tc1.course_id as c1_course_id, tc2.course_id as c2_course_id,
               c1.name as course_1_name, c2.name as course_2_name,
               t1.name as teacher_1_name, t2.name as teacher_2_name
        FROM class_schedule cs
        JOIN class c ON cs.class_id = c.id
        LEFT JOIN teacher_course_combo tc1 ON cs.combo_id = tc1.id
        LEFT JOIN course c1 ON tc1.course_id = c1.id
        LEFT JOIN teacher t1 ON tc1.teacher_id = t1.id
        LEFT JOIN teacher_course_combo tc2 ON cs.combo_id_2 = tc2.id
        LEFT JOIN course c2 ON tc2.course_id = c2.id
        LEFT JOIN teacher t2 ON tc2.teacher_id = t2.id
        WHERE cs.status IS NULL AND cs.scheduled_date >= '2026-05-01'
    """)
    missing_records = cur_bak.fetchall()
    conn_bak.close()

    print(f"Found {len(missing_records)} future missing records in backup.")
    
    # 2. Connect to CURRENT DB and insert them
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

    restored = 0
    for r in missing_records:
        cls_id = r[0]
        date = r[1]
        cls_name = r[5]
        
        # Course info from backup
        course_1_name = r[8]
        course_2_name = r[9]
        teacher_1_name = r[10]
        teacher_2_name = r[11]
        
        # Assign to highest sequence topic to prevent auto-cleanup!
        cursor.execute("SELECT project_id FROM class WHERE id = ?", (cls_id,))
        proj_id = cursor.fetchone()['project_id']
        cursor.execute("SELECT id FROM topic WHERE project_id = ? ORDER BY sequence DESC LIMIT 1", (proj_id,))
        topic = cursor.fetchone()
        topic_id = topic['id'] if topic else 1

        c1 = get_or_create_combo(get_or_create_teacher(teacher_1_name), course_1_name, topic_id)
        c2 = get_or_create_combo(get_or_create_teacher(teacher_2_name), course_2_name, topic_id)
        
        cursor.execute("SELECT id FROM class_schedule WHERE class_id = ? AND scheduled_date = ?", (cls_id, date))
        if cursor.fetchone():
            cursor.execute("UPDATE class_schedule SET topic_id = ?, combo_id = ?, combo_id_2 = ?, status='scheduled' WHERE class_id = ? AND scheduled_date = ?", (topic_id, c1, c2, cls_id, date))
        else:
            cursor.execute("INSERT INTO class_schedule (class_id, scheduled_date, topic_id, combo_id, combo_id_2, status) VALUES (?, ?, ?, ?, ?, 'scheduled')", (cls_id, date, topic_id, c1, c2))
        
        print(f"Restored: {cls_name} on {date} with Topic ID {topic_id} (Teachers: {teacher_1_name}, {teacher_2_name})")
        restored += 1

    conn.commit()
    conn.close()
    print(f"\nSuccessfully fully restored {restored} schedules into the current database.")

if __name__ == '__main__':
    restore_missing_schedules()
