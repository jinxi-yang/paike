"""全面验证已修复的15个班(ID=1-15)的所有维度"""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
from collections import Counter
from app import app
from models import db, ClassSchedule, TeacherCourseCombo, Teacher, Topic

with app.app_context():
    all_ok = True
    for cid in range(1, 21):
        ss = ClassSchedule.query.filter(
            ClassSchedule.class_id == cid, ClassSchedule.status != 'cancelled'
        ).order_by(ClassSchedule.scheduled_date).all()
        if not ss: continue
        name = ss[0].class_.name
        errors = []

        # 1. 空combo检查
        for s in ss:
            if not s.combo:
                errors.append(f"  空D1 combo: {s.scheduled_date}")

        # 2. combo-topic匹配检查
        for s in ss:
            if s.combo and s.combo.topic_id != s.topic_id:
                errors.append(f"  D1 combo课题错配: {s.scheduled_date} "
                    f"combo在[{s.combo.topic.name}] 排课在[{s.topic.name}]")
            if s.combo_2 and s.combo_2.topic_id != s.topic_id:
                errors.append(f"  D2 combo课题错配: {s.scheduled_date} "
                    f"combo在[{s.combo_2.topic.name}] 排课在[{s.topic.name}]")

        # 3. 核心课题不重复(非其他)
        tc = Counter()
        for s in ss:
            if s.topic and not s.topic.is_other:
                tc[s.topic.name] += 1
        dups = {k: v for k, v in tc.items() if v > 1}
        if dups:
            errors.append(f"  核心课题重复: {dups}")

        # 4. 8个核心课题齐全
        proj_id = ss[0].class_.project_id
        core = {t.name for t in Topic.query.filter_by(project_id=proj_id).filter(Topic.is_other != True)}
        used = {s.topic.name for s in ss if s.topic and not s.topic.is_other}
        missing = core - used
        if missing:
            errors.append(f"  缺失核心课题: {missing}")

        # 5. combo的讲师存在
        for s in ss:
            if s.combo and not s.combo.teacher:
                errors.append(f"  D1 combo讲师不存在: {s.scheduled_date}")
            if s.combo_2 and not s.combo_2.teacher:
                errors.append(f"  D2 combo讲师不存在: {s.scheduled_date}")

        # 6. combo课程名不为空
        for s in ss:
            if s.combo and not s.combo.course_name:
                errors.append(f"  D1 combo课程名空: {s.scheduled_date}")
            if s.combo_2 and not s.combo_2.course_name:
                errors.append(f"  D2 combo课程名空: {s.scheduled_date}")

        if errors:
            all_ok = False
            print(f"\n[!!] {name} (ID={cid}) — {len(errors)}个问题:")
            for e in errors:
                print(e)
        else:
            n_core = sum(1 for s in ss if not s.topic.is_other)
            n_other = sum(1 for s in ss if s.topic.is_other)
            n_d2 = sum(1 for s in ss if s.combo_2)
            print(f"[OK] {name} (ID={cid}): {len(ss)}节课({n_core}核心+{n_other}其他), D2有{n_d2}个")

    if all_ok:
        print(f"\n{'='*60}")
        print("15个班全部验证通过! 所有维度闭环!")
        print("="*60)
    else:
        print(f"\n{'='*60}")
        print("存在问题，请检查")
        print("="*60)
