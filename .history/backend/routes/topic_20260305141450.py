"""
课题API
"""
from flask import Blueprint, jsonify, request
from models import db, Topic, TeacherCourseCombo, ClassSchedule

topic_bp = Blueprint('topic', __name__)

@topic_bp.route('', methods=['GET'])
def get_all():
    """获取所有课题（可按项目过滤）"""
    project_id = request.args.get('project_id', type=int)
    # 兼容旧参数名
    if not project_id:
        project_id = request.args.get('training_type_id', type=int)
    query = Topic.query
    if project_id:
        query = query.filter_by(training_type_id=project_id)
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
    # 支持 project_id 或 training_type_id
    pid = data.get('project_id') or data.get('training_type_id')
    t = Topic(
        training_type_id=pid,
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

@topic_bp.route('/<int:id>', methods=['DELETE'])
def delete(id):
    """删除课题（有科教组合或排课引用时禁止删除）"""
    t = Topic.query.get_or_404(id)
    if TeacherCourseCombo.query.filter_by(topic_id=id).count() > 0:
        return jsonify({'error': '该课题下有科教组合配置，请先删除相关组合'}), 400
    if ClassSchedule.query.filter_by(topic_id=id).count() > 0:
        return jsonify({'error': '该课题已有排课记录，无法删除'}), 400
    db.session.delete(t)
    db.session.commit()
    return jsonify({'message': '删除成功'})
