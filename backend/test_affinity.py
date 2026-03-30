import sys
import os

import logging
from app import create_app
from services.config_service import _cfg

app = create_app()
with app.app_context():
    from models import ClassSchedule, MonthlyPlan, Class
    from routes.schedule import _precompute_class_data, _run_best_of_n, _score_candidate
    from datetime import date
    
    start_d = date(2026, 4, 1)
    end_d = date(2026, 5, 1)
    month_schedules = ClassSchedule.query.filter(
        ClassSchedule.scheduled_date >= start_d,
        ClassSchedule.scheduled_date < end_d,
        ClassSchedule.status == 'scheduled'
    ).all()
    
    print(f'Found {len(month_schedules)} scheduled records in April')
    for s in month_schedules:
        print(f'Class {s.class_.name} (ID: {s.class_id}): existing date {s.scheduled_date}')
        
    precomputed = _precompute_class_data(2026, 4, {}, month_schedules=month_schedules)
    print('Original dates extracted:', precomputed.get('original_dates'))
    
    for info in precomputed['class_infos']:
        cid = info['cls'].id
        orig = precomputed['original_dates'].get(cid)
        print(f"Class {cid} orig date: {orig}")
