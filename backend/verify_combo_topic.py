"""验证5个班的combo-topic闭环"""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
from app import app
from models import db, ClassSchedule

with app.app_context():
    for cid in [1, 2, 3, 4, 5]:
        scheds = ClassSchedule.query.filter(
            ClassSchedule.class_id == cid,
            ClassSchedule.status != 'cancelled'
        ).order_by(ClassSchedule.scheduled_date).all()
        issues = []
        for s in scheds:
            if s.combo and s.combo.topic_id != s.topic_id:
                issues.append(
                    f'  {s.scheduled_date} D1: combo在[{s.combo.topic.name}] 但排课在[{s.topic.name}]'
                )
            if s.combo_2 and s.combo_2.topic_id != s.topic_id:
                issues.append(
                    f'  {s.scheduled_date} D2: combo在[{s.combo_2.topic.name}] 但排课在[{s.topic.name}]'
                )
        name = scheds[0].class_.name if scheds else f'ID={cid}'
        if issues:
            print(f'\n{name}: {len(issues)}个不匹配!')
            for i in issues:
                print(i)
        else:
            print(f'{name}: 全部闭环 OK')
