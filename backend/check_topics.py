from app import app
from models import db, ClassSchedule, Topic
import json

with app.app_context():
    cls_sch = ClassSchedule.query.filter(ClassSchedule.class_.has(name='北清EMBA123期')).first()
    if cls_sch and cls_sch.class_ and cls_sch.class_.project:
        cls = cls_sch.class_
        print("Project Name:", cls.project.name)
        topics = cls.project.topics.order_by(Topic.sequence).all()
        for t in topics:
            print(f"ID: {t.id}, Seq: {t.sequence}, Name: {t.name}, is_other: {t.is_other}")
    else:
        print("Could not load class 北清EMBA123期")
