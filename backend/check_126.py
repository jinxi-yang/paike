from app import app
from models import ClassSchedule, Class

with app.app_context():
    cls = Class.query.filter(Class.name.like('%126%')).first()
    print(f"Class: {cls.name}")
    schedules = ClassSchedule.query.filter_by(class_id=cls.id).all()
    for s in schedules:
        print(f"  ID={s.id} | Date={s.scheduled_date} | Status={s.status} | TopicID={s.topic_id} | TopicName={s.topic.name if s.topic else 'None'}")
