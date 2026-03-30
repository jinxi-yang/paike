"""
迁移脚本：移除独立 Course 表，将 course_name 直接存储在 teacher_course_combo 表中。

步骤：
1. 给 teacher_course_combo 添加 course_name 列
2. 从 course 表填充 course_name
3. 重建 teacher_course_combo 表（去掉 course_id 列）
4. 删除 course 表
"""
import sqlite3
import os
import sys

db_path = os.path.join(os.path.dirname(__file__), 'scheduler.db')

def migrate():
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # 检查是否已经迁移过
    cursor.execute("PRAGMA table_info(teacher_course_combo)")
    columns = [col['name'] for col in cursor.fetchall()]
    if 'course_name' in columns and 'course_id' not in columns:
        print("已经迁移过，无需重复执行。")
        conn.close()
        return

    print("=== 开始迁移：移除 Course 表 ===")

    # Step 1: 检查当前数据
    cursor.execute("SELECT COUNT(*) as cnt FROM teacher_course_combo")
    combo_count = cursor.fetchone()['cnt']
    print(f"当前 combo 记录数: {combo_count}")

    cursor.execute("SELECT COUNT(*) as cnt FROM course")
    course_count = cursor.fetchone()['cnt']
    print(f"当前 course 记录数: {course_count}")

    # Step 2: 获取所有 combo 数据，附带 course_name
    cursor.execute("""
        SELECT tcc.id, tcc.topic_id, tcc.teacher_id, tcc.priority, tcc.created_at,
               c.name as course_name
        FROM teacher_course_combo tcc
        LEFT JOIN course c ON tcc.course_id = c.id
    """)
    combos = cursor.fetchall()

    # 检查是否有找不到课程名的 combo
    missing = [c for c in combos if not c['course_name']]
    if missing:
        print(f"⚠️ 警告: {len(missing)} 个 combo 找不到对应的课程记录，将设置为 '未知课程'")

    # Step 3: 重建 teacher_course_combo 表
    cursor.execute("DROP TABLE IF EXISTS teacher_course_combo_new")
    cursor.execute("""
        CREATE TABLE teacher_course_combo_new (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            topic_id INTEGER NOT NULL REFERENCES topic(id),
            teacher_id INTEGER NOT NULL REFERENCES teacher(id),
            course_name TEXT NOT NULL DEFAULT '',
            priority INTEGER DEFAULT 0,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Step 4: 迁移数据
    for c in combos:
        cursor.execute("""
            INSERT INTO teacher_course_combo_new (id, topic_id, teacher_id, course_name, priority, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (c['id'], c['topic_id'], c['teacher_id'], c['course_name'] or '未知课程', c['priority'], c['created_at']))

    migrated_count = cursor.rowcount if cursor.rowcount > 0 else len(combos)
    print(f"迁移了 {len(combos)} 条 combo 记录")

    # Step 5: 替换旧表
    cursor.execute("DROP TABLE teacher_course_combo")
    cursor.execute("ALTER TABLE teacher_course_combo_new RENAME TO teacher_course_combo")

    # Step 6: 删除 course 表
    cursor.execute("DROP TABLE IF EXISTS course")
    print("已删除 course 表")

    conn.commit()

    # Step 7: 验证
    cursor.execute("SELECT COUNT(*) as cnt FROM teacher_course_combo")
    new_count = cursor.fetchone()['cnt']
    print(f"\n=== 迁移完成 ===")
    print(f"combo 记录数: {combo_count} → {new_count}")

    cursor.execute("PRAGMA table_info(teacher_course_combo)")
    new_columns = [col['name'] for col in cursor.fetchall()]
    print(f"新表列: {new_columns}")

    assert new_count == combo_count, f"记录数不一致！预期 {combo_count}，实际 {new_count}"
    assert 'course_name' in new_columns, "缺少 course_name 列"
    assert 'course_id' not in new_columns, "course_id 列未删除"

    # 抽样检查
    cursor.execute("SELECT id, teacher_id, course_name FROM teacher_course_combo LIMIT 5")
    print("\n抽样数据:")
    for row in cursor.fetchall():
        print(f"  combo#{row['id']}: teacher_id={row['teacher_id']}, course_name={row['course_name']}")

    # 确认排课引用完好
    cursor.execute("""
        SELECT COUNT(*) as cnt FROM class_schedule cs
        WHERE cs.combo_id IS NOT NULL 
        AND cs.combo_id NOT IN (SELECT id FROM teacher_course_combo)
    """)
    orphan1 = cursor.fetchone()['cnt']
    cursor.execute("""
        SELECT COUNT(*) as cnt FROM class_schedule cs
        WHERE cs.combo_id_2 IS NOT NULL 
        AND cs.combo_id_2 NOT IN (SELECT id FROM teacher_course_combo)
    """)
    orphan2 = cursor.fetchone()['cnt']
    if orphan1 > 0 or orphan2 > 0:
        print(f"⚠️ 警告: 有 {orphan1 + orphan2} 条排课记录引用了不存在的 combo")
    else:
        print("✅ 所有排课记录的 combo 引用完好")

    conn.close()
    print("\n✅ 迁移成功完成！")

if __name__ == '__main__':
    migrate()
