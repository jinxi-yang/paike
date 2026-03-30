import sqlite3
import os

db_path = os.path.join(os.path.dirname(__file__), 'scheduler.db')
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# 1. Update Course names
cursor.execute("""
    UPDATE course SET name = '国际形势与宏观经济' 
    WHERE id = (SELECT course_id FROM teacher_course_combo WHERE id = 68)
""")
cursor.execute("""
    UPDATE course SET name = 'AI时代下的新营销九段法' 
    WHERE id = (SELECT course_id FROM teacher_course_combo WHERE id = 14)
""")

# Schedule mappings: Date -> (combo_id, combo_id_2)
# Using the dates from the previous query for Class 1
schedule_updates = {
    '2025-04-12': (None, 10),
    '2025-05-24': (35, 68),
    '2025-06-28': (4, None),
    '2025-08-09': (14, None),
    '2025-10-18': (110, None),
    '2025-12-06': (73, None),
    '2026-03-21': (75, None),
    '2026-05-09': (44, 78)
}

for date, combos in schedule_updates.items():
    c1, c2 = combos
    cursor.execute("""
        UPDATE class_schedule 
        SET combo_id = ?, combo_id_2 = ?
        WHERE class_id = 1 AND scheduled_date = ?
    """, (c1, c2, date))

conn.commit()
print("Schedules updated successfully.")
conn.close()
