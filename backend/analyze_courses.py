import sqlite3
import os
import json

db_path = os.path.join(os.path.dirname(__file__), 'scheduler.db')
conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

def analyze_courses():
    # Find all courses
    cursor.execute("SELECT id, name FROM course")
    courses = cursor.fetchall()

    # Find courses that are actually used in some class schedule
    cursor.execute("""
        SELECT DISTINCT c.id, c.name 
        FROM course c
        JOIN teacher_course_combo tcc ON c.id = tcc.course_id
        JOIN class_schedule cs ON cs.combo_id = tcc.id OR cs.combo_id_2 = tcc.id
    """)
    used_in_schedule = {row['id']: row['name'] for row in cursor.fetchall()}

    # Find courses bound to an active combo (even if not scheduled)
    cursor.execute("""
        SELECT DISTINCT c.id, c.name 
        FROM course c
        JOIN teacher_course_combo tcc ON c.id = tcc.course_id
    """)
    in_combos = {row['id']: row['name'] for row in cursor.fetchall()}

    # Courses with 《》
    book_courses = [c for c in courses if '《' in c['name'] or '》' in c['name']]

    print(f"Total courses: {len(courses)}")
    print(f"Courses in combos: {len(in_combos)}")
    print(f"Courses used in schedules: {len(used_in_schedule)}")
    
    print("\n--- Courses with 《》 ---")
    for c in book_courses:
        is_scheduled = "YES" if c['id'] in used_in_schedule else "NO"
        is_in_combo = "YES" if c['id'] in in_combos else "NO"
        print(f"ID: {c['id']:3} | Scheduled: {is_scheduled} | Combo: {is_in_combo} | Name: {c['name']}")

if __name__ == '__main__':
    analyze_courses()
    conn.close()
