import sqlite3
import os

db_path = os.path.join(os.path.dirname(__file__), 'scheduler.db')
bak_path = os.path.join(os.path.dirname(__file__), 'scheduler.db.bak_before_course_removal')

def get_all_schedules(db_file):
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT cs.id, c.name, cs.scheduled_date, cs.status
        FROM class_schedule cs
        JOIN class c ON cs.class_id = c.id
        WHERE cs.scheduled_date IS NOT NULL
    """)
    rows = cursor.fetchall()
    conn.close()
    
    # dictionary: (class_name, date) -> list of statuses
    data = {}
    for r in rows:
        key = (r[1], r[2])
        if key not in data:
            data[key] = []
        data[key].append(r[3])
    return data

curr_data = get_all_schedules(db_path)
bak_data = get_all_schedules(bak_path)

missing_keys = set(bak_data.keys()) - set(curr_data.keys())

# We ignore newly added items like EMBA126 on different dates since we might have added them?
# Wait, let's just see any differences
diff_count = 0
print("=== MISSING SCHEDULES (In Backup, NOT in Current) ===")
for key in sorted(missing_keys, key=lambda x: x[1]): # sort by date
    k_class, k_date = key
    statuses = bak_data[key]
    print(f"MISSING: Class {k_class} on {k_date} (Statuses in backup: {statuses})")
    diff_count += 1
    
extra_keys = set(curr_data.keys()) - set(bak_data.keys())
print("\n=== EXTRA SCHEDULES (In Current, NOT in Backup) ===")
for key in sorted(extra_keys, key=lambda x: x[1]):
    k_class, k_date = key
    statuses = curr_data[key]
    print(f"EXTRA: Class {k_class} on {k_date} (Statuses in current: {statuses})")
    diff_count += 1

print(f"\nTotal Discrepancies Found: {diff_count}")
