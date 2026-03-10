"""
Fix test data: create proper conflict pairs and set correct Chinese notes
"""
import sys, os
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from models import db, ClassSchedule
from datetime import date

app = create_app()

with app.app_context():
    schedules = ClassSchedule.query.filter(
        ClassSchedule.scheduled_date >= date(2026, 4, 1),
        ClassSchedule.scheduled_date < date(2026, 5, 1)
    ).order_by(ClassSchedule.scheduled_date).all()
    
    if not schedules:
        print("No April schedules")
        sys.exit(1)
    
    print(f"Found {len(schedules)} records")
    
    # Print current status of all records
    for s in schedules:
        cls_name = s.class_.name if s.class_ else '?'
        t1 = s.combo.teacher.name if s.combo and s.combo.teacher else '?'
        print(f"  #{s.id} | {cls_name} | status={s.status} | merged_with={s.merged_with} | notes={s.notes} | teacher={t1} | date={s.scheduled_date}")
    
    # Find two records on the same date to make a conflict pair
    date_groups = {}
    for s in schedules:
        d = s.scheduled_date.isoformat()
        if d not in date_groups:
            date_groups[d] = []
        date_groups[d].append(s)
    
    print("\nDate groups:")
    for d, group in date_groups.items():
        names = [s.class_.name for s in group if s.class_]
        print(f"  {d}: {len(group)} records -> {names}")
    
    # Make the first date group into a conflict pair (both records red)
    conflict_created = False
    for d, group in date_groups.items():
        if len(group) >= 2 and not conflict_created:
            s1, s2 = group[0], group[1]
            cls1 = s1.class_.name if s1.class_ else '?'
            cls2 = s2.class_.name if s2.class_ else '?'
            t1 = s1.combo.teacher.name if s1.combo and s1.combo.teacher else '?'
            t2 = s2.combo.teacher.name if s2.combo and s2.combo.teacher else '?'
            
            # Clear any merged status first
            s1.merged_with = None
            s2.merged_with = None
            
            s1.status = 'conflict'
            s1.conflict_type = 'teacher'
            s1.notes = f'\u8bb2\u5e08\u51b2\u7a81\uff1a{t1} \u4e0e {cls2} \u649e\u8bfe\uff08\u540c\u65e5{d}\uff09'
            
            s2.status = 'conflict'  
            s2.conflict_type = 'teacher'
            s2.notes = f'\u8bb2\u5e08\u51b2\u7a81\uff1a{t2} \u4e0e {cls1} \u649e\u8bfe\uff08\u540c\u65e5{d}\uff09'
            
            print(f"\nConflict pair on {d}:")
            print(f"  #{s1.id} {cls1} -> CONFLICT (RED)")
            print(f"  #{s2.id} {cls2} -> CONFLICT (RED)")
            conflict_created = True
            break
    
    # Find another date group for merge pair
    merge_created = False
    for d, group in date_groups.items():
        if len(group) >= 2 and not merge_created:
            # Skip the conflict group
            if group[0].status == 'conflict':
                continue
            s1, s2 = group[0], group[1]
            cls1 = s1.class_.name if s1.class_ else '?'
            cls2 = s2.class_.name if s2.class_ else '?'
            
            s1.status = 'scheduled'
            s1.notes = f'\u5408\u73ed\u4e3b\u8bb0\u5f55\uff08\u542b {cls2}\uff09'
            s1.merged_with = None
            
            s2.status = 'scheduled'
            s2.merged_with = s1.id
            s2.notes = f'\u5408\u73ed\u81f3 {cls1}'
            
            print(f"\nMerge pair on {d}:")
            print(f"  #{s1.id} {cls1} -> MERGED MAIN (PURPLE)")
            print(f"  #{s2.id} {cls2} -> MERGED SECONDARY (PURPLE)")
            merge_created = True
    
    # Find one record for completed
    completed_created = False
    for s in schedules:
        if s.status not in ('conflict',) and not s.merged_with and not (s.notes and '\u5408\u73ed\u4e3b\u8bb0\u5f55' in (s.notes or '')):
            if not completed_created:
                s.status = 'completed'
                s.notes = None
                cls = s.class_.name if s.class_ else '?'
                print(f"\nCompleted:")
                print(f"  #{s.id} {cls} -> COMPLETED (GREEN)")
                completed_created = True

    db.session.commit()
    print("\nDone! Refresh browser to see April schedule.")
