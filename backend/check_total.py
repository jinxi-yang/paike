from app import app
from models import db, ClassSchedule, Topic

with app.app_context():
    cls_sch = ClassSchedule.query.filter(ClassSchedule.class_.has(name='北清EMBA123期')).first()
    if cls_sch:
        cls_id = cls_sch.class_id
        core = Topic.query.filter_by(project_id=cls_sch.class_.project_id, is_other=False).count()
        other_cc = ClassSchedule.query.join(Topic).filter(
            ClassSchedule.class_id == cls_id, 
            db.or_(ClassSchedule.status != 'cancelled', ClassSchedule.status.is_(None)), 
            Topic.is_other == True
        ).count()
        print(f"Total: {core} + {other_cc} = {core + other_cc}")
