from app import create_app
from models import ClassSchedule, Class

app = create_app()
with app.app_context():
    cls = Class.query.filter(Class.name.like('%130%')).first()
    if not cls:
        print("Class not found")
    else:
        print(f"Class: {cls.name}")
        schedules = ClassSchedule.query.filter_by(class_id=cls.id).order_by(ClassSchedule.scheduled_date).all()
        print(f"\n{'课次':>4}  {'日期':<12}  {'状态':^8}  {'第一天讲师':<12}  {'第一天课程':<20}  {'combo_id':>8}  {'第二天讲师':<12}  {'第二天课程':<20}  {'combo_id_2':>10}")
        print("-" * 110)
        for s in schedules:
            t1 = s.combo.teacher.name if s.combo and s.combo.teacher else '(无)'
            c1 = s.combo.course_name if s.combo else '(无)'
            t2 = s.combo_2.teacher.name if s.combo_2 and s.combo_2.teacher else '(null)'
            c2 = s.combo_2.course_name if s.combo_2 else '(null)'
            print(f"{s.week_number or '-':>4}  {str(s.scheduled_date):<12}  {s.status:^8}  {t1:<12}  {c1:<20}  {s.combo_id or '':>8}  {t2:<12}  {c2:<20}  {s.combo_id_2 or 'null':>10}")
