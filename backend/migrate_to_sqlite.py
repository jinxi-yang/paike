"""
MySQL → SQLite 迁移脚本
用法: python migrate_to_sqlite.py
功能: 读取现有MySQL数据，导出到SQLite数据库文件
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from app import create_app
from models import db, Project, Topic, Homeroom, Teacher, Course, TeacherCourseCombo
from models import Class, ClassSchedule, MonthlyPlan, ScheduleConstraint
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

def migrate():
    # 1. 从MySQL读数据
    print("📖 从 MySQL 读取数据...")
    app = create_app()
    with app.app_context():
        projects = [row_to_dict(p) for p in Project.query.all()]
        topics = [row_to_dict(t) for t in Topic.query.all()]
        homerooms = [row_to_dict(h) for h in Homeroom.query.all()]
        teachers = [row_to_dict(t) for t in Teacher.query.all()]
        courses = [row_to_dict(c) for c in Course.query.all()]
        combos = [row_to_dict(c) for c in TeacherCourseCombo.query.all()]
        classes = [row_to_dict(c) for c in Class.query.all()]
        schedules = [row_to_dict(s) for s in ClassSchedule.query.all()]
        plans = [row_to_dict(p) for p in MonthlyPlan.query.all()]
        constraints = [row_to_dict(c) for c in ScheduleConstraint.query.all()]

    print(f"  项目: {len(projects)}, 课题: {len(topics)}, 班主任: {len(homerooms)}")
    print(f"  讲师: {len(teachers)}, 课程: {len(courses)}, 组合: {len(combos)}")
    print(f"  班级: {len(classes)}, 课表: {len(schedules)}")
    print(f"  月度计划: {len(plans)}, 约束: {len(constraints)}")

    # 2. 创建SQLite数据库
    db_path = os.path.join(os.path.dirname(__file__), 'scheduler.db')
    if os.path.exists(db_path):
        os.remove(db_path)
        print(f"🗑️  已删除旧数据库: {db_path}")

    sqlite_uri = f"sqlite:///{db_path}"
    engine = create_engine(sqlite_uri)

    # 用metadata创建所有表
    db.metadata.create_all(engine)
    print(f"✅ 已创建SQLite数据库: {db_path}")

    # 3. 写入数据 (按外键顺序)
    print("📝 写入数据...")
    with Session(engine) as session:
        for table_cls, data, name in [
            (Project, projects, '项目'),
            (Topic, topics, '课题'),
            (Homeroom, homerooms, '班主任'),
            (Teacher, teachers, '讲师'),
            (Course, courses, '课程'),
            (TeacherCourseCombo, combos, '教-课组合'),
            (Class, classes, '班级'),
            (ClassSchedule, schedules, '课表'),
            (MonthlyPlan, plans, '月度计划'),
            (ScheduleConstraint, constraints, '约束'),
        ]:
            for row in data:
                session.execute(table_cls.__table__.insert().values(**row))
            session.commit()
            print(f"  ✅ {name}: {len(data)} 条")

    print("\n🎉 迁移完成！请修改 config.py 使用 SQLite 连接。")

def row_to_dict(obj):
    """将SQLAlchemy对象转为字典（只包含列字段）"""
    return {c.name: getattr(obj, c.name) for c in obj.__table__.columns}

if __name__ == '__main__':
    migrate()
