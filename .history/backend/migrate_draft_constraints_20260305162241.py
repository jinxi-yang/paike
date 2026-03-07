"""
迁移脚本：为新功能添加数据库字段和表
- monthly_plan 表添加 updated_at 字段
- 创建 schedule_constraint 表
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from app import create_app
from models import db

app = create_app()

with app.app_context():
    conn = db.engine.raw_connection()
    cursor = conn.cursor()
    
    changes = []
    
    # 1. monthly_plan 添加 updated_at 列
    try:
        cursor.execute("SELECT updated_at FROM monthly_plan LIMIT 1")
        print("✓ monthly_plan.updated_at 已存在")
    except Exception:
        conn.rollback()
        try:
            cursor.execute("ALTER TABLE monthly_plan ADD COLUMN updated_at DATETIME DEFAULT NULL")
            conn.commit()
            changes.append("monthly_plan.updated_at")
            print("✓ 已添加 monthly_plan.updated_at")
        except Exception as e:
            conn.rollback()
            print(f"✗ 添加 monthly_plan.updated_at 失败: {e}")
    
    # 2. 创建 schedule_constraint 表
    try:
        cursor.execute("SELECT 1 FROM schedule_constraint LIMIT 1")
        print("✓ schedule_constraint 表已存在")
    except Exception:
        conn.rollback()
        try:
            cursor.execute("""
                CREATE TABLE schedule_constraint (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    monthly_plan_id INT NOT NULL,
                    constraint_type VARCHAR(30) DEFAULT 'custom' COMMENT '类型',
                    description TEXT NOT NULL COMMENT '原始描述',
                    parsed_data TEXT COMMENT 'AI解析后的JSON',
                    is_active TINYINT(1) DEFAULT 1 COMMENT '是否启用',
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (monthly_plan_id) REFERENCES monthly_plan(id) ON DELETE CASCADE
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
            """)
            conn.commit()
            changes.append("schedule_constraint 表")
            print("✓ 已创建 schedule_constraint 表")
        except Exception as e:
            conn.rollback()
            print(f"✗ 创建 schedule_constraint 表失败: {e}")
    
    cursor.close()
    conn.close()
    
    if changes:
        print(f"\n完成！共 {len(changes)} 项变更: {', '.join(changes)}")
    else:
        print("\n无需变更，所有结构已是最新")
