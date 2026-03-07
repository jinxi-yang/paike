
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from models import db, Class, ClassSchedule, Topic, TeacherCourseCombo
from datetime import date, timedelta
from routes.schedule import is_holiday, find_next_available_saturday

def debug_generation():
    app = create_app()
    with app.app_context():
        print("=== Debugging Schedule Generation ===")
        
        # 1. Get an active class
        # Try to find one that has some history or is new
        cls = Class.query.filter(Class.status.in_(['active', 'planning'])).first()
        if not cls:
            print("No active/planning classes found!")
            return

        print(f"Testing with Class: {cls.name} (ID: {cls.id})")
        
        # 2. Find next topic
        # Logic from schedule.py
        target_month_start = date(2026, 3, 1) # User mentioned March 2026 in screenshots
        print(f"Target Month: {target_month_start}")
        
        last_schedule = ClassSchedule.query.filter(
            ClassSchedule.class_id == cls.id,
            ClassSchedule.scheduled_date < target_month_start
        ).order_by(ClassSchedule.topic_id.desc()).first()
        
        if last_schedule:
            print(f"Last Schedule: {last_schedule.topic.name} (Seq: {last_schedule.topic.sequence}) Date: {last_schedule.scheduled_date}")
        else:
            print("No previous schedules found (First class?)")
            
        all_topics = cls.project.topics.order_by("sequence").all()
        print(f"Total Topics: {len(all_topics)}")
        
        next_topic = None
        if not last_schedule:
            if all_topics: 
                next_topic = all_topics[0]
        else:
            current_seq = last_schedule.topic.sequence
            for t in all_topics:
                if t.sequence > current_seq:
                    next_topic = t
                    break
        
        if not next_topic:
            print("No next topic found (Course completed?)")
            return
            
        print(f"Next Topic: {next_topic.name} (ID: {next_topic.id})")
        
        # 3. Check Combos
        combos = TeacherCourseCombo.query.filter_by(topic_id=next_topic.id).order_by(TeacherCourseCombo.id.desc()).all()
        print(f"Combos found: {len(combos)}")
        for c in combos:
            print(f" - Combo {c.id}: Teacher {c.teacher.name} Course {c.course.name}")
            
        if not combos:
            print("ERROR: No combos found! Scheduling will fail/mark pending.")
            # Note: The code continues but marks as pending allocation? 
            # Let's check schedule.py logic. 
            # It blindly takes combos[0] if exists.
            
        # 4. Find Date
        # Logic: Find Saturdays in target month
        saturdays = []
        d = target_month_start
        while d.weekday() != 5:
            d += timedelta(days=1)
        while d.month == target_month_start.month:
            saturdays.append(d)
            d += timedelta(days=7)
            
        print(f"Candidate Saturdays in March: {saturdays}")
        
        # Logic in schedule.py iterates saturdays
        candidate_date = None
        for sat in saturdays:
            print(f"Checking Saturday: {sat}")
            
            # Check Holiday
            is_hol = is_holiday(sat)
            print(f"  Is Holiday? {is_hol}")
            
            if not is_hol:
                candidate_date = sat
                print(f"  -> Candidate Found: {candidate_date}")
                break
            else:
                print("  -> Skipped (Holiday)")
        
        if not candidate_date:
            print("No available Saturday found in month (All holidays?)")
            return

        # 5. Check Conflicts (Mock)
        # If we have a combo, check teacher
        if combos:
            combo1 = combos[0]
            print(f"Checking conflicts for Teacher {combo1.teacher.name} on {candidate_date}")
            
            # Query conflicts
            teacher_conflicts = ClassSchedule.query.join(
                TeacherCourseCombo, ClassSchedule.combo_id == TeacherCourseCombo.id
            ).filter(
                TeacherCourseCombo.teacher_id == combo1.teacher_id,
                ClassSchedule.scheduled_date == candidate_date
            ).all()
            
            if teacher_conflicts:
                print(f"  Conflict Found! Teacher busy with {len(teacher_conflicts)} classes.")
                for c in teacher_conflicts:
                    print(f"    - {c.class_.name} ({c.status})")
            else:
                print("  No teacher conflicts.")
        
        print("Debug Complete.")

if __name__ == "__main__":
    debug_generation()
