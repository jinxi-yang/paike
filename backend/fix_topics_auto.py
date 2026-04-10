"""
自动修复课题分配：确保每个班8个核心课题各一次，>8的归其他，combo都匹配
算法：
1. 按日期排序，>8的后面归其他
2. 每个combo查找它最可能的"原始课题"(最早的combo记录)
3. 贪心分配：优先用自然匹配，冲突时用缺失课题填充
"""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from app import app
from models import db, ClassSchedule, TeacherCourseCombo, Teacher, Topic
from collections import Counter

def get_natural_topic_for_combo(combo):
    """找到同一讲师+课程名的最早combo，其topic_id就是'自然课题'"""
    if not combo:
        return None
    earliest = TeacherCourseCombo.query.filter_by(
        teacher_id=combo.teacher_id, course_name=combo.course_name
    ).order_by(TeacherCourseCombo.id).first()
    return earliest.topic_id if earliest else combo.topic_id

def find_or_create_combo(topic_id, teacher_id, course_name):
    combo = TeacherCourseCombo.query.filter_by(
        topic_id=topic_id, teacher_id=teacher_id, course_name=course_name
    ).first()
    if not combo:
        combo = TeacherCourseCombo(topic_id=topic_id, teacher_id=teacher_id, course_name=course_name)
        db.session.add(combo)
        db.session.flush()
    return combo

def reassign_schedule_topic(sch, new_topic_id):
    """修改schedule的topic并迁移combo"""
    if sch.topic_id == new_topic_id:
        return  # 已是正确课题
    
    old_name = sch.topic.name if sch.topic else '?'
    new_topic = db.session.get(Topic, new_topic_id)
    
    sch.topic_id = new_topic_id
    
    if sch.combo:
        new_c = find_or_create_combo(new_topic_id, sch.combo.teacher_id, sch.combo.course_name)
        sch.combo_id = new_c.id
    if sch.combo_2:
        new_c2 = find_or_create_combo(new_topic_id, sch.combo_2.teacher_id, sch.combo_2.course_name)
        sch.combo_id_2 = new_c2.id
    
    print(f"    {sch.scheduled_date} [{old_name}] -> [{new_topic.name}]")

def auto_fix_class(class_id, class_name):
    print(f"\n{'='*60}")
    print(f"{class_name} (ID={class_id})")
    print(f"{'='*60}")
    
    schedules = ClassSchedule.query.filter(
        ClassSchedule.class_id == class_id,
        ClassSchedule.status != 'cancelled'
    ).order_by(ClassSchedule.scheduled_date).all()
    
    if not schedules:
        print("  无排课记录")
        return
    
    cls = schedules[0].class_
    project_id = cls.project_id
    
    # 获取所有核心课题
    core_topics = Topic.query.filter_by(project_id=project_id).filter(
        Topic.is_other != True
    ).order_by(Topic.sequence).all()
    core_topic_ids = {t.id for t in core_topics}
    other_topic = Topic.query.filter_by(project_id=project_id, is_other=True).first()
    
    n = len(schedules)
    print(f"  共{n}节课, 核心课题{len(core_topics)}个")
    
    # Step 1: >8的归其他
    core_scheds = schedules[:8]
    extra_scheds = schedules[8:]
    
    if extra_scheds:
        print(f"\n  [Step 1] {len(extra_scheds)}节超出8课 → 改【其他】")
        for s in extra_scheds:
            if s.topic_id != other_topic.id:
                reassign_schedule_topic(s, other_topic.id)
            else:
                print(f"    {s.scheduled_date} 已是[其他] ✓")
    
    # Step 2: 为前8课确定最佳课题
    print(f"\n  [Step 2] 分配核心课题")
    
    # 每个schedule的"自然课题"(基于combo)
    natural = {}
    for s in core_scheds:
        nat = get_natural_topic_for_combo(s.combo) if s.combo else s.topic_id
        natural[s.id] = nat
    
    # 贪心分配：先处理自然课题唯一的，再处理冲突的
    assigned = {}    # topic_id -> schedule
    conflicts = []   # 自然课题已被占用的schedule
    
    # 第一轮：自然课题无冲突的直接分配
    for s in core_scheds:
        nat = natural[s.id]
        if nat in core_topic_ids and nat not in assigned:
            assigned[nat] = s
        else:
            conflicts.append(s)
    
    # 找出缺失的核心课题
    missing = [t.id for t in core_topics if t.id not in assigned]
    
    # 第二轮：冲突的用缺失课题填充
    for s, tid in zip(conflicts, missing):
        assigned[tid] = s
    
    # 如果还有剩余冲突(不应该发生)
    if len(conflicts) > len(missing):
        print(f"  ⚠️ 异常: {len(conflicts)}个冲突 > {len(missing)}个缺失")
        for s in conflicts[len(missing):]:
            assigned[other_topic.id] = s
    
    # 应用分配
    changes = 0
    for topic_id, s in assigned.items():
        if s.topic_id != topic_id:
            reassign_schedule_topic(s, topic_id)
            changes += 1
        else:
            tn = s.topic.name if s.topic else '?'
            print(f"    {s.scheduled_date} [{tn}] ✓ 无需变更")
    
    if changes == 0:
        print("  全部课题已正确 ✓")
    
    # 验证
    print(f"\n  [验证]")
    all_s = ClassSchedule.query.filter(
        ClassSchedule.class_id == class_id,
        ClassSchedule.status != 'cancelled'
    ).order_by(ClassSchedule.scheduled_date).all()
    tc = Counter()
    for s in all_s:
        if s.topic and not s.topic.is_other:
            tc[s.topic.name] += 1
    dups = {k:v for k,v in tc.items() if v > 1}
    if dups:
        print(f"  ⚠️ 仍有重复: {dups}")
    else:
        print(f"  ✓ 核心课题无重复")
    
    used = {s.topic.name for s in all_s if s.topic and not s.topic.is_other}
    all_core = {t.name for t in core_topics}
    miss = all_core - used
    if miss:
        print(f"  ⚠️ 仍缺主题: {miss}")
    else:
        print(f"  ✓ 所有核心课题齐全")

with app.app_context():
    classes_to_fix = [
        (1, "EMBA122期"),
        (2, "EMBA123期"),
        (3, "EMBA125期"),
        (4, "EMBA126期"),
        (5, "EMBA127期"),
    ]
    
    for cid, name in classes_to_fix:
        auto_fix_class(cid, name)
    
    db.session.commit()
    print("\n\n" + "="*60)
    print("全部修复完成!")
    print("="*60)
