"""
批次2: EMBA128/129/130/131/132
1. 填写空combo
2. 自动修复课题重复
3. 验证闭环
"""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from datetime import date
from collections import Counter
from app import app
from models import db, ClassSchedule, TeacherCourseCombo, Teacher, Topic

def find_or_create_teacher(name):
    t = Teacher.query.filter_by(name=name).first()
    if not t:
        t = Teacher(name=name)
        db.session.add(t)
        db.session.flush()
        print(f"  [NEW TEACHER] {name} (id={t.id})")
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
        topic = db.session.get(Topic, topic_id)
        print(f"  [NEW COMBO] id={combo.id}: [{topic.name}] {teacher_name}/{course_name}")
    return combo

def fix_schedule(class_id, date_str, day, topic_id, teacher_name, course_name):
    y, m, d = map(int, date_str.split('-'))
    sch = ClassSchedule.query.filter_by(class_id=class_id, scheduled_date=date(y, m, d)).first()
    if not sch:
        print(f"  [SKIP] 未找到 class_id={class_id} date={date_str}")
        return None
    combo = find_or_create_combo(topic_id, teacher_name, course_name)
    if day == 1:
        sch.combo_id = combo.id
        print(f"  [FIX D{day}] {date_str} → {teacher_name}/{course_name}")
    else:
        sch.combo_id_2 = combo.id
        print(f"  [FIX D{day}] {date_str} → {teacher_name}/{course_name}")
    return sch

def get_natural_topic(combo):
    if not combo: return None
    earliest = TeacherCourseCombo.query.filter_by(
        teacher_id=combo.teacher_id, course_name=combo.course_name
    ).order_by(TeacherCourseCombo.id).first()
    return earliest.topic_id if earliest else combo.topic_id

def find_or_create_combo_under(topic_id, teacher_id, course_name):
    combo = TeacherCourseCombo.query.filter_by(
        topic_id=topic_id, teacher_id=teacher_id, course_name=course_name
    ).first()
    if not combo:
        combo = TeacherCourseCombo(topic_id=topic_id, teacher_id=teacher_id, course_name=course_name)
        db.session.add(combo)
        db.session.flush()
    return combo

def auto_fix_topics(class_id, class_name):
    print(f"\n  [TOPIC FIX] {class_name}")
    schedules = ClassSchedule.query.filter(
        ClassSchedule.class_id == class_id,
        ClassSchedule.status != 'cancelled'
    ).order_by(ClassSchedule.scheduled_date).all()
    
    cls = schedules[0].class_
    core_topics = Topic.query.filter_by(project_id=cls.project_id).filter(
        Topic.is_other != True
    ).order_by(Topic.sequence).all()
    core_ids = {t.id for t in core_topics}
    other_topic = Topic.query.filter_by(project_id=cls.project_id, is_other=True).first()
    
    # >8的归其他
    core_scheds = schedules[:8]
    for s in schedules[8:]:
        if s.topic_id != other_topic.id:
            old = s.topic.name
            s.topic_id = other_topic.id
            if s.combo:
                nc = find_or_create_combo_under(other_topic.id, s.combo.teacher_id, s.combo.course_name)
                s.combo_id = nc.id
            if s.combo_2:
                nc2 = find_or_create_combo_under(other_topic.id, s.combo_2.teacher_id, s.combo_2.course_name)
                s.combo_id_2 = nc2.id
            print(f"    {s.scheduled_date} [{old}] -> [其他]")
    
    # 前8课分配不重复的核心课题
    assigned = {}
    conflicts = []
    for s in core_scheds:
        nat = get_natural_topic(s.combo) if s.combo else s.topic_id
        if nat in core_ids and nat not in assigned:
            assigned[nat] = s
        else:
            conflicts.append(s)
    
    missing = [t.id for t in core_topics if t.id not in assigned]
    for s, tid in zip(conflicts, missing):
        assigned[tid] = s
    
    for topic_id, s in assigned.items():
        if s.topic_id != topic_id:
            old = s.topic.name
            new_t = db.session.get(Topic, topic_id)
            s.topic_id = topic_id
            if s.combo:
                nc = find_or_create_combo_under(topic_id, s.combo.teacher_id, s.combo.course_name)
                s.combo_id = nc.id
            if s.combo_2:
                nc2 = find_or_create_combo_under(topic_id, s.combo_2.teacher_id, s.combo_2.course_name)
                s.combo_id_2 = nc2.id
            print(f"    {s.scheduled_date} [{old}] -> [{new_t.name}]")

def verify_class(class_id, class_name):
    scheds = ClassSchedule.query.filter(
        ClassSchedule.class_id == class_id,
        ClassSchedule.status != 'cancelled'
    ).order_by(ClassSchedule.scheduled_date).all()
    
    issues = []
    for s in scheds:
        if s.combo and s.combo.topic_id != s.topic_id:
            issues.append(f"D1 mismatch {s.scheduled_date}")
        if s.combo_2 and s.combo_2.topic_id != s.topic_id:
            issues.append(f"D2 mismatch {s.scheduled_date}")
    
    tc = Counter()
    for s in scheds:
        if s.topic and not s.topic.is_other:
            tc[s.topic.name] += 1
    dups = {k:v for k,v in tc.items() if v > 1}
    
    empty = sum(1 for s in scheds if not s.combo)
    
    status = "OK" if not issues and not dups and empty == 0 else "⚠️"
    print(f"  [{status}] {class_name}: "
          f"空combo={empty}, 课题重复={len(dups)}, combo错配={len(issues)}")
    if dups: print(f"       重复: {dups}")
    if issues: print(f"       错配: {issues}")

with app.app_context():
    topics = {t.name: t.id for t in Topic.query.all()}
    # 用于初始填combo时关联到当前schedule的topic
    def sch_topic(class_id, date_str):
        y,m,d = map(int, date_str.split('-'))
        s = ClassSchedule.query.filter_by(class_id=class_id, scheduled_date=date(y,m,d)).first()
        return s.topic_id if s else None

    # === EMBA128 (ID=6) ===
    print("="*60)
    print("EMBA128期 (ID=6) — 填combo")
    print("="*60)
    fix_schedule(6, '2025-09-20', 2, sch_topic(6,'2025-09-20'), '钟彩民', '商业模式设计与创新')
    fix_schedule(6, '2025-12-20', 1, sch_topic(6,'2025-12-20'), '董俊豪', '企业AI Deepseek战略课')
    fix_schedule(6, '2025-12-20', 2, sch_topic(6,'2025-12-20'), '常亮', '公司股权架构设计与激励')
    fix_schedule(6, '2026-05-09', 2, sch_topic(6,'2026-05-09'), '阙登峰', '"投入不变 业绩倍增"的全过程管理')
    fix_schedule(6, '2026-06-27', 1, sch_topic(6,'2026-06-27'), '刘钰', '待定')
    fix_schedule(6, '2026-06-27', 2, sch_topic(6,'2026-06-27'), '龙平敬', '企业资本价值倍增之道')
    auto_fix_topics(6, "EMBA128")

    # === EMBA129 (ID=7) ===
    print("\n" + "="*60)
    print("EMBA129期 (ID=7) — 填combo")
    print("="*60)
    # 开学D1
    fix_schedule(7, '2025-07-26', 1, sch_topic(7,'2025-07-26'), '院长', '院长课')
    s = ClassSchedule.query.filter_by(class_id=7, scheduled_date=date(2025,7,26)).first()
    if s and not s.has_opening:
        s.has_opening = True; s.has_team_building = True
        print("  [FLAG] 设置开学典礼+团建")
    # 12/20
    fix_schedule(7, '2025-12-20', 1, sch_topic(7,'2025-12-20'), '刘春华', 'AI时代下的新营销九段法')
    fix_schedule(7, '2025-12-20', 2, sch_topic(7,'2025-12-20'), '刘春华', 'AI时代下的新营销九段法')
    # 5/9 吴子敬(图片写吴梓境，疑似同一人)/待定
    fix_schedule(7, '2026-05-09', 1, sch_topic(7,'2026-05-09'), '吴子敬', '待定')
    fix_schedule(7, '2026-05-09', 2, sch_topic(7,'2026-05-09'), '吴子敬', '待定')
    auto_fix_topics(7, "EMBA129")

    # === EMBA130 (ID=8) ===
    print("\n" + "="*60)
    print("EMBA130期 (ID=8) — 填combo")
    print("="*60)
    # 注意: 8/9-10开学典礼不在数据库中
    print("  [NOTE] 8/9-10开学典礼+张庆安不在DB中，需确认是否添加")
    # 3/21
    fix_schedule(8, '2026-03-21', 1, sch_topic(8,'2026-03-21'), '刘春华', 'AI时代下的新营销九段法')
    fix_schedule(8, '2026-03-21', 2, sch_topic(8,'2026-03-21'), '刘春华', 'AI时代下的新营销九段法')
    # 6/19
    fix_schedule(8, '2026-06-19', 1, sch_topic(8,'2026-06-19'), '张益铭', '家庭幸福与企业效益')
    fix_schedule(8, '2026-06-19', 2, sch_topic(8,'2026-06-19'), '张益铭', '家庭幸福与企业效益')
    auto_fix_topics(8, "EMBA130")

    # === EMBA131 (ID=9) ===
    print("\n" + "="*60)
    print("EMBA131期 (ID=9) — 填combo")
    print("="*60)
    # 10/25 D2
    fix_schedule(9, '2025-10-25', 2, sch_topic(9,'2025-10-25'), '张涛', '大数据时代突发事件管理与网络舆情应对')
    # 8/22 D2
    fix_schedule(9, '2026-08-22', 2, sch_topic(9,'2026-08-22'), '岳庆平', '中国历代王朝的治乱兴衰')
    auto_fix_topics(9, "EMBA131")

    # === EMBA132 (ID=10) ===
    print("\n" + "="*60)
    print("EMBA132期 (ID=10) — 填combo")
    print("="*60)
    # 3/7 D2
    fix_schedule(10, '2026-03-07', 2, sch_topic(10,'2026-03-07'), '宗英涛', '稻盛和夫的经营哲学')
    # 4/18 D1+D2
    fix_schedule(10, '2026-04-18', 1, sch_topic(10,'2026-04-18'), '刘钰', '股权设计和资本路径')
    fix_schedule(10, '2026-04-18', 2, sch_topic(10,'2026-04-18'), '黄宏', '商业模式创新与落地')
    # 6/13 D1+D2
    fix_schedule(10, '2026-06-13', 1, sch_topic(10,'2026-06-13'), '刘春华', 'AI时代下的新营销九段法')
    fix_schedule(10, '2026-06-13', 2, sch_topic(10,'2026-06-13'), '刘春华', 'AI时代下的新营销九段法')
    # 8/15 D1+D2
    fix_schedule(10, '2026-08-15', 1, sch_topic(10,'2026-08-15'), '董俊豪', '企业AI Deepseek战略课')
    fix_schedule(10, '2026-08-15', 2, sch_topic(10,'2026-08-15'), '曲融', '投资视角下的行业研究体系分析')
    # 10/17 D2
    fix_schedule(10, '2026-10-17', 2, sch_topic(10,'2026-10-17'), '孔海钦', '国学的新思维')
    auto_fix_topics(10, "EMBA132")

    db.session.commit()

    # 最终验证
    print("\n" + "="*60)
    print("最终验证")
    print("="*60)
    for cid, name in [(6,"EMBA128"),(7,"EMBA129"),(8,"EMBA130"),(9,"EMBA131"),(10,"EMBA132")]:
        verify_class(cid, name)
    print("\n全部完成!")
