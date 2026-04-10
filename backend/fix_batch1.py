"""
批次1修复脚本 - EMBA122/123/125/126/127
对比用户课表图片与数据库，通过新增combo并关联到schedule来消除空缺
"""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from app import app
from models import db, ClassSchedule, TeacherCourseCombo, Teacher, Topic

def find_or_create_teacher(name):
    t = Teacher.query.filter_by(name=name).first()
    if not t:
        t = Teacher(name=name)
        db.session.add(t)
        db.session.flush()
        print(f"  [NEW TEACHER] 新增讲师: {name} (id={t.id})")
    return t

def find_or_create_combo(topic_id, teacher_name, course_name):
    teacher = find_or_create_teacher(teacher_name)
    combo = TeacherCourseCombo.query.filter_by(
        topic_id=topic_id, teacher_id=teacher.id, course_name=course_name
    ).first()
    if not combo:
        combo = TeacherCourseCombo(topic_id=topic_id, teacher_id=teacher.id, course_name=course_name)
        db.session.add(combo)
        db.session.flush()
        topic = Topic.query.get(topic_id)
        print(f"  [NEW COMBO] combo_id={combo.id}: 课题=[{topic.name}] 讲师={teacher_name} 课程={course_name}")
    else:
        print(f"  [EXISTING COMBO] combo_id={combo.id}: 讲师={teacher_name} 课程={course_name}")
    return combo

def fix_schedule(class_id, date_str, day, topic_id, teacher_name, course_name):
    """day=1 → combo_id, day=2 → combo_id_2"""
    from datetime import date
    y, m, d = map(int, date_str.split('-'))
    sch = ClassSchedule.query.filter_by(class_id=class_id, scheduled_date=date(y, m, d)).first()
    if not sch:
        print(f"  [SKIP] 未找到 class_id={class_id} date={date_str} 的排课记录")
        return False
    
    combo = find_or_create_combo(topic_id, teacher_name, course_name)
    
    if day == 1:
        old = sch.combo_id
        sch.combo_id = combo.id
        print(f"  [FIX D1] schedule_id={sch.id} combo_id: {old} → {combo.id}")
    else:
        old = sch.combo_id_2
        sch.combo_id_2 = combo.id
        print(f"  [FIX D2] schedule_id={sch.id} combo_id_2: {old} → {combo.id}")
    return True

with app.app_context():
    # 先查出所有topic_id
    topics = {t.name: t.id for t in Topic.query.all()}
    T_MACRO   = topics['宏观经济与企业战略创新']
    T_AI      = topics['人工智能与商业应用']
    T_FINANCE = topics['财务管理与风险管理优化']
    T_DIGITAL = topics['企业数字化变革与数智创新']
    T_HR      = topics['人力资源管理与组织效能提升']
    T_SALES   = topics['销售管理与客户关系经营']
    T_LEADER  = topics['领导力与团队建设']
    T_BRAND   = topics['品牌营销与数智化营销']
    T_OTHER   = topics['其他']

    print("="*60)
    print("EMBA122期 (ID=1)")
    print("="*60)
    # 5/24 D2: 张庆安/国际形势与宏观经济 (topic=财务管理)
    fix_schedule(1, '2025-05-24', 2, T_FINANCE, '张庆安', '国际形势与宏观经济')

    print("\n" + "="*60)
    print("EMBA123期 (ID=2)")
    print("="*60)
    # 3/7 D2: 杨台轩/3D领导力 (topic=人工智能)
    fix_schedule(2, '2026-03-07', 2, T_AI, '杨台轩', '3D领导力—企业与员工成长发展的战略性突破')
    # 6/13 D1: 陈晋蓉/资本运营新策略 (topic=企业数字化变革)
    fix_schedule(2, '2026-06-13', 1, T_DIGITAL, '陈晋蓉', '资本运营新策略')
    # 6/13 D2: 刘钰/公司治理与股权设计 (topic=企业数字化变革)
    fix_schedule(2, '2026-06-13', 2, T_DIGITAL, '刘钰', '公司治理与股权设计')

    print("\n" + "="*60)
    print("EMBA125期 (ID=3)")
    print("="*60)
    # 7/26 D1+D2: 严小云/卓越薪酬绩效管理体系 (topic=人力资源)
    fix_schedule(3, '2025-07-26', 1, T_HR, '严小云', '卓越薪酬绩效管理体系')
    fix_schedule(3, '2025-07-26', 2, T_HR, '严小云', '卓越薪酬绩效管理体系')
    # 10/18 D2: 刘勇/AI全网矩阵营销与产业互联网进化 (topic=人力资源)
    fix_schedule(3, '2025-10-18', 2, T_HR, '刘勇', 'AI全网矩阵营销与产业互联网进化')
    # 12/20 D1: 董俊豪/企业AI Deepseek战略课 (topic=人工智能)
    fix_schedule(3, '2025-12-20', 1, T_AI, '董俊豪', '企业AI Deepseek战略课')
    # 12/20 D2: 常亮/公司股权架构设计与激励 (topic=人工智能)
    fix_schedule(3, '2025-12-20', 2, T_AI, '常亮', '公司股权架构设计与激励')
    # 5/9 D2: 曲融/投资视角下的行业研究体系分析 (topic=宏观经济)
    fix_schedule(3, '2026-05-09', 2, T_MACRO, '曲融', '投资视角下的行业研究体系分析')

    print("\n" + "="*60)
    print("EMBA126期 (ID=4)")
    print("="*60)
    # 8/16 D1+D2: 吴子敬/股权设计、股权合伙与激励 (topic=财务管理)
    fix_schedule(4, '2025-08-16', 1, T_FINANCE, '吴子敬', '股权设计、股权合伙与激励')
    fix_schedule(4, '2025-08-16', 2, T_FINANCE, '吴子敬', '股权设计、股权合伙与激励')
    # 3/7 D1+D2: 刘春华/AI时代下的新营销九段法 (topic=人工智能) — 图片写的"九步法"，按DB已有名称
    fix_schedule(4, '2026-03-07', 1, T_AI, '刘春华', 'AI时代下的新营销九段法')
    fix_schedule(4, '2026-03-07', 2, T_AI, '刘春华', 'AI时代下的新营销九段法')
    # 注意: 4/18 D1(董俊豪)+D2(易正) 课程名图片看不清，暂不处理
    # 注意: 5/23 D2(王薇华?) 课程名图片看不清，暂不处理

    print("\n" + "="*60)
    print("EMBA127期 (ID=5)")
    print("="*60)
    # 3/14 D2: 韩铁林/企业战略规划与制定 (topic=财务管理)
    fix_schedule(5, '2026-03-14', 2, T_FINANCE, '韩铁林', '企业战略规划与制定')
    # 4/18 D1: 董俊豪/AI驱动增长：企业家的战略蓝图与实战路径 (topic=企业数字化变革)
    fix_schedule(5, '2026-04-18', 1, T_DIGITAL, '董俊豪', 'AI驱动增长：企业家的战略蓝图与实战路径')
    # 4/18 D2: 尚旭/易经智慧与经营决策 (topic=企业数字化变革)
    fix_schedule(5, '2026-04-18', 2, T_DIGITAL, '尚旭', '易经智慧与经营决策')
    # 8/1 D2: 易正/中国古法姓名学 (topic=企业数字化变革)
    fix_schedule(5, '2026-08-01', 2, T_DIGITAL, '易正', '中国古法姓名学')

    db.session.commit()
    print("\n" + "="*60)
    print("全部修复已提交！")
    print("="*60)
