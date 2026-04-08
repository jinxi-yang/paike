src = open('d:/学习/outputmsg/排课/paike/backend/routes/schedule.py', encoding='utf-8').read()
lines = src.splitlines()
for i, l in enumerate(lines):
    if 'combo_id_2' in l and ('.combo_id_2 =' in l):
        print(f'{i+1}: {l.strip()[:140]}')
