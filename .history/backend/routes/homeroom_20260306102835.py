"""
班主任API
"""
from flask import Blueprint, jsonify, request
from models import db, Homeroom, Class

homeroom_bp = Blueprint('homeroom', __name__)

@homeroom_bp.route('', methods=['GET'])
def get_all():
    """获取所有班主任"""
    homerooms = Homeroom.query.all()
    return jsonify([h.to_dict() for h in homerooms])

@homeroom_bp.route('/<int:id>', methods=['GET'])
def get_one(id):
    """获取单个班主任"""
    h = Homeroom.query.get_or_404(id)
    return jsonify(h.to_dict())

@homeroom_bp.route('', methods=['POST'])
def create():
    """创建班主任"""
    data = request.get_json()
    h = Homeroom(
        name=data.get('name'),
        phone=data.get('phone'),
        email=data.get('email')
    )
    db.session.add(h)
    db.session.commit()
    return jsonify(h.to_dict()), 201

@homeroom_bp.route('/<int:id>', methods=['PUT'])
def update(id):
    """更新班主任"""
    h = Homeroom.query.get_or_404(id)
    data = request.get_json()
    for field in ['name', 'phone', 'email']:
        if field in data:
            setattr(h, field, data[field])
    db.session.commit()
    return jsonify(h.to_dict())

@homeroom_bp.route('/<int:id>', methods=['DELETE'])
def delete(id):
    """删除班主任（仅在有活跃班级时拒绝）"""
    h = Homeroom.query.get_or_404(id)
    active_classes = Class.query.filter(
        Class.homeroom_id == id,
        Class.status.notin_(['completed'])
    ).count()
    if active_classes > 0:
        return jsonify({'error': f'该班主任有 {active_classes} 个进行中的班级，无法删除'}), 400
    db.session.delete(h)
    db.session.commit()
    return jsonify({'message': '删除成功'})
