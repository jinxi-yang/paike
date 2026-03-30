import sqlite3
import os
import sys

def get_db():
    db_path = os.path.join(os.path.dirname(__file__), 'scheduler.db')
    return sqlite3.connect(db_path)

def auto_fix_schedule(class_name, schedule_data):
    """
    schedule_data format:
    [
        {
            "date": "2025-04-12", # 必须是周六日期
            "day1": {"teacher": "钟彩民", "course": "商业模式设计与创新"}, # 如果为空则传 None
            "day2": None, # 或者类似 day1 的字典
        },
        ...
    ]
    """
    conn = get_db()
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # 1. 查找班级
    cursor.execute("SELECT id FROM class WHERE name LIKE ?", (f'%{class_name}%',))
    cls = cursor.fetchone()
    if not cls:
        print(f"Error: 找不到班级 {class_name}")
        return
    class_id = cls['id']

    for item in schedule_data:
        date = item['date']
        c1_id = None
        c2_id = None

        for day_key, c_id_ref in [('day1', c1_id), ('day2', c2_id)]:
            if item.get(day_key):
                t_name = item[day_key]['teacher']
                c_name = item[day_key]['course']

                # 查找讲师
                cursor.execute("SELECT id FROM teacher WHERE name = ?", (t_name,))
                teacher = cursor.fetchone()
                if not teacher:
                    print(f"Warning: 找不到讲师 {t_name}，为其创建基础记录")
                    cursor.execute("INSERT INTO teacher (name) VALUES (?)", (t_name,))
                    t_id = cursor.lastrowid
                else:
                    t_id = teacher['id']

                # 查找课程
                cursor.execute("SELECT id FROM course WHERE name = ?", (c_name,))
                course = cursor.fetchone()
                if not course:
                    print(f"Warning: 找不到课程 {c_name}，为其创建记录")
                    cursor.execute("INSERT INTO course (name, duration_days) VALUES (?, 2)", (c_name,))
                    c_id = cursor.lastrowid
                else:
                    c_id = course['id']

                # 查找教-课组合 (Combo)
                cursor.execute("SELECT id FROM teacher_course_combo WHERE teacher_id = ? AND course_id = ?", (t_id, c_id))
                combo = cursor.fetchone()
                if not combo:
                    print(f"Warning: 找不到讲师-课程组合 ({t_name}-{c_name})，正在创建")
                    # Needs topic_id, use a default or find an existing
                    cursor.execute("SELECT topic_id FROM teacher WHERE id = ?", (t_id,))
                    t_topic = cursor.fetchone()
                    topic_id = t_topic['topic_id'] if t_topic and t_topic['topic_id'] else 1 # Default fallback
                    cursor.execute("INSERT INTO teacher_course_combo (topic_id, teacher_id, course_id) VALUES (?, ?, ?)", 
                                   (topic_id, t_id, c_id))
                    combo_id = cursor.lastrowid
                else:
                    combo_id = combo['id']

                if day_key == 'day1':
                    c1_id = combo_id
                else:
                    c2_id = combo_id

        # 更新排课记录
        cursor.execute("""
            UPDATE class_schedule 
            SET combo_id = ?, combo_id_2 = ?
            WHERE class_id = ? AND scheduled_date = ?
        """, (c1_id, c2_id, class_id, date))
        
        if cursor.rowcount == 0:
            print(f"Warning: 班级 {class_name} 在 {date} 这一天没有基础排课记录，可能需要手动插入排课！")
        else:
            print(f"[{date}] 已更新 Day1教课ID: {c1_id}, Day2教课ID: {c2_id}")

    conn.commit()
    print(f"班级 {class_name} 的排课修复完毕！")
    conn.close()

if __name__ == "__main__":
    # Example usage:
    # auto_fix_schedule("EMBA122", [
    #     {"date": "2025-04-12", "day1": None, "day2": {"teacher": "钟彩民", "course": "商业模式设计与创新"}},
    # ])
    pass
