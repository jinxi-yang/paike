"""
班级API - 含三重降级自动排课功能
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
    project_id = data.get('project_id')
    start_date_str = data.get('start_date')
    horizon_weeks = int(data.get('horizon_weeks', 16))

    if not project_id or not start_date_str:
        return jsonify({'error': 'Missing project_id/start_date'}), 400

    try:
        start_date = date.fromisoformat(start_date_str)
    except ValueError:
        return jsonify({'error': 'Invalid start_date format, expected YYYY-MM-DD'}), 400

    topics = Topic.query.filter_by(project_id=project_id).order_by(Topic.sequence).all()
    if not topics:
        return jsonify({
            'project_id': project_id,
            'topic_count': 0,
            'predicted_dates': [],
            'homeroom_recommendations': [],
            'risk_hints': ['当前项目下无课题，无法预检']
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
        'project_id': project_id,
        'topic_count': len(topics),
        'predicted_dates': [d.isoformat() for d in predicted_dates],
        'holiday_skips': holiday_skips,
        'homeroom_recommendations': recommendations[:8],
        'risk_hints': risk_hints
    })

def sync_class_statuses():
    """自动同步状态 - 班级 planning→active + 排课 scheduled→completed（按日期）+ 反向纠正"""
    from datetime import date as dt_date
    today = dt_date.today()
    
    # 1. 班级状态: planning → active（开课日期已过）
    updated_classes = Class.query.filter(
        Class.status == 'planning',
        Class.start_date != None,
        Class.start_date <= today
    ).update({Class.status: 'active'}, synchronize_session='fetch')
    
    # 2. 排课状态: scheduled/confirmed → completed（课程日期已过）
    updated_schedules = ClassSchedule.query.filter(
        ClassSchedule.status.in_(['scheduled', 'confirmed']),
        ClassSchedule.scheduled_date < today
    ).update({ClassSchedule.status: 'completed'}, synchronize_session='fetch')
    
    # 3. 反向纠正: completed → scheduled（课程日期尚未到来，不应标记为已完成）
    fixed_schedules = ClassSchedule.query.filter(
        ClassSchedule.status == 'completed',
        ClassSchedule.scheduled_date >= today
    ).update({ClassSchedule.status: 'scheduled'}, synchronize_session='fetch')
    
    if updated_classes or updated_schedules or fixed_schedules:
        db.session.commit()


def check_class_completion(class_id):
    """检查单个班级是否所有课题已完成 - 仅在排课变更时调用（含反向纠正）"""
    cls = Class.query.get(class_id)
    if not cls:
        return
    
    total_topics = Topic.query.filter_by(project_id=cls.project_id).count()
    if total_topics == 0:
        return
    
    completed_topics = ClassSchedule.query.filter(
        ClassSchedule.class_id == class_id,
        ClassSchedule.status == 'completed'
    ).count()
    
    if completed_topics >= total_topics:
        if cls.status != 'completed':
            cls.status = 'completed'
            db.session.commit()
    else:
        # 反向纠正：班级标记为completed但仍有未完成课题
        if cls.status == 'completed':
            cls.status = 'active'
            db.session.commit()


@classes_bp.route('', methods=['GET'])
def get_all():
    """获取所有班级（可按项目过滤）"""
    sync_class_statuses()  # 自动同步状态
    
    project_id = request.args.get('project_id', type=int)
    status = request.args.get('status')
    
    query = Class.query
    if project_id:
        query = query.filter_by(project_id=project_id)
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
    
    # project_id
    pid = data.get('project_id')
    
    c = Class(
        project_id=pid,
        name=data.get('name'),
        homeroom_id=data.get('homeroom_id'),
        start_date=date.fromisoformat(data.get('start_date')) if data.get('start_date') else None,
        status='planning'
    )
    db.session.add(c)
    db.session.flush()  # 获取ID
    
    # 自动生成课表
    auto_generate = data.get('auto_generate', True)
    if auto_generate and c.start_date and c.project_id:
        result = auto_schedule_class(c)
        for s in result['schedules']:
            db.session.add(s)
    
    db.session.commit()
    
    # 返回班级信息（含课表和冲突详情）
    resp = c.to_dict(include_schedules=True)
    if auto_generate and c.start_date and c.project_id:
        resp['scheduling_report'] = {
            'total': result['total'],
            'conflict_count': result['conflict_count'],
            'conflicts': result['conflicts'],
            'topic_swaps': result['topic_swaps']
        }
    return jsonify(resp), 201

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
    if c.start_date and c.project_id:
        result = auto_schedule_class(c)
        for s in result['schedules']:
            db.session.add(s)
    
    db.session.commit()
    
    resp = c.to_dict(include_schedules=True)
    if c.start_date and c.project_id:
        resp['scheduling_report'] = {
            'total': result['total'],
            'conflict_count': result['conflict_count'],
            'conflicts': result['conflicts'],
            'topic_swaps': result['topic_swaps']
        }
    return jsonify(resp)


# ==================== 三重降级排课算法 ====================

def _get_occupied_teachers(target_date):
    """获取某日已被占用的讲师ID集合"""
    occupied = set()
    schedules = ClassSchedule.query.filter_by(scheduled_date=target_date).all()
    for s in schedules:
        if s.combo and s.combo.teacher_id:
            occupied.add(s.combo.teacher_id)
        if s.combo_2 and s.combo_2.teacher_id:
            occupied.add(s.combo_2.teacher_id)
    return occupied


def _check_homeroom_conflict(homeroom_id, target_date, exclude_class_id=None):
    """检查班主任在某日是否有冲突"""
    if not homeroom_id:
        return False
    query = ClassSchedule.query.join(Class).filter(
        Class.homeroom_id == homeroom_id,
        ClassSchedule.scheduled_date == target_date
    )
    if exclude_class_id:
        query = query.filter(ClassSchedule.class_id != exclude_class_id)
    return query.first() is not None


def _find_best_combo(topic_id, target_date, occupied_teachers):
    """
    在该课题下寻找不冲突的最优 combo。
    返回 (combo, conflict_type) 
    - combo: 选中的 combo 对象
    - conflict_type: None(无冲突) / 'teacher'(讲师冲突)
    """
    combos = TeacherCourseCombo.query.filter_by(topic_id=topic_id)\
        .order_by(TeacherCourseCombo.priority.desc(), TeacherCourseCombo.id.desc()).all()
    
    if not combos:
        return None, None
    
    # 优先找无冲突的
    for c in combos:
        if c.teacher_id not in occupied_teachers:
            return c, None
    
    # 全部冲突，选第一个（优先级最高）
    return combos[0], 'teacher'


def auto_schedule_class(class_obj):
    """
    三重降级自动排课算法：
    
    对每个课题（按序号排列）：
      策略A — 换科教组合：遍历所有 combo，找不冲突的
      策略B — 换课题顺序：与后续非固定课题交换位置后重试
      策略C — 标红告警：选冲突最少的方案落盘
    
    返回: {
        'schedules': [ClassSchedule, ...],
        'total': int,
        'conflict_count': int,
        'conflicts': [{'topic': str, 'date': str, 'type': str, 'detail': str}, ...],
        'topic_swaps': [{'from': str, 'to': str}, ...]
    }
    """
    from config import Config
    
    topics = list(Topic.query.filter_by(project_id=class_obj.project_id)
                       .order_by(Topic.sequence).all())
    
    if not topics:
        return {'schedules': [], 'total': 0, 'conflict_count': 0, 'conflicts': [], 'topic_swaps': []}
    
    schedules = []
    conflicts = []
    topic_swaps = []
    current_date = class_obj.start_date
    
    # 确保从周六开始
    current_date = find_next_available_saturday(current_date)
    
    for i in range(len(topics)):
        topic = topics[i]
        
        # 查找可用的周六（避开节假日）
        scheduled_date = current_date
        max_attempts = 10
        attempts = 0
        while attempts < max_attempts:
            if not is_holiday(scheduled_date):
                break
            scheduled_date = scheduled_date + timedelta(days=7)
            attempts += 1
        
        # 获取当天已占用资源
        occupied_teachers = _get_occupied_teachers(scheduled_date)
        homeroom_conflict = _check_homeroom_conflict(
            class_obj.homeroom_id, scheduled_date, class_obj.id
        )
        
        # ========== 策略A: 找不冲突的 combo ==========
        combo, combo_conflict = _find_best_combo(topic.id, scheduled_date, occupied_teachers)
        
        if combo_conflict is None and not homeroom_conflict:
            # 无冲突，直接落盘
            schedule = ClassSchedule(
                class_id=class_obj.id,
                topic_id=topic.id,
                combo_id=combo.id if combo else None,
                scheduled_date=scheduled_date,
                week_number=i + 1,
                status='planning'
            )
            schedules.append(schedule)
            current_date = scheduled_date + timedelta(weeks=Config.MIN_WEEKS_INTERVAL)
            continue
        
        # ========== 策略B: 尝试换课题顺序 ==========
        swapped = False
        if combo_conflict or homeroom_conflict:
            # 在后续未排课题中找一个非固定课题交换
            for j in range(i + 1, len(topics)):
                if topics[j].is_fixed:
                    continue
                
                # 用替代课题试试
                alt_combo, alt_conflict = _find_best_combo(
                    topics[j].id, scheduled_date, occupied_teachers
                )
                # 如果替代课题无讲师冲突（班主任冲突仍在但至少减少一个冲突源）
                if alt_conflict is None and not homeroom_conflict:
                    # 交换课题
                    topic_swaps.append({
                        'from': topic.name,
                        'to': topics[j].name,
                        'reason': '讲师冲突' if combo_conflict else '班主任冲突'
                    })
                    topics[i], topics[j] = topics[j], topics[i]
                    topic = topics[i]
                    combo = alt_combo
                    combo_conflict = None
                    
                    schedule = ClassSchedule(
                        class_id=class_obj.id,
                        topic_id=topic.id,
                        combo_id=combo.id if combo else None,
                        scheduled_date=scheduled_date,
                        week_number=i + 1,
                        status='planning'
                    )
                    schedules.append(schedule)
                    swapped = True
                    break
        
        if swapped:
            current_date = scheduled_date + timedelta(weeks=Config.MIN_WEEKS_INTERVAL)
            continue
        
        # ========== 策略C: 标红告警，选冲突最少的方案 ==========
        conflict_reasons = []
        conflict_type = None
        
        if homeroom_conflict:
            # 找出哪个班级占用了班主任
            conflicting_schedule = ClassSchedule.query.join(Class).filter(
                Class.homeroom_id == class_obj.homeroom_id,
                ClassSchedule.scheduled_date == scheduled_date,
                ClassSchedule.class_id != class_obj.id
            ).first()
            conflicting_class_name = conflicting_schedule.class_.name if conflicting_schedule else '未知班级'
            conflict_reasons.append(f'班主任撞课 ({conflicting_class_name})')
            conflict_type = 'homeroom'
        
        if combo_conflict and combo:
            conflict_reasons.append(f'讲师 {combo.teacher.name} 撞课')
            if not conflict_type:
                conflict_type = 'teacher'
        
        conflict_note = '周六: ' + '; '.join(conflict_reasons) if conflict_reasons else '未知冲突'
        
        conflicts.append({
            'topic': topic.name,
            'date': scheduled_date.isoformat(),
            'type': conflict_type,
            'detail': conflict_note
        })
        
        schedule = ClassSchedule(
            class_id=class_obj.id,
            topic_id=topic.id,
            combo_id=combo.id if combo else None,
            scheduled_date=scheduled_date,
            week_number=i + 1,
            status='conflict',
            conflict_type=conflict_type,
            notes=conflict_note
        )
        schedules.append(schedule)
        current_date = scheduled_date + timedelta(weeks=Config.MIN_WEEKS_INTERVAL)
    
    return {
        'schedules': schedules,
        'total': len(schedules),
        'conflict_count': len(conflicts),
        'conflicts': conflicts,
        'topic_swaps': topic_swaps
    }
