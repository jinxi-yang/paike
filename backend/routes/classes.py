"""
班级API - 含自动排课功能
"""
from flask import Blueprint, jsonify, request
from datetime import date, timedelta
from sqlalchemy import func
from models import db, Class, ClassSchedule, Topic, TeacherCourseCombo, Homeroom
from .schedule import is_holiday, find_next_available_saturday

classes_bp = Blueprint('classes', __name__)


@classes_bp.route('/precheck-plan', methods=['POST'])
def precheck_plan():
    """
    开班前预检：
    1. 预演课题排课日期（周末）
    2. 给出班主任冲突预测与推荐
    3. 输出风险提示，供前端在开班弹窗中展示
    """
    from config import Config

    data = request.get_json() or {}
    training_type_id = data.get('training_type_id')
    start_date_str = data.get('start_date')
    horizon_weeks = int(data.get('horizon_weeks', 16))

    if not training_type_id or not start_date_str:
        return jsonify({'error': 'Missing training_type_id/start_date'}), 400

    try:
        start_date = date.fromisoformat(start_date_str)
    except ValueError:
        return jsonify({'error': 'Invalid start_date format, expected YYYY-MM-DD'}), 400

    topics = Topic.query.filter_by(training_type_id=training_type_id).order_by(Topic.sequence).all()
    if not topics:
        return jsonify({
            'training_type_id': training_type_id,
            'topic_count': 0,
            'predicted_dates': [],
            'homeroom_recommendations': [],
            'risk_hints': ['当前培训班类型下无课题，无法预检']
        })

    min_interval = getattr(Config, 'MIN_WEEKS_INTERVAL', 2)
    first_sat = find_next_available_saturday(start_date)

    # 预演该班理论排课日期（自动跳过节假日）
    predicted_dates = []
    holiday_skips = 0
    curr_date = first_sat

    for _ in topics:
        attempts = 0
        while attempts < horizon_weeks and is_holiday(curr_date):
            curr_date = curr_date + timedelta(days=7)
            holiday_skips += 1
            attempts += 1

        predicted_dates.append(curr_date)
        curr_date = curr_date + timedelta(weeks=min_interval)

    predicted_set = set(predicted_dates)
    occupancy_rows = db.session.query(
        Class.homeroom_id,
        ClassSchedule.scheduled_date,
        func.count(ClassSchedule.id).label('cnt')
    ).join(
        Class, Class.id == ClassSchedule.class_id
    ).filter(
        Class.homeroom_id.isnot(None),
        ClassSchedule.scheduled_date.in_(predicted_set)
    ).group_by(
        Class.homeroom_id, ClassSchedule.scheduled_date
    ).all()

    occupancy_map = {
        (row.homeroom_id, row.scheduled_date): int(row.cnt)
        for row in occupancy_rows
    }

    recommendations = []
    homerooms = Homeroom.query.order_by(Homeroom.id.asc()).all()
    for h in homerooms:
        conflicts = []
        for d in predicted_dates:
            cnt = occupancy_map.get((h.id, d), 0)
            if cnt > 0:
                conflicts.append({
                    'date': d.isoformat(),
                    'existing_classes': cnt
                })

        conflict_count = len(conflicts)
        score = max(0, 100 - conflict_count * 18 - holiday_skips * 2)
        recommendations.append({
            'homeroom_id': h.id,
            'homeroom_name': h.name,
            'score': score,
            'conflict_count': conflict_count,
            'conflicts': conflicts[:5],
            'advice': '优先推荐' if conflict_count == 0 else '存在潜在撞课，建议备选'
        })

    recommendations.sort(key=lambda x: (x['conflict_count'], -x['score'], x['homeroom_id']))

    risk_hints = []
    if holiday_skips > 0:
        risk_hints.append(f'预演排课中已自动跳过 {holiday_skips} 次节假日周末')
    if any((predicted_dates[i] - predicted_dates[i - 1]).days > 60 for i in range(1, len(predicted_dates))):
        risk_hints.append('部分课题间隔超过两个月，建议人工复核课程节奏')
    if recommendations and recommendations[0]['conflict_count'] > 0:
        risk_hints.append('所有班主任都有潜在冲突，请优先处理班主任排班资源')

    return jsonify({
        'training_type_id': training_type_id,
        'topic_count': len(topics),
        'predicted_dates': [d.isoformat() for d in predicted_dates],
        'holiday_skips': holiday_skips,
        'homeroom_recommendations': recommendations[:8],
        'risk_hints': risk_hints
    })

@classes_bp.route('', methods=['GET'])
def get_all():
    """获取所有班级（可按培训班类型过滤）"""
    training_type_id = request.args.get('training_type_id', type=int)
    status = request.args.get('status')
    
    query = Class.query
    if training_type_id:
        query = query.filter_by(training_type_id=training_type_id)
    if status:
        query = query.filter_by(status=status)
    
    classes = query.order_by(Class.created_at.desc()).all()
    return jsonify([c.to_dict() for c in classes])

@classes_bp.route('/<int:id>', methods=['GET'])
def get_one(id):
    """获取单个班级（含课表）"""
    c = Class.query.get_or_404(id)
    return jsonify(c.to_dict(include_schedules=True))

@classes_bp.route('', methods=['POST'])
def create():
    """创建班级并自动生成课表"""
    data = request.get_json()
    
    # 创建班级
    c = Class(
        project_id=data.get('project_id'),
        training_type_id=data.get('training_type_id'),
        name=data.get('name'),
        homeroom_id=data.get('homeroom_id'),
        start_date=date.fromisoformat(data.get('start_date')) if data.get('start_date') else None,
        status='planning'
    )
    db.session.add(c)
    db.session.flush()  # 获取ID
    
    # 自动生成课表
    auto_generate = data.get('auto_generate', True)
    if auto_generate and c.start_date and c.training_type_id:
        schedules = auto_schedule_class(c)
        for s in schedules:
            db.session.add(s)
    
    db.session.commit()
    return jsonify(c.to_dict(include_schedules=True)), 201

@classes_bp.route('/<int:id>', methods=['PUT'])
def update(id):
    """更新班级信息"""
    c = Class.query.get_or_404(id)
    data = request.get_json()
    
    for field in ['name', 'homeroom_id', 'status']:
        if field in data:
            setattr(c, field, data[field])
    
    if 'start_date' in data:
        c.start_date = date.fromisoformat(data['start_date']) if data['start_date'] else None
    
    db.session.commit()
    return jsonify(c.to_dict())

@classes_bp.route('/<int:id>', methods=['DELETE'])
def delete(id):
    """删除班级及其课表"""
    c = Class.query.get_or_404(id)
    # 先删除课表
    ClassSchedule.query.filter_by(class_id=id).delete()
    db.session.delete(c)
    db.session.commit()
    return jsonify({'message': '删除成功'})

@classes_bp.route('/<int:id>/regenerate', methods=['POST'])
def regenerate_schedule(id):
    """重新生成班级课表"""
    c = Class.query.get_or_404(id)
    
    # 清除现有课表
    ClassSchedule.query.filter_by(class_id=id).delete()
    
    # 获取新的开始日期
    data = request.get_json() or {}
    if 'start_date' in data:
        c.start_date = date.fromisoformat(data['start_date'])
    
    # 重新生成
    if c.start_date and c.training_type_id:
        schedules = auto_schedule_class(c)
        for s in schedules:
            db.session.add(s)
    
    db.session.commit()
    return jsonify(c.to_dict(include_schedules=True))


def auto_schedule_class(class_obj):
    """
    自动为班级生成课表
    规则：
    1. 获取该培训班类型的8个课题
    2. 从start_date开始，每4周排一节课
    3. 只排周六（周日为同一课的第二天）
    4. 避开节假日
    5. 为每个课题预设一个默认教-课组合
    """
    from config import Config
    
    topics = Topic.query.filter_by(training_type_id=class_obj.training_type_id)\
                       .order_by(Topic.sequence).all()
    
    if not topics:
        return []
    
    schedules = []
    current_date = class_obj.start_date
    
    # 确保从周六开始
    current_date = find_next_available_saturday(current_date)
    
    for i, topic in enumerate(topics):
        # 查找可用的周六（避开节假日）
        scheduled_date = current_date
        max_attempts = 10
        attempts = 0
        while attempts < max_attempts:
            if not is_holiday(scheduled_date):
                break
            # 尝试下一周
            scheduled_date = scheduled_date + timedelta(days=7)
            attempts += 1
        
        # 查找该课题的默认教-课组合
        combo = TeacherCourseCombo.query.filter_by(topic_id=topic.id)\
                                        .order_by(TeacherCourseCombo.id.desc()).first()
        
        schedule = ClassSchedule(
            class_id=class_obj.id,
            topic_id=topic.id,
            combo_id=combo.id if combo else None,
            scheduled_date=scheduled_date,
            week_number=i + 1,
            status='planning'
        )
        schedules.append(schedule)
        
        # 下一节课至少间隔4周
        current_date = scheduled_date + timedelta(weeks=Config.MIN_WEEKS_INTERVAL)
    
    return schedules
