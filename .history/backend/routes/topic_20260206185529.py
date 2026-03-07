"""
课题API
"""
from flask import Blueprint, jsonify, request
from models import db, Topic

topic_bp = Blueprint('topic', __name__)

@topic_bp.route('', methods=['GET'])
def get_all():
    """获取所有课题（可按培训班类型过滤）"""
    training_type_id = request.args.get('training_type_id', type=int)
    query = Topic.query
    if training_type_id:
        query = query.filter_by(training_type_id=training_type_id)
    topics = query.order_by(Topic.training_type_id, Topic.sequence).all()
    return jsonify([t.to_dict() for t in topics])

@topic_bp.route('/<int:id>', methods=['GET'])
def get_one(id):
    """获取单个课题（含教-课组合）"""
    t = Topic.query.get_or_404(id)
    return jsonify(t.to_dict(include_combos=True))

@topic_bp.route('', methods=['POST'])
def create():
    """创建课题"""
    data = request.get_json()
    t = Topic(
        training_type_id=data.get('training_type_id'),
        sequence=data.get('sequence'),
        name=data.get('name'),
        is_fixed=data.get('is_fixed', False),
        description=data.get('description')
    )
    db.session.add(t)
    db.session.commit()
    return jsonify(t.to_dict()), 201

@topic_bp.route('/<int:id>', methods=['PUT'])
def update(id):
    """更新课题"""
    t = Topic.query.get_or_404(id)
    data = request.get_json()
    for field in ['name', 'sequence', 'is_fixed', 'description']:
        if field in data:
            setattr(t, field, data[field])
    db.session.commit()
    return jsonify(t.to_dict())
