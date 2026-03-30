from app import app
from models import Class
from sqlalchemy import or_

with app.app_context():
    c1 = Class.query.filter(Class.name.like('%151%')).first()
    c2 = Class.query.filter(Class.name.like('%152%')).first()
    c3 = Class.query.filter(Class.name.like('%156%')).first()
    
    ids = []
    if c1: ids.append(c1.id)
    if c2: ids.append(c2.id)
    if c3: ids.append(c3.id)
    print(f"Correct IDs for 151, 152, 156: {ids}")
    
    from routes.schedule import _run_best_of_n
    assignments, report = _run_best_of_n(
        year=2026, month=4, constraints={}, n_rounds=1, 
        conflict_mode='smart', overrides={}, skip_class_ids=set(),
        homeroom_overrides={}, combo_overrides={}, target_class_ids=ids
    )
    
    for a in assignments:
        is_skipped = a.get('assigned_date') is None
        cname = a.get('class_name')
        if is_skipped:
            print(f"SKIPPED: {cname} - Reason: {a.get('skip_reason')}")
        else:
            print(f"SCHEDULED: {cname} on {a.get('assigned_date')} with Score {a.get('score')} | Conflicts: {a.get('conflicts')}")
