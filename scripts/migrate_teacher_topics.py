"""
一次性迁移脚本：
1. 为 Teacher 表新增 topic_id 和 courses 字段（如不存在）
2. 从现有 TeacherCourseCombo 数据反填到 Teacher 记录
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from app import create_app
from models import db, Teacher, TeacherCourseCombo, Course
import json
from collections import defaultdict

app = create_app()

with app.app_context():
    # Step 1: 确保新字段存在（SQLite ALTER TABLE）
    import sqlite3
    db_path = app.config['SQLALCHEMY_DATABASE_URI'].replace('sqlite:///', '')
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # 检查 teacher 表是否已有 topic_id 列
    cursor.execute("PRAGMA table_info(teacher)")
    columns = [col[1] for col in cursor.fetchall()]

    if 'topic_id' not in columns:
        print("Adding 'topic_id' column to teacher table...")
        cursor.execute("ALTER TABLE teacher ADD COLUMN topic_id INTEGER REFERENCES topic(id)")
    else:
        print("'topic_id' column already exists.")

    if 'courses' not in columns:
        print("Adding 'courses' column to teacher table...")
        cursor.execute("ALTER TABLE teacher ADD COLUMN courses TEXT")
    else:
        print("'courses' column already exists.")

    conn.commit()
    conn.close()

    # Step 2: 从 TeacherCourseCombo 回填到 Teacher
    print("\n--- 开始数据迁移 ---")
    
    # 按 teacher_id 分组收集 combo 信息
    all_combos = TeacherCourseCombo.query.all()
    teacher_data = defaultdict(lambda: {'topics': defaultdict(list), 'courses': set()})

    for combo in all_combos:
        tid = combo.teacher_id
        course_name = combo.course.name if combo.course else None
        teacher_data[tid]['topics'][combo.topic_id].append(combo)
        if course_name:
            teacher_data[tid]['courses'].add(course_name)

    migrated = 0
    warnings = []
    for teacher_id, data in teacher_data.items():
        teacher = Teacher.query.get(teacher_id)
        if not teacher:
            warnings.append(f"  ⚠ Teacher id={teacher_id} 不存在，跳过")
            continue

        # 选择 combo 最多的课题
        topics = data['topics']
        if len(topics) > 1:
            best_topic = max(topics.keys(), key=lambda k: len(topics[k]))
            other_topics = [str(k) for k in topics.keys() if k != best_topic]
            warnings.append(
                f"  [WARN] 讲师 '{teacher.name}' 关联了多个课题({list(topics.keys())})，"
                f"选择组合最多的课题 {best_topic}，其余课题 [{', '.join(other_topics)}] 的 combo 保留不动"
            )
        else:
            best_topic = list(topics.keys())[0]

        # 收集该课题下的课程名
        topic_courses = []
        for combo in topics[best_topic]:
            if combo.course and combo.course.name:
                if combo.course.name not in topic_courses:
                    topic_courses.append(combo.course.name)

        # 回填
        if not teacher.topic_id:
            teacher.topic_id = best_topic
        if not teacher.courses:
            teacher.courses = json.dumps(topic_courses, ensure_ascii=False) if topic_courses else None

        migrated += 1
        print(f"  [OK] {teacher.name}: topic_id={best_topic}, courses={topic_courses}")

    db.session.commit()
    print(f"\n--- 迁移完成：{migrated} 位讲师已更新 ---")
    if warnings:
        print("\n--- 警告信息 ---")
        for w in warnings:
            print(w)
