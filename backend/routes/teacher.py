"""
授课讲师API — 含自动联动维护教课组合
"""
from flask import Blueprint, jsonify, request
from models import db, Teacher, TeacherCourseCombo, ClassSchedule, Topic
import json as _json

teacher_bp = Blueprint('teacher', __name__)

@teacher_bp.route('', methods=['GET'])
def get_all():
    """获取所有讲师（可按课题过滤）"""
    topic_id = request.args.get('topic_id', type=int)
    query = Teacher.query
    if topic_id:
        query = query.filter_by(topic_id=topic_id)
    teachers = query.all()
    return jsonify([t.to_dict() for t in teachers])

@teacher_bp.route('/<int:id>', methods=['GET'])
def get_one(id):
    """获取单个讲师"""
    t = Teacher.query.get_or_404(id)
    return jsonify(t.to_dict())

@teacher_bp.route('', methods=['POST'])
def create():
    """创建讲师（自动联动创建教课组合）"""
    data = request.get_json()
    name = data.get('name', '').strip() if data.get('name') else ''
    if not name:
        return jsonify({'error': '讲师姓名不能为空'}), 400

    topic_id = data.get('topic_id')
    if topic_id and not Topic.query.get(topic_id):
        return jsonify({'error': '所选课题不存在'}), 400

    courses_list = data.get('courses', [])
    if not isinstance(courses_list, list):
        courses_list = []
    # 去除空字符串
    courses_list = [c.strip() for c in courses_list if c and c.strip()]

    t = Teacher(
        name=name,
        title=data.get('title'),
        expertise=data.get('expertise'),
        phone=data.get('phone'),
        topic_id=topic_id if topic_id else None,
        courses=_json.dumps(courses_list, ensure_ascii=False) if courses_list else None
    )
    db.session.add(t)
    # 不再自动联动创建 combo，由课题管理手动关联
    db.session.commit()
    return jsonify(t.to_dict()), 201

@teacher_bp.route('/<int:id>', methods=['PUT'])
def update(id):
    """更新讲师（自动同步教课组合）"""
    t = Teacher.query.get_or_404(id)
    data = request.get_json()

    for field in ['name', 'title', 'expertise', 'phone']:
        if field in data:
            setattr(t, field, data[field])

    # topic_id 保留可写入能力（向后兼容），但不再触发 combo 联动
    topic_id = data.get('topic_id')
    if topic_id is not None:
        if topic_id and not Topic.query.get(topic_id):
            return jsonify({'error': '所选课题不存在'}), 400
        t.topic_id = topic_id if topic_id else None

    courses_list = data.get('courses')
    if courses_list is not None:
        if not isinstance(courses_list, list):
            courses_list = []
        courses_list = [c.strip() for c in courses_list if c and c.strip()]
        t.courses = _json.dumps(courses_list, ensure_ascii=False) if courses_list else None

    # 不再自动联动 combo，由课题管理手动关联
    db.session.commit()
    return jsonify(t.to_dict())

@teacher_bp.route('/<int:id>', methods=['DELETE'])
def delete(id):
    """删除讲师（有排课引用时拒绝，含历史数据保护）"""
    t = Teacher.query.get_or_404(id)
    ref_count = ClassSchedule.query.join(
        TeacherCourseCombo, 
        db.or_(
            ClassSchedule.combo_id == TeacherCourseCombo.id,
            ClassSchedule.combo_id_2 == TeacherCourseCombo.id
        )
    ).filter(
        TeacherCourseCombo.teacher_id == id,
        ClassSchedule.status.notin_(['cancelled'])
    ).count()
    
    if ref_count > 0:
        schedules = ClassSchedule.query.join(
            TeacherCourseCombo, 
            db.or_(
                ClassSchedule.combo_id == TeacherCourseCombo.id,
                ClassSchedule.combo_id_2 == TeacherCourseCombo.id
            )
        ).filter(
            TeacherCourseCombo.teacher_id == id,
            ClassSchedule.status.notin_(['cancelled'])
        ).limit(3).all()
        refs = [f"【{s.class_.name} - {s.scheduled_date.strftime('%Y-%m-%d')}】" for s in schedules]
        msg = f"该讲师在排课 {'、'.join(refs)}"
        if ref_count > len(schedules):
            msg += f" 等共 {ref_count} 个排课记录"
        msg += " 中被引用，无法删除。"
        return jsonify({'error': msg}), 400
        
    # 删除关联的 combo
    TeacherCourseCombo.query.filter_by(teacher_id=id).delete()
    db.session.delete(t)
    db.session.commit()
    return jsonify({'message': '删除成功'})


def _sync_teacher_combos(teacher, topic_id, courses_list, old_topic_id=None):
    """同步讲师的教课组合记录。
    
    逻辑：
    1. 为每个课程名确保存在 Combo 记录（直接用 course_name 文本）
    2. 删除该讲师下不再使用的旧 combo（但保留有排课引用的）
    """
    # 如果课题变了，需要处理旧课题下的 combo
    if old_topic_id and old_topic_id != topic_id:
        _cleanup_orphan_combos(teacher.id, old_topic_id)

    # 确保每个课程名都有对应的 combo 记录
    active_course_names = set()
    for course_name in courses_list:
        active_course_names.add(course_name)

        # 查找同讲师+同课题+同课程名的 combo
        combo = TeacherCourseCombo.query.filter_by(
            topic_id=topic_id, teacher_id=teacher.id, course_name=course_name
        ).first()
        if not combo:
            combo = TeacherCourseCombo(
                topic_id=topic_id, teacher_id=teacher.id, course_name=course_name
            )
            db.session.add(combo)

    # 清理不再使用的 combo（同讲师同课题下，不在 active 列表中的）
    stale_combos = TeacherCourseCombo.query.filter(
        TeacherCourseCombo.teacher_id == teacher.id,
        TeacherCourseCombo.topic_id == topic_id,
        TeacherCourseCombo.course_name.notin_(active_course_names) if active_course_names else True
    ).all()
    for sc in stale_combos:
        # 检查是否有排课引用
        ref = ClassSchedule.query.filter(
            ClassSchedule.status.notin_(['cancelled']),
            db.or_(ClassSchedule.combo_id == sc.id, ClassSchedule.combo_id_2 == sc.id)
        ).count()
        if ref == 0:
            db.session.delete(sc)


def _cleanup_orphan_combos(teacher_id, old_topic_id):
    """清理讲师在旧课题下的 combo（无排课引用的删除）"""
    old_combos = TeacherCourseCombo.query.filter_by(
        teacher_id=teacher_id, topic_id=old_topic_id
    ).all()
    for oc in old_combos:
        ref = ClassSchedule.query.filter(
            ClassSchedule.status.notin_(['cancelled']),
            db.or_(ClassSchedule.combo_id == oc.id, ClassSchedule.combo_id_2 == oc.id)
        ).count()
        if ref == 0:
            db.session.delete(oc)
