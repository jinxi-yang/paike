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

# Data for 132
add_or_update_schedule('132', '2025-09-27', '院长', '院长课', '张庆安', '《当前国际格局态势与中国宏观经济走向》')
add_or_update_schedule('132', '2025-11-01', '李继延', '《创新思维与战略管理》', None, None)
add_or_update_schedule('132', '2025-12-06', '蔡毅臣', '新形势下的战略人力资源管理', None, None)
add_or_update_schedule('132', '2026-03-07', '於丙才', '金税四期下:企业高爆雷涉税风险及防范', '宗英涛', '稻盛和夫的经营哲学')
add_or_update_schedule('132', '2026-04-18', '刘钰', '股权设计和资本路径', '黄宏', '商业模式创新与落地')
add_or_update_schedule('132', '2026-06-13', '刘春华', 'AI时代下的新营销九步法', None, None)
add_or_update_schedule('132', '2026-08-15', '董俊豪', '企业AI Deepseek战略课', '曲融', '投资视角下的行业研究体系分析')
add_or_update_schedule('132', '2026-10-17', '沈佳', '企业家卓越领导能力构建', '孔海钦', '国学的新思维')

# Data for 133
add_or_update_schedule('133', '2025-12-13', '刘钰', '商业模式设计与盈利增长', '杨军', 'AI驱动时代：企业股权融资创新之道')
add_or_update_schedule('133', '2026-03-14', '董俊豪', '《AI驱动增长：企业家的战略蓝图与实战路径》', '张凯寓', '《企业AI增长引擎：从战略全景到90天落地行动》')
add_or_update_schedule('133', '2026-04-18', '霍振先', '总裁决策者财税思维', None, None)
add_or_update_schedule('133', '2026-05-23', '李江涛', 'AI时代企业战略管理', None, None)
add_or_update_schedule('133', '2026-06-27', '刘春华', 'AI时代下的新营销九步法', None, None)
add_or_update_schedule('133', '2026-08-15', '曲融', '投资视角下的行业研究体系分析', None, None)
add_or_update_schedule('133', '2026-10-17', '陈晋蓉', '资本财务思维', None, None)
add_or_update_schedule('133', '2026-11-21', '孔维勤', '王阳明心学——知行合一', None, None)
add_or_update_schedule('133', '2026-12-26', '宗英涛', '稻盛和夫的经营哲学', '杨波', '领导力赋能组织活力')

# Data for 135
add_or_update_schedule('135', '2025-10-25', '院长', '院长课', '张庆安', '当前国际格局态势与中国宏观经济走向')
add_or_update_schedule('135', '2025-12-13', '刘春华', 'AI时代下的新营销九步法', None, None)
add_or_update_schedule('135', '2026-03-07', '霍振先', '总裁财务思维与经营决策', None, None)
add_or_update_schedule('135', '2026-04-11', '张华光', 'AI时代的商业模式创新系统与趋势', None, None)
add_or_update_schedule('135', '2026-05-30', '李继延', '创新思维与战略管理', None, None)
add_or_update_schedule('135', '2026-07-04', '张华光', 'AI时代的商业模式创新系统与趋势', None, None)
add_or_update_schedule('135', '2026-09-19', '宗英涛', '稻盛和夫的经营哲学', '董俊豪', '企业 AI Deepseek 战略课')
add_or_update_schedule('135', '2026-10-24', '罗毅', '股权设计与股权激励', None, None)

# Data for 136
add_or_update_schedule('136', '2025-11-22', '刘春华', 'AI时代下的新营销九步法', None, None)
add_or_update_schedule('136', '2025-12-27', '院长', '院长课', '张庆安', '宏观经济与政策分析')
add_or_update_schedule('136', '2026-03-14', '刘钰', '股权设计和资本路径', '韩铁林', '企业战略规划与制定')
add_or_update_schedule('136', '2026-05-16', '蔡毅臣', '新形势下的战略人力资源管理', None, None)
add_or_update_schedule('136', '2026-07-10', '王京刚', '企业战略与数字化转型', None, None)
add_or_update_schedule('136', '2026-09-12', '霍振先', '总裁决策者财税思维', None, None)
add_or_update_schedule('136', '2026-11-14', '董俊豪', '企业 AI Deepseek 战略课', '梁培霖', '战略洞察力提升实战')
add_or_update_schedule('136', '2027-01-15', '尚旭', '易经智慧与经营决策', '沈佳', '企业家卓越领导能力构建')
add_or_update_schedule('136', '2027-03-12', '谢华', '存量市场数字化新商业模式', None, None)

# Data for 138
add_or_update_schedule('138', '2025-11-29', '院长', '院长课', '张庆安', '最新国际形势与中国宏观经济')
add_or_update_schedule('138', '2025-12-27', '刘春华', 'AI时代下的新营销九步法', None, None)
add_or_update_schedule('138', '2026-03-07', '韩迎娣', '《科技创新的思维与认知》', '刘钰', '《赢在顶层设计—企业持续成功的底层逻辑》')
add_or_update_schedule('138', '2026-04-25', '杨波', '《领导力赋能组织活力》', '张晓丽', '资本趋势破解：经济周期研判与思维重构')
add_or_update_schedule('138', '2026-05-30', '蔡毅臣', '新形势下的战略人力资源管理', None, None)
add_or_update_schedule('138', '2026-07-18', '吴子敬', '股权设计、股权合伙与激励', None, None)
add_or_update_schedule('138', '2026-09-12', '韩铁林', '企业战略规划与制定', '董俊豪', '企业AI Deepseek战略课')
add_or_update_schedule('138', '2026-11-21', '宗英涛', '稻盛和夫的经营哲学', '尚旭', '企业布局的财富智慧')

conn.commit()
conn.close()
print("Schedules successfully fixed!")
