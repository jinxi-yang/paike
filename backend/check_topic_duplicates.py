"""检查每个班的课题使用情况：是否每个核心课题只出现一次，是否有重复"""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from app import app
from models import db, Class, ClassSchedule, Topic
from collections import Counter

with app.app_context():
    classes = Class.query.order_by(Class.id).all()
    
    for cls in classes:
        schedules = ClassSchedule.query.filter(
            ClassSchedule.class_id == cls.id,
            ClassSchedule.status != 'cancelled'
        ).order_by(ClassSchedule.scheduled_date).all()
        
        if not schedules:
            continue
        
        # 统计每个课题出现次数
        topic_counts = Counter()
        topic_details = {}  # topic_name -> [(date, sch_id), ...]
        
        for s in schedules:
            t = s.topic
            if not t:
                continue
            topic_counts[t.name] += 1
            if t.name not in topic_details:
                topic_details[t.name] = []
            topic_details[t.name].append((s.scheduled_date.isoformat(), s.id, t.is_other))
        
        # 检查是否有核心课题（非其他）重复
        duplicates = {name: details for name, details in topic_details.items() 
                     if topic_counts[name] > 1 and not details[0][2]}
        
        if duplicates:
            print(f"\n{'='*60}")
            print(f"[!] {cls.name} (ID={cls.id}) — 有重复核心课题:")
            print(f"{'='*60}")
            for name, details in duplicates.items():
                print(f"  {name} 出现 {len(details)} 次:")
                for dt, sid, _ in details:
                    print(f"    - {dt}  (schedule_id={sid})")
        
        # 检查缺失的核心课题
        project_topics = Topic.query.filter_by(project_id=cls.project_id).filter(
            Topic.is_other != True
        ).all()
        core_topic_names = {t.name for t in project_topics}
        used_topics = {name for name, details in topic_details.items() if not details[0][2]}
        missing = core_topic_names - used_topics
        if missing:
            if not duplicates:
                print(f"\n{cls.name} (ID={cls.id}):")
            print(f"  缺失课题: {', '.join(missing)}")
    
    print("\n" + "="*60)
    print("检查完毕")
    print("="*60)
