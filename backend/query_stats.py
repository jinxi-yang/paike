import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
from app import app
from models import db, ClassSchedule

with app.app_context():
    scheds = ClassSchedule.query.filter(ClassSchedule.status != 'cancelled').all()
    total = len(scheds)
    
    d2_empty = [s for s in scheds if not s.combo_2]
    
    print(f"总课表数据条数: {total}")
    print(f"第二天没课的条数: {len(d2_empty)}")
    
    for s in d2_empty:
        tn = s.combo.teacher.name if s.combo and s.combo.teacher else "?"
        cn = s.combo.course_name if s.combo else "?"
        cls_name = s.class_.name
        print(f"  - {cls_name} | {s.scheduled_date} | D1有课: {tn}/{cn}")
