#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
重置数据库脚本 - 清空所有表数据
使用前请确认！此操作不可逆！
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from models import db, TrainingType, Topic, Homeroom, Teacher, Course, TeacherCourseCombo, Class, ClassSchedule

def reset_database():
    """清空数据库所有数据"""
    app = create_app()
    
    with app.app_context():
        print("=" * 60)
        print("⚠️  警告：即将清空数据库所有数据！")
        print("=" * 60)
        
        # 统计现有数据
        print(f"\n当前数据统计:")
        print(f"  - 培训班类型: {TrainingType.query.count()}")
        print(f"  - 课题: {Topic.query.count()}")
        print(f"  - 班主任: {Homeroom.query.count()}")
        print(f"  - 讲师: {Teacher.query.count()}")
        print(f"  - 课程: {Course.query.count()}")
        print(f"  - 教-课组合: {TeacherCourseCombo.query.count()}")
        print(f"  - 班级: {Class.query.count()}")
        print(f"  - 课表记录: {ClassSchedule.query.count()}")
        
        confirm = input("\n确认清空所有数据？(输入 YES 继续): ")
        if confirm != "YES":
            print("已取消")
            return
        
        print("\n开始清空数据...")
        
        # 按依赖顺序删除（从子表到父表）
        try:
            ClassSchedule.query.delete()
            print("✓ 清空课表记录")
            
            Class.query.delete()
            print("✓ 清空班级")
            
            TeacherCourseCombo.query.delete()
            print("✓ 清空教-课组合")
            
            Course.query.delete()
            print("✓ 清空课程")
            
            Teacher.query.delete()
            print("✓ 清空讲师")
            
            Homeroom.query.delete()
            print("✓ 清空班主任")
            
            Topic.query.delete()
            print("✓ 清空课题")
            
            TrainingType.query.delete()
            print("✓ 清空培训班类型")
            
            db.session.commit()
            print("\n✅ 数据库已清空！")
            print("现在可以运行 python init_data.py 重新初始化数据")
            
        except Exception as e:
            db.session.rollback()
            print(f"\n❌ 清空失败: {e}")
            raise

if __name__ == '__main__':
    reset_database()
