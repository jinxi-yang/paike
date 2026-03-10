"""
Create REAL conflict data: assign the same teacher to 2 different classes on the same date
"""
import sys, os
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from models import db, ClassSchedule, TeacherCourseCombo
from datetime import date

app = create_app()

with app.app_context():
    schedules = ClassSchedule.query.filter(
        ClassSchedule.scheduled_date >= date(2026, 4, 1),
        ClassSchedule.scheduled_date < date(2026, 5, 1)
    ).order_by(ClassSchedule.scheduled_date).all()
    
    print(f"Found {len(schedules)} April records")
    
    # STEP 1: Reset ALL to clean
    for s in schedules:
        s.status = 'scheduled'
        s.conflict_type = None
        s.merged_with = None
        s.notes = None
    db.session.flush()
    print("All reset.")
    
    # STEP 2: Find same-date records and create REAL conflict
    # by assigning the SAME teacher combo to two classes
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
        if len(group) >= 4 and not conflict_done:
            s1, s2, s3, s4 = group[0], group[1], group[2], group[3]
            
            # Create REAL conflict: assign s1's teacher combo to s2 as well
            # This means the SAME teacher is teaching TWO classes on the same Saturday
            original_combo = s1.combo
            if original_combo:
                teacher_name = original_combo.teacher.name if original_combo.teacher else '?'
                c1 = s1.class_.name if s1.class_ else '?'
                c2 = s2.class_.name if s2.class_ else '?'
                
                # Save original combo_id of s2 for reference
                old_combo_id = s2.combo_id
                old_combo_name = s2.combo.teacher.name if s2.combo and s2.combo.teacher else '?'
                
                # Assign SAME combo to s2 (same teacher!)
                s2.combo_id = s1.combo_id
                
                # Now mark both as conflict
                s1.status = 'conflict'
                s1.conflict_type = 'teacher'
                s1.notes = f'\u8bb2\u5e08\u51b2\u7a81\uff1a{teacher_name} \u540c\u65e5\u8fd8\u6388 {c2}\uff08\u540c\u4e00\u8bb2\u5e08\u5206\u914d\u4e86\u4e24\u4e2a\u73ed\u7ea7\uff09'
                
                s2.status = 'conflict'
                s2.conflict_type = 'teacher'
                s2.notes = f'\u8bb2\u5e08\u51b2\u7a81\uff1a{teacher_name} \u540c\u65e5\u8fd8\u6388 {c1}\uff08\u540c\u4e00\u8bb2\u5e08\u5206\u914d\u4e86\u4e24\u4e2a\u73ed\u7ea7\uff09'
                
                print(f"REAL CONFLICT: Teacher {teacher_name} assigned to:")
                print(f"  #{s1.id} {c1} on {d}")
                print(f"  #{s2.id} {c2} on {d} (combo changed from {old_combo_name} to {teacher_name})")
                conflict_done = True
            
            # Set completed
            s3.status = 'completed'
            c3 = s3.class_.name if s3.class_ else '?'
            print(f"COMPLETED: #{s3.id} {c3}")
            completed_done = True
            
            # Set merge pair from remaining
            remaining = group[4:]
            if len(remaining) >= 2:
                sm, ss = remaining[0], remaining[1]
                cm = sm.class_.name if sm.class_ else '?'
                cs = ss.class_.name if ss.class_ else '?'
                sm.notes = f'\u5408\u73ed\u4e3b\u8bb0\u5f55\uff08\u542b {cs}\uff09'
                ss.merged_with = sm.id
                ss.notes = f'\u5408\u73ed\u81f3 {cm}'
                print(f"MERGED: #{sm.id} {cm}(main) + #{ss.id} {cs}(sec)")
                merge_done = True
            break
    
    # Fallback merge if not done
    if not merge_done:
        for d, group in sorted(date_groups.items()):
            avail = [s for s in group if s.status == 'scheduled' and not s.merged_with]
            if len(avail) >= 2:
                sm, ss = avail[0], avail[1]
                cm = sm.class_.name if sm.class_ else '?'
                cs = ss.class_.name if ss.class_ else '?'
                sm.notes = f'\u5408\u73ed\u4e3b\u8bb0\u5f55\uff08\u542b {cs}\uff09'
                ss.merged_with = sm.id
                ss.notes = f'\u5408\u73ed\u81f3 {cm}'
                print(f"MERGED: #{sm.id} {cm}(main) + #{ss.id} {cs}(sec)")
                merge_done = True
                break
    
    db.session.commit()
    
    print("\n--- Final state ---")
    for s in schedules:
        c = s.class_.name if s.class_ else '?'
        t = s.combo.teacher.name if s.combo and s.combo.teacher else '?'
        print(f"  #{s.id} {c:25s} teacher={t:8s} status={s.status:12s} merged={str(s.merged_with):5s}")
    print("\nDone!")
