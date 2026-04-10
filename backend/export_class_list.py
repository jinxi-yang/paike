"""导出所有班级列表和课题/combo信息"""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from app import app
from models import db, Class, ClassSchedule, Topic, TeacherCourseCombo

with app.app_context():
    # 1. 所有班级
    print("="*60)
    print("所有班级:")
    print("="*60)
    for c in Class.query.order_by(Class.id).all():
        sch_count = ClassSchedule.query.filter(
            ClassSchedule.class_id == c.id,
            ClassSchedule.status != 'cancelled'
        ).count()
        print(f"  ID={c.id:>3}  {c.name:<25}  项目={c.project.name if c.project else '?'}  课次={sch_count}")
    
    # 2. 所有课题
    print(f"\n{'='*60}")
    print("所有课题:")
    print("="*60)
    for t in Topic.query.order_by(Topic.project_id, Topic.sequence).all():
        combo_count = TeacherCourseCombo.query.filter_by(topic_id=t.id).count()
        print(f"  ID={t.id:>3}  seq={t.sequence}  {'[其他]' if t.is_other else ''} {t.name:<30}  项目ID={t.project_id}  combo数={combo_count}")
    
    # 3. 所有combo
    print(f"\n{'='*60}")
    print("所有教-课组合:")
    print("="*60)
    for combo in TeacherCourseCombo.query.order_by(TeacherCourseCombo.topic_id).all():
        t_name = combo.topic.name if combo.topic else '?'
        teacher_name = combo.teacher.name if combo.teacher else '?'
        print(f"  combo_id={combo.id:>3}  课题=[{t_name}]  讲师={teacher_name}  课程={combo.course_name}")
