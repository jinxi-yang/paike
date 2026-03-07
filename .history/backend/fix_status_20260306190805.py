"""
修复排课状态逻辑漏洞 - 数据迁移脚本
1. planning → scheduled
2. 清理重复记录 (class_id, topic_id)
3. 过去日期的 scheduled → completed
"""
import sys
sys.path.insert(0, 'backend')
from app import create_app
from models import db, ClassSchedule, Class
from datetime import date

app = create_app()

with app.app_context():
    print("=" * 60)
    print("排课状态修复脚本")
    print("=" * 60)
    
    # === Fix 1: planning → scheduled ===
    print("\n[Fix 1] planning → scheduled ...")
    planning_records = ClassSchedule.query.filter_by(status='planning').all()
    print(f"  发现 {len(planning_records)} 条 planning 记录")
    for r in planning_records:
        r.status = 'scheduled'
    print(f"  已全部更新为 scheduled")
    
    # === Fix 2: 清理重复记录 ===
    print("\n[Fix 2] 清理重复 (class_id, topic_id) 记录 ...")
    all_records = ClassSchedule.query.order_by(
        ClassSchedule.class_id, 
        ClassSchedule.topic_id,
        ClassSchedule.updated_at.desc()
    ).all()
    
    seen = {}  # (class_id, topic_id) → best record
    duplicates = []
    for r in all_records:
        key = (r.class_id, r.topic_id)
        if key not in seen:
            seen[key] = r
        else:
            # Keep the one with better status (completed > scheduled > conflict)
            existing = seen[key]
            priority = {'completed': 3, 'scheduled': 2, 'conflict': 1}
            if priority.get(r.status, 0) > priority.get(existing.status, 0):
                # This record is better, swap
                duplicates.append(existing)
                seen[key] = r
            else:
                duplicates.append(r)
    
    print(f"  发现 {len(duplicates)} 条重复记录:")
    for d in duplicates:
        print(f"    class_id={d.class_id}, topic_id={d.topic_id}, status={d.status}, date={d.scheduled_date}")
        db.session.delete(d)
    
    # === Fix 3: 过去日期 scheduled → completed ===
    print("\n[Fix 3] 过去日期 scheduled → completed ...")
    today = date.today()
    past_scheduled = ClassSchedule.query.filter(
        ClassSchedule.status == 'scheduled',
        ClassSchedule.scheduled_date < today
    ).all()
    print(f"  发现 {len(past_scheduled)} 条过去日期的 scheduled 记录")
    for r in past_scheduled:
        r.status = 'completed'
        print(f"    class_id={r.class_id}, topic_id={r.topic_id}, date={r.scheduled_date} → completed")
    
    # Commit all changes
    db.session.commit()
    
    # === Summary ===
    print("\n" + "=" * 60)
    print("修复完成！当前状态统计：")
    for status in ['scheduled', 'completed', 'conflict', 'cancelled']:
        count = ClassSchedule.query.filter_by(status=status).count()
        if count > 0:
            print(f"  {status}: {count} 条")
    
    # Check for any remaining unexpected statuses
    from sqlalchemy import func
    unexpected = db.session.query(
        ClassSchedule.status, func.count(ClassSchedule.id)
    ).group_by(ClassSchedule.status).all()
    print("\n  全部状态分布:")
    for status, count in unexpected:
        print(f"    {status}: {count}")
