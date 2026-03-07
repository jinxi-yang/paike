
import sys
import os
import json
import logging
from datetime import date

# Ensure we can import from backend
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from models import db, Class, Homeroom, Project, Topic, Teacher, Course, TeacherCourseCombo, ClassSchedule

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def verify_homeroom_constraint():
    app = create_app()
    app.config['TESTING'] = True
    
    with app.app_context():
        # Setup Data
        logger.info("Setting up test data...")
        
        # 1. Create Homeroom Teacher
        hr_name = "TestHR_Li"
        hr = Homeroom.query.filter_by(name=hr_name).first()
        if not hr:
            hr = Homeroom(name=hr_name)
            db.session.add(hr)
            db.session.commit()
            
        # 2. Create/Get Training Type & Topic
        tt = Project.query.first()
        if not tt:
            tt = Project(name="TestType")
            db.session.add(tt)
            db.session.commit()
            
        topic = Topic.query.filter_by(project_id=tt.id).first()
        if not topic:
            topic = Topic(project_id=tt.id, name="TestTopic", sequence=1)
            db.session.add(topic)
            db.session.commit()
            
        # 3. Create Class
        cls_name = "TestClass_HR_Constraint"
        cls = Class.query.filter_by(name=cls_name).first()
        if not cls:
            cls = Class(project_id=tt.id, name=cls_name, homeroom_id=hr.id, status='active', start_date=date(2026, 4, 1))
            db.session.add(cls)
            db.session.commit()
        else:
            # Update homeroom just in case
            cls.homeroom_id = hr.id
            db.session.commit()
            
        # Clear existing schedules for this class in April 2026
        ClassSchedule.query.filter(
            ClassSchedule.class_id == cls.id,
            ClassSchedule.scheduled_date >= date(2026, 4, 1),
            ClassSchedule.scheduled_date <= date(2026, 4, 30)
        ).delete()
        db.session.commit()

        # 4. Prepare Constraints
        # Block April 11 (Saturday) for Homeroom Teacher
        target_date = "2026-04-11"
        constraints = {
            "homeroom_unavailable": [
                {
                    "homeroom_name": hr_name,
                    "dates": [target_date],
                    "reason": "Test Leave"
                }
            ]
        }
        
        # 5. Call Generate API
        logger.info(f"Testing generation with constraint: {hr_name} unavailable on {target_date}")
        
        client = app.test_client()
        resp = client.post('/api/schedule/generate', json={
            'year': 2026,
            'month': 4,
            'constraints': constraints,
            'conflict_mode': 'postpone' # Should skip the date
        })
        
        data = resp.get_json()
        logger.info(f"Response: {data.get('message')}")
        
        # 6. Verify Result
        # Check if any schedule was created on 2026-04-11 for this class
        schedules = ClassSchedule.query.filter(
            ClassSchedule.class_id == cls.id,
            ClassSchedule.scheduled_date == date(2026, 4, 11)
        ).all()
        
        if schedules:
            logger.error(f"FAIL: Found schedule on blocked date {target_date}!")
            for s in schedules:
                logger.error(f" - {s.status}: {s.notes}")
        else:
            logger.info(f"PASS: No schedule found on blocked date {target_date}.")
            
            # Check if it scheduled on other dates (e.g., April 4 or 18)
            other_schedules = ClassSchedule.query.filter(
                ClassSchedule.class_id == cls.id,
                ClassSchedule.scheduled_date >= date(2026, 4, 1),
                ClassSchedule.scheduled_date <= date(2026, 4, 30)
            ).all()
            if other_schedules:
                logger.info(f"PASS: Successfully scheduled on valid dates: {[s.scheduled_date.isoformat() for s in other_schedules]}")
            else:
                logger.warning("WARNING: No schedules generated at all (maybe no topics/combos available?)")

if __name__ == "__main__":
    verify_homeroom_constraint()
