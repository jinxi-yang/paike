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
    include_combos = request.args.get('include_combos', 'false').lower() == 'true'
    query = Topic.query
    if project_id:
        query = query.filter_by(project_id=project_id)
    topics = query.order_by(Topic.project_id, Topic.id).all()
    return jsonify([t.to_dict(include_combos=include_combos) for t in topics])

@topic_bp.route('/<int:id>', methods=['GET'])
def get_one(id):
    """获取单个课题（含教-课组合）"""
    t = Topic.query.get_or_404(id)
    return jsonify(t.to_dict(include_combos=True))

@topic_bp.route('', methods=['POST'])
def create():
    """创建课题"""
    from models import Project
    data = request.get_json()
    pid = data.get('project_id')
    if not pid or not Project.query.get(pid):
        return jsonify({'error': '项目不存在'}), 400
    t = Topic(
        project_id=pid,
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
    """删除课题（有排课引用时拒绝，含历史数据保护）"""
    t = Topic.query.get_or_404(id)
    ref_count = ClassSchedule.query.filter(
        ClassSchedule.topic_id == id,
        ClassSchedule.status.notin_(['cancelled'])
    ).count()
    if ref_count > 0:
        return jsonify({'error': f'该课题有 {ref_count} 条排课记录引用，无法删除'}), 400
    # Safe to delete — also cascade-delete its combos
    TeacherCourseCombo.query.filter_by(topic_id=id).delete()
    db.session.delete(t)
    db.session.commit()
    return jsonify({'message': '删除成功'})


@topic_bp.route('/<int:id>/combos', methods=['GET'])
def get_topic_combos(id):
    """获取课题下的讲师-课程组合列表"""
    topic = Topic.query.get_or_404(id)
    combos = TeacherCourseCombo.query.filter_by(topic_id=id).all()
    result = []
    for c in combos:
        result.append({
            'id': c.id,
            'teacher_id': c.teacher_id,
            'teacher_name': c.teacher.name if c.teacher else None,
            'course_name': c.course_name,
        })
    return jsonify(result)


@topic_bp.route('/<int:id>/combos/<int:combo_id>', methods=['DELETE'])
def delete_topic_combo(id, combo_id):
    """删除课题下的单个讲师-课程组合（有排课引用时拒绝）"""
    combo = TeacherCourseCombo.query.get_or_404(combo_id)
    if combo.topic_id != id:
        return jsonify({'error': '组合不属于该课题'}), 400
    ref_count = ClassSchedule.query.filter(
        ClassSchedule.status.notin_(['cancelled']),
        db.or_(
            ClassSchedule.combo_id == combo_id,
            ClassSchedule.combo_id_2 == combo_id
        )
    ).count()
    if ref_count > 0:
        return jsonify({'error': f'该组合有 {ref_count} 条排课记录引用，无法删除'}), 400
    db.session.delete(combo)
    db.session.commit()
    return jsonify({'message': '删除成功'})
