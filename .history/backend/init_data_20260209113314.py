"""
数据初始化脚本 - 北清商学院排课系统
运行此脚本将创建数据库表并插入初始数据
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from models import db, TrainingType, Topic, Homeroom, Teacher, Course, TeacherCourseCombo, Class, ClassSchedule
from routes.schedule import is_holiday, find_next_available_saturday

# ... (inside init_mock_classes loop)

            # 为该班级生成8个课程安排
            current_date = start_date
            # 确保从周六开始
            current_date = find_next_available_saturday(current_date)
            
            for i, topic in enumerate(topics):
                # 跳过节假日
                check_attempts = 0
                while check_attempts < 5:  # 防止无限循环
                    if not is_holiday(current_date):
                        break
                    # 如果是节假日，顺延一周
                    current_date = current_date + timedelta(days=7)
                    check_attempts += 1

                # 确定该课程状态
                # ... (rest of logic) ...
                
                # 下一节课间隔4周
                current_date_next = current_date + timedelta(weeks=4)
                # 简单处理：确保下次也是周六（通常加4周还是周六，除非遇到跨年等特殊调休，这里暂不深究）
                current_date = find_next_available_saturday(current_date_next)

def init_database():
    """初始化数据库"""
    app = create_app()
    
    with app.app_context():
        # 创建所有表
        db.create_all()
        print("✓ 数据库表创建成功")
        
        # 检查是否已有数据
        if TrainingType.query.first():
            print("! 数据库已有数据，跳过初始化")
            print("  如需重新初始化，请先清空数据库")
            return
        
        # 插入培训班类型和课题
        init_training_types_and_topics()
        
        # 插入班主任
        init_homerooms()
        
        # 插入讲师
        init_teachers()
        
        # 插入课程
        init_courses()
        
        # 插入教-课组合
        init_combos()
        
        # 插入模拟历史班级和课表数据
        init_mock_classes()
        
        print("\n✓ 所有数据初始化完成！")
        print("  - 7 种培训班类型")
        print("  - 56 个课题")
        print("  - 10 个班主任")
        print("  - 20 个授课讲师")
        print("  - 课程和教-课组合")
        print("  - 模拟历史班级和课表数据")


def init_training_types_and_topics():
    """初始化培训班类型和课题"""
    
    training_data = [
        {
            "name": "领袖增长本科班",
            "description": "夯实领袖基础，搭建系统认知",
            "topics": [
                {"seq": 1, "name": "开班仪式与宏观经济形势分析", "fixed": True},
                {"seq": 2, "name": "战略思维与商业模式创新", "fixed": False},
                {"seq": 3, "name": "组织管理与团队领导力", "fixed": False},
                {"seq": 4, "name": "财务管理与资本运作基础", "fixed": False},
                {"seq": 5, "name": "市场营销与品牌建设", "fixed": False},
                {"seq": 6, "name": "数字化转型与科技创新", "fixed": False},
                {"seq": 7, "name": "企业法务与风险管理", "fixed": False},
                {"seq": 8, "name": "结课典礼与领袖成长路演", "fixed": True},
            ]
        },
        {
            "name": "领袖增长硕士班",
            "description": "深化领袖能力，赋能战略突破",
            "topics": [
                {"seq": 1, "name": "开班仪式与宏观经济趋势研判", "fixed": True},
                {"seq": 2, "name": "战略规划与竞争优势构建", "fixed": False},
                {"seq": 3, "name": "组织变革与人才梯队建设", "fixed": False},
                {"seq": 4, "name": "资本市场与投融资实务", "fixed": False},
                {"seq": 5, "name": "全球化视野与跨国经营", "fixed": False},
                {"seq": 6, "name": "产业生态与平台战略", "fixed": False},
                {"seq": 7, "name": "企业传承与基业长青", "fixed": False},
                {"seq": 8, "name": "结课典礼与战略突破路演", "fixed": True},
            ]
        },
        {
            "name": "国学班",
            "description": "以国学智慧，润领袖心智",
            "topics": [
                {"seq": 1, "name": "开班仪式与易经智慧概论", "fixed": True},
                {"seq": 2, "name": "儒家思想与修身齐家", "fixed": False},
                {"seq": 3, "name": "道家哲学与无为而治", "fixed": False},
                {"seq": 4, "name": "兵法谋略与竞争智慧", "fixed": False},
                {"seq": 5, "name": "禅宗心法与企业家心性修炼", "fixed": False},
                {"seq": 6, "name": "史学经典与历史镜鉴", "fixed": False},
                {"seq": 7, "name": "中医养生与身心平衡", "fixed": False},
                {"seq": 8, "name": "结课典礼与国学智慧分享", "fixed": True},
            ]
        },
        {
            "name": "数字化转型总裁班",
            "description": "聚焦数字化，破解转型难题",
            "topics": [
                {"seq": 1, "name": "开班仪式与数字经济宏观解读", "fixed": True},
                {"seq": 2, "name": "数字化战略规划与转型路径", "fixed": False},
                {"seq": 3, "name": "数据中台与智能决策", "fixed": False},
                {"seq": 4, "name": "人工智能与业务场景融合", "fixed": False},
                {"seq": 5, "name": "数字营销与客户体验重塑", "fixed": False},
                {"seq": 6, "name": "组织敏捷与数字化人才培养", "fixed": False},
                {"seq": 7, "name": "网络安全与数据合规", "fixed": False},
                {"seq": 8, "name": "结课典礼与数字化转型成果展示", "fixed": True},
            ]
        },
        {
            "name": "EMBA创新实验班",
            "description": "融合EMBA核心，聚焦创新突破",
            "topics": [
                {"seq": 1, "name": "开班仪式与创新经济学导论", "fixed": True},
                {"seq": 2, "name": "创新思维与设计思维方法论", "fixed": False},
                {"seq": 3, "name": "商业模式创新与颠覆式创新", "fixed": False},
                {"seq": 4, "name": "创新组织与创业生态构建", "fixed": False},
                {"seq": 5, "name": "技术前沿与产业创新趋势", "fixed": False},
                {"seq": 6, "name": "创新资本与风险投资策略", "fixed": False},
                {"seq": 7, "name": "创新实践与项目孵化", "fixed": False},
                {"seq": 8, "name": "结课典礼与创新项目路演", "fixed": True},
            ]
        },
        {
            "name": "女性领导力研修营",
            "description": "赋能女性领袖，彰显女性力量",
            "topics": [
                {"seq": 1, "name": "开班仪式与女性领导力觉醒", "fixed": True},
                {"seq": 2, "name": "自我认知与个人品牌塑造", "fixed": False},
                {"seq": 3, "name": "沟通艺术与影响力提升", "fixed": False},
                {"seq": 4, "name": "职业发展与事业家庭平衡", "fixed": False},
                {"seq": 5, "name": "财务独立与财富管理", "fixed": False},
                {"seq": 6, "name": "团队建设与赋能型领导", "fixed": False},
                {"seq": 7, "name": "健康管理与优雅生活美学", "fixed": False},
                {"seq": 8, "name": "结课典礼与女性力量分享", "fixed": True},
            ]
        },
        {
            "name": "医疗产业实战班",
            "description": "立足医疗行业，聚焦实战落地",
            "topics": [
                {"seq": 1, "name": "开班仪式与医疗产业宏观政策解读", "fixed": True},
                {"seq": 2, "name": "医疗机构运营与精细化管理", "fixed": False},
                {"seq": 3, "name": "医药研发与创新药物开发", "fixed": False},
                {"seq": 4, "name": "医疗器械与智能医疗设备", "fixed": False},
                {"seq": 5, "name": "医疗投融资与并购重组", "fixed": False},
                {"seq": 6, "name": "互联网医疗与数字健康", "fixed": False},
                {"seq": 7, "name": "医疗合规与医保政策应对", "fixed": False},
                {"seq": 8, "name": "结课典礼与医疗产业创新路演", "fixed": True},
            ]
        }
    ]
    
    for tt_data in training_data:
        tt = TrainingType(
            name=tt_data["name"],
            description=tt_data["description"]
        )
        db.session.add(tt)
        db.session.flush()  # 获取ID
        
        for topic_data in tt_data["topics"]:
            topic = Topic(
                training_type_id=tt.id,
                sequence=topic_data["seq"],
                name=topic_data["name"],
                is_fixed=topic_data["fixed"]
            )
            db.session.add(topic)
    
    db.session.commit()
    print("✓ 培训班类型和课题初始化完成")


def init_homerooms():
    """初始化班主任（10人）"""
    homerooms = [
        {"name": "张晓明", "phone": "13800001001", "email": "zhangxm@beiqing.edu"},
        {"name": "李婷婷", "phone": "13800001002", "email": "litt@beiqing.edu"},
        {"name": "王建国", "phone": "13800001003", "email": "wangjg@beiqing.edu"},
        {"name": "刘芳芳", "phone": "13800001004", "email": "liuff@beiqing.edu"},
        {"name": "陈志强", "phone": "13800001005", "email": "chenzq@beiqing.edu"},
        {"name": "赵雪梅", "phone": "13800001006", "email": "zhaoxm@beiqing.edu"},
        {"name": "孙伟东", "phone": "13800001007", "email": "sunwd@beiqing.edu"},
        {"name": "周丽华", "phone": "13800001008", "email": "zhoulh@beiqing.edu"},
        {"name": "吴俊杰", "phone": "13800001009", "email": "wujj@beiqing.edu"},
        {"name": "郑美玲", "phone": "13800001010", "email": "zhengml@beiqing.edu"},
    ]
    
    for h_data in homerooms:
        h = Homeroom(**h_data)
        db.session.add(h)
    
    db.session.commit()
    print("✓ 班主任初始化完成（10人）")


def init_teachers():
    """初始化授课讲师（20人）"""
    teachers = [
        {"name": "王芳教授", "title": "教授", "expertise": "战略管理、组织行为学", "phone": "13900001001"},
        {"name": "刘杰博士", "title": "副教授", "expertise": "财务管理、资本运作", "phone": "13900001002"},
        {"name": "陈明华", "title": "教授", "expertise": "市场营销、品牌管理", "phone": "13900001003"},
        {"name": "张国强", "title": "副教授", "expertise": "数字化转型、IT战略", "phone": "13900001004"},
        {"name": "李文龙", "title": "教授", "expertise": "宏观经济学、政策分析", "phone": "13900001005"},
        {"name": "赵静怡", "title": "副教授", "expertise": "人力资源、组织发展", "phone": "13900001006"},
        {"name": "孙建平", "title": "教授", "expertise": "企业法务、合规管理", "phone": "13900001007"},
        {"name": "周海涛", "title": "教授", "expertise": "创新管理、创业学", "phone": "13900001008"},
        {"name": "吴晓燕", "title": "副教授", "expertise": "领导力、团队建设", "phone": "13900001009"},
        {"name": "郑大伟", "title": "教授", "expertise": "国学智慧、易经哲学", "phone": "13900001010"},
        {"name": "钱学森", "title": "教授", "expertise": "人工智能、数据科学", "phone": "13900001011"},
        {"name": "林志豪", "title": "副教授", "expertise": "投融资、私募股权", "phone": "13900001012"},
        {"name": "黄立", "title": "教授", "expertise": "女性领导力、职业发展", "phone": "13900001013"},
        {"name": "杨光明", "title": "副教授", "expertise": "医疗管理、医院运营", "phone": "13900001014"},
        {"name": "徐文静", "title": "教授", "expertise": "网络安全、数据合规", "phone": "13900001015"},
        {"name": "马云飞", "title": "副教授", "expertise": "平台经济、商业模式", "phone": "13900001016"},
        {"name": "何明月", "title": "教授", "expertise": "中医养生、健康管理", "phone": "13900001017"},
        {"name": "罗建华", "title": "副教授", "expertise": "医药研发、新药开发", "phone": "13900001018"},
        {"name": "谢天宇", "title": "教授", "expertise": "跨国经营、国际商务", "phone": "13900001019"},
        {"name": "唐晓峰", "title": "副教授", "expertise": "风险投资、创业孵化", "phone": "13900001020"},
    ]
    
    for t_data in teachers:
        t = Teacher(**t_data)
        db.session.add(t)
    
    db.session.commit()
    print("✓ 授课讲师初始化完成（20人）")


def init_courses():
    """初始化课程"""
    courses = [
        # 通用课程
        {"name": "宏观经济形势与政策解读", "description": "分析当前经济形势，解读政策走向", "duration_days": 2},
        {"name": "战略思维与决策方法", "description": "培养战略性思维，掌握科学决策方法", "duration_days": 2},
        {"name": "组织管理与领导力提升", "description": "组织管理理论与实践，领导力培养", "duration_days": 2},
        {"name": "财务管理与资本运营", "description": "企业财务管理，资本运作策略", "duration_days": 2},
        {"name": "市场营销与品牌战略", "description": "市场营销理论与品牌建设实践", "duration_days": 2},
        {"name": "数字化转型战略", "description": "企业数字化转型路径与实施策略", "duration_days": 2},
        {"name": "企业法务与风险防控", "description": "企业法律风险识别与防范", "duration_days": 2},
        
        # 国学相关
        {"name": "易经智慧与管理应用", "description": "易经哲学在企业管理中的应用", "duration_days": 2},
        {"name": "儒家管理哲学", "description": "儒家思想与现代管理融合", "duration_days": 2},
        {"name": "道家智慧与领导艺术", "description": "道家无为而治的管理智慧", "duration_days": 2},
        {"name": "孙子兵法与竞争策略", "description": "兵法谋略在商战中的应用", "duration_days": 2},
        {"name": "禅修与企业家心性", "description": "禅宗心法与内心修炼", "duration_days": 2},
        {"name": "中医养生与健康管理", "description": "传统中医养生智慧", "duration_days": 2},
        
        # 数字化相关
        {"name": "数据中台建设与应用", "description": "企业数据中台架构与实施", "duration_days": 2},
        {"name": "人工智能商业应用", "description": "AI技术在企业中的落地应用", "duration_days": 2},
        {"name": "数字营销与用户增长", "description": "数字时代的营销策略", "duration_days": 2},
        {"name": "网络安全与数据保护", "description": "企业网络安全与合规", "duration_days": 2},
        
        # 创新相关
        {"name": "设计思维与创新方法", "description": "创新思维方法论与实践", "duration_days": 2},
        {"name": "商业模式创新", "description": "商业模式设计与创新", "duration_days": 2},
        {"name": "创业生态与孵化", "description": "创业生态构建与项目孵化", "duration_days": 2},
        {"name": "风险投资与融资策略", "description": "VC/PE投资与企业融资", "duration_days": 2},
        
        # 医疗相关
        {"name": "医疗产业政策解读", "description": "医疗行业政策分析与趋势", "duration_days": 2},
        {"name": "医院运营管理", "description": "医疗机构精细化运营", "duration_days": 2},
        {"name": "医药研发与创新", "description": "新药研发流程与创新", "duration_days": 2},
        {"name": "智能医疗设备", "description": "医疗器械与智能医疗", "duration_days": 2},
        {"name": "互联网医疗与数字健康", "description": "互联网+医疗的创新实践", "duration_days": 2},
        
        # 女性领导力相关
        {"name": "个人品牌与影响力", "description": "个人品牌塑造与影响力提升", "duration_days": 2},
        {"name": "高效沟通与谈判技巧", "description": "沟通艺术与商务谈判", "duration_days": 2},
        {"name": "财富管理与投资规划", "description": "个人财富管理策略", "duration_days": 2},
        {"name": "工作生活平衡艺术", "description": "职业发展与家庭平衡", "duration_days": 2},
    ]
    
    for c_data in courses:
        c = Course(**c_data)
        db.session.add(c)
    
    db.session.commit()
    print("✓ 课程初始化完成（30门）")


def init_combos():
    """初始化教-课组合（为每个课题配置2-3个可选组合）"""
    # 获取所有课题
    topics = Topic.query.all()
    teachers = Teacher.query.all()
    courses = Course.query.all()
    
    # 简化配置：根据课题关键词匹配合适的讲师和课程
    keyword_teacher_map = {
        "宏观经济": [4],  # 李文龙
        "战略": [0, 7],   # 王芳, 周海涛
        "组织": [5],      # 赵静怡
        "财务": [1],      # 刘杰
        "资本": [1, 11],  # 刘杰, 林志豪
        "营销": [2],      # 陈明华
        "数字化": [3, 10], # 张国强, 钱学森
        "法务": [6],      # 孙建平
        "领导力": [8],    # 吴晓燕
        "国学": [9],      # 郑大伟
        "易经": [9],      # 郑大伟
        "儒家": [9],      # 郑大伟
        "道家": [9],      # 郑大伟
        "兵法": [9],      # 郑大伟
        "禅": [9],        # 郑大伟
        "中医": [16],     # 何明月
        "养生": [16],     # 何明月
        "人工智能": [10], # 钱学森
        "数据": [3, 10],  # 张国强, 钱学森
        "网络安全": [14], # 徐文静
        "创新": [7, 19],  # 周海涛, 唐晓峰
        "创业": [7, 19],  # 周海涛, 唐晓峰
        "风险投资": [19], # 唐晓峰
        "女性": [12],     # 黄立
        "医疗": [13, 17], # 杨光明, 罗建华
        "医药": [17],     # 罗建华
        "互联网": [3],    # 张国强
        "跨国": [18],     # 谢天宇
        "全球化": [18],   # 谢天宇
        "平台": [15],     # 马云飞
        "商业模式": [15], # 马云飞
        "品牌": [2],      # 陈明华
        "沟通": [8],      # 吴晓燕
        "团队": [8],      # 吴晓燕
        "财富": [1],      # 刘杰
        "传承": [0],      # 王芳
        "人才": [5],      # 赵静怡
    }
    
    combo_count = 0
    for topic in topics:
        # 找到匹配的讲师索引
        matched_teachers = []
        for keyword, teacher_indices in keyword_teacher_map.items():
            if keyword in topic.name:
                matched_teachers.extend(teacher_indices)
        
        # 去重并限制数量
        matched_teachers = list(set(matched_teachers))[:3]
        
        # 如果没有匹配，使用默认讲师
        if not matched_teachers:
            matched_teachers = [0, 1]  # 王芳, 刘杰
        
        # 为每个匹配的讲师创建教-课组合
        for i, teacher_idx in enumerate(matched_teachers):
            if teacher_idx < len(teachers):
                # 选择相关课程（简单使用序号）
                course_idx = min(topic.id % len(courses), len(courses) - 1)
                
                combo = TeacherCourseCombo(
                    topic_id=topic.id,
                    teacher_id=teachers[teacher_idx].id,
                    course_id=courses[course_idx].id,
                    priority=len(matched_teachers) - i  # 第一个优先级最高
                )
                db.session.add(combo)
                combo_count += 1
    
    db.session.commit()
    print(f"✓ 教-课组合初始化完成（{combo_count}个）")


def init_mock_classes():
    """初始化模拟历史班级和课表数据"""
    
    # 获取培训班类型
    training_types = TrainingType.query.all()
    homerooms = Homeroom.query.all()
    
    if not training_types or not homerooms:
        print("! 缺少培训班类型或班主任数据，跳过模拟班级生成")
        return
    
    # 模拟班级配置：每种培训班创建2-3个班级
    mock_classes_config = [
        # 领袖增长本科班
        {"tt_idx": 0, "classes": [
            {"name": "领袖增长本科班1期", "start": "2025-09-06", "homeroom_idx": 0, "completed": 8},
            {"name": "领袖增长本科班2期", "start": "2025-11-08", "homeroom_idx": 1, "completed": 5},
            {"name": "领袖增长本科班3期", "start": "2026-02-14", "homeroom_idx": 2, "completed": 0},
        ]},
        # 领袖增长硕士班
        {"tt_idx": 1, "classes": [
            {"name": "领袖增长硕士班1期", "start": "2025-10-11", "homeroom_idx": 3, "completed": 6},
            {"name": "领袖增长硕士班2期", "start": "2026-01-10", "homeroom_idx": 4, "completed": 2},
        ]},
        # 国学班
        {"tt_idx": 2, "classes": [
            {"name": "国学班1期", "start": "2025-08-16", "homeroom_idx": 5, "completed": 8},
            {"name": "国学班2期", "start": "2025-12-06", "homeroom_idx": 6, "completed": 3},
        ]},
        # 数字化转型总裁班
        {"tt_idx": 3, "classes": [
            {"name": "数字化转型总裁班1期", "start": "2025-09-13", "homeroom_idx": 7, "completed": 7},
            {"name": "数字化转型总裁班2期", "start": "2026-01-17", "homeroom_idx": 8, "completed": 1},
        ]},
        # EMBA创新实验班
        {"tt_idx": 4, "classes": [
            {"name": "EMBA创新实验班1期", "start": "2025-07-12", "homeroom_idx": 9, "completed": 8},
            {"name": "EMBA创新实验班2期", "start": "2025-11-15", "homeroom_idx": 0, "completed": 4},
        ]},
        # 女性领导力研修营
        {"tt_idx": 5, "classes": [
            {"name": "女性领导力研修营1期", "start": "2025-10-18", "homeroom_idx": 1, "completed": 5},
            {"name": "女性领导力研修营2期", "start": "2026-02-21", "homeroom_idx": 2, "completed": 0},
        ]},
        # 医疗产业实战班
        {"tt_idx": 6, "classes": [
            {"name": "医疗产业实战班1期", "start": "2025-08-23", "homeroom_idx": 3, "completed": 8},
            {"name": "医疗产业实战班2期", "start": "2025-12-13", "homeroom_idx": 4, "completed": 2},
            {"name": "医疗产业实战班3期", "start": "2026-03-07", "homeroom_idx": 5, "completed": 0},
        ]},
    ]
    
    class_count = 0
    schedule_count = 0
    
    for config in mock_classes_config:
        tt = training_types[config["tt_idx"]]
        topics = Topic.query.filter_by(training_type_id=tt.id).order_by(Topic.sequence).all()
        
        for class_cfg in config["classes"]:
            # 创建班级
            start_date = date.fromisoformat(class_cfg["start"])
            completed_count = class_cfg["completed"]
            
            # 确定状态
            if completed_count == 8:
                status = "completed"
            elif completed_count > 0:
                status = "active"
            else:
                status = "planning"
            
            new_class = Class(
                training_type_id=tt.id,
                name=class_cfg["name"],
                homeroom_id=homerooms[class_cfg["homeroom_idx"]].id,
                start_date=start_date,
                status=status
            )
            db.session.add(new_class)
            db.session.flush()
            class_count += 1
            
            # 为该班级生成8个课程安排
            current_date = start_date
            # 确保从周六开始
            days_until_saturday = (5 - current_date.weekday()) % 7
            if days_until_saturday > 0:
                current_date = current_date + timedelta(days=days_until_saturday)
            
            for i, topic in enumerate(topics):
                # 确定该课程状态
                if i < completed_count:
                    sched_status = "completed"
                elif i == completed_count and status == "active":
                    sched_status = "scheduled"
                else:
                    sched_status = "scheduled"
                
                # 获取该课题的教-课组合
                combo = TeacherCourseCombo.query.filter_by(topic_id=topic.id)\
                                                .order_by(TeacherCourseCombo.priority.desc()).first()
                
                schedule = ClassSchedule(
                    class_id=new_class.id,
                    topic_id=topic.id,
                    combo_id=combo.id if combo else None,
                    scheduled_date=current_date,
                    week_number=i + 1,
                    status=sched_status
                )
                db.session.add(schedule)
                schedule_count += 1
                
                # 下一节课间隔4周
                current_date = current_date + timedelta(weeks=4)
    
    db.session.commit()
    print(f"✓ 模拟班级初始化完成（{class_count}个班级，{schedule_count}个课表记录）")


if __name__ == '__main__':
    print("=" * 50)
    print("北清商学院排课系统 - 数据初始化")
    print("=" * 50)
    print(f"数据库: MySQL @ 10.156.195.35:3306/bqsxy")
    print("=" * 50)
    
    init_database()
    
    print("\n" + "=" * 50)
    print("数据初始化完成！")
    print("现在可以运行 python app.py 启动后端服务")
    print("=" * 50)
