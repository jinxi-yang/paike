"""
数据库迁移脚本 - 添加 conflict_type 字段，清理旧 project 表引用
运行方法: python migrate_to_project.py
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from models import db

def migrate():
    app = create_app()
    
    with app.app_context():
        conn = db.engine.raw_connection()
        cursor = conn.cursor()
        
        print("=" * 50)
        print("北清商学院排课系统 - 数据库迁移")
        print("=" * 50)
        
        # 1. 为 class_schedule 添加 conflict_type 字段
        print("\n[1/4] 添加 class_schedule.conflict_type 字段...")
        try:
            cursor.execute("""
                SELECT COUNT(*) FROM information_schema.COLUMNS
                WHERE TABLE_SCHEMA = DATABASE()
                AND TABLE_NAME = 'class_schedule'
                AND COLUMN_NAME = 'conflict_type'
            """)
            exists = cursor.fetchone()[0]
            if exists:
                print("  → 字段已存在，跳过")
            else:
                cursor.execute("""
                    ALTER TABLE class_schedule
                    ADD COLUMN conflict_type VARCHAR(20) NULL
                    COMMENT '冲突类型: teacher/homeroom/holiday'
                    AFTER status
                """)
                print("  → 添加成功")
        except Exception as e:
            print(f"  → 错误: {e}")
        
        # 2. 回填 conflict_type（根据现有 notes 关键词）
        print("\n[2/4] 回填已有冲突记录的 conflict_type...")
        try:
            cursor.execute("""
                UPDATE class_schedule SET conflict_type = 'homeroom'
                WHERE status = 'conflict' AND conflict_type IS NULL
                AND notes LIKE '%班主任%'
            """)
            homeroom_count = cursor.rowcount
            
            cursor.execute("""
                UPDATE class_schedule SET conflict_type = 'teacher'
                WHERE status = 'conflict' AND conflict_type IS NULL
                AND notes LIKE '%讲师%'
            """)
            teacher_count = cursor.rowcount
            
            print(f"  → 回填完成: {homeroom_count} 条班主任冲突, {teacher_count} 条讲师冲突")
        except Exception as e:
            print(f"  → 错误: {e}")
        
        # 3. 移除 class 表上多余的 project_id 外键和列
        print("\n[3/4] 清理 class 表的 project_id 字段...")
        try:
            # 先尝试移除外键约束
            cursor.execute("""
                SELECT CONSTRAINT_NAME FROM information_schema.KEY_COLUMN_USAGE
                WHERE TABLE_SCHEMA = DATABASE()
                AND TABLE_NAME = 'class'
                AND COLUMN_NAME = 'project_id'
                AND REFERENCED_TABLE_NAME IS NOT NULL
            """)
            fk_rows = cursor.fetchall()
            for fk in fk_rows:
                try:
                    cursor.execute(f"ALTER TABLE `class` DROP FOREIGN KEY `{fk[0]}`")
                    print(f"  → 移除外键约束 {fk[0]}")
                except:
                    pass
            
            # 检查 project_id 列是否存在
            cursor.execute("""
                SELECT COUNT(*) FROM information_schema.COLUMNS
                WHERE TABLE_SCHEMA = DATABASE()
                AND TABLE_NAME = 'class'
                AND COLUMN_NAME = 'project_id'
            """)
            if cursor.fetchone()[0] > 0:
                cursor.execute("ALTER TABLE `class` DROP COLUMN `project_id`")
                print("  → 已移除 project_id 列")
            else:
                print("  → project_id 列不存在，跳过")
        except Exception as e:
            print(f"  → 警告: {e}")
        
        # 4. 删除旧 project 表
        print("\n[4/4] 移除旧 project 表...")
        try:
            cursor.execute("DROP TABLE IF EXISTS `project`")
            print("  → 已删除旧 project 表")
        except Exception as e:
            print(f"  → 警告: {e}")
        
        conn.commit()
        cursor.close()
        conn.close()
        
        print("\n" + "=" * 50)
        print("迁移完成！")
        print("  - class_schedule 新增 conflict_type 字段")
        print("  - 已回填冲突类型数据")
        print("  - 已清理旧 project 表")
        print("  - 现在 Project 统一使用 training_type 表")
        print("=" * 50)


if __name__ == '__main__':
    migrate()
