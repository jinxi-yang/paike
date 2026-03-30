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

# Data for 125
add_or_update_schedule('125', '2025-05-17', '院长', '院长课', '郑翔洲', '《新资本商业模式创新》')
add_or_update_schedule('125', '2025-06-21', '霍振先', '总裁财务思维与经营决策', None, None)
add_or_update_schedule('125', '2025-07-26', '严小云', '《卓越薪酬绩效管理体系》', None, None)
add_or_update_schedule('125', '2025-08-23', '郝军龙', '战略目标与落地执行', None, None)
add_or_update_schedule('125', '2025-10-18', '杨台轩', '《3D领导力—企业与员工成长发展的战略性突破》', '刘勇', '《AI全网矩阵营销与产业互联网进化》')
add_or_update_schedule('125', '2025-12-20', '董俊豪', '企业AI Deepseek战略课', '常亮', '《公司股权架构设计与激励》')
add_or_update_schedule('125', '2026-03-21', '吴子敬', '股权设计、合伙激励与融资', None, None)
add_or_update_schedule('125', '2026-05-09', '张涛', '大数据时代突发事件管理与网络舆情应对', '曲融', '投资视角下的行业研究体系分析')

# Data for 129
add_or_update_schedule('129', '2025-07-26', '院长', '院长课', '王正', '卓越领导与高效团队')
add_or_update_schedule('129', '2025-08-30', '蔡毅臣', '新形势下的战略人力资源管理', None, None)
add_or_update_schedule('129', '2025-10-11', '李继延', '创新思维与企业战略', None, None)
add_or_update_schedule('129', '2025-11-15', '熊郭健', '《从造物到谋事：商业模式落地实操》', None, None)
add_or_update_schedule('129', '2025-12-20', '刘春华', 'AI时代下的新营销九步法', None, None)
add_or_update_schedule('129', '2026-03-07', '霍振先', '《总裁财务思维与经营决策》', None, None)
add_or_update_schedule('129', '2026-04-18', '杨波', '领导力', '张晓丽', '资本')
add_or_update_schedule('129', '2026-05-09', '吴子敬', '待定', None, None)
cursor.execute("DELETE FROM class_schedule WHERE class_id = (SELECT id FROM class WHERE name LIKE '%129%') AND scheduled_date IN ('2026-01-17', '2026-04-04')")

# Data for 130
add_or_update_schedule('130', '2025-09-13', '钟彩民', '商业模式设计与创新', None, None)
add_or_update_schedule('130', '2025-10-18', '蔡毅臣', '新形势下的战略人力资源管理', None, None)
add_or_update_schedule('130', '2025-11-22', '霍振先', '总裁决策者财税思维', None, None)
add_or_update_schedule('130', '2025-12-18', '孔海钦', '国学的新思维', None, None)
add_or_update_schedule('130', '2026-01-17', '杨波', '领导力赋能组织活力', None, None)
add_or_update_schedule('130', '2026-03-21', '刘春华', 'AI时代下的新营销九步法', None, None)
add_or_update_schedule('130', '2026-05-23', '曲融', '宏观环境与产业机遇分析', None, None)
add_or_update_schedule('130', '2026-06-19', '张益铭', '家庭幸福与企业效益', None, None)
add_or_update_schedule('130', '2026-07-23', '岳庆平', '中国历代王朝的治乱兴衰', None, None)
add_or_update_schedule('130', '2026-08-29', '吴子敬', '股权设计、股权合伙与激励', None, None)
cursor.execute("DELETE FROM class_schedule WHERE class_id = (SELECT id FROM class WHERE name LIKE '%130%') AND scheduled_date = '2025-08-09'")

# Data for 131
add_or_update_schedule('131', '2025-08-30', '院长', '院长课', '史璐', '《最新国际形势与中国宏观经济》')
add_or_update_schedule('131', '2025-09-20', '李继延', '创新思维与企业战略', None, None)
add_or_update_schedule('131', '2025-10-25', '杨波', '《领导力赋能组织活力》', '张涛', '《大数据时代突发事件管理与网络舆情应对》')
add_or_update_schedule('131', '2025-11-29', '蔡毅臣', '新形势下的战略人力资源管理', None, None)
add_or_update_schedule('131', '2025-12-27', '齐昊', '《卓越经营者的财务管理必修课》', None, None)
add_or_update_schedule('131', '2026-03-28', '吴子敬', '《股权激励与公司治理》', None, None)
add_or_update_schedule('131', '2026-05-16', '张华光', 'AI时代的商业模式创新系统与趋势', None, None)
add_or_update_schedule('131', '2026-07-18', '万力', '专精特新的第一品牌', None, None)
add_or_update_schedule('131', '2026-08-22', '孔海钦', '国学的新思维', '岳庆平', '中国历代王朝的治乱兴衰')

conn.commit()
conn.close()
print("Schedules for 125, 129, 130, 131 successfully fixed!")
