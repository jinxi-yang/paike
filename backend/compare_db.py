import sqlite3
import json
from datetime import datetime

DB_CURRENT = 'd:/学习/outputmsg/排课/paike/backend/scheduler.db'
DB_OLD = 'd:/学习/outputmsg/排课/paike/backend/scheduler_old.db'

def get_connection(db_path):
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

def compare_table(curr_conn, old_conn, table_name, pk='id'):
    curr_rows = {row[pk]: dict(row) for row in curr_conn.execute(f"SELECT * FROM {table_name}")}
    old_rows = {row[pk]: dict(row) for row in old_conn.execute(f"SELECT * FROM {table_name}")}
    
    # Find common columns
    common_cols = set(curr_rows[list(curr_rows.keys())[0]].keys()) if curr_rows else set()
    if old_rows:
        old_cols = set(old_rows[list(old_rows.keys())[0]].keys())
        if common_cols:
            common_cols &= old_cols
        else:
            common_cols = old_cols
    
    added = []
    removed = []
    modified = []
    
    all_pks = set(curr_rows.keys()) | set(old_rows.keys())
    
    for k in sorted(all_pks):
        if k not in old_rows:
            added.append(curr_rows[k])
        elif k not in curr_rows:
            removed.append(old_rows[k])
        else:
            diff = {}
            for col in common_cols:
                if curr_rows[k][col] != old_rows[k][col]:
                    diff[col] = {'old': old_rows[k][col], 'new': curr_rows[k][col]}
            if diff:
                modified.append({'id': k, 'changes': diff, 'data': curr_rows[k]})
                
    return added, removed, modified

def main():
    curr_conn = get_connection(DB_CURRENT)
    old_conn = get_connection(DB_OLD)
    
    print(f"Comparing databases...")
    print(f"Current: {DB_CURRENT}")
    print(f"Old:     {DB_OLD}")
    print("-" * 50)
    
    # Tables to compare
    tables = ['class', 'topic', 'teacher', 'teacher_course_combo', 'class_schedule']
    
    results = {}
    for table in tables:
        added, removed, modified = compare_table(curr_conn, old_conn, table)
        results[table] = {'added': added, 'removed': removed, 'modified': modified}
        
    # Summarize findings
    for table, res in results.items():
        if res['added'] or res['removed'] or res['modified']:
            print(f"Table: {table}")
            print(f"  Added:    {len(res['added'])}")
            print(f"  Removed:  {len(res['removed'])}")
            print(f"  Modified: {len(res['modified'])}")
            
            if table == 'class_schedule' and res['modified']:
                print("\n  Top modified schedule details:")
                for m in res['modified'][:10]:
                    changes = []
                    for col, val in m['changes'].items():
                        changes.append(f"{col}: {val['old']} -> {val['new']}")
                    
                    # Get class name and topic name for context
                    class_id = m['data']['class_id']
                    topic_id = m['data']['topic_id']
                    class_name = curr_conn.execute("SELECT name FROM class WHERE id=?", (class_id,)).fetchone()[0]
                    topic_name = curr_conn.execute("SELECT name FROM topic WHERE id=?", (topic_id,)).fetchone()[0]
                    
                    print(f"    - ID {m['id']} (Class: {class_name}, Topic: {topic_name}):")
                    for c in changes:
                        print(f"      * {c}")
            
            if table == 'class_schedule' and res['added']:
                print("\n  Added schedule details:")
                for a in res['added'][:10]:
                    class_name = curr_conn.execute("SELECT name FROM class WHERE id=?", (a['class_id'],)).fetchone()[0]
                    topic_name = curr_conn.execute("SELECT name FROM topic WHERE id=?", (a['topic_id'],)).fetchone()[0]
                    print(f"    - ID {a['id']} (Class: {class_name}, Topic: {topic_name}, Date: {a['scheduled_date']})")
            
            print("-" * 30)
    
    curr_conn.close()
    old_conn.close()

if __name__ == '__main__':
    main()
