"""
课程API
"""
from flask import Blueprint, jsonify, request
from models import db, Course

course_bp = Blueprint('course', __name__)

@course_bp.route('', methods=['GET'])
def get_all():
    """获取所有课程"""
    courses = Course.query.all()
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
    c = Course(
        name=data.get('name'),
        description=data.get('description'),
        duration_days=data.get('duration_days', 2)
    )
    db.session.add(c)
    db.session.commit()
    return jsonify(c.to_dict()), 201

@course_bp.route('/<int:id>', methods=['PUT'])
def update(id):
    """更新课程"""
    c = Course.query.get_or_404(id)
    data = request.get_json()
    for field in ['name', 'description', 'duration_days']:
        if field in data:
            setattr(c, field, data[field])
    db.session.commit()
    return jsonify(c.to_dict())

@course_bp.route('/<int:id>', methods=['DELETE'])
def delete(id):
    """删除课程"""
    c = Course.query.get_or_404(id)
    db.session.delete(c)
    db.session.commit()
    return jsonify({'message': '删除成功'})
