"""修复脚本：修正 NULL status 记录，然后重新计算所有 week_number"""
import sys, os
backend_dir = os.path.abspath(os.path.dirname(__file__))
if backend_dir not in sys.path:
    sys.path.append(backend_dir)

from app import app
from models import db, Class, ClassSchedule
from routes.schedule import _resequence_topics_by_date

with app.app_context():
    # 1. 修复 status=NULL 的记录 → 设为 'scheduled'
    null_count = ClassSchedule.query.filter(ClassSchedule.status.is_(None)).count()
    print(f"1. 发现 {null_count} 条 status=NULL 的排课记录")
    if null_count > 0:
        ClassSchedule.query.filter(ClassSchedule.status.is_(None)).update(
            {ClassSchedule.status: 'scheduled'}, synchronize_session='fetch'
        )
        db.session.commit()
        print(f"   已将它们的 status 修复为 'scheduled'")

    # 2. 修复 week_number=NULL 或 =0 的记录
    bad_wn = ClassSchedule.query.filter(
        db.or_(ClassSchedule.week_number.is_(None), ClassSchedule.week_number == 0)
    ).count()
    print(f"2. 发现 {bad_wn} 条 week_number 为 NULL 或 0 的记录")

    # 3. 重新给所有班级排序
    classes = Class.query.all()
    for c in classes:
        _resequence_topics_by_date(c.id)
    db.session.commit()
    print(f"3. 已重新计算 {len(classes)} 个班级的 week_number")

    # 4. 验证
    still_bad = ClassSchedule.query.filter(
        db.or_(ClassSchedule.week_number.is_(None), ClassSchedule.week_number == 0)
    ).count()
    still_null_status = ClassSchedule.query.filter(ClassSchedule.status.is_(None)).count()
    print(f"\n验证: week_number异常={still_bad}, status=NULL={still_null_status}")
    if still_bad == 0 and still_null_status == 0:
        print("✅ 全部修复完成！")
    else:
        print("⚠️ 仍有未修复的记录，请检查")
