"""
教-课组合API
"""
from flask import Blueprint, jsonify, request
from models import db, TeacherCourseCombo

combo_bp = Blueprint('combo', __name__)

@combo_bp.route('', methods=['GET'])
def get_all():
    """获取所有教-课组合（可按课题过滤）"""
    topic_id = request.args.get('topic_id', type=int)
    query = TeacherCourseCombo.query
    if topic_id:
        query = query.filter_by(topic_id=topic_id)
    combos = query.order_by(TeacherCourseCombo.id.desc()).all()
    return jsonify([c.to_dict() for c in combos])

@combo_bp.route('/<int:id>', methods=['GET'])
def get_one(id):
    """获取单个教-课组合"""
    c = TeacherCourseCombo.query.get_or_404(id)
    return jsonify(c.to_dict())

@combo_bp.route('', methods=['POST'])
def create():
    """创建教-课组合"""
    data = request.get_json()
    c = TeacherCourseCombo(
        topic_id=data.get('topic_id'),
        teacher_id=data.get('teacher_id'),
        course_id=data.get('course_id'),
        priority=data.get('priority', 0)
    )
    db.session.add(c)
    db.session.commit()
    return jsonify(c.to_dict()), 201

@combo_bp.route('/<int:id>', methods=['PUT'])
def update(id):
    """更新教-课组合"""
    c = TeacherCourseCombo.query.get_or_404(id)
    data = request.get_json()
    for field in ['topic_id', 'teacher_id', 'course_id', 'priority']:
        if field in data:
            setattr(c, field, data[field])
    db.session.commit()
    return jsonify(c.to_dict())

@combo_bp.route('/<int:id>', methods=['DELETE'])
def delete(id):
    """删除教-课组合"""
    c = TeacherCourseCombo.query.get_or_404(id)
    db.session.delete(c)
    db.session.commit()
    return jsonify({'message': '删除成功'})
