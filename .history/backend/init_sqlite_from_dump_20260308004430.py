"""
从MySQL转储文件初始化SQLite数据库（无需MySQL连接）
用法: python init_sqlite_from_dump.py [path_to_sql_file]
默认读取桌面的 bqsxy.sql
"""
import re
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from app import create_app
from models import db

def parse_inserts(sql_text):
    """解析INSERT语句，返回 [(table_name, values_str), ...]"""
    pattern = re.compile(
        r"INSERT INTO `(\w+)` VALUES \((.+?)\);",
        re.DOTALL
    )
    results = []
    for m in pattern.finditer(sql_text):
        table = m.group(1)
        vals = m.group(2)
        results.append((table, vals))
    return results

def parse_values(vals_str):
    """解析一条VALUES中的值列表"""
    values = []
    i = 0
    current = ''
    in_quote = False
    while i < len(vals_str):
        c = vals_str[i]
        if c == "'" and not in_quote:
            in_quote = True
            current += c
        elif c == "'" and in_quote:
            # 检查转义
            if i + 1 < len(vals_str) and vals_str[i + 1] == "'":
                current += "''"
                i += 2
                continue
            in_quote = False
            current += c
        elif c == ',' and not in_quote:
            values.append(current.strip())
            current = ''
        else:
            current += c
        i += 1
    if current.strip():
        values.append(current.strip())
    return values

def sql_val_to_python(val):
    """将SQL值转为Python值"""
    if val == 'NULL':
        return None
    if val.startswith("'") and val.endswith("'"):
        return val[1:-1].replace("''", "'").replace("\\'", "'")
    try:
        return int(val)
    except ValueError:
        try:
            return float(val)
        except ValueError:
            return val

# 表的列顺序（与MySQL导出一致）
TABLE_COLUMNS = {
    'project': ['id', 'name', 'description', 'created_at'],
    'topic': ['id', 'project_id', 'sequence', 'name', 'is_fixed', 'description'],
    'homeroom': ['id', 'name', 'phone', 'email', 'created_at'],
    'teacher': ['id', 'name', 'title', 'expertise', 'phone', 'created_at'],
    'course': ['id', 'topic_id', 'name', 'description', 'duration_days', 'created_at'],
    'teacher_course_combo': ['id', 'topic_id', 'teacher_id', 'course_id', 'priority', 'created_at'],
    'class': ['id', 'project_id', 'name', 'homeroom_id', 'start_date', 'status', 'created_at'],
    'class_schedule': ['id', 'class_id', 'topic_id', 'combo_id', 'combo_id_2',
                        'scheduled_date', 'week_number', 'status', 'conflict_type',
                        'notes', 'merged_with', 'created_at', 'updated_at'],
    'monthly_plan': ['id', 'year', 'month', 'status', 'published_at', 'created_at', 'updated_at'],
    'schedule_constraint': ['id', 'monthly_plan_id', 'constraint_type', 'description',
                            'parsed_data', 'is_active', 'created_at'],
}

def main():
    # 确定SQL文件路径
    if len(sys.argv) > 1:
        sql_path = sys.argv[1]
    else:
        sql_path = os.path.expanduser('~/Desktop/bqsxy.sql')

    if not os.path.exists(sql_path):
        print(f"❌ 找不到SQL文件: {sql_path}")
        print("用法: python init_sqlite_from_dump.py [path_to_sql_file]")
        sys.exit(1)

    print(f"📖 读取SQL文件: {sql_path}")
    with open(sql_path, 'r', encoding='utf-8') as f:
        sql_text = f.read()

    inserts = parse_inserts(sql_text)
    print(f"  解析到 {len(inserts)} 条INSERT语句")

    # 创建数据库
    app = create_app()
    db_path = os.path.join(os.path.dirname(__file__), 'scheduler.db')

    with app.app_context():
        if os.path.exists(db_path):
            os.remove(db_path)
            print(f"🗑️  已删除旧数据库")

        db.create_all()
        print(f"✅ 已创建SQLite数据库: {db_path}")

        # 按表统计
        counts = {}
        for table, vals_str in inserts:
            if table not in TABLE_COLUMNS:
                print(f"  ⚠️ 跳过未知表: {table}")
                continue
            cols = TABLE_COLUMNS[table]
            vals = parse_values(vals_str)
            py_vals = [sql_val_to_python(v) for v in vals]

            # 构建字典
            row = {}
            for i, col in enumerate(cols):
                if i < len(py_vals):
                    row[col] = py_vals[i]

            sql = db.text(
                f"INSERT INTO \"{table}\" ({', '.join(cols)}) "
                f"VALUES ({', '.join([':' + c for c in cols])})"
            )
            db.session.execute(sql, row)
            counts[table] = counts.get(table, 0) + 1

        db.session.commit()
        print("\n📊 导入统计:")
        for t, c in counts.items():
            print(f"  ✅ {t}: {c} 条")

    print("\n🎉 初始化完成！可以直接启动应用: python app.py")

if __name__ == '__main__':
    main()
