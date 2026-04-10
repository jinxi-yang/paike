"""补录EMBA130 8/9-10开学典礼，然后重新跑topic auto-fix"""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
from datetime import date
from collections import Counter
from app import app
from models import db, ClassSchedule, TeacherCourseCombo, Teacher, Topic

def find_or_create_combo(topic_id, teacher_name, course_name):
    teacher = Teacher.query.filter_by(name=teacher_name).first()
    if not teacher:
        teacher = Teacher(name=teacher_name)
        db.session.add(teacher); db.session.flush()
    combo = TeacherCourseCombo.query.filter_by(
        topic_id=topic_id, teacher_id=teacher.id, course_name=course_name
    ).first()
    if not combo:
        combo = TeacherCourseCombo(topic_id=topic_id, teacher_id=teacher.id, course_name=course_name)
        db.session.add(combo); db.session.flush()
        print(f"  [NEW COMBO] id={combo.id}: {teacher_name}/{course_name}")
    return combo

def find_or_create_combo_under(topic_id, teacher_id, course_name):
    combo = TeacherCourseCombo.query.filter_by(
        topic_id=topic_id, teacher_id=teacher_id, course_name=course_name
    ).first()
    if not combo:
        combo = TeacherCourseCombo(topic_id=topic_id, teacher_id=teacher_id, course_name=course_name)
        db.session.add(combo); db.session.flush()
    return combo

def get_natural_topic(combo):
    if not combo: return None
    earliest = TeacherCourseCombo.query.filter_by(
        teacher_id=combo.teacher_id, course_name=combo.course_name
    ).order_by(TeacherCourseCombo.id).first()
    return earliest.topic_id if earliest else combo.topic_id

with app.app_context():
    cls_id = 8
    topics = {t.name: t.id for t in Topic.query.all()}
    T_MACRO = topics['宏观经济与企业战略创新']
    T_OTHER_ID = Topic.query.filter_by(is_other=True).first().id
    
    # 检查是否已存在
    existing = ClassSchedule.query.filter_by(
        class_id=cls_id, scheduled_date=date(2025, 8, 9)
    ).first()
    
    if existing:
        print(f"记录已存在 schedule_id={existing.id}, 跳过")
    else:
        # 查现有最小week_number
        first = ClassSchedule.query.filter_by(class_id=cls_id).order_by(
            ClassSchedule.scheduled_date
        ).first()
        
        # 新增开学典礼记录
        combo_d1 = find_or_create_combo(T_MACRO, '院长', '院长课')
        combo_d2 = find_or_create_combo(T_MACRO, '张庆安', '最新国际形势与中国宏观经济')
        
        new_sch = ClassSchedule(
            class_id=cls_id,
            scheduled_date=date(2025, 8, 9),
            topic_id=T_MACRO,
            combo_id=combo_d1.id,
            combo_id_2=combo_d2.id,
            week_number=0,
            has_opening=True,
            has_team_building=True,
            status='scheduled'
        )
        db.session.add(new_sch)
        db.session.flush()
        print(f"[NEW] schedule_id={new_sch.id}: 2025-08-09 EMBA130 开学典礼")
        print(f"  D1: 院长/院长课, D2: 张庆安/最新国际形势与中国宏观经济")
        print(f"  开学典礼=True, 团建=True")
    
    # 重新排week_number
    all_sch = ClassSchedule.query.filter(
        ClassSchedule.class_id == cls_id,
        ClassSchedule.status != 'cancelled'
    ).order_by(ClassSchedule.scheduled_date).all()
    
    for i, s in enumerate(all_sch, 1):
        s.week_number = i
    print(f"\n重排week_number: {len(all_sch)}条记录")
    
    # 重新跑topic auto-fix (11条,前8是核心,后3是其他)
    print(f"\n[TOPIC FIX] EMBA130 ({len(all_sch)}节课)")
    
    core_topics = Topic.query.filter_by(project_id=all_sch[0].class_.project_id).filter(
        Topic.is_other != True
    ).order_by(Topic.sequence).all()
    core_ids = {t.id for t in core_topics}
    
    core_scheds = all_sch[:8]
    extras = all_sch[8:]
    
    for s in extras:
        if s.topic_id != T_OTHER_ID:
            old = s.topic.name
            s.topic_id = T_OTHER_ID
            if s.combo:
                nc = find_or_create_combo_under(T_OTHER_ID, s.combo.teacher_id, s.combo.course_name)
                s.combo_id = nc.id
            if s.combo_2:
                nc2 = find_or_create_combo_under(T_OTHER_ID, s.combo_2.teacher_id, s.combo_2.course_name)
                s.combo_id_2 = nc2.id
            print(f"  {s.scheduled_date} [{old}] -> [其他]")
        else:
            print(f"  {s.scheduled_date} 已是[其他] ✓")
    
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
            print(f"  {s.scheduled_date} [{old}] -> [{new_t.name}]")
    
    db.session.commit()
    
    # 验证
    print(f"\n[验证] EMBA130")
    scheds = ClassSchedule.query.filter(
        ClassSchedule.class_id == cls_id, ClassSchedule.status != 'cancelled'
    ).order_by(ClassSchedule.scheduled_date).all()
    issues = []
    for s in scheds:
        if s.combo and s.combo.topic_id != s.topic_id:
            issues.append(f"D1 {s.scheduled_date}")
        if s.combo_2 and s.combo_2.topic_id != s.topic_id:
            issues.append(f"D2 {s.scheduled_date}")
    tc = Counter(s.topic.name for s in scheds if not s.topic.is_other)
    dups = {k:v for k,v in tc.items() if v > 1}
    empty = sum(1 for s in scheds if not s.combo)
    
    if not issues and not dups and empty == 0:
        print("  全部OK ✅")
    else:
        if dups: print(f"  重复: {dups}")
        if issues: print(f"  错配: {issues}")
        if empty: print(f"  空combo: {empty}")
    
    for s in scheds:
        tn = s.topic.name if s.topic else '?'
        is_other = '[其他]' if s.topic and s.topic.is_other else ''
        print(f"  {s.scheduled_date} wk={s.week_number} [{tn}] {is_other}")
