from app import app
from models import ClassSchedule, Class, db

with app.app_context():
    # Query all records in April
    schedules = ClassSchedule.query.filter(
        ClassSchedule.scheduled_date >= '2026-04-01',
        ClassSchedule.scheduled_date < '2026-05-01'
    ).order_by(ClassSchedule.scheduled_date).all()
    
    print(f'Total April Schedule Records: {len(schedules)}')
    for s in schedules:
        cname = s.class_.name if s.class_ else 'Unknown'
        topic_name = s.topic.name if s.topic else 'Unknown'
        print(f"ID={s.id} | Class={cname} | Date={s.scheduled_date} | Status={s.status} | Merged={s.merged_with} | Notes={s.notes}")

    # Query all records across all time to see if April classes got moved
    print("\n--- Let's find classes that might have been moved out of April ---")
    all_schedules = ClassSchedule.query.order_by(ClassSchedule.scheduled_date).all()
    # Just show a summary or recent ones that could have been in April
    # For a small DB it's fine
