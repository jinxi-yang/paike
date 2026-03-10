"""
Create test data to demonstrate the 3 color statuses: conflict(red), completed(green), merged(purple)
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
        print("No April schedules found")
        sys.exit(1)
    
    print(f"Found {len(schedules)} April schedule records")
    
    # Set first record to conflict (red)
    if len(schedules) >= 1:
        s = schedules[0]
        s.status = 'conflict'
        s.conflict_type = 'teacher'
        s.notes = 'teacher conflict test'
        print(f"  #{s.id} -> conflict (RED)")
    
    # Set second record to completed (green)
    if len(schedules) >= 2:
        s = schedules[1]
        s.status = 'completed'
        s.notes = None
        print(f"  #{s.id} -> completed (GREEN)")
    
    # Set third+fourth as merged (purple)
    if len(schedules) >= 4:
        main_s = schedules[2]
        sec_s = schedules[3]
        class_name_main = main_s.class_.name if main_s.class_ else 'unknown'
        class_name_sec = sec_s.class_.name if sec_s.class_ else 'unknown'
        main_s.notes = f'\u5408\u73ed\u4e3b\u8bb0\u5f55\uff08\u542b {class_name_sec}\uff09'
        sec_s.merged_with = main_s.id
        sec_s.notes = f'\u5408\u73ed\u81f3 {class_name_main}'
        print(f"  #{main_s.id} -> merged main (PURPLE)")
        print(f"  #{sec_s.id} -> merged secondary (PURPLE)")
    elif len(schedules) >= 3:
        s = schedules[2]
        s.notes = '\u5408\u73ed\u4e3b\u8bb0\u5f55\uff08\u542b test\uff09'
        print(f"  #{s.id} -> merged (PURPLE)")
    
    db.session.commit()
    print("\nDone! Refresh browser to see April schedule with 3 colors:")
    print("  RED = conflict | GREEN = completed | PURPLE = merged")
