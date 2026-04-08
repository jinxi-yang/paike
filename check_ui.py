with open('frontend/index.html', encoding='utf-8') as f:
    lines = f.readlines()
# find all lines with the day2 assignment pattern
print("=== Day 2 display logic in all views ===\n")
for i, l in enumerate(lines):
    if ('combo_2' in l or 'combo_id_2' in l) and ('day1Teacher' in l or 'day1Course' in l or 'day2Teacher' in l or 'day2Course' in l):
        print(f"Line {i+1}: {l.rstrip()[:150]}")
