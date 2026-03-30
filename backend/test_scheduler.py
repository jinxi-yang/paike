import json
from app import app
from routes.schedule import _run_best_of_n
from models import Class, ClassSchedule, Topic, TeacherCourseCombo

with app.app_context():
    target_class_ids = [2, 7, 12, 13, 15, 11] + [4, 5, 10]
    
    print("Testing _run_best_of_n for April 2026...")
    assignments, report = _run_best_of_n(
        year=2026, month=4, constraints={}, n_rounds=1, 
        conflict_mode='smart', overrides={}, skip_class_ids=set(),
        homeroom_overrides={}, combo_overrides={}, target_class_ids=target_class_ids
    )
    
    for a in assignments:
        is_skipped = a.get('assigned_date') is None
        cname = a.get('class_name')
        if is_skipped:
            print(f"SKIPPED: {cname} - Reason: {a.get('skip_reason')}")
        else:
            print(f"SCHEDULED: {cname} on {a.get('assigned_date')}")
            
    print(f"\nTotal scheduled: {len([a for a in assignments if a.get('assigned_date')])}")
