"""
Clean up ALL stale data and set up clean test cases
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
    
    print(f"Found {len(schedules)} April records")
    
    # STEP 1: Reset ALL records to clean state
    for s in schedules:
        s.status = 'scheduled'
        s.conflict_type = None
        s.merged_with = None
        s.notes = None
    db.session.flush()
    print("All records reset to scheduled.")
    
    # STEP 2: Set up conflict pair - pick first 2 on same date
    date_groups = {}
    for s in schedules:
        d = s.scheduled_date.isoformat()
        if d not in date_groups:
            date_groups[d] = []
        date_groups[d].append(s)
    
    conflict_done = False
    merge_done = False
    completed_done = False
    
    for d, group in sorted(date_groups.items()):
        if not conflict_done and len(group) >= 2:
            s1, s2 = group[0], group[1]
            c1 = s1.class_.name if s1.class_ else '?'
            c2 = s2.class_.name if s2.class_ else '?'
            t1 = s1.combo.teacher.name if s1.combo and s1.combo.teacher else '?'
            t2 = s2.combo.teacher.name if s2.combo and s2.combo.teacher else '?'
            
            s1.status = 'conflict'
            s1.conflict_type = 'teacher'
            s1.notes = f'\u8bb2\u5e08\u51b2\u7a81\uff1a{t1} \u5728 {d} \u4e0e {c2}\uff08{t2}\uff09\u649e\u8bfe'
            
            s2.status = 'conflict'
            s2.conflict_type = 'teacher'
            s2.notes = f'\u8bb2\u5e08\u51b2\u7a81\uff1a{t2} \u5728 {d} \u4e0e {c1}\uff08{t1}\uff09\u649e\u8bfe'
            
            print(f"CONFLICT: #{s1.id} {c1} + #{s2.id} {c2} on {d}")
            conflict_done = True
            
            # Set completed and merge from remaining records in same group
            remaining = group[2:]
            if not completed_done and len(remaining) >= 1:
                sc = remaining[0]
                sc.status = 'completed'
                print(f"COMPLETED: #{sc.id} {sc.class_.name}")
                completed_done = True
                remaining = remaining[1:]
            
            if not merge_done and len(remaining) >= 2:
                sm, ss = remaining[0], remaining[1]
                cm = sm.class_.name if sm.class_ else '?'
                cs = ss.class_.name if ss.class_ else '?'
                sm.notes = f'\u5408\u73ed\u4e3b\u8bb0\u5f55\uff08\u542b {cs}\uff09'
                ss.merged_with = sm.id
                ss.notes = f'\u5408\u73ed\u81f3 {cm}'
                print(f"MERGED: #{sm.id} {cm}(main) + #{ss.id} {cs}(sec)")
                merge_done = True
    
    # If not enough on first date, use other dates
    if not merge_done:
        for d, group in sorted(date_groups.items()):
            if merge_done:
                break
            for s in group:
                if s.status == 'scheduled' and not s.merged_with:
                    # Not yet used
                    pass
            if len(group) >= 2:
                avail = [s for s in group if s.status == 'scheduled' and not s.merged_with and not (s.notes and '\u5408\u73ed' in s.notes)]
                if len(avail) >= 2:
                    sm, ss = avail[0], avail[1]
                    cm = sm.class_.name if sm.class_ else '?'
                    cs = ss.class_.name if ss.class_ else '?'
                    sm.notes = f'\u5408\u73ed\u4e3b\u8bb0\u5f55\uff08\u542b {cs}\uff09'
                    ss.merged_with = sm.id
                    ss.notes = f'\u5408\u73ed\u81f3 {cm}'
                    print(f"MERGED: #{sm.id} {cm}(main) + #{ss.id} {cs}(sec)")
                    merge_done = True
    
    if not completed_done:
        for s in schedules:
            if s.status == 'scheduled' and not s.merged_with and not (s.notes and '\u5408\u73ed' in (s.notes or '')):
                s.status = 'completed'
                print(f"COMPLETED: #{s.id} {s.class_.name}")
                completed_done = True
                break
    
    db.session.commit()
    
    print("\n--- Final state ---")
    for s in schedules:
        c = s.class_.name if s.class_ else '?'
        print(f"  #{s.id} {c:20s} status={s.status:12s} merged_with={str(s.merged_with):5s} notes={s.notes}")
    print("\nDone!")
