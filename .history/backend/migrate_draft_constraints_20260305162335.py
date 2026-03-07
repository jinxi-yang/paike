"""
Migration: add updated_at to monthly_plan, create schedule_constraint table
"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))

from app import create_app
from models import db

app = create_app()

with app.app_context():
    conn = db.engine.raw_connection()
    cursor = conn.cursor()
    changes = []

    # 1. monthly_plan add updated_at
    try:
        cursor.execute("SELECT updated_at FROM monthly_plan LIMIT 1")
        print("[OK] monthly_plan.updated_at exists")
    except Exception:
        conn.rollback()
        try:
            cursor.execute("ALTER TABLE monthly_plan ADD COLUMN updated_at DATETIME DEFAULT NULL")
            conn.commit()
            changes.append("monthly_plan.updated_at")
            print("[OK] Added monthly_plan.updated_at")
        except Exception as e:
            conn.rollback()
            print(f"[FAIL] monthly_plan.updated_at: {e}")

    # 2. create schedule_constraint table
    try:
        cursor.execute("SELECT 1 FROM schedule_constraint LIMIT 1")
        print("[OK] schedule_constraint table exists")
    except Exception:
        conn.rollback()
        try:
            cursor.execute("""
                CREATE TABLE schedule_constraint (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    monthly_plan_id INT NOT NULL,
                    constraint_type VARCHAR(30) DEFAULT 'custom',
                    description TEXT NOT NULL,
                    parsed_data TEXT,
                    is_active TINYINT(1) DEFAULT 1,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (monthly_plan_id) REFERENCES monthly_plan(id) ON DELETE CASCADE
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
            """)
            conn.commit()
            changes.append("schedule_constraint table")
            print("[OK] Created schedule_constraint table")
        except Exception as e:
            conn.rollback()
            print(f"[FAIL] schedule_constraint: {e}")

    cursor.close()
    conn.close()
    print(f"\nDone! {len(changes)} changes: {', '.join(changes) if changes else 'none needed'}")
