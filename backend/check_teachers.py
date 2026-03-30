import sqlite3
import os
import sys
import codecs

if sys.platform == "win32":
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.detach())

db_path = os.path.join(os.path.dirname(__file__), 'scheduler.db')
conn = sqlite3.connect(db_path)
cursor = conn.cursor()
cursor.execute("SELECT name FROM teacher WHERE name LIKE '%吴%'")
rows = cursor.fetchall()
for r in rows:
    print(r[0])
conn.close()
