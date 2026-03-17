"""
数据库模型 - 北清商学院排课系统
"""
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

# ==================== 项目（原培训班类型） ====================
class Project(db.Model):
    """项目（统一概念，原'培训班类型'）"""
    __tablename__ = 'project'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(100), nullable=False, unique=True, comment='项目名称')
    description = db.Column(db.Text, comment='项目描述')
    created_at = db.Column(db.DateTime, default=datetime.now, comment='创建时间')
    
    # 关系
    topics = db.relationship('Topic', backref='project', lazy='dynamic', order_by='Topic.sequence')
    classes = db.relationship('Class', backref='project', lazy='dynamic')
    
    def to_dict(self, include_topics=False, include_classes=False):
        result = {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
        if include_topics:
            result['topics'] = [t.to_dict(include_combos=True) for t in self.topics.all()]
        if include_classes:
            result['classes'] = [c.to_dict() for c in self.classes.all()]
        return result

# 向后兼容别名，方便其他模块过渡
TrainingType = Project


# ==================== 课题 ====================
class Topic(db.Model):
    """课题（教学模块）"""
    __tablename__ = 'topic'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    project_id = db.Column(db.Integer, db.ForeignKey('project.id'), nullable=False, comment='项目ID')
    sequence = db.Column(db.Integer, nullable=False, comment='课题顺序(1-8)')
    name = db.Column(db.String(200), nullable=False, comment='课题名称')
    is_fixed = db.Column(db.Boolean, default=False, comment='是否固定(首尾)')
    description = db.Column(db.Text, comment='课题描述')
    
    # 关系
    combos = db.relationship('TeacherCourseCombo', backref='topic', lazy='dynamic')
    schedules = db.relationship('ClassSchedule', backref='topic', lazy='dynamic')
    
    def to_dict(self, include_combos=False):
        result = {
            'id': self.id,
            'project_id': self.project_id,
            'sequence': self.sequence,
            'name': self.name,
            'is_fixed': self.is_fixed,
            'description': self.description
        }
        if include_combos:
            result['combos'] = [c.to_dict() for c in self.combos.all()]
        return result


# ==================== 班主任 ====================
class Homeroom(db.Model):
    """班主任"""
    __tablename__ = 'homeroom'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(50), nullable=False, comment='姓名')
    phone = db.Column(db.String(20), comment='联系电话')
    email = db.Column(db.String(100), comment='邮箱')
    created_at = db.Column(db.DateTime, default=datetime.now)
    
    # 关系
    classes = db.relationship('Class', backref='homeroom', lazy='dynamic')
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'phone': self.phone,
            'email': self.email
        }


# ==================== 授课讲师 ====================
class Teacher(db.Model):
    """授课讲师"""
    __tablename__ = 'teacher'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(50), nullable=False, comment='姓名')
    title = db.Column(db.String(50), comment='职称')
    expertise = db.Column(db.Text, comment='擅长领域')
    phone = db.Column(db.String(20), comment='联系电话')
    created_at = db.Column(db.DateTime, default=datetime.now)
    
    # 关系
    combos = db.relationship('TeacherCourseCombo', backref='teacher', lazy='dynamic')
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'title': self.title,
            'expertise': self.expertise,
            'phone': self.phone
        }


# ==================== 课程 ====================
class Course(db.Model):
    """课程"""
    __tablename__ = 'course'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    topic_id = db.Column(db.Integer, db.ForeignKey('topic.id'), comment='关联课题(用于归类)')
    name = db.Column(db.String(200), nullable=False, comment='课程名称')
    description = db.Column(db.Text, comment='课程描述')
    duration_days = db.Column(db.Integer, default=2, comment='时长(天)')
    created_at = db.Column(db.DateTime, default=datetime.now)
    
    # 关系
    combos = db.relationship('TeacherCourseCombo', backref='course', lazy='dynamic')
    
    def to_dict(self):
        return {
            'id': self.id,
            'topic_id': self.topic_id,
            'name': self.name,
            'description': self.description,
            'duration_days': self.duration_days
        }


# ==================== 教-课组合 ====================
class TeacherCourseCombo(db.Model):
    """教-课组合"""
    __tablename__ = 'teacher_course_combo'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    topic_id = db.Column(db.Integer, db.ForeignKey('topic.id'), nullable=False, comment='关联课题')
    teacher_id = db.Column(db.Integer, db.ForeignKey('teacher.id'), nullable=False, comment='关联讲师')
    course_id = db.Column(db.Integer, db.ForeignKey('course.id'), nullable=False, comment='关联课程')
    priority = db.Column(db.Integer, default=0, comment='优先级(用于推荐)')
    created_at = db.Column(db.DateTime, default=datetime.now)
    
    def to_dict(self):
        return {
            'id': self.id,
            'topic_id': self.topic_id,
            'teacher_id': self.teacher_id,
            'teacher_name': self.teacher.name if self.teacher else None,
            'course_id': self.course_id,
            'course_name': self.course.name if self.course else None
        }


# ==================== 班级 ====================
class Class(db.Model):
    """班级"""
    __tablename__ = 'class'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    project_id = db.Column(db.Integer, db.ForeignKey('project.id'), nullable=False, comment='所属项目')
    name = db.Column(db.String(100), nullable=False, comment='班级名称')
    homeroom_id = db.Column(db.Integer, db.ForeignKey('homeroom.id'), comment='班主任')
    start_date = db.Column(db.Date, comment='首次开课日期')
    status = db.Column(db.String(20), default='planning', comment='状态: planning/active/completed')
    created_at = db.Column(db.DateTime, default=datetime.now)
    
    # 关系
    schedules = db.relationship('ClassSchedule', backref='class_', lazy='dynamic', order_by='ClassSchedule.scheduled_date')
    
    def to_dict(self, include_schedules=False):
        result = {
            'id': self.id,
            'project_id': self.project_id,
            'project_name': self.project.name if self.project else None,
            'name': self.name,
            'homeroom_id': self.homeroom_id,
            'homeroom_name': self.homeroom.name if self.homeroom else None,
            'start_date': self.start_date.isoformat() if self.start_date else None,
            'status': self.status
        }
        if include_schedules:
            result['schedules'] = [s.to_dict() for s in self.schedules.all()]
        return result


# ==================== 班级课表 ====================
class ClassSchedule(db.Model):
    """班级课表"""
    __tablename__ = 'class_schedule'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    class_id = db.Column(db.Integer, db.ForeignKey('class.id'), nullable=False, comment='班级')
    topic_id = db.Column(db.Integer, db.ForeignKey('topic.id'), nullable=False, comment='课题')
    combo_id = db.Column(db.Integer, db.ForeignKey('teacher_course_combo.id'), comment='教-课组合(Day1)')
    combo_id_2 = db.Column(db.Integer, db.ForeignKey('teacher_course_combo.id'), comment='教-课组合(Day2)')
    scheduled_date = db.Column(db.Date, nullable=False, comment='排课日期(周六)')
    week_number = db.Column(db.Integer, comment='第几周')
    status = db.Column(db.String(20), default='scheduled', comment='状态: scheduled/completed/cancelled/conflict')
    conflict_type = db.Column(db.String(20), comment='冲突类型: teacher/homeroom/holiday')
    notes = db.Column(db.Text, comment='备注')
    merged_with = db.Column(db.Integer, comment='合班标识(指向主课表ID)')
    merge_snapshot = db.Column(db.Text, comment='合班前快照(JSON): 保存合班前的原始日期和组合，拆分时恢复')
    homeroom_override_id = db.Column(db.Integer, db.ForeignKey('homeroom.id'), comment='本次排课临时班主任(覆盖班级默认班主任)')
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    
    # 关系
    combo = db.relationship('TeacherCourseCombo', foreign_keys=[combo_id], backref=db.backref('schedules', lazy='dynamic'))
    combo_2 = db.relationship('TeacherCourseCombo', foreign_keys=[combo_id_2], backref=db.backref('secondary_schedules', lazy='dynamic'))
    homeroom_override = db.relationship('Homeroom', foreign_keys=[homeroom_override_id])

    def to_dict(self):
        topic_name = self.topic.name if self.topic else None
        topic_seq = self.topic.sequence if self.topic else None
        total = self.class_.project.topics.count() if self.class_ and self.class_.project else 0

        # 拼接仪式前缀：第一节课 → 开班仪式+课程名，最后一节课 → 结业典礼+课程名
        display_name = topic_name
        if topic_name and topic_seq and total > 0:
            if topic_seq == 1:
                display_name = f'开班仪式+{topic_name}'
            elif topic_seq == total:
                display_name = f'结课典礼+{topic_name}'

        return {
            'id': self.id,
            'class_id': self.class_id,
            'class_name': self.class_.name if self.class_ else None,
            'project_name': self.class_.project.name if self.class_ and self.class_.project else None,
            'topic_id': self.topic_id,
            'topic_name': topic_name,
            'display_topic_name': display_name,
            'topic_sequence': topic_seq,
            'combo_id': self.combo_id,
            'combo': self.combo.to_dict() if self.combo else None,
            'combo_id_2': self.combo_id_2,
            'combo_2': self.combo_2.to_dict() if self.combo_2 else None,
            'scheduled_date': self.scheduled_date.isoformat() if self.scheduled_date else None,
            'week_number': self.week_number,
            'status': self.status,
            'conflict_type': self.conflict_type,
            'notes': self.notes,
            'merged_with': self.merged_with,
            'merge_snapshot': self.merge_snapshot,
            'homeroom_name': (self.homeroom_override.name if self.homeroom_override else (self.class_.homeroom.name if self.class_ and self.class_.homeroom else '未分配')),
            'homeroom_override_id': self.homeroom_override_id,
            'total_topics': total
        }


# ==================== 月度计划 ====================
class MonthlyPlan(db.Model):
    """月度计划"""
    __tablename__ = 'monthly_plan'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    year = db.Column(db.Integer, nullable=False, comment='年份')
    month = db.Column(db.Integer, nullable=False, comment='月份')
    status = db.Column(db.String(20), default='draft', comment='状态: draft/published')
    published_at = db.Column(db.DateTime, comment='发布时间')
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    
    __table_args__ = (
        db.UniqueConstraint('year', 'month', name='uix_year_month'),
    )
    
    # 关系
    constraints = db.relationship('ScheduleConstraint', backref='monthly_plan', lazy='dynamic', cascade='all, delete-orphan')
    
    def to_dict(self):
        return {
            'id': self.id,
            'year': self.year,
            'month': self.month,
            'status': self.status,
            'published_at': self.published_at.isoformat() if self.published_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class ScheduleConstraint(db.Model):
    """排课约束条件"""
    __tablename__ = 'schedule_constraint'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    monthly_plan_id = db.Column(db.Integer, db.ForeignKey('monthly_plan.id'), nullable=False, comment='所属月度计划')
    constraint_type = db.Column(db.String(30), default='custom', comment='类型: teacher_unavailable/blocked_date/custom')
    description = db.Column(db.Text, nullable=False, comment='原始描述文本')
    parsed_data = db.Column(db.Text, comment='AI解析后的JSON数据')
    is_active = db.Column(db.Boolean, default=True, comment='是否启用')
    created_at = db.Column(db.DateTime, default=datetime.now)

    def to_dict(self):
        import json as _json
        return {
            'id': self.id,
            'monthly_plan_id': self.monthly_plan_id,
            'constraint_type': self.constraint_type,
            'description': self.description,
            'parsed_data': _json.loads(self.parsed_data) if self.parsed_data else None,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

