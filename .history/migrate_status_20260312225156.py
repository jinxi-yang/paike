"""
数据迁移脚本：将旧状态统一到简化后的状态模型
status: planning/confirmed/conflict/merged → all become 'scheduled'

运行方式: python migrate_status.py
"""
import sqlite3
import os
import shutil

DB_PATH = os.path.join(os.path.dirname(__file__), 'backend', 'instance', 'scheduler.db')

if not os.path.exists(DB_PATH):
    print(f"数据库不存在: {DB_PATH}")
    exit(1)

# 备份
backup_path = DB_PATH + '.bak_status_migration'
shutil.copy2(DB_PATH, backup_path)
print(f"已备份数据库到: {backup_path}")

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# 查看迁移前的状态分布
cursor.execute("SELECT status, COUNT(*) FROM class_schedule GROUP BY status")
print("\n迁移前状态分布:")
for row in cursor.fetchall():
    print(f"  {row[0]}: {row[1]} 条")

# 执行迁移
cursor.execute("""
    UPDATE class_schedule 
    SET status = 'scheduled' 
    WHERE status IN ('planning', 'confirmed', 'conflict', 'merged')
""")
migrated = cursor.rowcount

conn.commit()

# 验证
cursor.execute("SELECT status, COUNT(*) FROM class_schedule GROUP BY status")
print(f"\n迁移完成，共更新 {migrated} 条记录")
print("迁移后状态分布:")
for row in cursor.fetchall():
    print(f"  {row[0]}: {row[1]} 条")

conn.close()
print("\n✅ 完成！如需回滚，恢复备份文件即可。")
