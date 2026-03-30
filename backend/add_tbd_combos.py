import sqlite3
import os

db_path = os.path.join(os.path.dirname(__file__), 'scheduler.db')
conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

# 1. 确保存在名为“待定”的课程
cursor.execute("SELECT id FROM course WHERE name = '待定'")
course = cursor.fetchone()
if not course:
    cursor.execute("INSERT INTO course (name, duration_days) VALUES ('待定', 2)")
    course_id = cursor.lastrowid
else:
    course_id = course['id']

# 2. 获取所有讲师
cursor.execute("SELECT id, name, topic_id FROM teacher")
teachers = cursor.fetchall()

added_count = 0
for t in teachers:
    t_id = t['id']
    # 查找为该讲师绑定的主课题ID。若没有，则默认1
    t_topic_id = t['topic_id'] if t['topic_id'] else 1
    
    # 检查是否已存在该老师的“待定”组合
    cursor.execute("SELECT id FROM teacher_course_combo WHERE teacher_id = ? AND course_id = ?", (t_id, course_id))
    combo = cursor.fetchone()
    if not combo:
        # 添加组合：将优先级设为非常低（比如-1），即使不小心被查出来也会排在最末尾
        cursor.execute(
            "INSERT INTO teacher_course_combo (topic_id, teacher_id, course_id, priority) VALUES (?, ?, ?, -1)", 
            (t_topic_id, t_id, course_id)
        )
        added_count += 1

conn.commit()
print(f"为全系统师资库增加了 {added_count} 个待定组合配置！")
conn.close()
