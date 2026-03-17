"""
授课讲师API
"""
from flask import Blueprint, jsonify, request
from models import db, Teacher, TeacherCourseCombo, ClassSchedule

teacher_bp = Blueprint('teacher', __name__)

@teacher_bp.route('', methods=['GET'])
def get_all():
    """获取所有讲师"""
    teachers = Teacher.query.all()
    return jsonify([t.to_dict() for t in teachers])

@teacher_bp.route('/<int:id>', methods=['GET'])
def get_one(id):
    """获取单个讲师"""
    t = Teacher.query.get_or_404(id)
    return jsonify(t.to_dict())

@teacher_bp.route('', methods=['POST'])
def create():
    """创建讲师"""
    data = request.get_json()
    name = data.get('name', '').strip() if data.get('name') else ''
    if not name:
        return jsonify({'error': '讲师姓名不能为空'}), 400
    t = Teacher(
        name=name,
        title=data.get('title'),
        expertise=data.get('expertise'),
        phone=data.get('phone')
    )
    db.session.add(t)
    db.session.commit()
    return jsonify(t.to_dict()), 201

@teacher_bp.route('/<int:id>', methods=['PUT'])
def update(id):
    """更新讲师"""
    t = Teacher.query.get_or_404(id)
    data = request.get_json()
    for field in ['name', 'title', 'expertise', 'phone']:
        if field in data:
            setattr(t, field, data[field])
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
        return jsonify({'error': f'该讲师有 {ref_count} 条排课记录引用，无法删除'}), 400
    db.session.delete(t)
    db.session.commit()
    return jsonify({'message': '删除成功'})
