import sqlite3
import os

db_path = os.path.join(os.path.dirname(__file__), 'scheduler.db')
bak_path = os.path.join(os.path.dirname(__file__), 'scheduler.db.bak_before_course_removal')

def restore_safely():
    conn_bak = sqlite3.connect(bak_path)
    cur_bak = conn_bak.cursor()
    cur_bak.execute("""
        SELECT cs.class_id, cs.scheduled_date,
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

    def get_safe_topic_id(cls_id):
        # find completed topics
        cursor.execute("SELECT topic_id FROM class_schedule WHERE class_id = ? AND status = 'completed'", (cls_id,))
        completed = set(r['topic_id'] for r in cursor.fetchall() if r['topic_id'])
        # find a topic NOT in completed
        cursor.execute("SELECT id FROM topic")
        for t in cursor.fetchall():
            if t['id'] not in completed:
                return t['id']
        # if incredibly, all topics are completed, create a dummy topic
        cursor.execute("INSERT INTO topic (name, sequence, project_id) VALUES ('附加选修课题', 99, 1)")
        return cursor.lastrowid

    restored = 0
    for r in missing_records:
        cls_id = r[0]
        date = r[1]
        cls_name = r[2]
        
        # Check if it already exists in CURRENT DB cleanly
        cursor.execute("SELECT id FROM class_schedule WHERE class_id = ? AND scheduled_date = ?", (cls_id, date))
        if cursor.fetchone():
            continue  # already exists
            
        course_1_name = r[5]
        course_2_name = r[6]
        teacher_1_name = r[7]
        teacher_2_name = r[8]
        
        safe_topic_id = get_safe_topic_id(cls_id)

        c1 = get_or_create_combo(get_or_create_teacher(teacher_1_name), course_1_name, safe_topic_id)
        c2 = get_or_create_combo(get_or_create_teacher(teacher_2_name), course_2_name, safe_topic_id)
        
        cursor.execute("INSERT INTO class_schedule (class_id, scheduled_date, topic_id, combo_id, combo_id_2, status) VALUES (?, ?, ?, ?, ?, 'scheduled')", (cls_id, date, safe_topic_id, c1, c2))
        
        print(f"SAFELY RESTORED: {cls_name} on {date} with Safe Topic ID {safe_topic_id}")
        restored += 1

    conn.commit()
    conn.close()
    print(f"\nSafely inserted {restored} schedules.")

if __name__ == '__main__':
    restore_safely()
