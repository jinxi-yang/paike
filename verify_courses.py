#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
验证课程-课题关联的脚本
"""
import sys
sys.path.insert(0, 'D:/项目/AI/北清商学院/paike/backend')

from models import db, Course, Topic, TrainingType
from app import app

def verify_course_topic_association():
    with app.app_context():
        print("=" * 60)
        print("课程-课题关联验证")
        print("=" * 60)
        
        # 统计
        total_courses = Course.query.count()
        assigned_courses = Course.query.filter(Course.topic_id.isnot(None)).count()
        unassigned_courses = total_courses - assigned_courses
        
        print(f"\n总课程数: {total_courses}")
        print(f"已关联课题: {assigned_courses}")
        print(f"未关联课题: {unassigned_courses}")
        
        # 按培训班类型统计
        print("\n" + "=" * 60)
        print("按培训班类型统计")
        print("=" * 60)
        
        training_types = TrainingType.query.all()
        for tt in training_types:
            print(f"\n【{tt.name}】")
            topics = Topic.query.filter_by(training_type_id=tt.id).all()
            for topic in topics:
                courses = Course.query.filter_by(topic_id=topic.id).all()
                print(f"  - {topic.name}: {len(courses)}门课程")
                for c in courses:
                    print(f"    • {c.name}")
        
        # 未关联的课程
        if unassigned_courses > 0:
            print("\n" + "=" * 60)
            print("⚠️ 未关联课题的课程")
            print("=" * 60)
            unassigned = Course.query.filter(Course.topic_id.is_(None)).all()
            for c in unassigned:
                print(f"  - {c.name}")

if __name__ == '__main__':
    verify_course_topic_association()
