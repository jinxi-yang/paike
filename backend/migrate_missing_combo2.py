from app import create_app
from models import db, ClassSchedule

def migrate():
    app = create_app()
    with app.app_context():
        # Find all scheduled/completed classes where combo_id is set but combo_id_2 is null
        schedules = ClassSchedule.query.filter(
            ClassSchedule.combo_id.isnot(None),
            ClassSchedule.combo_id_2.is_(None)
        ).all()
        
        count = 0
        for s in schedules:
            s.combo_id_2 = s.combo_id
            count += 1
            
        db.session.commit()
        print(f"Migrated {count} schedules to explicitly set combo_id_2 = combo_id")

if __name__ == '__main__':
    migrate()
