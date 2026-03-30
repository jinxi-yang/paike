from app import app
from models import Class, ClassSchedule, Topic, db
from sqlalchemy import or_

with app.app_context():
    for cid in [4, 5, 10]:
        cls = Class.query.get(cid)
        print(f"\n--- Class {cls.name} ---")
        
        all_topics = list(cls.project.topics.order_by(Topic.sequence.asc()).all())
        print("All Topics:")
        for t in all_topics:
            print(f"  Seq {t.sequence}: {t.name} (ID: {t.id})")
            
        last_completed = ClassSchedule.query.filter(
            ClassSchedule.class_id == cls.id,
            or_(
                ClassSchedule.status == 'completed',
                db.and_(
                    ClassSchedule.status == 'scheduled',
                    ClassSchedule.scheduled_date < '2026-04-01'
                )
            )
        ).join(Topic).order_by(Topic.sequence.desc()).first()
        
        if last_completed:
            print(f"Last Completed: {last_completed.topic.name} (Seq {last_completed.topic.sequence})")
            current_seq = last_completed.topic.sequence
            next_topic = None
            for t in all_topics:
                if t.sequence > current_seq:
                    next_topic = t
                    break
        else:
            print("No Last Completed!")
            next_topic = all_topics[0] if all_topics else None
            
        print(f"Next Topic chosen by new algorithm: {next_topic.name if next_topic else None}")
