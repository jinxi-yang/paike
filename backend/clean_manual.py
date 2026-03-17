import sys, os
os.chdir(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, '.')
from app import create_app
from models import db, ClassSchedule

app = create_app()
with app.app_context():
    manuals = ClassSchedule.query.filter(ClassSchedule.conflict_type == 'manual').all()
    print(f'Found {len(manuals)} records with conflict_type=manual')
    for s in manuals:
        cn = s.class_.name if s.class_ else '?'
        print(f'  id={s.id} class={cn} date={s.scheduled_date} notes={s.notes}')
    
    if manuals:
        for s in manuals:
            s.conflict_type = None
            if s.notes and ('手动' in s.notes or '强制' in s.notes):
                if '合班' not in (s.notes or ''):
                    s.notes = None
        db.session.commit()
        print(f'Cleared {len(manuals)} stale manual conflict_type records')
    else:
        print('No cleanup needed')
