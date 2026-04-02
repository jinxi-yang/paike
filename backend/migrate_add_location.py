"""
迁移脚本：为 class_schedule 表添加 location_id 字段
"""
import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), 'scheduler.db')

def migrate():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # 检查字段是否已存在
    cursor.execute("PRAGMA table_info(class_schedule)")
    columns = [row[1] for row in cursor.fetchall()]
    
    if 'location_id' not in columns:
        cursor.execute("ALTER TABLE class_schedule ADD COLUMN location_id INTEGER REFERENCES city(id)")
        conn.commit()
        print("[OK] class_schedule.location_id added")
    else:
        print("[INFO] class_schedule.location_id already exists, skip")
    
    conn.close()

if __name__ == '__main__':
    migrate()
    print("Migration done")
