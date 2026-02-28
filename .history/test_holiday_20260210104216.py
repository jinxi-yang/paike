
import json
from datetime import date, timedelta

_local_holiday_data = {}
try:
    with open('backend/holidays_2026.json', 'r', encoding='utf-8') as f:
        _local_holiday_data = json.load(f)
    print(f"Loaded {len(_local_holiday_data)} holiday records")
except Exception as e:
    print(f"Error loading: {e}")

def is_holiday(check_date):
    if isinstance(check_date, str):
        check_date = date.fromisoformat(check_date)
    
    date_str = check_date.isoformat()
    
    # Check local (The bug is here)
    if date_str in _local_holiday_data:
        print(f"DEBUG: Found {date_str} in local data")
        return _local_holiday_data[date_str].get('holiday', False)
    
    # Mismatch check: try MM-DD
    mm_dd = date_str[5:]
    if mm_dd in _local_holiday_data:
        print(f"DEBUG: Found {mm_dd} in local data (Matched by MM-DD)")
        return _local_holiday_data[mm_dd].get('holiday', False)

    is_sunday = check_date.weekday() == 6
    return is_sunday

# Test a known Saturday/Sunday in March 2026
# March 7 (Sat), March 8 (Sun)
sat = date(2026, 3, 7)
sun = date(2026, 3, 8)

print(f"Checking {sat}: {is_holiday(sat)}")
print(f"Checking {sun}: {is_holiday(sun)}")

if is_holiday(sat) or is_holiday(sun):
    print("RESULT: Weekend conflict detected!")
else:
    print("RESULT: No conflict.")
