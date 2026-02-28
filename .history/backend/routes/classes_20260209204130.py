"""
班级API - 含自动排课功能
"""
from flask import Blueprint, jsonify, request
from datetime import date, timedelta
from models import db, Class, ClassSchedule, Topic, TeacherCourseCombo
from .schedule import is_holiday, find_next_available_saturday

classes_bp = Blueprint('classes', __name__)

@classes_bp.route('', methods=['GET'])
def get_all():
    """获取所有班级（可按培训班类型过滤）"""
    training_type_id = request.args.get('training_type_id', type=int)
    status = request.args.get('status')
    
    query = Class.query
    if training_type_id:
        query = query.filter_by(training_type_id=training_type_id)
    if status:
        query = query.filter_by(status=status)
    
    classes = query.order_by(Class.created_at.desc()).all()
    return jsonify([c.to_dict() for c in classes])

@classes_bp.route('/<int:id>', methods=['GET'])
def get_one(id):
    """获取单个班级（含课表）"""
    c = Class.query.get_or_404(id)
    return jsonify(c.to_dict(include_schedules=True))

@classes_bp.route('', methods=['POST'])
def create():
    """创建班级并自动生成课表"""
    data = request.get_json()
    
    # 创建班级
    c = Class(
        training_type_id=data.get('training_type_id'),
        name=data.get('name'),
        homeroom_id=data.get('homeroom_id'),
        start_date=date.fromisoformat(data.get('start_date')) if data.get('start_date') else None,
        status='planning'
    )
    db.session.add(c)
    db.session.flush()  # 获取ID
    
    # 自动生成课表
    auto_generate = data.get('auto_generate', True)
    if auto_generate and c.start_date and c.training_type_id:
        schedules = auto_schedule_class(c)
        for s in schedules:
            db.session.add(s)
    
    db.session.commit()
    return jsonify(c.to_dict(include_schedules=True)), 201

@classes_bp.route('/<int:id>', methods=['PUT'])
def update(id):
    """更新班级信息"""
    c = Class.query.get_or_404(id)
    data = request.get_json()
    
    for field in ['name', 'homeroom_id', 'status']:
        if field in data:
            setattr(c, field, data[field])
    
    if 'start_date' in data:
        c.start_date = date.fromisoformat(data['start_date']) if data['start_date'] else None
    
    db.session.commit()
    return jsonify(c.to_dict())

@classes_bp.route('/<int:id>', methods=['DELETE'])
def delete(id):
    """删除班级及其课表"""
    c = Class.query.get_or_404(id)
    # 先删除课表
    ClassSchedule.query.filter_by(class_id=id).delete()
    db.session.delete(c)
    db.session.commit()
    return jsonify({'message': '删除成功'})

@classes_bp.route('/<int:id>/regenerate', methods=['POST'])
def regenerate_schedule(id):
    """重新生成班级课表"""
    c = Class.query.get_or_404(id)
    
    # 清除现有课表
    ClassSchedule.query.filter_by(class_id=id).delete()
    
    # 获取新的开始日期
    data = request.get_json() or {}
    if 'start_date' in data:
        c.start_date = date.fromisoformat(data['start_date'])
    
    # 重新生成
    if c.start_date and c.training_type_id:
        schedules = auto_schedule_class(c)
        for s in schedules:
            db.session.add(s)
    
    db.session.commit()
    return jsonify(c.to_dict(include_schedules=True))


def auto_schedule_class(class_obj):
    """
    自动为班级生成课表
    规则：
    1. 获取该培训班类型的8个课题
    2. 从start_date开始，每4周排一节课
    3. 只排周六（周日为同一课的第二天）
    4. 避开节假日
    5. 为每个课题预设一个默认教-课组合
    """
    from config import Config
    
    topics = Topic.query.filter_by(training_type_id=class_obj.training_type_id)\
                       .order_by(Topic.sequence).all()
    
    if not topics:
        return []
    
    schedules = []
    current_date = class_obj.start_date
    
    # 确保从周六开始
    current_date = find_next_available_saturday(current_date)
    
    for i, topic in enumerate(topics):
        # 查找可用的周六（避开节假日）
        scheduled_date = current_date
        max_attempts = 10
        attempts = 0
        while attempts < max_attempts:
            if not is_holiday(scheduled_date):
                break
            # 尝试下一周
            scheduled_date = scheduled_date + timedelta(days=7)
            attempts += 1
        
        # 查找该课题的默认教-课组合
        combo = TeacherCourseCombo.query.filter_by(topic_id=topic.id)\
                                        .order_by(TeacherCourseCombo.id.desc()).first()
        
        schedule = ClassSchedule(
            class_id=class_obj.id,
            topic_id=topic.id,
            combo_id=combo.id if combo else None,
            scheduled_date=scheduled_date,
            week_number=i + 1,
            status='planning'
        )
        schedules.append(schedule)
        
        # 下一节课至少间隔4周
        current_date = scheduled_date + timedelta(weeks=Config.MIN_WEEKS_INTERVAL)
    
    return schedules
