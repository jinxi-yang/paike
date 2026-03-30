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

# Data for 139
add_or_update_schedule('139', '2025-12-27', '院长', '院长课', '史璐', '宏观经济与政策解读')
add_or_update_schedule('139', '2026-03-07', '沈佳', '《企业家卓越领导能力构建》', '陈晋蓉', '经营管理与财务分析')
add_or_update_schedule('139', '2026-04-25', '霍振先', '总裁财务思维与经营决策', None, None)
add_or_update_schedule('139', '2026-05-16', '蔡毅臣', '新形势下的战略人力资源管理', None, None)
add_or_update_schedule('139', '2026-07-18', '李继延', '企业战略规划与制定', None, None)
add_or_update_schedule('139', '2026-08-22', '熊郭健', '从造物到谋事：商业模式落地实操', None, None)
add_or_update_schedule('139', '2026-10-10', '董俊豪', '企业AI Deepseek战略课', '曲融', '投资视角下的行业研究体系分析')
add_or_update_schedule('139', '2026-11-14', '刘钰', '股权设计和资本路径', '尚旭', '企业布局的财富智慧')

# Data for 151
add_or_update_schedule('151', '2025-01-31', '院长', '院长课', '谷晟阳', '《国学易经大智慧与企业家居风水学》')
add_or_update_schedule('151', '2025-03-14', '蔡毅臣', '新形势下的战略人力资源管理', None, None)
add_or_update_schedule('151', '2025-04-11', '黄宏', '商业模式创新与落地', '刘钰', '股权设计和资本路径')
add_or_update_schedule('151', '2025-05-23', '梁培霖', '《5D战略屋方法论》-从战略到执行的制胜密码', None, None)
add_or_update_schedule('151', '2025-06-27', '李中生', 'AI新媒体营销', None, None)
add_or_update_schedule('151', '2025-08-15', '董俊豪', '企业 AI Deepseek 战略课', '宗英涛', '稻盛和夫的经营哲学')
add_or_update_schedule('151', '2025-10-17', '于洋', '人力资源开发与管理', None, None)
add_or_update_schedule('151', '2025-12-12', '谢华', '存量市场数字化新商业模式', '沈佳', '企业家卓越领导能力构建')

# Data for 152
add_or_update_schedule('152', '2025-03-28', '院长', '院长课', '史璐', '宏观经济与政策解读')
add_or_update_schedule('152', '2025-04-25', '蔡毅臣', '新形势下的战略人力资源管理', None, None)
add_or_update_schedule('152', '2025-05-30', '刘春华', 'AI时代下的新营销九步法', None, None)
add_or_update_schedule('152', '2025-07-04', '杨台轩', '3D领导力—企业与员工成长发展的战略性突破', None, None)
add_or_update_schedule('152', '2025-08-22', '李益诚', '公司治理与商业模式', None, None)
add_or_update_schedule('152', '2025-10-24', '王悦', '掌控财务风险，赋能经营管理', None, None)
add_or_update_schedule('152', '2025-12-19', '王京刚', '企业战略与数字化转型', None, None)
add_or_update_schedule('152', '2026-02-27', '程国辉', '企业文化从墙上到心上', '苏伟', '企业家信念管理')

# Data for 153
add_or_update_schedule('153', '2025-03-21', '院长', '院长课', '张庆安', '最新国际形势与中国宏观经济')
add_or_update_schedule('153', '2025-04-25', '李继延', '创新思维与战略管理', None, None)
add_or_update_schedule('153', '2025-05-30', '蔡毅臣', '新形势下的战略人力资源管理', None, None)
add_or_update_schedule('153', '2025-07-11', '沈佳', '企业家卓越领导能力构建', '董俊豪', '企业AI Deepseek战略课')
add_or_update_schedule('153', '2025-09-12', '刘春华', 'AI时代下的新营销九步法', None, None)
add_or_update_schedule('153', '2025-11-07', '熊郭健', '从造物到谋事：商业模式落地实操', None, None)
add_or_update_schedule('153', '2025-12-19', '吕定杰', '新公司法下企业财税与风险管控', None, None)
add_or_update_schedule('153', '2026-01-16', '刘钰', '股权设计与资本路径', '龙平敬', '企业资本价值倍增之道')

conn.commit()
conn.close()
print("Schedules for 139, 151, 152, 153 successfully fixed!")
