"""
API路由模块
"""
from .project import project_bp
from .topic import topic_bp
from .homeroom import homeroom_bp
from .teacher import teacher_bp
from .course import course_bp
from .combo import combo_bp
from .classes import classes_bp
from .schedule import schedule_bp
from .ai import ai_bp

# 向后兼容
training_type_bp = project_bp

__all__ = [
    'project_bp',
    'training_type_bp',
    'topic_bp',
    'homeroom_bp',
    'teacher_bp',
    'course_bp',
    'combo_bp',
    'classes_bp',
    'schedule_bp',
    'ai_bp'
]
