from app import app
from models import Class, ClassSchedule, db, Topic

with app.app_context():
    active_classes = Class.query.filter(Class.status.in_(['active', 'planning'])).all()
    print(f'Total active/planning classes: {len(active_classes)}')
    
    count_schedulable = 0
    for cls in active_classes:
        schedules = ClassSchedule.query.filter(ClassSchedule.class_id == cls.id, db.or_(ClassSchedule.status == 'completed', db.and_(ClassSchedule.status == 'scheduled', ClassSchedule.scheduled_date < '2026-04-01'))).all()
        sch_topics = {s.topic_id for s in schedules}
        all_topics = list(cls.project.topics.order_by(Topic.sequence.asc()).all()) if cls.project else []
        next_topic = next((t for t in all_topics if t.id not in sch_topics), None)
        
        # Check if next_topic has combo
        from models import TeacherCourseCombo
        has_combo = False
        if next_topic:
            has_combo = TeacherCourseCombo.query.filter_by(topic_id=next_topic.id).count() > 0
            if has_combo:
                count_schedulable += 1
            
        print(f'{cls.name} -> Next Topic: {next_topic.name if next_topic else None} (Has Combo: {has_combo})')
        
    print(f'\nTotal classes that can be scheduled (has next topic & combo): {count_schedulable}')
