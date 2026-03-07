"""
数据初始化脚本 - 北清商学院排课系统
运行此脚本将创建数据库表并插入初始数据
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from models import db, Project, Topic, Homeroom, Teacher, Course, TeacherCourseCombo, Class, ClassSchedule
from datetime import date, timedelta
from routes.schedule import is_holiday, find_next_available_saturday

def init_database():
    """初始化数据库"""
    app = create_app()
    
    with app.app_context():
        # 创建所有表
        db.create_all()
        print("✓ 数据库表创建成功")
        
        # 检查是否已有数据
        if Project.query.first():
            print("! 数据库已有数据，跳过初始化")
            print("  如需重新初始化，请先清空数据库")
            return
        
        # 插入项目和课题
        init_projects_and_topics()
        
        # 插入班主任
        init_homerooms()
        
        # 插入讲师
        init_teachers()
        
        # 插入课程
        init_courses()
        
        # 插入教-课组合
        init_combos()
        
        # 插入模拟项目数据再生成历史班级和课表
        init_mock_projects_and_classes()
        
        print("\n✓ 所有数据初始化完成！")
        print("  - 7 个项目")
        print("  - 56 个课题")
        print("  - 10 个班主任")
        print("  - 20 个授课讲师")
        print("  - 课程和教-课组合")
        print("  - 模拟历史班级和课表数据")


def init_projects_and_topics():
    """初始化项目和课题"""
    
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
        tt = Project(
            name=tt_data["name"],
            description=tt_data["description"]
        )
        db.session.add(tt)
        db.session.flush()  # 获取ID
        
        for topic_data in tt_data["topics"]:
            topic = Topic(
                project_id=tt.id,
                sequence=topic_data["seq"],
                name=topic_data["name"],
                is_fixed=topic_data["fixed"]
            )
            db.session.add(topic)
    
    db.session.commit()
    print("✓ 项目和课题初始化完成")


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
        {"name": "钱海", "title": "教授", "expertise": "人工智能、数据科学", "phone": "13900001011"},
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
    """初始化课程 (明确指定课题关联)"""
    # 先获取所有课题
    topics = Topic.query.all()
    topic_map = {t.name: t.id for t in topics}  # 课题名 -> ID
    
    courses_data = [
        # 领袖增长本科班课程
        {"name": "宏观经济形势与政策解读", "topic_name": "开班仪式与宏观经济形势分析"},
        {"name": "战略思维与决策方法", "topic_name": "战略思维与商业模式创新"},
        {"name": "商业模式创新实战", "topic_name": "战略思维与商业模式创新"},
        {"name": "组织管理与领导力提升", "topic_name": "组织管理与团队领导力"},
        {"name": "团队建设与激励", "topic_name": "组织管理与团队领导力"},
        {"name": "财务管理基础", "topic_name": "财务管理与资本运作基础"},
        {"name": "资本运营实务", "topic_name": "财务管理与资本运作基础"},
        {"name": "市场营销策略", "topic_name": "市场营销与品牌建设"},
        {"name": "品牌建设与传播", "topic_name": "市场营销与品牌建设"},
        {"name": "企业数字化转型路径", "topic_name": "数字化转型与科技创新"},
        {"name": "企业法务风险防范", "topic_name": "企业法务与风险管理"},
        {"name": "合同管理与合规", "topic_name": "企业法务与风险管理"},
        
        # 领袖增长硕士班课程
        {"name": "全球经济与中国机遇", "topic_name": "开班仪式与宏观经济趋势研判"},
        {"name": "战略规划实战", "topic_name": "战略规划与竞争优势构建"},
        {"name": "组织变革管理", "topic_name": "组织变革与人才梯队建设"},
        {"name": "人才梯队建设", "topic_name": "组织变革与人才梯队建设"},
        {"name": "投融资实务", "topic_name": "资本市场与投融资实务"},
        {"name": "跨国经营战略", "topic_name": "全球化视野与跨国经营"},
        {"name": "平台战略与生态构建", "topic_name": "产业生态与平台战略"},
        {"name": "企业传承之道", "topic_name": "企业传承与基业长青"},
        
        # 国学班课程
        {"name": "易经智慧与决策", "topic_name": "开班仪式与易经智慧概论"},
        {"name": "易经与人生", "topic_name": "开班仪式与易经智慧概论"},
        {"name": "儒家修身齐家", "topic_name": "儒家思想与修身齐家"},
        {"name": "儒商精神", "topic_name": "儒家思想与修身齐家"},
        {"name": "道家无为而治", "topic_name": "道家哲学与无为而治"},
        {"name": "道德经导读", "topic_name": "道家哲学与无为而治"},
        {"name": "孙子兵法精讲", "topic_name": "兵法谋略与竞争智慧"},
        {"name": "商战谋略", "topic_name": "兵法谋略与竞争智慧"},
        {"name": "禅宗与心性修炼", "topic_name": "禅宗心法与企业家心性修炼"},
        {"name": "正念领导力", "topic_name": "禅宗心法与企业家心性修炼"},
        {"name": "中医养生基础", "topic_name": "中医养生与身心平衡"},
        {"name": "四季养生智慧", "topic_name": "中医养生与身心平衡"},
        
        # 数字化转型总裁班课程
        {"name": "数字经济趋势分析", "topic_name": "开班仪式与数字经济宏观解读"},
        {"name": "数字化战略规划", "topic_name": "数字化战略规划与转型路径"},
        {"name": "数字化转型路径设计", "topic_name": "数字化战略规划与转型路径"},
        {"name": "数据中台建设", "topic_name": "数据中台与智能决策"},
        {"name": "智能决策系统", "topic_name": "数据中台与智能决策"},
        {"name": "人工智能应用", "topic_name": "人工智能与业务场景融合"},
        {"name": "AI业务场景设计", "topic_name": "人工智能与业务场景融合"},
        {"name": "数字营销实战", "topic_name": "数字营销与客户体验重塑"},
        {"name": "客户体验优化", "topic_name": "数字营销与客户体验重塑"},
        {"name": "组织敏捷转型", "topic_name": "组织敏捷与数字化人才培养"},
        {"name": "数字化人才体系", "topic_name": "组织敏捷与数字化人才培养"},
        {"name": "网络安全管理", "topic_name": "网络安全与数据合规"},
        {"name": "数据合规实务", "topic_name": "网络安全与数据合规"},
        
        # EMBA创新实验班课程
        {"name": "创新经济学", "topic_name": "开班仪式与创新经济学导论"},
        {"name": "创新思维训练", "topic_name": "创新思维与设计思维方法论"},
        {"name": "设计思维实战", "topic_name": "创新思维与设计思维方法论"},
        {"name": "商业模式创新", "topic_name": "商业模式创新与颠覆式创新"},
        {"name": "颠覆式创新案例", "topic_name": "商业模式创新与颠覆式创新"},
        {"name": "创新组织设计", "topic_name": "创新组织与创业生态构建"},
        {"name": "创业生态打造", "topic_name": "创新组织与创业生态构建"},
        {"name": "技术前沿解读", "topic_name": "技术前沿与产业创新趋势"},
        {"name": "产业创新趋势", "topic_name": "技术前沿与产业创新趋势"},
        {"name": "风险投资策略", "topic_name": "创新资本与风险投资策略"},
        {"name": "创新项目孵化", "topic_name": "创新实践与项目孵化"},
        
        # 女性领导力研修营课程
        {"name": "女性领导力觉醒", "topic_name": "开班仪式与女性领导力觉醒"},
        {"name": "自我认知与定位", "topic_name": "自我认知与个人品牌塑造"},
        {"name": "个人品牌塑造", "topic_name": "自我认知与个人品牌塑造"},
        {"name": "商务沟通艺术", "topic_name": "沟通艺术与影响力提升"},
        {"name": "高情商沟通", "topic_name": "沟通艺术与影响力提升"},
        {"name": "职业发展规划", "topic_name": "职业发展与事业家庭平衡"},
        {"name": "事业家庭平衡", "topic_name": "职业发展与事业家庭平衡"},
        {"name": "女性财务规划", "topic_name": "财务独立与财富管理"},
        {"name": "财富管理实务", "topic_name": "财务独立与财富管理"},
        {"name": "团队赋能领导", "topic_name": "团队建设与赋能型领导"},
        {"name": "健康管理", "topic_name": "健康管理与优雅生活美学"},
        {"name": "生活美学", "topic_name": "健康管理与优雅生活美学"},
        
        # 医疗产业实战班课程
        {"name": "医疗产业政策深度解读", "topic_name": "开班仪式与医疗产业宏观政策解读"},
        {"name": "医疗机构运营", "topic_name": "医疗机构运营与精细化管理"},
        {"name": "医院精细化管理", "topic_name": "医疗机构运营与精细化管理"},
        {"name": "创新药研发趋势", "topic_name": "医药研发与创新药物开发"},
        {"name": "药物开发流程", "topic_name": "医药研发与创新药物开发"},
        {"name": "医疗器械市场分析", "topic_name": "医疗器械与智能医疗设备"},
        {"name": "智能医疗设备", "topic_name": "医疗器械与智能医疗设备"},
        {"name": "医疗投融资", "topic_name": "医疗投融资与并购重组"},
        {"name": "医疗并购案例", "topic_name": "医疗投融资与并购重组"},
        {"name": "互联网医疗", "topic_name": "互联网医疗与数字健康"},
        {"name": "数字健康生态", "topic_name": "互联网医疗与数字健康"},
        {"name": "医疗合规管理", "topic_name": "医疗合规与医保政策应对"},
        {"name": "医保政策应对", "topic_name": "医疗合规与医保政策应对"},
    ]
    
    courses_created = 0
    unmatched = []
    
    for c_data in courses_data:
        topic_name = c_data.get("topic_name")
        topic_id = topic_map.get(topic_name) if topic_name else None
        
        if topic_name and not topic_id:
            unmatched.append(f"{c_data['name']} -> {topic_name}")
        
        c = Course(
            name=c_data["name"],
            description=c_data.get("description", c_data["name"]),
            duration_days=c_data.get("duration_days", 1),
            topic_id=topic_id
        )
        db.session.add(c)
        courses_created += 1
    
    db.session.commit()
    
    if unmatched:
        print(f"! 警告：以下课程未匹配到课题:")
        for u in unmatched:
            print(f"  - {u}")
    
    print(f"✓ 课程初始化完成（{courses_created}门），已关联课题")




def init_combos():
    """初始化教-课组合（确保每个课题有2个组合用于双天排课）"""
    topics = Topic.query.all()
    teachers = Teacher.query.all()
    
    combo_count = 0
    
    for topic in topics:
        # 1. 找该课题关联的课程
        topic_courses = Course.query.filter_by(topic_id=topic.id).all()
        
        # 如果没有关联课程，为了演示，我们随机绑定2个无主课程给它 (临时为了数据丰富)
        if not topic_courses:
            orphan_courses = Course.query.filter_by(topic_id=None).limit(2).all()
            for oc in orphan_courses:
                oc.topic_id = topic.id # 抢过来
            db.session.commit()
            topic_courses = orphan_courses
            
        # 仍然没有？创建默认的
        if not topic_courses:
            # 每个课题只创建1门课程，双天授课通过combo/combo_2处理
            c1 = Course(name=topic.name, topic_id=topic.id, duration_days=1)
            db.session.add(c1)
            db.session.commit()
            topic_courses = [c1]

        # 2. 为这些课程分配讲师
        # 简单轮询分配
        for i, course in enumerate(topic_courses):
            # 选讲师：尽量不同
            teacher = teachers[(topic.id + i) % len(teachers)]
            
            # Day 1 or Day 2 Logic?
            # 假设我们为每个Topic至少创建2个combo
            # 1. TopicID-TeacherA-CourseA (Priority 10)
            # 2. TopicID-TeacherB-CourseB (Priority 9)
            
            combo = TeacherCourseCombo(
                topic_id=topic.id,
                teacher_id=teacher.id,
                course_id=course.id
            )
            db.session.add(combo)
            combo_count += 1
            
            # 如果只有1门课，给它再加一个不同老师的组合备用
            if len(topic_courses) == 1:
                teacher2 = teachers[(topic.id + i + 1) % len(teachers)]
                combo2 = TeacherCourseCombo(
                    topic_id=topic.id,
                    teacher_id=teacher2.id,
                    course_id=course.id
                )
                db.session.add(combo2)
                combo_count += 1

    db.session.commit()
    print(f"✓ 教-课组合初始化完成（{combo_count}个），已覆盖双课程逻辑")


def init_mock_projects_and_classes():
    """创建模拟项目并在每个项目下生成历史班级和课表数据"""

    # 每个项目
    projects = Project.query.all()
    homerooms = Homeroom.query.all()
    
    if not projects or not homerooms:
        print("! 缺少项目或班主任数据，跳过模拟班级生成")
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
        project = projects[config["tt_idx"]]
        topics = Topic.query.filter_by(project_id=project.id).order_by(Topic.sequence).all()
        
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
                project_id=project.id,
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
                is_future = current_date > date.today()
                
                if i < completed_count and not is_future:
                    sched_status = "completed"
                elif i == completed_count and status == "active" and not is_future:
                    # 如果正好是第N+1节，且已经是过去/今天，那就是completed? 
                    # 不，active意味着正在进行或即将进行。
                    # 如果current_date < today，那么它应该是"completed" (漏打卡) 或者 "scheduled" (未开始)？
                    # 简化：只把未来的标记为planning/scheduled
                    sched_status = "scheduled"
                elif i < completed_count and is_future:
                   # 异常：计数说完成了，但时间在未来。强制改为 scheduled/planning
                   sched_status = "scheduled" 
                else:
                    sched_status = "planning"
                
                # 获取该课题的教-课组合 (尽量取2个不同的，用于周六和周日)
                combos = TeacherCourseCombo.query.filter_by(topic_id=topic.id)\
                                                .order_by(TeacherCourseCombo.id.desc()).all()

                # 冲突检测：避免同一日期班主任重复以及讲师重复
                max_shift_attempts = 6
                shift_attempts = 0
                selected_combo1 = None
                selected_combo2 = None

                while shift_attempts < max_shift_attempts:
                    # 跳过节假日
                    if is_holiday(current_date):
                        current_date = current_date + timedelta(days=7)
                        shift_attempts += 1
                        continue

                    # 是否有其他班级在同一天由相同班主任负责？
                    homeroom_conflict = ClassSchedule.query.join(Class)\
                        .filter(Class.homeroom_id == new_class.homeroom_id, ClassSchedule.scheduled_date == current_date)\
                        .first()

                    # 收集当天已被占用的讲师ID
                    occupied_teacher_ids = set()
                    other_schedules = ClassSchedule.query.filter_by(scheduled_date=current_date).all()
                    for os in other_schedules:
                        if os.combo and os.combo.teacher_id:
                            occupied_teacher_ids.add(os.combo.teacher_id)
                        if os.combo_2 and os.combo_2.teacher_id:
                            occupied_teacher_ids.add(os.combo_2.teacher_id)

                    # 在可用combos中挑选不冲突的讲师组合
                    # 优先选择不同讲师
                    for c in combos:
                        if c.teacher_id not in occupied_teacher_ids:
                            selected_combo1 = c
                            break
                    if not selected_combo1 and combos:
                        selected_combo1 = combos[0]

                    # 找第二个不同讲师
                    for c in combos:
                        if c.id == (selected_combo1.id if selected_combo1 else None):
                            continue
                        if c.teacher_id not in occupied_teacher_ids:
                            selected_combo2 = c
                            break
                    if not selected_combo2:
                        # 没有可用不同讲师，允许重复使用同一讲师（退而求其次）
                        selected_combo2 = selected_combo1

                    # 如果班主任冲突或首日讲师被占用，则顺延一周再试
                    teacher_conflict = (selected_combo1 and selected_combo1.teacher_id in occupied_teacher_ids) or \
                                     (selected_combo2 and selected_combo2.teacher_id in occupied_teacher_ids)

                    if homeroom_conflict or teacher_conflict:
                        current_date = current_date + timedelta(days=7)
                        shift_attempts += 1
                        # 重置选择，继续下一轮
                        selected_combo1 = None
                        selected_combo2 = None
                        continue

                    # 找到合适的日期和讲师组合，退出循环
                    break

                # 最后无论是否完全避开冲突，使用已选的组合（可能与原逻辑不同，但能减少大部分冲突）
                combo1 = selected_combo1
                combo2 = selected_combo2 if selected_combo2 else selected_combo1

                schedule = ClassSchedule(
                    class_id=new_class.id,
                    topic_id=topic.id,
                    combo_id=combo1.id if combo1 else None,
                    combo_id_2=combo2.id if combo2 else None,
                    scheduled_date=current_date,
                    week_number=i + 1,
                    status=sched_status
                )
                db.session.add(schedule)
                schedule_count += 1

                # 下一节课间隔4周（从当前安排的周六开始计算）
                current_date_next = current_date + timedelta(weeks=4)
                current_date = find_next_available_saturday(current_date_next)
    
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
