"""
EMBA 数据导入脚本
根据 Excel 数据创建：讲师、课程、组合、班主任、班级、排课记录
"""
import sys, os, io, json, re
from datetime import date, timedelta
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from app import create_app
from models import db, Project, Topic, Teacher, Course, TeacherCourseCombo, Homeroom, Class, ClassSchedule, City

app = create_app()

# ========== 配置数据 ==========

# 9个课题 + 讲师归属
TOPICS = {
    1: {'name': '宏观经济与企业战略创新', 'teachers': {
        '张庆安': ['宏观经济与政策分析'],
        '史璐': ['战略发展与市场经济'],
        '李其': ['宏观经济与政策分析'],
        '岳庆平': ['中国历代王朝的治乱兴衰', '宏观经济与政策分析'],
    }},
    2: {'name': '企业数字化变革与数智创新', 'teachers': {
        '张华光': ['AI商业模式与数智化增长'],
        '谢华': ['存量市场数字化新商业模式'],
        '张涛': ['企业数字化转型'],
        '韩迎娣': ['企业数字化转型'],
        '钟彩民': ['商业模式设计与创新'],
        '郑翔洲': ['数智化商业模式与资本运作'],
        '黄宏': ['商业模式创新与产业升级'],
        '熊郭健': ['产业思维与商业模式创新'],
    }},
    3: {'name': '人工智能与商业应用', 'teachers': {
        '刘春华': ['AI时代下的新营销九步法'],
        '董俊豪': ['AI驱动增长：企业家的战略蓝图与实战路径', '企业 AI Deepseek 战略课'],
        '张凯寓': ['企业AI战略课'],
        '李江涛': ['AI战略与企业转型'],
        '刘勇': ['AI全网矩阵营销'],
    }},
    4: {'name': '品牌营销与数智化营销', 'teachers': {
        '万力': ['专精特新的第一品牌'],
        '阙登峰': ['"投入不变 业绩倍增"的全过程管理'],
        '曲融': ['资本趋势与投资分析'],
        '张晓丽': ['财富管理与资产配置'],
        '龙平敬': ['投资分析与决策'],
    }},
    5: {'name': '财务管理与风险管理优化', 'teachers': {
        '霍振先': ['总经理的财务管理'],
        '齐昊': ['金税四期下:企业高爆雷涉税风险及防范'],
        '陈晋蓉': ['财务管理与风险控制'],
        '於丙才': ['金税四期下:企业高爆雷涉税风险及防范'],
        '刘钰': ['股权设计和资本路径'],
        '吴子敬': ['企业投融资实务与案例教学'],
        '吴梓境': ['企业资本运营与投融资'],
        '常亮': ['股权激励与合伙人制度'],
        '罗毅': ['财务分析与决策'],
        '杨军': ['税务筹划与风险管理'],
        '王晓耕': ['公司治理与公司法'],
    }},
    6: {'name': '人力资源管理与组织效能提升', 'teachers': {
        '蔡毅臣': ['管理者的心智修炼与管理赋能'],
        '杨台轩': ['高效团队建设与管理'],
        '严小云': ['卓越薪酬绩效管理'],
    }},
    7: {'name': '销售管理与客户关系经营', 'teachers': {
        '李继延': ['战略规划与执行落地'],
        '韩铁林': ['战略管理落地执行'],
        '郝军龙': ['企业战略规划实务'],
        '梁培霖': ['战略销售与客户管理'],
        '王京刚': ['企业战略与运营管理'],
    }},
    8: {'name': '领导力与团队建设', 'teachers': {
        '杨波': ['领导力赋能组织活力'],
        '王正': ['企业家卓越领导能力构建'],
        '沈佳': ['企业家卓越领导能力构建'],
        '程国辉': ['领导力与组织建设'],
        '张益铭': ['家庭幸福与企业效益'],
    }},
    9: {'name': '国学智慧与人文素养', 'teachers': {
        '孔海钦': ['国学的新思维'],
        '孔维勤': ['王阳明心学——知行合一'],
        '宗英涛': ['稻盛和夫的经营哲学'],
        '尚旭': ['易经智慧与经营决策', '企业布局的财富智慧'],
        '易正': ['中国古法姓名学'],
    }},
}

# 20个班级配置
CLASSES = [
    {'name': '北清EMBA122期', 'homeroom': '郭一菲', 'city': '北京'},
    {'name': '北清EMBA123期', 'homeroom': '宋艳英', 'city': '北京'},
    {'name': '北清EMBA125期', 'homeroom': '沈欢欢', 'city': '北京'},
    {'name': '北清EMBA126期', 'homeroom': '吕东楟', 'city': '北京'},
    {'name': '北清EMBA127期', 'homeroom': '赵邤颐', 'city': '北京'},
    {'name': '北清EMBA128期', 'homeroom': '郭一菲', 'city': '北京'},
    {'name': '北清EMBA129期', 'homeroom': '赵彩霞', 'city': '北京'},
    {'name': '北清EMBA130期', 'homeroom': '张星', 'city': '北京'},
    {'name': '北清EMBA131期', 'homeroom': '冯子玲', 'city': '北京'},
    {'name': '北清EMBA132期', 'homeroom': '李彩云', 'city': '北京'},
    {'name': '北清EMBA133期——宁夏分院', 'homeroom': None, 'city': '宁夏'},
    {'name': '北清EMBA135期', 'homeroom': '赵彩霞', 'city': '北京'},
    {'name': '北清EMBA136期——太原崇德班', 'homeroom': None, 'city': '太原'},
    {'name': '北清EMBA138期', 'homeroom': '刘宇', 'city': '北京'},
    {'name': '北清EMBA139期', 'homeroom': '王珞瑾', 'city': '北京'},
    {'name': '北清151期', 'homeroom': '伍子琪', 'city': '北京'},
    {'name': '北清152期', 'homeroom': '李艳霞', 'city': '北京'},
    {'name': '北清153期', 'homeroom': None, 'city': '北京'},
    {'name': '北清155期', 'homeroom': None, 'city': '北京'},
    {'name': '北清156期——深圳分院', 'homeroom': None, 'city': '深圳'},  # Excel中叫 北清商学院深圳分院M26156班
]

# 构建讲师→课题映射（用于从Excel teacher name找到topic）
TEACHER_TOPIC_MAP = {}
for tid, info in TOPICS.items():
    for tname in info['teachers']:
        TEACHER_TOPIC_MAP[tname] = tid


def parse_excel_date(raw, working_year, prev_month=None):
    """解析Excel中的各种日期格式
    working_year: 当前推算年份（会因跨年而递增）
    返回 (date, working_year_out, month)
    """
    if not raw or raw.strip() == '':
        return None, working_year, prev_month
    
    raw = raw.strip().rstrip('日')
    
    # ISO date format "2026-04-12" — xlrd自动转换的日期
    # 关键修复：使用 working_year 覆盖ISO中的年份
    m = re.match(r'(\d{4})-(\d{2})-(\d{2})', raw)
    if m:
        try:
            iso_month, iso_day = int(m.group(2)), int(m.group(3))
            # 跨年推断
            if prev_month and iso_month < prev_month and iso_month <= 3:
                working_year = working_year + 1
            d = date(working_year, iso_month, iso_day)
            return d, working_year, iso_month
        except ValueError:
            pass
    
    # Excel 数字日期 (e.g., "45782.0" = days since 1899-12-30)
    try:
        num = float(raw)
        if num > 40000:
            base = date(1899, 12, 30)
            d = base + timedelta(days=int(num))
            # 用月份做跨年推断
            if prev_month and d.month < prev_month and d.month <= 3:
                working_year = working_year + 1
            try:
                d = date(working_year, d.month, d.day)
            except ValueError:
                pass
            return d, working_year, d.month
    except ValueError:
        pass
    
    # "5月24-25" or "5月24—25" or "5.24-25" or "5月24、25"
    m = re.match(r'(\d+)[月.](\d+)[-—、/](\d+)', raw)
    if m:
        month, day1 = int(m.group(1)), int(m.group(2))
        if prev_month and month < prev_month and month <= 3:
            working_year = working_year + 1
        try:
            d = date(working_year, month, day1)
            return d, working_year, month
        except ValueError:
            return None, working_year, prev_month
    
    # "5月24日" or "5月24" or "5.24"
    m = re.match(r'(\d+)[月.](\d+)', raw)
    if m:
        month, day = int(m.group(1)), int(m.group(2))
        if prev_month and month < prev_month and month <= 3:
            working_year = working_year + 1
        try:
            d = date(working_year, month, day)
            return d, working_year, month
        except ValueError:
            return None, working_year, prev_month
    
    return None, working_year, prev_month


def find_topic_for_teacher(teacher_name):
    """根据讲师名找到对应课题ID"""
    return TEACHER_TOPIC_MAP.get(teacher_name)


def run_import():
    with app.app_context():
        # 确保有 EMBA 项目
        project = Project.query.filter_by(name='EMBA').first()
        if not project:
            project = Project(name='EMBA', description='北清EMBA项目')
            db.session.add(project)
            db.session.flush()
            print(f'✅ 创建项目: EMBA (id={project.id})')
        else:
            print(f'ℹ️ 项目已存在: EMBA (id={project.id})')
        
        # ========== 1. 创建9个课题 ==========
        topic_map = {}  # seq -> Topic obj
        for seq, info in TOPICS.items():
            topic = Topic.query.filter_by(project_id=project.id, sequence=seq).first()
            if not topic:
                topic = Topic(
                    project_id=project.id,
                    sequence=seq,
                    name=info['name']
                )
                db.session.add(topic)
                db.session.flush()
                print(f'  创建课题 {seq}: {info["name"]} (id={topic.id})')
            else:
                print(f'  课题已存在 {seq}: {topic.name}')
            topic_map[seq] = topic
        
        # ========== 2. 创建讲师 + 课程 + 组合 ==========
        teacher_obj_map = {}  # teacher_name -> Teacher obj
        combo_map = {}  # (teacher_name, course_name) -> combo obj
        
        for seq, info in TOPICS.items():
            topic = topic_map[seq]
            for teacher_name, course_names in info['teachers'].items():
                # 创建讲师
                teacher = Teacher.query.filter_by(name=teacher_name).first()
                if not teacher:
                    teacher = Teacher(
                        name=teacher_name,
                        topic_id=topic.id,
                        courses=json.dumps(course_names, ensure_ascii=False)
                    )
                    db.session.add(teacher)
                    db.session.flush()
                teacher_obj_map[teacher_name] = teacher
                
                # 为每个课程名创建 Course + Combo
                for cname in course_names:
                    course = Course.query.filter_by(name=cname, topic_id=topic.id).first()
                    if not course:
                        course = Course(name=cname, topic_id=topic.id)
                        db.session.add(course)
                        db.session.flush()
                    
                    combo = TeacherCourseCombo.query.filter_by(
                        teacher_id=teacher.id, course_id=course.id, topic_id=topic.id
                    ).first()
                    if not combo:
                        combo = TeacherCourseCombo(
                            teacher_id=teacher.id,
                            course_id=course.id,
                            topic_id=topic.id,
                            priority=0
                        )
                        db.session.add(combo)
                        db.session.flush()
                    combo_map[(teacher_name, cname)] = combo
        
        print(f'✅ 创建了 {len(teacher_obj_map)} 个讲师, {len(combo_map)} 个组合')
        
        # 创建院长讲师（不归属课题）
        dean_teacher = Teacher.query.filter_by(name='院长').first()
        if not dean_teacher:
            dean_teacher = Teacher(name='院长', topic_id=None, courses='["院长课"]')
            db.session.add(dean_teacher)
            db.session.flush()
        dean_course = Course.query.filter_by(name='院长课').first()
        if not dean_course:
            dean_course = Course(name='院长课', topic_id=topic_map[1].id)  # 归属课题①
            db.session.add(dean_course)
            db.session.flush()
        # 院长 combo 归属课题①（开学典礼用）
        dean_combo = TeacherCourseCombo.query.filter_by(
            teacher_id=dean_teacher.id, course_id=dean_course.id
        ).first()
        if not dean_combo:
            dean_combo = TeacherCourseCombo(
                teacher_id=dean_teacher.id,
                course_id=dean_course.id,
                topic_id=topic_map[1].id,
                priority=0
            )
            db.session.add(dean_combo)
            db.session.flush()
        print(f'✅ 院长讲师 (id={dean_teacher.id})')
        
        # ========== 3. 创建班主任 ==========
        homeroom_map = {}  # name -> Homeroom obj
        all_homeroom_names = set(c['homeroom'] for c in CLASSES if c['homeroom'])
        for hrm_name in all_homeroom_names:
            hrm = Homeroom.query.filter_by(name=hrm_name).first()
            if not hrm:
                hrm = Homeroom(name=hrm_name)
                db.session.add(hrm)
                db.session.flush()
            homeroom_map[hrm_name] = hrm
        print(f'✅ 创建了 {len(homeroom_map)} 个班主任')
        
        # ========== 4. 获取城市映射 ==========
        city_map = {}  # name -> City obj
        for city in City.query.all():
            city_map[city.name] = city
        
        # ========== 5. 读取 Excel 数据 ==========
        with open(r'C:\tmp\excel_output_full.json', 'r', encoding='utf-8') as f:
            excel_data = json.load(f)
        rows = excel_data['Sheet1']['data']
        print(f'Excel total rows: {len(rows)}')
        
        # 3列布局（北清155/156只用前2列组）
        col_groups = [(0,1,2,3), (5,6,7,8), (10,11,12,13)]
        
        # 找到所有班级标题行
        title_positions = []
        for r_idx, row in enumerate(rows):
            for gi, (c0,c1,c2,c3) in enumerate(col_groups):
                val = row[c0].strip() if c0 < len(row) and len(row) > c0 else ''
                if val and ('EMBA' in val or '北清' in val or '商学院' in val) and '课次' not in val and '2025' not in val and '2026' not in val:
                    title_positions.append((r_idx, gi, val))
        
        print(f'\n找到 {len(title_positions)} 个班级区块')
        
        # 构建期号→配置映射
        class_by_number = {}
        for cc in CLASSES:
            m = re.search(r'(\d{3})', cc['name'])
            if m:
                class_by_number[m.group(1)] = cc
        # 北清155 和 北清156 也能通过 3位数 匹配
        print(f'班级号映射: {list(class_by_number.keys())}')
        
        # ========== 6. 逐班解析并创建 ==========
        today = date.today()
        classes_created = 0
        schedules_created = 0
        
        for tp_idx, (tr, gi, title_raw) in enumerate(title_positions):
            c0, c1, c2, c3 = col_groups[gi]
            
            # 从标题提取期号匹配
            m = re.search(r'(\d{3})', title_raw)
            class_config = None
            if m:
                class_config = class_by_number.get(m.group(1))
            # 兜底：M26156 格式 → 提取最后3位
            if not class_config:
                m2 = re.search(r'M\d{2}(\d{3})', title_raw)
                if m2:
                    class_config = class_by_number.get(m2.group(1))
            
            if not class_config:
                print(f'  ⚠️ 跳过无法匹配的班级: {title_raw}')
                continue
            
            # 检查班级是否已存在
            existing = Class.query.filter_by(name=class_config['name'], project_id=project.id).first()
            if existing:
                print(f'  ⚠️ 班级已存在: {class_config["name"]}')
                continue
            
            # 解析课次数据
            weekends = []
            working_year = 2025  # 初始年份，由 "2025年"/"2026年" 行重置，跨年时递增
            prev_month = None
            current_weekend = None
            
            # 确定搜索范围：到下一个班级标题行或文件结尾
            next_title_row = len(rows)
            for ntp in title_positions:
                if ntp[0] > tr and ntp[1] == gi:  # 同列组的下一个标题
                    next_title_row = ntp[0]
                    break
                if ntp[0] > tr and gi < 2 and ntp[1] > gi:  # 同行更后面列组的标题
                    pass  # 同一行的其他列组不影响
            # 也考虑不同列组的标题行作为边界
            for ntp in title_positions:
                if ntp[0] > tr and ntp[0] < next_title_row:
                    next_title_row = ntp[0]
            
            for r in range(tr+1, next_title_row):
                row = rows[r]
                seq_val = row[c0].strip() if c0 < len(row) else ''
                date_val = row[c1].strip() if c1 < len(row) else ''
                teacher_val = row[c2].strip().strip('《》') if c2 < len(row) else ''
                course_val = row[c3].strip().strip('《》') if c3 < len(row) else ''
                
                # 年份标记行 — 重置 working_year 和 prev_month
                if seq_val in ('2025年', '2026年'):
                    working_year = int(seq_val[:4])
                    prev_month = None
                    continue
                
                # 跳过表头
                if seq_val == '课次':
                    continue
                
                # 新课次行（有课次序号）
                if seq_val and seq_val not in ('', '课次'):
                    try:
                        seq = int(float(seq_val))
                    except (ValueError, TypeError):
                        continue
                    
                    parsed_date, working_year, prev_month = parse_excel_date(date_val, working_year, prev_month)
                    current_weekend = {
                        'seq': seq, 'date': parsed_date,
                        'day1_teacher': '', 'day1_course': '',
                        'day2_teacher': '', 'day2_course': '',
                        'teacher_count': 0  # 已分配的讲师数
                    }
                    weekends.append(current_weekend)
                    
                    # 检查同一行的讲师（课次行本身可能有讲师信息）
                    if teacher_val:
                        # 检查是否是开学/典礼/游学行
                        ceremony_kw = ['开学', '结业典礼', '团建', '院长课']
                        travel_kw = ['游学', '上海游', '北京游', '深圳游', '太原游']
                        if any(kw in teacher_val for kw in ceremony_kw):
                            # 标记仪式旗帜，但不分配为Day1讲师
                            if '开学' in teacher_val:
                                current_weekend['has_opening'] = True
                            if '团建' in teacher_val:
                                current_weekend['has_team_building'] = True
                            if '结业' in teacher_val:
                                current_weekend['has_closing'] = True
                            if '院长' in teacher_val:
                                current_weekend['has_opening'] = True
                                current_weekend['has_team_building'] = True
                        elif any(kw in teacher_val for kw in travel_kw):
                            pass  # 游学行跳过
                        else:
                            # 正常讲师 — 分配为 Day1
                            current_weekend['day1_teacher'] = teacher_val
                            current_weekend['day1_course'] = course_val
                            current_weekend['teacher_count'] = 1
                    continue
                
                # 续行（没有课次序号 — 同一课次的第二行或更多行）
                if not current_weekend:
                    continue
                
                if not teacher_val:
                    continue
                
                # 跳过典礼/游学续行
                ceremony_kw = ['开学', '结业典礼', '团建', '院长课']
                travel_kw = ['游学', '上海游', '北京游', '深圳游', '太原游']
                if any(kw in teacher_val for kw in ceremony_kw) or any(kw in course_val for kw in ceremony_kw):
                    if '开学' in teacher_val or '开学' in course_val:
                        current_weekend['has_opening'] = True
                    if '团建' in teacher_val or '团建' in course_val:
                        current_weekend['has_team_building'] = True
                    if '结业' in teacher_val or '结业' in course_val:
                        current_weekend['has_closing'] = True
                    continue
                if any(kw in teacher_val for kw in travel_kw) or any(kw in course_val for kw in travel_kw):
                    continue
                
                # 讲师名过长跳过（备注等）
                if len(teacher_val) > 15:
                    continue
                
                # 分配 Day1 或 Day2
                if current_weekend['teacher_count'] == 0:
                    current_weekend['day1_teacher'] = teacher_val
                    current_weekend['day1_course'] = course_val
                    current_weekend['teacher_count'] = 1
                elif current_weekend['teacher_count'] == 1:
                    current_weekend['day2_teacher'] = teacher_val
                    current_weekend['day2_course'] = course_val
                    current_weekend['teacher_count'] = 2
                # 第3+个讲师忽略
            
            if not weekends:
                print(f'  ⚠️ 无排课数据: {class_config["name"]}')
                # 仍然创建班级（如 北清153 空数据）
            
            # 创建班级
            city = city_map.get(class_config['city'])
            hrm = homeroom_map.get(class_config['homeroom'])
            first_date = weekends[0]['date'] if weekends and weekends[0]['date'] else None
            
            new_class = Class(
                project_id=project.id,
                name=class_config['name'],
                homeroom_id=hrm.id if hrm else None,
                city_id=city.id if city else None,
                start_date=first_date,
                status='active' if weekends else 'planning'
            )
            db.session.add(new_class)
            db.session.flush()
            classes_created += 1
            
            # 创建排课记录
            used_topics = set()
            for i, w in enumerate(weekends):
                t1_name = w.get('day1_teacher', '')
                t2_name = w.get('day2_teacher', '')
                c1_name = w.get('day1_course', '')
                c2_name = w.get('day2_course', '')
                
                # 找 combo
                combo1 = None
                combo2 = None
                topic_id = None
                
                # Day1 combo
                if t1_name and t1_name in teacher_obj_map:
                    teacher = teacher_obj_map[t1_name]
                    # 找这个老师的 combo
                    for key, cb in combo_map.items():
                        if key[0] == t1_name:
                            combo1 = cb
                            if topic_id is None:
                                topic_id = cb.topic_id
                            break
                elif t1_name:
                    # 未知老师→创建占位
                    placeholder_name = f'[系统生成] {t1_name}'
                    pt = Teacher.query.filter_by(name=placeholder_name).first()
                    if not pt:
                        # 找合适的课题
                        guess_topic = find_topic_for_teacher(t1_name)
                        pt_topic_id = topic_map[guess_topic].id if guess_topic else topic_map[1].id
                        pt = Teacher(name=placeholder_name, topic_id=pt_topic_id,
                                    courses=json.dumps([f'[系统生成] {c1_name or t1_name}课程'], ensure_ascii=False))
                        db.session.add(pt)
                        db.session.flush()
                        pc = Course(name=f'[系统生成] {c1_name or t1_name}课程', topic_id=pt_topic_id)
                        db.session.add(pc)
                        db.session.flush()
                        pcombo = TeacherCourseCombo(teacher_id=pt.id, course_id=pc.id, topic_id=pt_topic_id)
                        db.session.add(pcombo)
                        db.session.flush()
                        combo1 = pcombo
                        if topic_id is None:
                            topic_id = pt_topic_id
                        teacher_obj_map[placeholder_name] = pt
                        combo_map[(placeholder_name, pc.name)] = pcombo
                    else:
                        for key, cb in combo_map.items():
                            if key[0] == placeholder_name:
                                combo1 = cb
                                if topic_id is None:
                                    topic_id = cb.topic_id
                                break
                
                # Day2 combo
                if t2_name and t2_name in teacher_obj_map:
                    teacher = teacher_obj_map[t2_name]
                    for key, cb in combo_map.items():
                        if key[0] == t2_name:
                            combo2 = cb
                            if topic_id is None:
                                topic_id = cb.topic_id
                            break
                elif t2_name:
                    placeholder_name = f'[系统生成] {t2_name}'
                    pt = Teacher.query.filter_by(name=placeholder_name).first()
                    if not pt:
                        guess_topic = find_topic_for_teacher(t2_name)
                        pt_topic_id = topic_map[guess_topic].id if guess_topic else topic_map[1].id
                        pt = Teacher(name=placeholder_name, topic_id=pt_topic_id,
                                    courses=json.dumps([f'[系统生成] {c2_name or t2_name}课程'], ensure_ascii=False))
                        db.session.add(pt)
                        db.session.flush()
                        pc = Course(name=f'[系统生成] {c2_name or t2_name}课程', topic_id=pt_topic_id)
                        db.session.add(pc)
                        db.session.flush()
                        pcombo = TeacherCourseCombo(teacher_id=pt.id, course_id=pc.id, topic_id=pt_topic_id)
                        db.session.add(pcombo)
                        db.session.flush()
                        combo2 = pcombo
                        if topic_id is None:
                            topic_id = pt_topic_id
                        teacher_obj_map[placeholder_name] = pt
                        combo_map[(placeholder_name, pc.name)] = pcombo
                    else:
                        for key, cb in combo_map.items():
                            if key[0] == placeholder_name:
                                combo2 = cb
                                if topic_id is None:
                                    topic_id = cb.topic_id
                                break
                
                # 如果没找到课题，用第一个未使用的课题
                if not topic_id:
                    for seq in range(1, 10):
                        if topic_map[seq].id not in used_topics:
                            topic_id = topic_map[seq].id
                            break
                    if not topic_id:
                        topic_id = topic_map[1].id
                
                used_topics.add(topic_id)
                
                # 确定状态
                sched_date = w.get('date')
                if not sched_date:
                    print(f'    ⚠️ 课次{w["seq"]}: 日期解析失败，跳过')
                    continue
                
                if sched_date < today:
                    status = 'completed'
                else:
                    status = 'scheduled'
                
                schedule = ClassSchedule(
                    class_id=new_class.id,
                    topic_id=topic_id,
                    combo_id=combo1.id if combo1 else None,
                    combo_id_2=combo2.id if combo2 else None,
                    scheduled_date=sched_date,
                    week_number=w['seq'],
                    status=status,
                    has_opening=w.get('has_opening', i == 0),
                    has_team_building=w.get('has_team_building', i == 0),
                    has_closing=w.get('has_closing', i == len(weekends) - 1),
                    notes=None
                )
                db.session.add(schedule)
                schedules_created += 1
            
            print(f'  ✅ {class_config["name"]}: {len(weekends)}课次, 城市={class_config["city"]}')
        
        try:
            db.session.commit()
            print(f'\n========== 导入完成 ==========')
            print(f'班级: {classes_created}')
            print(f'排课: {schedules_created}')
            print(f'讲师: {len(teacher_obj_map)}')
            print(f'组合: {len(combo_map)}')
        except Exception as e:
            db.session.rollback()
            print(f'\n❌ 提交失败: {e}')
            raise


if __name__ == '__main__':
    run_import()
