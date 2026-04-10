"""
EMBA127 课题修正:
- 企业数字化变革出现3次 → 保留4/18(课次7),  6/27(课次9)和8/1(课次10)改为【其他】(超出8课的)
- 财务管理出现2次, 缺销售管理 → 需要确认哪个改(先不动)
"""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from datetime import date
from app import app
from models import db, ClassSchedule, TeacherCourseCombo, Teacher, Topic

def find_or_create_combo_under_topic(topic_id, teacher_id, course_name):
    combo = TeacherCourseCombo.query.filter_by(
        topic_id=topic_id, teacher_id=teacher_id, course_name=course_name
    ).first()
    if not combo:
        combo = TeacherCourseCombo(topic_id=topic_id, teacher_id=teacher_id, course_name=course_name)
        db.session.add(combo)
        db.session.flush()
        topic = Topic.query.get(topic_id)
        teacher = Teacher.query.get(teacher_id)
        print(f"  [NEW COMBO] combo_id={combo.id}: [{topic.name}] {teacher.name}/{course_name}")
    else:
        print(f"  [EXISTING] combo_id={combo.id}")
    return combo

def reassign_topic(sch, new_topic_id):
    old_topic = sch.topic.name if sch.topic else '?'
    new_topic = Topic.query.get(new_topic_id)
    print(f"\n  schedule_id={sch.id} date={sch.scheduled_date}")
    print(f"  课题: [{old_topic}] -> [{new_topic.name}]")
    
    sch.topic_id = new_topic_id
    
    if sch.combo:
        new_c = find_or_create_combo_under_topic(new_topic_id, sch.combo.teacher_id, sch.combo.course_name)
        sch.combo_id = new_c.id
    if sch.combo_2:
        new_c2 = find_or_create_combo_under_topic(new_topic_id, sch.combo_2.teacher_id, sch.combo_2.course_name)
        sch.combo_id_2 = new_c2.id

with app.app_context():
    T_OTHER = Topic.query.filter_by(is_other=True).first().id
    
    print("="*60)
    print("EMBA127 (ID=5): 企业数字化变革 课次9(6/27)和课次10(8/1) → 改【其他】")
    print("="*60)
    
    # 课次9: 2026-06-27 (schedule_id=41) 熊郭健 → 改其他
    sch9 = ClassSchedule.query.get(41)
    reassign_topic(sch9, T_OTHER)
    
    # 课次10: 2026-08-01 (schedule_id=195) 杨波+易正 → 改其他
    sch10 = ClassSchedule.query.get(195)
    reassign_topic(sch10, T_OTHER)
    
    db.session.commit()
    
    # 验证
    print("\n\n--- 修复后EMBA127课题分布 ---")
    from collections import Counter
    scheds = ClassSchedule.query.filter_by(class_id=5).filter(ClassSchedule.status != 'cancelled').order_by(ClassSchedule.scheduled_date).all()
    for s in scheds:
        t = s.topic
        print(f"  {s.scheduled_date} [{t.name}] {'[其他]' if t.is_other else ''}")
    
    tc = Counter(s.topic.name for s in scheds if not s.topic.is_other)
    dups = {k:v for k,v in tc.items() if v > 1}
    if dups:
        print(f"\n  仍有重复: {dups}")
    else:
        print(f"\n  核心课题无重复 ✓")
