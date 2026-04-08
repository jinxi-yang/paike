from app import create_app
from models import ClassSchedule
from collections import Counter

app = create_app()
with app.app_context():
    recs = ClassSchedule.query.filter(
        ClassSchedule.combo_id != None,
        ClassSchedule.combo_id_2 == None
    ).all()
    print(f'Total records with combo_id set but combo_id_2 null: {len(recs)}')
    by_class = Counter(s.class_.name if s.class_ else '?' for s in recs)
    print('\nBreakdown by class:')
    for name, cnt in sorted(by_class.items(), key=lambda x: -x[1]):
        print(f'  {name}: {cnt}条')
    print(f'\nTotal distinct classes: {len(by_class)}')
    
    # Also show status breakdown
    by_status = Counter(s.status for s in recs)
    print(f'\nStatus breakdown: {dict(by_status)}')
