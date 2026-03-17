"""
课程API
"""
from flask import Blueprint, jsonify, request
from models import db, Course, TeacherCourseCombo, ClassSchedule

course_bp = Blueprint('course', __name__)

@course_bp.route('', methods=['GET'])
def get_all():
    """获取所有课程（可按课题过滤）"""
    topic_id = request.args.get('topic_id', type=int)
    query = Course.query
    if topic_id:
        query = query.filter_by(topic_id=topic_id)
    courses = query.all()
    return jsonify([c.to_dict() for c in courses])

@course_bp.route('/<int:id>', methods=['GET'])
def get_one(id):
    """获取单个课程"""
    c = Course.query.get_or_404(id)
    return jsonify(c.to_dict())

@course_bp.route('', methods=['POST'])
def create():
    """创建课程"""
    data = request.get_json()
    name = data.get('name', '').strip() if data.get('name') else ''
    if not name:
        return jsonify({'error': '课程名称不能为空'}), 400
    c = Course(
        name=name,
        description=data.get('description'),
        duration_days=data.get('duration_days', 1),
        topic_id=data.get('topic_id')  # 支持关联课题
    )
    db.session.add(c)
    db.session.commit()
    return jsonify(c.to_dict()), 201

@course_bp.route('/<int:id>', methods=['PUT'])
def update(id):
    """更新课程"""
    c = Course.query.get_or_404(id)
    data = request.get_json()
    for field in ['name', 'description', 'duration_days', 'topic_id']:
        if field in data:
            setattr(c, field, data[field])
    db.session.commit()
    return jsonify(c.to_dict())

@course_bp.route('/<int:id>', methods=['DELETE'])
def delete(id):
    """删除课程（有排课引用时拒绝，含历史数据保护）"""
    c = Course.query.get_or_404(id)
    ref_count = ClassSchedule.query.join(
        TeacherCourseCombo,
        db.or_(
            ClassSchedule.combo_id == TeacherCourseCombo.id,
            ClassSchedule.combo_id_2 == TeacherCourseCombo.id
        )
    ).filter(
        TeacherCourseCombo.course_id == id,
        ClassSchedule.status.notin_(['cancelled'])
    ).count()
    if ref_count > 0:
        return jsonify({'error': f'该课程有 {ref_count} 条排课记录引用，无法删除'}), 400
    db.session.delete(c)
    db.session.commit()
    return jsonify({'message': '删除成功'})
