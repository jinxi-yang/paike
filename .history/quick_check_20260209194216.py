#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys
sys.path.insert(0, 'D:/项目/AI/北清商学院/paike/backend')

from models import db, Course, Topic
from app import create_app

app = create_app()
with app.app_context():
    total = Course.query.count()
    assigned = Course.query.filter(Course.topic_id.isnot(None)).count()
    unassigned = total - assigned
    
    print(f"总课程: {total}")
    print(f"已关联: {assigned}")
    print(f"未关联: {unassigned}")
    
    if unassigned > 0:
        print("\n未关联的课程:")
        for c in Course.query.filter(Course.topic_id.is_(None)).limit(10).all():
            print(f"  - {c.name}")
    
    print(f"\n课题总数: {Topic.query.count()}")
    if Topic.query.count() > 0:
        print("前3个课题名称:")
        for t in Topic.query.limit(3).all():
            print(f"  - '{t.name}'")
