"""Database migration script - Add City table, Class.city_id, ClassSchedule ceremony toggles"""
import sys, os, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.path.insert(0, os.path.dirname(__file__))

from app import create_app
from models import db

app = create_app()

with app.app_context():
    # Use raw SQL for SQLite migrations since ALTER TABLE is limited
    conn = db.engine.raw_connection()
    cursor = conn.cursor()
    
    # 1. Create City table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS city (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name VARCHAR(50) NOT NULL UNIQUE,
            max_classrooms INTEGER DEFAULT 99,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    print("✅ Created city table")
    
    # 2. Insert default cities
    for name, rooms in [('北京', 7), ('太原', 99), ('宁夏', 99), ('深圳', 99)]:
        try:
            cursor.execute("INSERT INTO city (name, max_classrooms) VALUES (?, ?)", (name, rooms))
            print(f"  → Inserted city: {name} (max_classrooms={rooms})")
        except Exception as e:
            if 'UNIQUE' in str(e):
                print(f"  → City {name} already exists, skipping")
            else:
                raise
    
    # 3. Add city_id to class table if not exists
    try:
        cursor.execute("ALTER TABLE class ADD COLUMN city_id INTEGER REFERENCES city(id)")
        print("✅ Added class.city_id")
    except Exception as e:
        if 'duplicate column' in str(e).lower():
            print("⚠️ class.city_id already exists")
        else:
            raise
    
    # 4. Add ceremony toggles to class_schedule
    for col in ['has_opening', 'has_team_building', 'has_closing']:
        try:
            cursor.execute(f"ALTER TABLE class_schedule ADD COLUMN {col} BOOLEAN DEFAULT 0")
            print(f"✅ Added class_schedule.{col}")
        except Exception as e:
            if 'duplicate column' in str(e).lower():
                print(f"⚠️ class_schedule.{col} already exists")
            else:
                raise
    
    conn.commit()
    conn.close()
    print("\n✅ Migration complete!")
