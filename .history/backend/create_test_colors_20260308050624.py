"""
创建测试数据，演示三种背景色：冲突(红)、已完成(绿)、合班(紫)
运行方式: cd backend && python create_test_colors.py
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from models import db, ClassSchedule
from datetime import date

app = create_app()

with app.app_context():
    # 获取当前4月份的排课记录
    schedules = ClassSchedule.query.filter(
        ClassSchedule.scheduled_date >= date(2026, 4, 1),
        ClassSchedule.scheduled_date < date(2026, 5, 1)
    ).order_by(ClassSchedule.scheduled_date).all()
    
    if not schedules:
        print("❌ 4月份无排课数据，请先生成课表")
        sys.exit(1)
    
    print(f"找到 {len(schedules)} 条4月排课记录")
    
    # 把第一条设为 conflict（冲突-红色）
    if len(schedules) >= 1:
        s = schedules[0]
        s.status = 'conflict'
        s.conflict_type = 'teacher'
        s.notes = '测试冲突：讲师时间冲突'
        print(f"  ✅ #{s.id} {s.class_.name} -> 冲突(红色)")
    
    # 把第二条设为 completed（已完成-绿色）
    if len(schedules) >= 2:
        s = schedules[1]
        s.status = 'completed'
        s.notes = None
        print(f"  ✅ #{s.id} {s.class_.name} -> 已完成(绿色)")
    
    # 如果有第三条和第四条，设为合班（紫色）
    if len(schedules) >= 4:
        main_s = schedules[2]
        sec_s = schedules[3]
        # 设置合班关系
        main_s.notes = f'合班主记录（含 {sec_s.class_.name}）'
        sec_s.merged_with = main_s.id
        sec_s.notes = f'合班至 {main_s.class_.name}'
        print(f"  ✅ #{main_s.id} {main_s.class_.name} -> 合班主记录(紫色)")
        print(f"  ✅ #{sec_s.id} {sec_s.class_.name} -> 合班次记录(紫色)")
    elif len(schedules) >= 3:
        # 只有3条，把第3条标记为合班
        s = schedules[2]
        s.notes = '合班主记录（含 测试班级）'
        print(f"  ✅ #{s.id} {s.class_.name} -> 合班(紫色)")
    
    db.session.commit()
    print("\n🎨 测试数据已准备完毕！刷新浏览器查看4月排课。")
    print("   • 红色行 = 冲突")
    print("   • 绿色行 = 已完成")
    print("   • 紫色行 = 合班")
