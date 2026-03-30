import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), 'scheduler.db')

def migrate():
    print("Connecting to database...")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    columns_to_add = [
        ('day2_has_opening', 'BOOLEAN DEFAULT 0'),
        ('day2_has_team_building', 'BOOLEAN DEFAULT 0'),
        ('day2_has_closing', 'BOOLEAN DEFAULT 0')
    ]
    
    for col_name, col_def in columns_to_add:
        try:
            cursor.execute(f"ALTER TABLE class_schedule ADD COLUMN {col_name} {col_def}")
            print(f"Added column {col_name}")
        except sqlite3.OperationalError as e:
            if "duplicate column name" in str(e).lower():
                print(f"Column {col_name} already exists.")
            else:
                print(f"Error adding {col_name}: {e}")
                
    conn.commit()
    conn.close()
    print("Migration finished.")

if __name__ == '__main__':
    migrate()
