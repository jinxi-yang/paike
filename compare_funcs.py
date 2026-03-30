import re

# Get all disassembled functions
with open("schedule_full_disassembled.txt", "r", encoding="utf-8") as f:
    dis_funcs = re.findall(r"--- Function/Code: ([a-zA-Z_]\w*) ---", f.read())

dis_funcs = [f for f in dis_funcs if f != '<module>' and f != '<listcomp>' and f != '<dictcomp>' and f != '<genexpr>']
dis_funcs_set = set(dis_funcs)

# Get all current functions
with open(r"backend\routes\schedule.py", "r", encoding="utf-8") as f:
    curr_funcs = re.findall(r"def ([a-zA-Z_]\w*)\(", f.read())

curr_funcs_set = set(curr_funcs)

missing = dis_funcs_set - curr_funcs_set
extra = curr_funcs_set - dis_funcs_set

print("Missing from current (Existed in compiled Pyc, but wiped):")
for m in sorted(missing):
    print("  -", m)

print("\nExtra in current (Did not exist in Pyc):")
for e in sorted(extra):
    print("  -", e)
