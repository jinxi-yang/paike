import sqlite3
import os

db_path = os.path.join(os.path.dirname(__file__), 'scheduler.db')
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Fix EMBA 128 Session 8
# Find the schedule ID for EMBA 128 on 2026-06-27
cursor.execute("""
    SELECT cs.id, cs.combo_id 
    FROM class_schedule cs 
    JOIN class c ON cs.class_id = c.id 
    WHERE c.name LIKE '%128%' AND cs.scheduled_date = '2026-06-27'
""")
res = cursor.fetchone()
if res:
    sched_id, combo_id = res
    # Update the combo_id's course name if it's "待定"
    cursor.execute("UPDATE teacher_course_combo SET course_name = '企业资本价值倍增之道' WHERE id = ? AND course_name = '待定'", (combo_id,))
    print(f"Updated EMBA 128 combo {combo_id} course name.")

conn.commit()
conn.close()
