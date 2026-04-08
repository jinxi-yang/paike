from app import create_app
from models import db, ClassSchedule

def rollback():
    app = create_app()
    with app.app_context():
        # Revert records where combo_id_2 == combo_id (those we just incorrectly filled in)
        # We distinguish them because they are exactly equal - users who genuinely set the same
        # teacher for both days would have combo_id_2 set to a different (or same) ID explicitly.
        # The only safe revert: set combo_id_2 back to None where combo_id_2 == combo_id
        schedules = ClassSchedule.query.filter(
            ClassSchedule.combo_id.isnot(None),
            ClassSchedule.combo_id_2.isnot(None)
        ).all()

        count = 0
        for s in schedules:
            if s.combo_id_2 == s.combo_id:
                s.combo_id_2 = None
                count += 1

        db.session.commit()
        print(f"Rolled back {count} schedules, restored combo_id_2 = None")

if __name__ == '__main__':
    rollback()
