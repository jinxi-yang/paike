"""
数据库模型 - 北清商学院排课系统
"""
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


# ==================== 城市（教室容量配置） ====================
class City(db.Model):
    """城市（上课地点及教室容量配置）"""
    __tablename__ = 'city'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(50), nullable=False, unique=True, comment='城市名称')
    max_classrooms = db.Column(db.Integer, default=99, comment='教室数量上限')
    created_at = db.Column(db.DateTime, default=datetime.now)
    
    # 关系
    classes = db.relationship('Class', backref='city_ref', lazy='dynamic')
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'max_classrooms': self.max_classrooms
        }


# ==================== 项目（原培训班类型） ====================
class Project(db.Model):
    """项目（统一概念，原'培训班类型'）"""
    __tablename__ = 'project'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(100), nullable=False, unique=True, comment='项目名称')
    description = db.Column(db.Text, comment='项目描述')
    created_at = db.Column(db.DateTime, default=datetime.now, comment='创建时间')
    
    # 关系
    topics = db.relationship('Topic', backref='project', lazy='dynamic')
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
            # 直接返回该课题下所有 combo（不再用 teacher.topic_id 过滤）
            result['combos'] = [c.to_dict() for c in self.combos.all() if c.teacher]
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
    topic_id = db.Column(db.Integer, db.ForeignKey('topic.id'), comment='所属课题')
    courses = db.Column(db.Text, comment='课程名称列表(JSON数组)')
    created_at = db.Column(db.DateTime, default=datetime.now)
    
    # 关系
    combos = db.relationship('TeacherCourseCombo', backref='teacher', lazy='dynamic')
    topic = db.relationship('Topic', backref=db.backref('teachers', lazy='dynamic'))
    
    def to_dict(self):
        import json as _json
        courses_list = []
        if self.courses:
            try:
                courses_list = _json.loads(self.courses)
            except (ValueError, TypeError):
                courses_list = []
        return {
            'id': self.id,
            'name': self.name,
            'title': self.title,
            'expertise': self.expertise,
            'phone': self.phone,
            'courses': courses_list
        }


# ==================== 教-课组合 ====================
class TeacherCourseCombo(db.Model):
    """教-课组合"""
    __tablename__ = 'teacher_course_combo'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    topic_id = db.Column(db.Integer, db.ForeignKey('topic.id'), nullable=False, comment='关联课题')
    teacher_id = db.Column(db.Integer, db.ForeignKey('teacher.id'), nullable=False, comment='关联讲师')
    course_name = db.Column(db.String(200), nullable=False, default='', comment='课程名称')
    priority = db.Column(db.Integer, default=0, comment='优先级(用于推荐)')
    created_at = db.Column(db.DateTime, default=datetime.now)
    
    def to_dict(self):
        return {
            'id': self.id,
            'topic_id': self.topic_id,
            'topic_name': self.topic.name if self.topic else None,
            'project_id': self.topic.project_id if self.topic else None,
            'teacher_id': self.teacher_id,
            'teacher_name': self.teacher.name if self.teacher else None,
            'course_name': self.course_name
        }


# ==================== 班级 ====================
class Class(db.Model):
    """班级"""
    __tablename__ = 'class'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    project_id = db.Column(db.Integer, db.ForeignKey('project.id'), nullable=False, comment='所属项目')
    name = db.Column(db.String(100), nullable=False, comment='班级名称')
    homeroom_id = db.Column(db.Integer, db.ForeignKey('homeroom.id'), comment='班主任')
    city_id = db.Column(db.Integer, db.ForeignKey('city.id'), comment='上课城市')
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
            'city_id': self.city_id,
            'city_name': self.city_ref.name if self.city_ref else '北京',
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
    status = db.Column(db.String(20), default='scheduled', comment='状态: scheduled(已排课)/completed(已完成)/cancelled(已取消)')
    conflict_type = db.Column(db.String(20), comment='冲突类型: teacher/homeroom/holiday')
    notes = db.Column(db.Text, comment='备注')
    merged_with = db.Column(db.Integer, comment='合班标识(指向主课表ID)')
    merge_snapshot = db.Column(db.Text, comment='合班前快照(JSON): 保存合班前的原始日期和组合，拆分时恢复')
    homeroom_override_id = db.Column(db.Integer, db.ForeignKey('homeroom.id'), comment='本次排课临时班主任(覆盖班级默认班主任)')
    location_id = db.Column(db.Integer, db.ForeignKey('city.id'), comment='本次上课地点(覆盖班级默认地点，为空则用班级默认)')
    has_opening = db.Column(db.Boolean, default=False, comment='(周六)开学典礼')
    has_team_building = db.Column(db.Boolean, default=False, comment='(周六)团建')
    has_closing = db.Column(db.Boolean, default=False, comment='(周六)结业典礼')
    day2_has_opening = db.Column(db.Boolean, default=False, comment='(周日)开学典礼')
    day2_has_team_building = db.Column(db.Boolean, default=False, comment='(周日)团建')
    day2_has_closing = db.Column(db.Boolean, default=False, comment='(周日)结业典礼')
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    
    # 关系
    combo = db.relationship('TeacherCourseCombo', foreign_keys=[combo_id], backref=db.backref('schedules', lazy='dynamic'))
    combo_2 = db.relationship('TeacherCourseCombo', foreign_keys=[combo_id_2], backref=db.backref('secondary_schedules', lazy='dynamic'))
    homeroom_override = db.relationship('Homeroom', foreign_keys=[homeroom_override_id])
    location = db.relationship('City', foreign_keys=[location_id])

    def to_dict(self):
        topic_name = self.topic.name if self.topic else None
        topic_seq = self.topic.sequence if self.topic else None
        total = self.class_.project.topics.count() if self.class_ and self.class_.project else 0

        # 拼接仪式前缀：根据开关字段动态拼接
        display_name = topic_name
        if topic_name:
            prefixes = []
            if self.has_opening or self.day2_has_opening:
                prefixes.append('开学典礼')
            if self.has_team_building or self.day2_has_team_building:
                prefixes.append('团建')
            if self.has_closing or self.day2_has_closing:
                prefixes.append('结业典礼')
            if prefixes:
                display_name = '+'.join(prefixes) + '+' + topic_name

        return {
            'id': self.id,
            'class_id': self.class_id,
            'class_name': self.class_.name if self.class_ else None,
            'project_id': self.class_.project_id if self.class_ else None,
            'project_name': self.class_.project.name if self.class_ and self.class_.project else None,
            'city_name': (self.class_.city_ref.name if self.class_ and self.class_.city_ref else '北京'),
            'location_id': self.location_id,
            'location_name': (self.location.name if self.location else (self.class_.city_ref.name if self.class_ and self.class_.city_ref else '北京')),
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
            'has_opening': bool(self.has_opening),
            'has_team_building': bool(self.has_team_building),
            'has_closing': bool(self.has_closing),
            'day2_has_opening': bool(self.day2_has_opening),
            'day2_has_team_building': bool(self.day2_has_team_building),
            'day2_has_closing': bool(self.day2_has_closing),
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


# ==================== 合班配置 ====================
class MergeConfig(db.Model):
    """合班关系配置（独立于课表记录，持久化存储）"""
    __tablename__ = 'merge_config'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    monthly_plan_id = db.Column(db.Integer, db.ForeignKey('monthly_plan.id'), nullable=False, comment='所属月度计划')
    topic_id = db.Column(db.Integer, db.ForeignKey('topic.id'), nullable=False, comment='合班课题')
    primary_class_id = db.Column(db.Integer, db.ForeignKey('class.id'), nullable=False, comment='主班')
    merged_class_id = db.Column(db.Integer, db.ForeignKey('class.id'), nullable=False, comment='并入班')
    combo_id = db.Column(db.Integer, db.ForeignKey('teacher_course_combo.id'), comment='合班周六组合')
    combo_id_2 = db.Column(db.Integer, db.ForeignKey('teacher_course_combo.id'), comment='合班周日组合')
    created_at = db.Column(db.DateTime, default=datetime.now)

    __table_args__ = (
        db.UniqueConstraint('monthly_plan_id', 'topic_id', 'merged_class_id', name='uix_merge_config'),
    )

    # 关系
    monthly_plan = db.relationship('MonthlyPlan', backref=db.backref('merge_configs', lazy='dynamic'))
    topic = db.relationship('Topic')
    primary_class = db.relationship('Class', foreign_keys=[primary_class_id])
    merged_class = db.relationship('Class', foreign_keys=[merged_class_id])

    def to_dict(self):
        return {
            'id': self.id,
            'monthly_plan_id': self.monthly_plan_id,
            'topic_id': self.topic_id,
            'topic_name': self.topic.name if self.topic else None,
            'primary_class_id': self.primary_class_id,
            'primary_class_name': self.primary_class.name if self.primary_class else None,
            'merged_class_id': self.merged_class_id,
            'merged_class_name': self.merged_class.name if self.merged_class else None,
            'combo_id': self.combo_id,
            'combo_id_2': self.combo_id_2,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
