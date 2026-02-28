import sys, os
sys.path.insert(0, os.path.join(os.getcwd(), 'backend'))
from routes import schedule
from datetime import date

# Simulate a class with homeroom name
class DummyClass:
    def __init__(self, homeroom_name):
        class H: pass
        self.homeroom = H()
        self.homeroom.name = homeroom_name

# Candidate Saturday
sat = date.fromisoformat('2026-04-18')  # Saturday of the week containing 2026-04-13..17

# Constraint: homeroom Wang Jianguo unavailable Mon-Fri 2026-04-13..17
constraints = {
    'homeroom_unavailable': [
        {
            'homeroom_name': '王建国',
            'dates': ['2026-04-13','2026-04-14','2026-04-15','2026-04-16','2026-04-17']
        }
    ]
}

cls = DummyClass('王建国')

# Reproduce the check block from generate_schedule
week_monday = sat - schedule.timedelta(days=5)
week_sunday = week_monday + schedule.timedelta(days=6)

found = False
for u in constraints.get('homeroom_unavailable', []):
    if u.get('homeroom_name') != cls.homeroom.name:
        continue
    dates = u.get('dates', [])
    parsed = []
    for item in dates:
        try:
            parsed.append(date.fromisoformat(item))
        except Exception:
            pass
    for pd in parsed:
        if week_monday <= pd <= week_sunday:
            print('CONFLICT: week', week_monday, 'to', week_sunday, 'contains', pd)
            found = True
            break
    if found:
        break

print('Result conflict?', found)
