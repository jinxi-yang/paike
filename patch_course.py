import re

with open(r"backend\routes\schedule.py", "r", encoding="utf-8") as f:
    content = f.read()

# Replace all variations of .course.name checks
content = re.sub(
    r"s\.combo\.course\.name if s\.combo\.teacher and s\.combo\.course else",
    r"s.combo.course_name if s.combo and s.combo.teacher else",
    content
)

content = re.sub(
    r"s\.combo_2\.course\.name if s\.combo_2\.teacher and s\.combo_2\.course else",
    r"s.combo_2.course_name if s.combo_2 and s.combo_2.teacher else",
    content
)

content = re.sub(
    r"s\.combo\.course\.name if s\.combo and s\.combo\.course else",
    r"s.combo.course_name if s.combo else",
    content
)

content = re.sub(
    r"s\.combo_2\.course\.name if s\.combo_2 and s\.combo_2\.course else",
    r"s.combo_2.course_name if s.combo_2 else",
    content
)

content = re.sub(
    r"c1\.course\.name if c1 and c1\.course else",
    r"c1.course_name if c1 else",
    content
)

content = re.sub(
    r"c2\.course\.name if c2 and c2\.course else",
    r"c2.course_name if c2 else",
    content
)

content = re.sub(
    r"c\.course\.name if c\.course else",
    r"c.course_name if c else",
    content
)

content = re.sub(
    r"combo1\.course\.name if combo1 and combo1\.course else",
    r"combo1.course_name if combo1 else",
    content
)

content = re.sub(
    r"combo2\.course\.name if combo2 and combo2\.course else",
    r"combo2.course_name if combo2 else",
    content
)

content = re.sub(
    r"best_combo1\.course\.name if best_combo1 and best_combo1\.course else",
    r"best_combo1.course_name if best_combo1 else",
    content
)

content = re.sub(
    r"best_combo2\.course\.name if best_combo2 and best_combo2\.course else",
    r"best_combo2.course_name if best_combo2 else",
    content
)

with open(r"backend\routes\schedule.py", "w", encoding="utf-8") as f:
    f.write(content)

print("Course name logic successfully patched.")
