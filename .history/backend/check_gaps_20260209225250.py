
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from models import db, Class, ClassSchedule
from datetime import timedelta

def check_gaps():
    app = create_app()
    with app.app_context():
        classes = Class.query.all()
        print(f"Checking {len(classes)} classes for gaps > 35 days (5 weeks)...")
        
        found_issues = False
        
        for cls in classes:
            schedules = ClassSchedule.query.filter_by(class_id=cls.id).order_by(ClassSchedule.scheduled_date).all()
            if not schedules:
                continue
                
            # print(f"Checking Class: {cls.name} ({len(schedules)} schedules)")
            
            for i in range(len(schedules) - 1):
                s1 = schedules[i]
                s2 = schedules[i+1]
                
                # Skip if months apart due to semester break? 
                # User config says interval is 4-5 weeks.
                # If gap > 40 days (approx 6 weeks), report it.
                
                gap = s2.scheduled_date - s1.scheduled_date
                
                if gap.days > 40:
                    print(f"[Gap Found] {cls.name}:")
                    print(f"  - {s1.scheduled_date} ({s1.status}) -> {s2.scheduled_date} ({s2.status})")
                    print(f"  - Gap: {gap.days} days ({gap.days // 7} weeks)")
                    found_issues = True
        
        if not found_issues:
            print("No abnormal gaps found.")
        else:
            print("\nFound issues! Suggest running a fix.")

if __name__ == "__main__":
    check_gaps()
