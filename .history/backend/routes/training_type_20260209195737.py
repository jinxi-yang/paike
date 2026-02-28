"""
培训班类型API
"""
from flask import Blueprint, jsonify, request
from models import db, TrainingType

training_type_bp = Blueprint('training_type', __name__)

@training_type_bp.route('', methods=['GET'])
def get_all():
    """获取所有培训班类型（含课题列表）"""
    types = TrainingType.query.all()
    return jsonify([t.to_dict(include_topics=True) for t in types])

@training_type_bp.route('/<int:id>', methods=['GET'])
def get_one(id):
    """获取单个培训班类型（含课题列表）"""
    t = TrainingType.query.get_or_404(id)
    return jsonify(t.to_dict(include_topics=True))

@training_type_bp.route('', methods=['POST'])
def create():
    """创建培训班类型"""
    data = request.get_json()
    t = TrainingType(
        name=data.get('name'),
        description=data.get('description')
    )
    db.session.add(t)
    db.session.commit()
    return jsonify(t.to_dict()), 201

@training_type_bp.route('/<int:id>', methods=['PUT'])
def update(id):
    """更新培训班类型"""
    t = TrainingType.query.get_or_404(id)
    data = request.get_json()
    if 'name' in data:
        t.name = data['name']
    if 'description' in data:
        t.description = data['description']
    db.session.commit()
    return jsonify(t.to_dict())

@training_type_bp.route('/<int:id>', methods=['DELETE'])
def delete(id):
    """删除培训班类型"""
    t = TrainingType.query.get_or_404(id)
    db.session.delete(t)
    db.session.commit()
    return jsonify({'message': '删除成功'})
