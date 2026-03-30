import sqlite3
import os
import json

db_path = os.path.join(os.path.dirname(__file__), 'scheduler.db')
conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

result = []

cursor.execute("SELECT id, name FROM class WHERE name LIKE '%122%'")
cls = cursor.fetchone()
if cls:
    result.append(f"Class: {cls['name']} (ID: {cls['id']})")
    
    cursor.execute("""
        SELECT cs.id, cs.scheduled_date as date, t.name as topic_name, tc.id as tc_id, 
               tc2.id as tc2_id, teacher1.name as teacher1_name, course1.name as course1_name,
               teacher2.name as teacher2_name, course2.name as course2_name,
               cs.has_opening as opening, cs.has_team_building as tb1,
               cs.day2_has_opening as op2, cs.day2_has_team_building as tb2
        FROM class_schedule cs
        LEFT JOIN topic t ON cs.topic_id = t.id
        LEFT JOIN teacher_course_combo tc ON cs.combo_id = tc.id
        LEFT JOIN teacher teacher1 ON tc.teacher_id = teacher1.id
        LEFT JOIN course course1 ON tc.course_id = course1.id
        LEFT JOIN teacher_course_combo tc2 ON cs.combo_id_2 = tc2.id
        LEFT JOIN teacher teacher2 ON tc2.teacher_id = teacher2.id
        LEFT JOIN course course2 ON tc2.course_id = course2.id
        WHERE cs.class_id = ?
        ORDER BY cs.scheduled_date
    """, (cls['id'],))
    
    schedules = cursor.fetchall()
    result.append("--- Schedule ---")
    for s in schedules:
        d1 = f"Day1: {s['teacher1_name']}-{s['course1_name']}" if s['tc_id'] else "Day1: None"
        d2 = f"Day2: {s['teacher2_name']}-{s['course2_name']}" if s['tc2_id'] else "Day2: None"
        flags = []
        if s['opening']: flags.append('Day1-Open')
        if s['tb1']: flags.append('Day1-TB')
        if s['op2']: flags.append('Day2-Open')
        if s['tb2']: flags.append('Day2-TB')
        result.append(f"Date(Sat): {s['date']}, Topic: {s['topic_name']}, {d1}, {d2}, Flags: {flags}")
else:
    result.append("Class not found.")

conn.close()

with open('output_122.txt', 'w', encoding='utf-8') as f:
    f.write('\n'.join(result))
