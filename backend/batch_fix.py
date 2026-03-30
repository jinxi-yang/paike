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

# Fix 122 Dean Course
add_or_update_schedule('122', '2025-04-12', '院长', '院长课', '钟彩民', '商业模式设计与创新')

# Data for 123
add_or_update_schedule('123', '2025-04-26', '院长', '院长课', '张庆安', '2025年国际局势与宏观趋势')
add_or_update_schedule('123', '2025-06-07', '刘春华', 'AI时代下的新营销九段法', None, None)
add_or_update_schedule('123', '2025-07-19', '霍振先', '总裁财务思维与经营决策', None, None)
add_or_update_schedule('123', '2025-09-27', '蔡毅臣', '新形势下的战略人力资源管理', None, None)
add_or_update_schedule('123', '2025-11-08', '岳庆平', '中国历代王朝的治乱兴衰', None, None)
add_or_update_schedule('123', '2026-03-07', '董俊豪', '企业 AI Deepseek 战略课', '杨台轩', '3D领导力—企业与员工成长发展的战略性突破')
add_or_update_schedule('123', '2026-04-11', '熊郭健', '《从造物到谋事：商业模式落地实操》', None, None)
add_or_update_schedule('123', '2026-06-13', '陈晋蓉', '资本运营新策略', '刘钰', '公司治理与股权设计')

# Data for 126
add_or_update_schedule('126', '2025-06-07', '院长', '院长课', '岳庆平', '宏观经济与政策分析')
add_or_update_schedule('126', '2025-07-05', '李继延', '创新思维与企业战略', None, None)
add_or_update_schedule('126', '2025-08-16', '吴子敬', '股权设计、股权合伙与激励', None, None)
add_or_update_schedule('126', '2025-10-18', '蔡毅臣', '新形势下的战略人力资源管理', None, None)
add_or_update_schedule('126', '2025-11-22', '霍振先', '总裁决策者财税思维', None, None)
add_or_update_schedule('126', '2026-03-07', '刘春华', 'AI时代下的新营销九步法', None, None)
add_or_update_schedule('126', '2026-04-18', '董俊豪', '待定', '易正', '待定')
add_or_update_schedule('126', '2026-05-23', '曲融', '投资视角下的行业研究体系分析', '王薇华', '待定')
cursor.execute("DELETE FROM class_schedule WHERE class_id = (SELECT id FROM class WHERE name LIKE '%126%') AND scheduled_date IN ('2025-08-02', '2025-08-30')")

# Data for 127
add_or_update_schedule('127', '2025-06-28', '院长', '院长课', '王正', '卓越领导与高效团队')
add_or_update_schedule('127', '2025-08-09', '蔡毅臣', '新形势下的战略人力资源管理', None, None)
add_or_update_schedule('127', '2025-09-27', '刘春华', 'AI时代下的新营销九步法', None, None)
add_or_update_schedule('127', '2025-10-25', '霍振先', '总裁财务思维与经营决策', None, None)
add_or_update_schedule('127', '2025-12-20', '岳庆平', '《中国历代王朝的治乱兴衰》', None, None)
add_or_update_schedule('127', '2026-03-14', '刘钰', '股权设计和资本路径', '韩铁林', '企业战略规划与制定')
add_or_update_schedule('127', '2026-04-18', '董俊豪', '《AI驱动增长：企业家的战略蓝图与实战路径》', '尚旭', '《易经智慧与经营决策》')
add_or_update_schedule('127', '2026-05-30', '曲融', '投资视角下的行业研究体系分析', None, None)
add_or_update_schedule('127', '2026-06-27', '熊郭健', '从造物到谋事：商业模式落地实操', None, None)
add_or_update_schedule('127', '2026-08-01', '杨波', '《领导力赋能组织活力》', '易正', '中国古法姓名学')

# Data for 128
add_or_update_schedule('128', '2025-07-12', '院长', '院长课', '李其', '宏观经济与政策解读')
add_or_update_schedule('128', '2025-08-16', '齐昊', '财务功守道—十倍价值增长', None, None)
add_or_update_schedule('128', '2025-09-20', '尚旭', '《易经智慧与经营决策》', '钟彩民', '《商业模式设计与创新》')
add_or_update_schedule('128', '2025-11-01', '蔡毅臣', '新形势下的战略人力资源管理', None, None)
add_or_update_schedule('128', '2025-12-20', '董俊豪', '企业AI Deepseek战略课', '常亮', '《公司股权架构设计与激励》')
add_or_update_schedule('128', '2026-03-21', '吴子敬', '股权设计、合伙激励与融资', None, None)
add_or_update_schedule('128', '2026-05-09', '杨波', '领导力赋能组织活力', '阙登峰', '“投入不变 业绩倍增”的全过程管理')
add_or_update_schedule('128', '2026-06-27', '刘钰', '待定', '龙平敬', '企业资本价值倍增之道')

conn.commit()
conn.close()
print("All schedules fixed")
