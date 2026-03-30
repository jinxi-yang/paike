import sqlite3
from app import app
from models import ClassSchedule, Class, db

with app.app_context():
    # Find all scheduled records with topic_id=1
    wrong_schedules = ClassSchedule.query.filter(ClassSchedule.topic_id == 1, db.or_(ClassSchedule.status == 'scheduled', ClassSchedule.status.is_(None))).all()
    print(f"Found {len(wrong_schedules)} schedules with topic_id=1 (status=scheduled or None)")
    
    for s in wrong_schedules:
        # check if this class already completed topic_id=1
        completed = ClassSchedule.query.filter(ClassSchedule.class_id == s.class_id, ClassSchedule.topic_id == 1, ClassSchedule.status == 'completed').first()
        if completed:
            cname = s.class_.name if s.class_ else '?'
            print(f"Warning: Class {cname} has a scheduled/None record for Topic 1 on {s.scheduled_date}, but ALREADY COMPLETED it on {completed.scheduled_date}!")
            # We can automatically try to fix its topic ID to the class's next uncompleted topic sequence!
            # But let's just list them for now.
    
    # Are there any other topics wrongly assigned?
    # Our batch scripts ONLY hardcoded topic_id=1 or 2 sometimes.
