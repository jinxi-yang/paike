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
from .init import init_bp
from .auth import auth_bp

__all__ = [
    'project_bp',
    'topic_bp',
    'homeroom_bp',
    'teacher_bp',
    'course_bp',
    'combo_bp',
    'classes_bp',
    'schedule_bp',
    'ai_bp',
    'init_bp',
    'auth_bp'
]
