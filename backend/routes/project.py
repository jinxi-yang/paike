"""
项目API（原培训班类型）
"""
from flask import Blueprint, jsonify, request
from models import db, Project, Topic

project_bp = Blueprint('project', __name__)

@project_bp.route('', methods=['GET'])
def get_all():
    """获取所有项目（含课题列表）"""
    projects = Project.query.all()
    return jsonify([p.to_dict(include_topics=True) for p in projects])

@project_bp.route('/<int:id>', methods=['GET'])
def get_one(id):
    """获取单个项目（含课题和班级）"""
    p = Project.query.get_or_404(id)
    return jsonify(p.to_dict(include_topics=True, include_classes=True))

@project_bp.route('', methods=['POST'])
def create():
    """创建项目"""
    data = request.get_json()
    p = Project(
        name=data.get('name'),
        description=data.get('description')
    )
    db.session.add(p)
    db.session.flush()  # 获取 p.id

    # 自动创建"其他"课题
    other_topic = Topic(
        project_id=p.id,
        sequence=99,
        name='其他',
        is_fixed=False,
        is_other=True
    )
    db.session.add(other_topic)
    db.session.commit()
    return jsonify(p.to_dict()), 201

@project_bp.route('/<int:id>', methods=['PUT'])
def update(id):
    """更新项目"""
    p = Project.query.get_or_404(id)
    data = request.get_json()
    if 'name' in data:
        p.name = data['name']
    if 'description' in data:
        p.description = data['description']
    db.session.commit()
    return jsonify(p.to_dict())

@project_bp.route('/<int:id>', methods=['DELETE'])
def delete(id):
    """删除项目（有班级引用时禁止删除）"""
    p = Project.query.get_or_404(id)
    if p.classes.count() > 0:
        return jsonify({'error': '该项目下有班级，无法删除'}), 400
    if p.topics.count() > 0:
        return jsonify({'error': '该项目下有课题，请先删除课题'}), 400
    db.session.delete(p)
    db.session.commit()
    return jsonify({'message': '删除成功'})
