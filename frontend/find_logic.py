import sys, re
with open('index.html', 'r', encoding='utf-8') as f:
    lines = f.readlines()
for i, line in enumerate(lines):
    if 'renderMonthly' in line or 'renderWeekly' in line or 'edit' in line.lower():
        print(f"{i+1}: {line.strip()[:100]}")
