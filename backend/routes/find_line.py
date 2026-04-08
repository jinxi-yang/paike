import ast
src = open('d:/学习/outputmsg/排课/paike/backend/routes/schedule.py', encoding='utf-8').read()
lines = src.splitlines()
for i, l in enumerate(lines):
    if 'weight_affinity =' in l:
        print(f"Line {i+1}: {l}")
    if 'SCORE_IN_MONTH' in l:
        print(f"Line {i+1}: {l}")
