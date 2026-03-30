with open(r"backend\routes\schedule.py", "r", encoding="utf-8") as f:
    content = f.read()

import re

# 1. evaluate preview
target = r"def _get_candidate_saturdays"
if re.search(target, content):
    print("Found _get_candidate_saturdays")
else:
    print("NOT Found _get_candidate_saturdays")

# 2. adjust schedule
target2 = r"if 'new_date' in data:\s*new_date = date.fromisoformat\(data\['new_date'\]\)\s*# 检查是否是周六\s*if new_date\.weekday\(\) != 5:"
if re.search(target2, content):
    print("Found adjust schedule")
else:
    print("NOT Found adjust schedule")
