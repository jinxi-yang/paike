"""
数据重置脚本 - 清空所有业务数据，保留账号和表结构
用途：部署测试环境前清空数据

用法：
    python reset_data.py          # 交互确认后清空
    python reset_data.py --force  # 跳过确认直接清空
"""
import sys
import os

# 确保可以导入项目模块
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from models import db

# 按依赖顺序删除（子表在前，父表在后）
TABLES_TO_CLEAR = [
    'schedule_constraint',
    'monthly_plan',
    'class_schedule',
    'class',
    'teacher_course_combo',
    'course',
    'topic',
    'project',
    'teacher',
    'homeroom',
]


def reset_data(force=False):
    if not force:
        print("=" * 50)
        print("⚠️  警告：此操作将清空所有业务数据！")
        print("=" * 50)
        print("\n将清空以下表：")
        for t in TABLES_TO_CLEAR:
            print(f"  - {t}")
        print("\n✅ 账号信息（admin/viewer）是代码内硬编码，不受影响。")
        print()
        confirm = input("确认清空？输入 yes 继续: ").strip().lower()
        if confirm != 'yes':
            print("已取消。")
            return

    app = create_app()
    with app.app_context():
        for table_name in TABLES_TO_CLEAR:
            result = db.session.execute(db.text(f"DELETE FROM [{table_name}]"))
            count = result.rowcount
            print(f"  🗑️  {table_name}: 删除 {count} 条记录")

        # 重置自增ID（SQLite）
        for table_name in TABLES_TO_CLEAR:
            try:
                db.session.execute(
                    db.text(f"DELETE FROM sqlite_sequence WHERE name='{table_name}'")
                )
            except Exception:
                pass  # 表可能没有自增序列

        db.session.commit()
        print("\n✅ 数据清空完成！自增ID已重置。")
        print("账号信息不受影响：admin / admin123 , viewer / viewer123")


if __name__ == '__main__':
    force = '--force' in sys.argv
    reset_data(force=force)
