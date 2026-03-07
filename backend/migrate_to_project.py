"""
数据库迁移脚本 - 彻底统一 training_type → project
运行方法: python migrate_to_project.py

执行内容:
1. 重命名表 training_type → project
2. 重命名 topic.training_type_id → topic.project_id
3. 重命名 class.training_type_id → class.project_id
4. 添加 class_schedule.conflict_type 字段
5. 回填冲突类型数据
6. 删除旧 project 表（若存在）
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import Config
from flask import Flask
from flask_sqlalchemy import SQLAlchemy

def migrate():
    app = Flask(__name__)
    app.config.from_object(Config)
    db = SQLAlchemy(app)
    
    with app.app_context():
        conn = db.engine.raw_connection()
        cursor = conn.cursor()
        
        print("=" * 60)
        print("北清商学院排课系统 - 数据库迁移（彻底统一到 Project）")
        print("=" * 60)
        
        # 0. 先检查是否需要迁移（如果 project 表已存在且是目标表则跳过）
        cursor.execute("""
            SELECT COUNT(*) FROM information_schema.TABLES
            WHERE TABLE_SCHEMA = DATABASE()
            AND TABLE_NAME = 'training_type'
        """)
        has_training_type = cursor.fetchone()[0] > 0
        
        cursor.execute("""
            SELECT COUNT(*) FROM information_schema.TABLES
            WHERE TABLE_SCHEMA = DATABASE()
            AND TABLE_NAME = 'project'
        """)
        has_project = cursor.fetchone()[0] > 0
        
        if has_training_type:
            # ========== Step 1: 处理旧 project 表（如果存在） ==========
            if has_project:
                print("\n[1/6] 发现旧 project 表，先处理...")
                # 检查旧 project 表是否被其他外键引用
                cursor.execute("""
                    SELECT CONSTRAINT_NAME, TABLE_NAME FROM information_schema.KEY_COLUMN_USAGE
                    WHERE TABLE_SCHEMA = DATABASE()
                    AND REFERENCED_TABLE_NAME = 'project'
                """)
                fks = cursor.fetchall()
                for fk_name, fk_table in fks:
                    try:
                        cursor.execute(f"ALTER TABLE `{fk_table}` DROP FOREIGN KEY `{fk_name}`")
                        print(f"  → 移除外键 {fk_table}.{fk_name}")
                    except Exception as e:
                        print(f"  → 警告: {e}")
                
                # 删除旧 project 表中引用它的列
                cursor.execute("""
                    SELECT COUNT(*) FROM information_schema.COLUMNS
                    WHERE TABLE_SCHEMA = DATABASE()
                    AND TABLE_NAME = 'class'
                    AND COLUMN_NAME = 'project_id'
                """)
                if cursor.fetchone()[0] > 0:
                    try:
                        cursor.execute("ALTER TABLE `class` DROP COLUMN `project_id`")
                        print("  → 移除 class.project_id 列（旧外键）")
                    except:
                        pass
                
                cursor.execute("DROP TABLE IF EXISTS `project`")
                print("  → 已删除旧 project 表")
            else:
                print("\n[1/6] 无旧 project 表，跳过")
            
            # ========== Step 2: 重命名 training_type → project ==========
            print("\n[2/6] 重命名表 training_type → project...")
            try:
                cursor.execute("RENAME TABLE `training_type` TO `project`")
                print("  → 表重命名成功")
            except Exception as e:
                print(f"  → 错误: {e}")
                print("  → 迁移终止！")
                conn.close()
                return
            
            # ========== Step 3: topic.training_type_id → topic.project_id ==========
            print("\n[3/6] 重命名 topic.training_type_id → topic.project_id...")
            try:
                # 先移除旧外键约束
                cursor.execute("""
                    SELECT CONSTRAINT_NAME FROM information_schema.KEY_COLUMN_USAGE
                    WHERE TABLE_SCHEMA = DATABASE()
                    AND TABLE_NAME = 'topic'
                    AND COLUMN_NAME = 'training_type_id'
                    AND REFERENCED_TABLE_NAME IS NOT NULL
                """)
                fks = cursor.fetchall()
                for (fk_name,) in fks:
                    cursor.execute(f"ALTER TABLE `topic` DROP FOREIGN KEY `{fk_name}`")
                    print(f"  → 移除旧外键 {fk_name}")
                
                # 重命名列
                cursor.execute("""
                    ALTER TABLE `topic` CHANGE COLUMN `training_type_id` `project_id`
                    INT NOT NULL COMMENT '项目ID'
                """)
                print("  → 列重命名成功")
                
                # 添加新外键
                cursor.execute("""
                    ALTER TABLE `topic` ADD CONSTRAINT `fk_topic_project`
                    FOREIGN KEY (`project_id`) REFERENCES `project`(`id`)
                """)
                print("  → 新外键约束添加成功")
            except Exception as e:
                print(f"  → 错误: {e}")
            
            # ========== Step 4: class.training_type_id → class.project_id ==========
            print("\n[4/6] 重命名 class.training_type_id → class.project_id...")
            try:
                # 先移除旧外键约束
                cursor.execute("""
                    SELECT CONSTRAINT_NAME FROM information_schema.KEY_COLUMN_USAGE
                    WHERE TABLE_SCHEMA = DATABASE()
                    AND TABLE_NAME = 'class'
                    AND COLUMN_NAME = 'training_type_id'
                    AND REFERENCED_TABLE_NAME IS NOT NULL
                """)
                fks = cursor.fetchall()
                for (fk_name,) in fks:
                    cursor.execute(f"ALTER TABLE `class` DROP FOREIGN KEY `{fk_name}`")
                    print(f"  → 移除旧外键 {fk_name}")
                
                # 重命名列
                cursor.execute("""
                    ALTER TABLE `class` CHANGE COLUMN `training_type_id` `project_id`
                    INT NOT NULL COMMENT '所属项目'
                """)
                print("  → 列重命名成功")
                
                # 添加新外键
                cursor.execute("""
                    ALTER TABLE `class` ADD CONSTRAINT `fk_class_project`
                    FOREIGN KEY (`project_id`) REFERENCES `project`(`id`)
                """)
                print("  → 新外键约束添加成功")
            except Exception as e:
                print(f"  → 错误: {e}")
                
        elif has_project:
            print("\n[1-4] training_type 表不存在，project 表已存在 → 可能已经迁移过")
            print("  → 跳过表重命名和列重命名步骤")
        else:
            print("\n[1-4] 两个表都不存在 → 首次运行，将由 db.create_all() 自动创建")
        
        # ========== Step 5: 添加 conflict_type 字段 ==========
        print("\n[5/6] 添加 class_schedule.conflict_type 字段...")
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
        
        # ========== Step 6: 回填冲突类型 ==========
        print("\n[6/6] 回填已有冲突记录的 conflict_type...")
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
        
        conn.commit()
        cursor.close()
        conn.close()
        
        print("\n" + "=" * 60)
        print("迁移完成！数据库现在完全统一为 project 概念：")
        print("  - 表名: project (原 training_type)")
        print("  - topic.project_id (原 training_type_id)")
        print("  - class.project_id (原 training_type_id)")
        print("  - class_schedule.conflict_type 字段已添加")
        print("=" * 60)


if __name__ == '__main__':
    migrate()
