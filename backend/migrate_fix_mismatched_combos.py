from app import app
from models import db, ClassSchedule, TeacherCourseCombo

def count_invalids(schedules):
    c = 0
    for s in schedules:
        if not s.topic_id: continue
        if (s.combo and s.combo.topic_id != s.topic_id) or (s.combo_2 and s.combo_2.topic_id != s.topic_id):
            c += 1
    return c

with app.app_context():
    all_s = ClassSchedule.query.filter(ClassSchedule.status != 'cancelled').all()
    initial_count = count_invalids(all_s)
    print(f"检测到 {initial_count} 条遗留不匹配记录。开始执行自动修复...\n")
    
    fixed_count = 0
    cleared_count = 0
    
    for s in all_s:
        if not s.topic_id: continue
        
        # 处理 Day 1
        if s.combo and s.combo.topic_id != s.topic_id:
            old_combo = s.combo
            valid_combo = TeacherCourseCombo.query.filter_by(
                topic_id=s.topic_id,
                teacher_id=old_combo.teacher_id,
                course_name=old_combo.course_name
            ).first()
            
            if valid_combo:
                s.combo_id = valid_combo.id
                fixed_count += 1
            else:
                s.combo_id = None
                cleared_count += 1
                
        # 处理 Day 2
        if s.combo_2 and s.combo_2.topic_id != s.topic_id:
            old_combo = s.combo_2
            valid_combo = TeacherCourseCombo.query.filter_by(
                topic_id=s.topic_id,
                teacher_id=old_combo.teacher_id,
                course_name=old_combo.course_name
            ).first()
            
            if valid_combo:
                s.combo_id_2 = valid_combo.id
                fixed_count += 1
            else:
                s.combo_id_2 = None
                cleared_count += 1
                
    db.session.commit()
    print("--------------------------------------------------")
    print(f"修复完成！")
    print(f"- 完美平替（新课题下存在同名讲师/课程组合）：{fixed_count} 条")
    print(f"- 安全清空（新课题下不存在同名组合，已清空处理防止报错）：{cleared_count} 条")
    print("--------------------------------------------------")
    
    remaining = count_invalids(ClassSchedule.query.filter(ClassSchedule.status != 'cancelled').all())
    print(f"最终校验：剩余 {remaining} 条不匹配记录。")

