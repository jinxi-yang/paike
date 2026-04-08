"""
迁移脚本：为 Topic 表添加 is_other 字段，并为已有项目自动创建"其他"课题
"""
import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), 'scheduler.db')

def migrate():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # 1. 添加 is_other 列（如果不存在）
    cursor.execute("PRAGMA table_info(topic)")
    columns = [col[1] for col in cursor.fetchall()]
    if 'is_other' not in columns:
        cursor.execute("ALTER TABLE topic ADD COLUMN is_other BOOLEAN DEFAULT 0")
        print("[migrate] 已添加 topic.is_other 列")
    else:
        print("[migrate] topic.is_other 列已存在，跳过")

    # 2. 将名称为"其他"的现有课题标记为 is_other=1
    cursor.execute("UPDATE topic SET is_other = 1 WHERE name = '其他' AND (is_other IS NULL OR is_other = 0)")
    updated = cursor.rowcount
    if updated:
        print(f"[migrate] 已将 {updated} 个名为'其他'的课题标记为 is_other=1")

    # 3. 为没有"其他"课题的现有项目自动创建
    cursor.execute("SELECT id FROM project")
    all_projects = [row[0] for row in cursor.fetchall()]
    created = 0
    for pid in all_projects:
        cursor.execute("SELECT COUNT(*) FROM topic WHERE project_id = ? AND is_other = 1", (pid,))
        count = cursor.fetchone()[0]
        if count == 0:
            # 获取当前最大 sequence
            cursor.execute("SELECT COALESCE(MAX(sequence), 0) FROM topic WHERE project_id = ?", (pid,))
            max_seq = cursor.fetchone()[0]
            cursor.execute(
                "INSERT INTO topic (project_id, sequence, name, is_fixed, is_other) VALUES (?, ?, '其他', 0, 1)",
                (pid, max_seq + 1)
            )
            created += 1
    if created:
        print(f"[migrate] 为 {created} 个项目自动创建了'其他'课题")

    conn.commit()
    conn.close()
    print("[migrate] 迁移完成！")

if __name__ == '__main__':
    migrate()
