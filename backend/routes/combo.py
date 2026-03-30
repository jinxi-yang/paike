"""
教-课组合API
"""
from flask import Blueprint, jsonify, request
from models import db, TeacherCourseCombo, Topic, Teacher

combo_bp = Blueprint('combo', __name__)

def _sync_course_to_teacher(teacher_id, course_name):
    if not course_name or course_name == '待定':
        return
    from models import Teacher
    import json
    teacher = Teacher.query.get(teacher_id)
    if not teacher: return
    courses = []
    if teacher.courses:
        try: courses = json.loads(teacher.courses)
        except: pass
    if course_name not in courses:
        courses.append(course_name)
        teacher.courses = json.dumps(courses, ensure_ascii=False)


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
    topic_id = data.get('topic_id')
    teacher_id = data.get('teacher_id')
    course_name = (data.get('course_name') or '').strip()
    # #11: 验证外键有效性
    errors = []
    if not topic_id or not Topic.query.get(topic_id):
        errors.append('课题不存在')
    if not teacher_id or not Teacher.query.get(teacher_id):
        errors.append('讲师不存在')
    if not course_name:
        errors.append('课程名称不能为空')
    if errors:
        return jsonify({'error': '、'.join(errors)}), 400
        
    # Check for duplicates
    existing = TeacherCourseCombo.query.filter_by(
        topic_id=topic_id, teacher_id=teacher_id, course_name=course_name
    ).first()
    if existing:
        return jsonify({'error': '该配置已存在，无法重复添加'}), 400
        
    c = TeacherCourseCombo(
        topic_id=topic_id,
        teacher_id=teacher_id,
        course_name=course_name,
        priority=data.get('priority', 0)
    )
    db.session.add(c)
    _sync_course_to_teacher(teacher_id, course_name)
    db.session.commit()
    return jsonify(c.to_dict()), 201

@combo_bp.route('/<int:id>', methods=['PUT'])
def update(id):
    """更新教-课组合"""
    c = TeacherCourseCombo.query.get_or_404(id)
    data = request.get_json()
    for field in ['topic_id', 'teacher_id', 'course_name', 'priority']:
        if field in data:
            setattr(c, field, data[field])
    _sync_course_to_teacher(c.teacher_id, c.course_name)
    db.session.commit()
    return jsonify(c.to_dict())

@combo_bp.route('/<int:id>', methods=['DELETE'])
def delete(id):
    """删除教-课组合（有排课引用时拒绝，含历史数据保护）"""
    from models import ClassSchedule
    c = TeacherCourseCombo.query.get_or_404(id)
    ref_count = ClassSchedule.query.filter(
        ClassSchedule.status.notin_(['cancelled']),
        db.or_(
            ClassSchedule.combo_id == id,
            ClassSchedule.combo_id_2 == id
        )
    ).count()
    
    if ref_count > 0:
        schedules = ClassSchedule.query.filter(
            ClassSchedule.status.notin_(['cancelled']),
            db.or_(
                ClassSchedule.combo_id == id,
                ClassSchedule.combo_id_2 == id
            )
        ).limit(3).all()
        refs = [f"【{s.class_.name} - {s.scheduled_date.strftime('%Y-%m-%d')}】" for s in schedules]
        msg = f"该组合在排课 {'、'.join(refs)}"
        if ref_count > len(schedules):
            msg += f" 等共 {ref_count} 个排课记录"
        msg += " 中被引用，无法删除。"
        return jsonify({'error': msg}), 400
        
    db.session.delete(c)
    db.session.commit()
    return jsonify({'message': '删除成功'})
