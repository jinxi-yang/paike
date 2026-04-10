"""
批次1补充修复:
1. EMBA126 4/18: 董俊豪/待定 + 易正/待定 (领导力)
2. EMBA126 5/23 D2: 王薇华/待定 (品牌营销)
3. EMBA126 7/5 删除多余的企业数字化变革记录
4. EMBA127 9/27: 刘春华/AI时代下的新营销九段法 (人工智能)
5. 开学典礼D1: 设置院长/院长课 + 事件标志
"""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from datetime import date
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
        topic_name = Topic.query.get(topic_id).name
        print(f"  [NEW COMBO] combo_id={combo.id}: [{topic_name}] {teacher_name}/{course_name}")
    else:
        print(f"  [EXISTING] combo_id={combo.id}: {teacher_name}/{course_name}")
    return combo

def fix_schedule(class_id, date_str, day, topic_id, teacher_name, course_name):
    y, m, d = map(int, date_str.split('-'))
    sch = ClassSchedule.query.filter_by(class_id=class_id, scheduled_date=date(y, m, d)).first()
    if not sch:
        print(f"  [SKIP] 未找到 class_id={class_id} date={date_str}")
        return None
    combo = find_or_create_combo(topic_id, teacher_name, course_name)
    if day == 1:
        old = sch.combo_id
        sch.combo_id = combo.id
        print(f"  [FIX D1] schedule_id={sch.id} combo_id: {old} -> {combo.id}")
    else:
        old = sch.combo_id_2
        sch.combo_id_2 = combo.id
        print(f"  [FIX D2] schedule_id={sch.id} combo_id_2: {old} -> {combo.id}")
    return sch

with app.app_context():
    topics = {t.name: t.id for t in Topic.query.all()}
    T_AI      = topics['人工智能与商业应用']
    T_DIGITAL = topics['企业数字化变革与数智创新']
    T_LEADER  = topics['领导力与团队建设']
    T_BRAND   = topics['品牌营销与数智化营销']
    T_OTHER   = topics['其他']

    # === 1. EMBA126 4/18: 董俊豪/待定 + 易正/待定 (领导力) ===
    print("="*60)
    print("1. EMBA126 4/18 领导力: 董俊豪/待定 + 易正/待定")
    print("="*60)
    fix_schedule(4, '2026-04-18', 1, T_LEADER, '董俊豪', '待定')
    fix_schedule(4, '2026-04-18', 2, T_LEADER, '易正', '待定')

    # === 2. EMBA126 5/23 D2: 王薇华/待定 (品牌营销) ===
    print("\n" + "="*60)
    print("2. EMBA126 5/23 D2: 王薇华/待定")
    print("="*60)
    fix_schedule(4, '2026-05-23', 2, T_BRAND, '王薇华', '待定')

    # === 3. 删除EMBA126 7/5多余的企业数字化变革记录 ===
    print("\n" + "="*60)
    print("3. 删除EMBA126 7/5多余记录")
    print("="*60)
    orphan = ClassSchedule.query.filter_by(
        class_id=4, scheduled_date=date(2025, 7, 5)
    ).filter(ClassSchedule.topic_id == topics['企业数字化变革与数智创新']).first()
    if orphan:
        print(f"  [DELETE] schedule_id={orphan.id} topic=企业数字化变革 date=2025-07-05 (多余记录)")
        db.session.delete(orphan)
    else:
        print("  [SKIP] 未找到多余记录")

    # === 4. EMBA127 9/27: 刘春华/AI时代下的新营销九段法 (人工智能) ===
    print("\n" + "="*60)
    print("4. EMBA127 9/27: 刘春华 两天相同")
    print("="*60)
    fix_schedule(5, '2025-09-27', 1, T_AI, '刘春华', 'AI时代下的新营销九段法')
    fix_schedule(5, '2025-09-27', 2, T_AI, '刘春华', 'AI时代下的新营销九段法')

    # === 5. 开学典礼D1: 院长/院长课 + 事件标志 ===
    print("\n" + "="*60)
    print("5. 开学典礼D1修复: 院长/院长课 + 事件标志")
    print("="*60)

    opening_fixes = [
        # (class_id, date_str, topic_id, events_on_d1)
        (1, '2025-04-12', T_DIGITAL, {'has_opening': True, 'has_team_building': True}),
        (3, '2025-05-17', T_DIGITAL, {'has_opening': True, 'has_team_building': True}),
        (5, '2025-06-28', T_LEADER,  {'has_opening': True, 'has_team_building': True}),
    ]
    for cls_id, dt, topic_id, events in opening_fixes:
        sch = fix_schedule(cls_id, dt, 1, topic_id, '院长', '院长课')
        if sch:
            for k, v in events.items():
                old_val = getattr(sch, k)
                if not old_val:
                    setattr(sch, k, v)
                    print(f"  [FLAG] schedule_id={sch.id} {k}: {old_val} -> {v}")

    db.session.commit()
    print("\n" + "="*60)
    print("补充修复全部完成!")
    print("="*60)
