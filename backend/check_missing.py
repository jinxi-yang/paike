from app import app
from models import ClassSchedule

with app.app_context():
    missing_ids = [175, 176, 185]
    for mid in missing_ids:
        s = ClassSchedule.query.get(mid)
        if s:
            print(f"ID {mid} still exists! Date={s.scheduled_date}, Status={s.status}, ClassId={s.class_id}")
        else:
            print(f"ID {mid} is completely DELETED from the database.")
            
    print("\nLet's check if there are other ClassSchedule records for Class IDs 4, 5, 10")
    for cid in [4, 5, 10]:
        schedules = ClassSchedule.query.filter_by(class_id=cid).all()
        print(f"\nClass ID {cid} schedules: {len(schedules)}")
        for s in schedules:
            print(f" - ID={s.id}, Date={s.scheduled_date}, Status={s.status}, Topic={s.topic.name if s.topic else '?'}")
