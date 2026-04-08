from app import app
from models import db, ClassSchedule

with app.app_context():
    all_s = ClassSchedule.query.filter(ClassSchedule.status != 'cancelled').all()
    c = 0
    i = []
    for s in all_s:
        if not s.topic_id: continue
        if (s.combo and s.combo.topic_id != s.topic_id) or (s.combo_2 and s.combo_2.topic_id != s.topic_id):
            c += 1
            i.append(f"【{s.class_.name}】{s.scheduled_date}")
    
    print(f"Total invalid rows in DB: {c}")
    for item in i[:10]:
        print(item)
