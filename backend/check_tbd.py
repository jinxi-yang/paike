from app import create_app
from models import db, TeacherCourseCombo, Teacher, Course

app = create_app()
with app.app_context():
    teachers = Teacher.query.filter_by(name='待定').all()
    print("Teachers named 待定:", teachers)
    combos = TeacherCourseCombo.query.all()
    has_tbd = False
    for c in combos:
        if c.teacher and c.teacher.name == '待定':
            print("Found combo with TBD teacher:", c.id, "Course:", c.course.name if c.course else None)
            has_tbd = True
    if not has_tbd:
        print("No combo with TBD teacher.")
