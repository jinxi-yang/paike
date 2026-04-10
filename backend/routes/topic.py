"""
课题API
"""
from flask import Blueprint, jsonify, request
from models import db, Topic, TeacherCourseCombo, ClassSchedule

topic_bp = Blueprint('topic', __name__)


def _normalize_project_topic_sequences(project_id):
    """规范项目内课题序号：普通课题连续1..N，“其他”固定99。"""
    topics = Topic.query.filter_by(project_id=project_id).order_by(Topic.sequence.asc(), Topic.id.asc()).all()
    normal_topics = [t for t in topics if not t.is_other]
    other_topics = [t for t in topics if t.is_other]

    for idx, t in enumerate(normal_topics, start=1):
        t.sequence = idx
    for t in other_topics:
        t.sequence = 99


@topic_bp.route('', methods=['GET'])
def get_all():
    """获取所有课题（可按项目过滤）"""
    project_id = request.args.get('project_id', type=int)
    include_combos = request.args.get('include_combos', 'false').lower() == 'true'
    query = Topic.query
    if project_id:
        query = query.filter_by(project_id=project_id)
    topics = query.order_by(Topic.project_id, Topic.sequence, Topic.id).all()
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
    db.session.flush()
    _normalize_project_topic_sequences(pid)
    db.session.commit()
    return jsonify(t.to_dict()), 201

@topic_bp.route('/<int:id>', methods=['PUT'])
def update(id):
    """更新课题"""
    t = Topic.query.get_or_404(id)
    data = request.get_json() or {}

    if 'name' in data:
        t.name = data['name']
    if 'description' in data:
        t.description = data['description']
    if 'is_fixed' in data:
        t.is_fixed = data['is_fixed']

    # “其他”课题序号固定99；普通课题改序号后全项目自动重排为连续1..N
    if t.is_other:
        t.sequence = 99
    elif 'sequence' in data:
        desired_seq = int(data.get('sequence') or 1)
        if desired_seq < 1:
            desired_seq = 1

        peers = Topic.query.filter_by(project_id=t.project_id).order_by(Topic.sequence.asc(), Topic.id.asc()).all()
        normal_peers = [x for x in peers if not x.is_other and x.id != t.id]
        if desired_seq > len(normal_peers) + 1:
            desired_seq = len(normal_peers) + 1

        normal_peers.insert(desired_seq - 1, t)
        for idx, item in enumerate(normal_peers, start=1):
            item.sequence = idx

        for other in [x for x in peers if x.is_other]:
            other.sequence = 99

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
    project_id = t.project_id
    TeacherCourseCombo.query.filter_by(topic_id=id).delete()
    db.session.delete(t)
    db.session.flush()
    _normalize_project_topic_sequences(project_id)
    db.session.commit()
    return jsonify({'message': '删除成功'})


@topic_bp.route('/reorder', methods=['POST'])
def reorder_topics():
    """批量重排同一项目下课题序号（拖拽排序）。
    兼容两种提交：
    1) 全量课题ID（含“其他”）
    2) 仅普通课题ID（不含“其他”）
    规则：普通课题按提交顺序重排；“其他”课题固定 sequence=99。
    """
    data = request.get_json() or {}
    project_id = data.get('project_id')
    topic_ids = data.get('topic_ids') or []

    if not project_id or not isinstance(topic_ids, list) or len(topic_ids) == 0:
        return jsonify({'error': '缺少 project_id 或 topic_ids'}), 400

    topics = Topic.query.filter_by(project_id=project_id).all()
    topic_map = {t.id: t for t in topics}
    normal_topics = [t for t in topics if not t.is_other]
    other_topics = [t for t in topics if t.is_other]

    normal_ids = {t.id for t in normal_topics}
    all_ids = {t.id for t in topics}
    submitted_ids = set(topic_ids)

    # 允许“全量提交”或“仅普通课题提交”
    if submitted_ids == all_ids:
        ordered_normal_ids = [tid for tid in topic_ids if tid in normal_ids]
    elif submitted_ids == normal_ids:
        ordered_normal_ids = topic_ids
    else:
        return jsonify({'error': '提交的课题列表与项目课题不匹配'}), 400

    for idx, tid in enumerate(ordered_normal_ids, start=1):
        topic_map[tid].sequence = idx

    # “其他”课题永远固定在99
    for t in other_topics:
        t.sequence = 99

    db.session.commit()
    return jsonify({'message': '排序已更新'})


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
