import sqlite3
import os
import glob

base_dir = os.path.dirname(__file__)
db_path = os.path.join(base_dir, 'scheduler.db')
backups = glob.glob(os.path.join(base_dir, 'scheduler.db.bak*'))

def get_may_schedules(db_file):
    try:
        conn = sqlite3.connect(db_file)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='class_schedule'")
        if not cursor.fetchone():
            return {}
            
        cursor.execute("""
            SELECT cs.id, c.name, cs.scheduled_date, cs.status, cs.topic_id
            FROM class_schedule cs
            JOIN class c ON cs.class_id = c.id
            WHERE cs.scheduled_date >= '2026-05-01' AND cs.scheduled_date < '2026-06-01'
            AND (cs.status != 'cancelled' OR cs.status IS NULL)
        """)
        rows = cursor.fetchall()
        conn.close()
        
        data = {}
        for r in rows:
            key = (r[1], r[2])
            # Store full row info
            data[key] = {
                'id': r[0],
                'status': r[3],
                'topic_id': r[4]
            }
        return data
    except sqlite3.OperationalError:
        return {}
    except Exception as e:
        print(f"Error reading {db_file}: {e}")
        return {}

curr_may = get_may_schedules(db_path)
print(f"Current DB May classes: {len(curr_may)}")
for k in sorted(curr_may.keys()):
    print(f"  {k[1]} - {k[0]}")

all_historical_keys = set()
backup_data = {}

for bak in backups:
    bak_name = os.path.basename(bak)
    may_data = get_may_schedules(bak)
    if may_data:
        print(f"\nBackup {bak_name} May classes: {len(may_data)}")
        for k in sorted(may_data.keys()):
            all_historical_keys.add(k)
            if k not in backup_data:
                backup_data[k] = []
            backup_data[k].append((bak_name, may_data[k]))

missing_keys = all_historical_keys - set(curr_may.keys())

print("\n=== MISSING MAY SCHEDULES (Ever existed in ANY backup, but NOT in Current DB) ===")
for k in sorted(missing_keys):
    print(f"MISSING: Class {k[0]} on {k[1]}")
    for b_name, b_info in backup_data[k]:
        print(f"    found in {b_name} (ID={b_info['id']}, Status={b_info['status']}, TopicID={b_info['topic_id']})")

if not missing_keys:
    print("\nNo Missing May schedules found across ALL backups.")
