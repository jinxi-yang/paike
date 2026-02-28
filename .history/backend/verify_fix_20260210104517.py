
import sys
import os
from datetime import date

# Ensure we can import from current directory
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from routes.schedule import is_holiday
except ImportError as e:
    print(f"Import Error: {e}")
    # Try adjusting path if needed, but it should work if run from backend/
    sys.exit(1)

def test():
    print("=== Verifying Holiday Logic ===")
    
    # Test Case 1: Weekend in March 2026 (Should NOT be conflicts now)
    sat = date(2026, 3, 7)
    sun = date(2026, 3, 8)
    
    print(f"Checking Saturday {sat}: Holiday={is_holiday(sat)}")
    print(f"Checking Sunday   {sun}: Holiday={is_holiday(sun)}")
    
    if not is_holiday(sat) and not is_holiday(sun):
        print("PASS: Weekend is available for scheduling.")
    else:
        print("FAIL: Weekend is still flagged as holiday.")

    # Test Case 2: Actual Holiday (e.g., Labor Day)
    may1 = date(2026, 5, 1)
    print(f"Checking Labor Day {may1}: Holiday={is_holiday(may1)}")
    if is_holiday(may1):
        print("PASS: Labor Day is correctly identified as holiday.")
    else:
        print("FAIL: Labor Day was NOT identified as holiday.")

if __name__ == "__main__":
    test()
