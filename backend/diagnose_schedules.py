"""
排课数据诊断脚本
列出每个班每节课的：课题、讲师、课程名、是否匹配
"""
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from app import app
from models import db, Class, ClassSchedule, Topic, TeacherCourseCombo

STATUS_OK       = "[OK]    正常"
STATUS_MISMATCH = "[WARN]  不匹配(combo挂错topic)"
STATUS_BROKEN   = "[ERR]   combo已失效(id存在但记录不存在)"
STATUS_EMPTY    = "[EMPTY] 待定(无combo)"

def check_combo(schedule, combo, combo_id, day_label):
    if combo_id and not combo:
        return STATUS_BROKEN, None, None, None
    if not combo_id:
        return STATUS_EMPTY, None, None, None
    if combo.topic_id != schedule.topic_id:
        return STATUS_MISMATCH, combo.teacher.name if combo.teacher else "?", combo.course_name, combo.topic_id
    return STATUS_OK, combo.teacher.name if combo.teacher else "?", combo.course_name, combo.topic_id

with app.app_context():
    classes = Class.query.order_by(Class.id).all()
    
    total_sessions = 0
    problem_sessions = 0
    
    for cls in classes:
        schedules = ClassSchedule.query.filter(
            ClassSchedule.class_id == cls.id,
            ClassSchedule.status != 'cancelled'
        ).order_by(ClassSchedule.scheduled_date).all()
        
        if not schedules:
            continue

        has_problem = any(
            check_combo(s, s.combo, s.combo_id, 'D1')[0] != STATUS_OK or
            check_combo(s, s.combo_2, s.combo_id_2, 'D2')[0] not in (STATUS_OK, STATUS_EMPTY)
            for s in schedules
        )
        
        print(f"\n{'='*70}")
        print(f"班级: {cls.name}  (ID={cls.id}, 项目={cls.project.name if cls.project else '?'})")
        print(f"{'='*70}")
        print(f"{'日期':<12} {'课题':<16} {'状态-D1':<10} {'讲师':<8} {'课程名':<20} {'状态-D2':<10} {'D2讲师':<8} {'D2课程':<20}")
        print(f"{'-'*120}")
        
        for s in schedules:
            topic_name = s.topic.name if s.topic else f"topic#{s.topic_id}"
            topic_is_other = s.topic.is_other if s.topic else False
            
            d1_status, d1_teacher, d1_course, d1_combo_topic = check_combo(s, s.combo, s.combo_id, 'D1')
            d2_status, d2_teacher, d2_course, d2_combo_topic = check_combo(s, s.combo_2, s.combo_id_2, 'D2')
            
            d1_ok = d1_status == STATUS_OK
            d2_ok = d2_status in (STATUS_OK, STATUS_EMPTY)
            
            total_sessions += 1
            if not d1_ok or not d2_ok:
                problem_sessions += 1
            
            flag = "" if (d1_ok and d2_ok) else "  ← 问题"
            
            print(f"{s.scheduled_date.isoformat():<12} {topic_name[:16]:<16} "
                  f"{d1_status[:8]:<10} {(d1_teacher or '-')[:8]:<8} {(d1_course or '-')[:20]:<20} "
                  f"{d2_status[:8]:<10} {(d2_teacher or '-')[:8]:<8} {(d2_course or '-')[:20]:<20}{flag}")
            
            # 打印不匹配细节
            if d1_status == STATUS_MISMATCH:
                wrong_topic = Topic.query.get(d1_combo_topic)
                print(f"           └─ D1 combo属于课题: [{wrong_topic.name if wrong_topic else '?'}]  ← 应属于: [{topic_name}]")
            if d2_status == STATUS_MISMATCH:
                wrong_topic = Topic.query.get(d2_combo_topic)
                print(f"           └─ D2 combo属于课题: [{wrong_topic.name if wrong_topic else '?'}]  ← 应属于: [{topic_name}]")
    
    print(f"\n{'='*70}")
    print(f"汇总: 共 {total_sessions} 节课，其中 {problem_sessions} 节有问题")
    print(f"{'='*70}")
