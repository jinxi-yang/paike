"""
迁移脚本：为现有排课记录回填 location_id（使用班级的默认城市 city_id）
"""
import sqlite3
import os

db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'scheduler.db')
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# 统计当前 location_id 为空的记录数
cursor.execute("SELECT COUNT(*) FROM class_schedule WHERE location_id IS NULL")
null_count = cursor.fetchone()[0]
print(f"[INFO] 当前有 {null_count} 条排课记录的 location_id 为空")

if null_count > 0:
    # 使用班级的默认城市 city_id 回填
    cursor.execute("""
        UPDATE class_schedule
        SET location_id = (
            SELECT c.city_id FROM class c WHERE c.id = class_schedule.class_id
        )
        WHERE location_id IS NULL
    """)
    updated = cursor.rowcount
    conn.commit()
    print(f"[OK] 已为 {updated} 条排课记录回填 location_id（使用班级默认城市）")
else:
    print("[INFO] 所有排课记录已有 location_id，无需回填")

# 验证
cursor.execute("SELECT COUNT(*) FROM class_schedule WHERE location_id IS NULL")
remaining = cursor.fetchone()[0]
print(f"[VERIFY] 回填后仍有 {remaining} 条记录 location_id 为空")

conn.close()
print("[DONE] 迁移完成")
