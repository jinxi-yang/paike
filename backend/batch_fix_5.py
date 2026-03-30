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

def get_or_create_course(name):
    if not name: return None
    cursor.execute("SELECT id FROM course WHERE name = ?", (name,))
    c = cursor.fetchone()
    if c: return c['id']
    cursor.execute("INSERT INTO course (name, duration_days) VALUES (?, 2)", (name,))
    return cursor.lastrowid

def get_or_create_combo(teacher_id, course_id):
    if not teacher_id or not course_id: return None
    cursor.execute("SELECT id FROM teacher_course_combo WHERE teacher_id = ? AND course_id = ?", (teacher_id, course_id))
    combo = cursor.fetchone()
    if combo: return combo['id']
    cursor.execute("INSERT INTO teacher_course_combo (topic_id, teacher_id, course_id) VALUES (1, ?, ?)", (teacher_id, course_id))
    return cursor.lastrowid

def add_or_update_schedule(class_name, date, d1_t, d1_c, d2_t, d2_c):
    cursor.execute("SELECT id FROM class WHERE name LIKE ?", (f'%{class_name}%',))
    cls = cursor.fetchone()
    if not cls: return
    cls_id = cls['id']
    
    c1 = get_or_create_combo(get_or_create_teacher(d1_t), get_or_create_course(d1_c))
    c2 = get_or_create_combo(get_or_create_teacher(d2_t), get_or_create_course(d2_c))
    
    cursor.execute("SELECT id FROM class_schedule WHERE class_id = ? AND scheduled_date = ?", (cls_id, date))
    if cursor.fetchone():
        cursor.execute("UPDATE class_schedule SET combo_id = ?, combo_id_2 = ? WHERE class_id = ? AND scheduled_date = ?", (c1, c2, cls_id, date))
    else:
        cursor.execute("INSERT INTO class_schedule (class_id, scheduled_date, topic_id, combo_id, combo_id_2) VALUES (?, ?, 1, ?, ?)", (cls_id, date, c1, c2))

# Data for 155
add_or_update_schedule('155', '2025-04-25', '院长', '院长课', '张庆安', '宏观经济与政策分析')
add_or_update_schedule('155', '2025-05-30', '蔡毅臣', '新形势下的战略人力资源管理', None, None)
add_or_update_schedule('155', '2025-07-04', '李继延', '创新思维与战略管理', None, None)
add_or_update_schedule('155', '2025-08-15', '刘春华', 'AI时代下的新营销九步法', None, None)
add_or_update_schedule('155', '2025-10-17', '刘钰', '股权设计和资本路径', '龙平敬', '企业资本价值倍增之道')
add_or_update_schedule('155', '2025-12-12', '曲融', '投资视角下的行业研究体系分析', None, None)
add_or_update_schedule('155', '2026-01-23', '黄洁', 'AI前沿趋势与现实场景应用', '黄宏', '商业模式创新与落地')
add_or_update_schedule('155', '2026-03-20', '杨波', '领导力赋能组织活力', '易正', '中国古法姓名学')

# Data for 156
add_or_update_schedule('156', '2025-04-25', '刘钰', '股权设计与资本路径', None, None)
add_or_update_schedule('156', '2025-05-30', '霍振先', '总裁决策者财税思维', None, None)
add_or_update_schedule('156', '2025-07-11', '蔡毅臣', '新形势下的战略人力资源管理', None, None)
add_or_update_schedule('156', '2025-08-22', '刘春华', 'AI时代下的新营销九步法', None, None)
add_or_update_schedule('156', '2025-10-10', '张庆安', '宏观经济与政策分析', '董俊豪', '企业AI战略课')
add_or_update_schedule('156', '2025-11-21', '李益诚', '公司治理与商业模式', None, None)
add_or_update_schedule('156', '2026-01-15', '沈佳', '企业家卓越领导能力构建', '宗英涛', '稻盛和夫的经营哲学')
add_or_update_schedule('156', '2026-03-13', '张晓丽', '资本趋势破解：经济周期研判与思维重构', '易正', '易经智慧与财富幸福')

conn.commit()
conn.close()
print("Schedules for 155, 156 successfully fixed!")
