"""
班级API - 含三重降级自动排课功能
"""
from flask import Blueprint, jsonify, request
from datetime import date, timedelta
from sqlalchemy import func
from models import db, Class, ClassSchedule, Topic, TeacherCourseCombo, Homeroom
from .schedule import is_holiday, find_next_available_saturday, _recheck_conflicts_for_dates, _cleanup_stale_scheduled_records, _resequence_topics_by_date

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

    topics = Topic.query.filter_by(project_id=project_id).order_by(Topic.id).all()
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
        
        # 计算下一预期日期（跳过同月）
        ideal_next = curr_date + timedelta(days=Config.TARGET_INTERVAL_DAYS)
        next_date = find_next_available_saturday(ideal_next)
        
        if next_date.year == curr_date.year and next_date.month == curr_date.month:
            if curr_date.month == 12:
                next_month_1st = date(curr_date.year + 1, 1, 1)
            else:
                next_month_1st = date(curr_date.year, curr_date.month + 1, 1)
            next_date = find_next_available_saturday(next_month_1st)
            
        curr_date = next_date

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
    
    updated_schedules = ClassSchedule.query.filter(
        ClassSchedule.status == 'scheduled',
        ClassSchedule.scheduled_date < today
    ).update({ClassSchedule.status: 'completed'}, synchronize_session='fetch')
    
    # 3. 反向纠正: completed → scheduled（课程日期尚未到来，不应标记为已完成）
    fixed_schedules = ClassSchedule.query.filter(
        ClassSchedule.status == 'completed',
        ClassSchedule.scheduled_date >= today
    ).update({ClassSchedule.status: 'scheduled'}, synchronize_session='fetch')
    
    if updated_classes or updated_schedules or fixed_schedules:
        db.session.commit()
    
    # 4. 禁用：不再在自动刷新时后台清理“过期未完成课程”，防止误删用户新加的未规划课题内容。
    # 用户明确删除时自行在前端操作。
    # _cleanup_stale_scheduled_records()
    pass


def check_class_completion(class_id):
    """检查单个班级是否所有课题已完成 - 按实际排课数量计算（含反向纠正）"""
    cls = Class.query.get(class_id)
    if not cls:
        return
    
    # 用该班级实际的排课数作为总数（不按项目课题总数）
    total_schedules = ClassSchedule.query.filter(
        ClassSchedule.class_id == class_id,
        ClassSchedule.merged_with.is_(None)
    ).count()
    if total_schedules == 0:
        return
    
    completed_schedules = ClassSchedule.query.filter(
        ClassSchedule.class_id == class_id,
        ClassSchedule.status == 'completed',
        ClassSchedule.merged_with.is_(None)
    ).count()
    
    if completed_schedules >= total_schedules:
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
        homeroom_id=data.get('homeroom_id') or None,
        city_id=data.get('city_id') or None,
        start_date=date.fromisoformat(data.get('start_date')) if data.get('start_date') else None,
        status='planning'
    )
    db.session.add(c)
    db.session.flush()  # 获取ID
    
    # 自动生成课表
    auto_generate = data.get('auto_generate', True)
    selected_topic_ids = data.get('selected_topic_ids')  # 灵活课题选择
    result = None
    if auto_generate and c.start_date and c.project_id:
        result = auto_schedule_class(c, selected_topic_ids)
        for s in result['schedules']:
            db.session.add(s)
        db.session.flush()
        # 重检冲突：新课表可能与其他班级的已有排课冲突
        if result['schedules']:
            affected_dates = set(s.scheduled_date for s in result['schedules'] if s.scheduled_date)
            _recheck_conflicts_for_dates(affected_dates)
    db.session.commit()
    _resequence_topics_by_date(c.id)
    
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

@classes_bp.route('/<int:id>', methods=['DELETE'])
def delete_class(id):
    """删除班级（级联删除所有排课记录和合班配置，并重检受影响日期的冲突）"""
    c = Class.query.get_or_404(id)
    
    # 1. 收集将被删除记录的日期，以便在删除后重检这些日期的冲突
    affected_dates = set()
    schedules = ClassSchedule.query.filter_by(class_id=id).all()
    for s in schedules:
        if s.scheduled_date:
            affected_dates.add(s.scheduled_date)
            
    # 2. 清除其他班级排课记录中指向该班级排课的 merged_with 引用
    this_class_schedule_ids = [s.id for s in schedules]
    if this_class_schedule_ids:
        ClassSchedule.query.filter(
            ClassSchedule.merged_with.in_(this_class_schedule_ids)
        ).update({ClassSchedule.merged_with: None}, synchronize_session='fetch')
    
    # 3. 删除合班配置
    from models import MergeConfig
    MergeConfig.query.filter(
        db.or_(MergeConfig.primary_class_id == id, MergeConfig.merged_class_id == id)
    ).delete(synchronize_session='fetch')
    
    # 4. 删除该班级的所有排课记录
    ClassSchedule.query.filter_by(class_id=id).delete(synchronize_session='fetch')
    
    # 5. 删除班级
    db.session.delete(c)
    db.session.flush() # 先 flush 以便查不到已删除的课
    
    # 6. 对影响的日期重新检测冲突，消除幽灵冲突提示
    if affected_dates:
        _recheck_conflicts_for_dates(affected_dates)
        
    db.session.commit()
    return jsonify({'message': f'班级「{c.name}」及其所有排课记录已删除'})

@classes_bp.route('/<int:id>', methods=['PUT'])
def update(id):
    """更新班级信息（含级联更新合班notes和merge_snapshot）"""
    import json as _json
    c = Class.query.get_or_404(id)
    data = request.get_json()
    old_name = c.name
    warnings = []

    # ── 基本字段更新 ──
    if 'name' in data:
        c.name = data['name']
    if 'homeroom_id' in data:
        c.homeroom_id = data['homeroom_id'] if data['homeroom_id'] else None
    if 'city_id' in data:
        c.city_id = data['city_id'] if data['city_id'] else None
    if 'status' in data:
        c.status = data['status']
    if 'start_date' in data:
        has_schedules = ClassSchedule.query.filter_by(class_id=id).count() > 0
        if has_schedules:
            return jsonify({'error': '已有排课记录，无法修改开课日期（请使用排课功能调整日期）'}), 400
        c.start_date = date.fromisoformat(data['start_date']) if data['start_date'] else None

    # ── 级联1: 班级名称变更 → 更新所有引用旧名的 notes 和 merge_snapshot ──
    new_name = c.name
    if new_name != old_name:
        # 1a. 更新 ClassSchedule.notes 中的旧班级名称
        #     合班记录的 notes 格式: "合班至 XXX" / "合班主记录（含 XXX, YYY）"
        affected_schedules = ClassSchedule.query.filter(
            ClassSchedule.notes.isnot(None),
            ClassSchedule.notes.contains(old_name)
        ).all()
        for s in affected_schedules:
            s.notes = s.notes.replace(old_name, new_name)

        # 1b. 更新 merge_snapshot JSON 内嵌的 notes 字段
        #     merge_snapshot 是合班前的快照，其 notes 可能包含更早一次合班的班级名
        snapshot_schedules = ClassSchedule.query.filter(
            ClassSchedule.merge_snapshot.isnot(None),
            ClassSchedule.merge_snapshot.contains(old_name)
        ).all()
        for s in snapshot_schedules:
            try:
                snap = _json.loads(s.merge_snapshot)
                if snap.get('notes') and old_name in snap['notes']:
                    snap['notes'] = snap['notes'].replace(old_name, new_name)
                    s.merge_snapshot = _json.dumps(snap, ensure_ascii=False)
            except (ValueError, _json.JSONDecodeError):
                pass

    # ── 级联2: 班主任变更 → 冲突预警 ──
    if 'homeroom_id' in data and c.homeroom_id:
        future_schedules = ClassSchedule.query.filter(
            ClassSchedule.class_id == id,
            ClassSchedule.scheduled_date >= date.today(),
            ClassSchedule.status.notin_(['cancelled'])
        ).all()
        for fs in future_schedules:
            # 使用有效班主任（homeroom_override 优先于班级默认班主任）
            if fs.homeroom_override_id:
                continue  # 该课时有临时覆盖，不受班级班主任变更影响
            conflict = ClassSchedule.query.join(Class).filter(
                Class.homeroom_id == c.homeroom_id,
                ClassSchedule.scheduled_date == fs.scheduled_date,
                ClassSchedule.class_id != id,
                ClassSchedule.status.notin_(['cancelled'])
            ).first()
            if conflict:
                warnings.append(
                    f'{fs.scheduled_date.isoformat()} 新班主任与 {conflict.class_.name} 撞课'
                )

    db.session.commit()

    result = c.to_dict()
    if warnings:
        result['warnings'] = warnings
    return jsonify(result)

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
    
    result = None
    if c.start_date and c.project_id:
        result = auto_schedule_class(c)
        for s in result['schedules']:
            db.session.add(s)
        db.session.flush()
        # 重检冲突：新课表可能与其他班级的已有排课冲突
        if result['schedules']:
            affected_dates = set(s.scheduled_date for s in result['schedules'] if s.scheduled_date)
            _recheck_conflicts_for_dates(affected_dates)
    db.session.commit()
    _resequence_topics_by_date(c.id)
    
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


@classes_bp.route('/<int:id>/add-schedule', methods=['POST'])
def add_schedule(id):
    """给班级追加一条排课"""
    c = Class.query.get_or_404(id)
    data = request.get_json()
    
    topic_id = data.get('topic_id')
    combo_id = data.get('combo_id')
    combo_id_2 = data.get('combo_id_2')
    scheduled_date_str = data.get('scheduled_date')
    postpone_weeks = data.get('postpone_weeks', 0)  # 推迟受影响课次的周数
    
    if not topic_id or not scheduled_date_str:
        return jsonify({'error': '缺少 topic_id 或 scheduled_date'}), 400
    
    scheduled_date = date.fromisoformat(scheduled_date_str)
    
    # 课题唯一性校验：非"其他"课题在班级中只能排一次
    topic = Topic.query.get(topic_id)
    if topic and not topic.is_other:
        existing = ClassSchedule.query.filter_by(
            class_id=id, topic_id=topic_id
        ).first()
        if existing:
            return jsonify({'error': f'课题「{topic.name}」已在本班课表中，普通课题只能排课一次。如需重复排课请使用【其他】课题。'}), 400
    
    # 地点校验
    from models import City
    from .schedule import _get_used_non_default_locations
    location_id_raw = data.get('location_id')
    location_id_val = int(location_id_raw) if location_id_raw else None
    if location_id_val and c.city_id and location_id_val != c.city_id:
        used_locations = _get_used_non_default_locations(id, c.city_id)
        if location_id_val in used_locations:
            loc = City.query.get(location_id_val)
            return jsonify({'error': f'该班级已去过地点「{loc.name if loc else location_id_val}」，不允许再次选择'}), 400
    
    # 推迟受影响的后续课次（避开节假日）
    postponed_count = 0
    if postpone_weeks and postpone_weeks > 0:
        from datetime import timedelta
        from .schedule import is_holiday
        shift_days = postpone_weeks * 7
        affected_schedules = ClassSchedule.query.filter(
            ClassSchedule.class_id == id,
            ClassSchedule.scheduled_date >= scheduled_date
        ).order_by(ClassSchedule.scheduled_date).all()
        for sch in affected_schedules:
            new_date = sch.scheduled_date + timedelta(days=shift_days)
            # 如果新日期落在节假日，继续往后找下一个可用周六
            while is_holiday(new_date):
                new_date += timedelta(weeks=1)
            sch.scheduled_date = new_date
            postponed_count += 1
    
    # 计算 week_number（当前班级最大课次+1）
    max_week = db.session.query(func.max(ClassSchedule.week_number)).filter(
        ClassSchedule.class_id == id
    ).scalar() or 0
    
    schedule = ClassSchedule(
        class_id=id,
        topic_id=topic_id,
        combo_id=combo_id,
        combo_id_2=combo_id_2,
        scheduled_date=scheduled_date,
        week_number=max_week + 1,
        status='scheduled',
        location_id=location_id_val,
        has_opening=data.get('has_opening', False),
        has_team_building=data.get('has_team_building', False),
        has_closing=data.get('has_closing', False)
    )
    db.session.add(schedule)
    db.session.commit()
    
    # 新增课次后重算次序
    _resequence_topics_by_date(id)
    schedule = ClassSchedule.query.get(schedule.id)
    
    result = schedule.to_dict()
    if postponed_count > 0:
        result['postponed_count'] = postponed_count
        result['postpone_message'] = f'已将 {postponed_count} 个后续课次推迟 {postpone_weeks} 周'
    
    return jsonify(result), 201


@classes_bp.route('/<int:id>/schedule/<int:sid>', methods=['DELETE'])
def remove_schedule(id, sid):
    """删除班级的一条排课"""
    schedule = ClassSchedule.query.get_or_404(sid)
    if schedule.class_id != id:
        return jsonify({'error': '排课记录不属于该班级'}), 400
    
    # 清理合班引用
    ClassSchedule.query.filter(
        ClassSchedule.merged_with == sid
    ).update({ClassSchedule.merged_with: None}, synchronize_session='fetch')
    
    affected_dates = set()
    if schedule.scheduled_date:
        affected_dates.add(schedule.scheduled_date)
        
    db.session.delete(schedule)
    db.session.flush() # Flush to make it effective for _recheck_conflicts
    
    _recheck_conflicts_for_dates(affected_dates)
    db.session.commit()
    
    # 删除后重排剩余课题顺序
    _resequence_topics_by_date(id)
    
    return jsonify({'message': '排课记录已删除'})


def auto_schedule_class(class_obj, selected_topic_ids=None):
    """
    课程录入排课算法 — 生成完整课表（所有课题）：
    
    从班级的 start_date 开始，按间隔为每个课题分配日期，排完所有课题。
    - 过去的日期 → status='completed'（已经上过的课）
    - 当月及未来 → status='planning'（系统推算的初步安排）
    
    可通过 selected_topic_ids 仅排指定课题（灵活课题数支持）。
    
    老师可查看完整课表并手动调整。
    月度「智能排课」会将当月 planning → scheduled（优化后的正式排课）。
    
    返回: {
        'schedules': [ClassSchedule, ...],
        'total': int,
        'conflict_count': int,
        'conflicts': [...],
        'topic_swaps': [],
        'skipped_topics': 0
    }
    """
    from config import Config
    from datetime import date as date_type
    
    topics = list(Topic.query.filter_by(project_id=class_obj.project_id)
                       .order_by(Topic.id).all())
    # 灵活课题：如果指定了选中的课题，只排选中的
    if selected_topic_ids:
        topics = [t for t in topics if t.id in selected_topic_ids]
    
    if not topics:
        return {'schedules': [], 'total': 0, 'conflict_count': 0, 
                'conflicts': [], 'topic_swaps': [], 'skipped_topics': 0}
    
    today = date_type.today()
    
    schedules = []
    conflicts = []
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
        
        # 判断状态：过去的为 completed，未来为 scheduled
        if scheduled_date < today:
            record_status = 'completed'
        else:
            record_status = 'scheduled'
        
        # 获取当天已占用资源
        occupied_teachers = _get_occupied_teachers(scheduled_date)
        homeroom_conflict = _check_homeroom_conflict(
            class_obj.homeroom_id, scheduled_date, class_obj.id
        )
        
        # 找最佳 combo（周六讲师）
        combo, combo_conflict = _find_best_combo(topic.id, scheduled_date, occupied_teachers)
        
        # 找 combo2（周日讲师，选不同讲师的组合）
        combo2 = None
        all_combos = TeacherCourseCombo.query.filter_by(topic_id=topic.id)\
            .order_by(TeacherCourseCombo.priority.desc(), TeacherCourseCombo.id.desc()).all()
        if all_combos and combo:
            for c in all_combos:
                if c.teacher_id != combo.teacher_id:
                    combo2 = c
                    break
            if not combo2:
                combo2 = combo  # 只有一个讲师则复用
        
        # 冲突检查（已过去的日期不标冲突）
        has_conflict = False
        if record_status != 'completed':
            has_conflict = combo_conflict is not None or homeroom_conflict
        
        if has_conflict:
            conflict_reasons = []
            conflict_type = None
            if homeroom_conflict:
                conflicting_schedule = ClassSchedule.query.join(Class).filter(
                    Class.homeroom_id == class_obj.homeroom_id,
                    ClassSchedule.scheduled_date == scheduled_date,
                    ClassSchedule.class_id != class_obj.id
                ).first()
                cname = conflicting_schedule.class_.name if conflicting_schedule else '?'
                conflict_reasons.append(f'班主任撞课 ({cname})')
                conflict_type = 'homeroom'
            if combo_conflict and combo:
                conflict_reasons.append(f'讲师 {combo.teacher.name} 撞课')
                if not conflict_type:
                    conflict_type = 'teacher'
            
            note = '; '.join(conflict_reasons)
            conflicts.append({
                'topic': topic.name, 'date': scheduled_date.isoformat(),
                'type': conflict_type, 'detail': note
            })
            final_status = record_status  # 状态只管生命周期，冲突通过 conflict_type 标记
        else:
            final_status = record_status
            note = None
            conflict_type = None
        
        schedule = ClassSchedule(
            class_id=class_obj.id,
            topic_id=topic.id,
            combo_id=combo.id if combo else None,
            combo_id_2=combo2.id if combo2 else None,
            scheduled_date=scheduled_date,
            week_number=i + 1,
            status=final_status,
            conflict_type=conflict_type if has_conflict else None,
            notes=note,
            has_opening=(i == 0),
            has_team_building=(i == 0),
            has_closing=(i == len(topics) - 1),
            location_id=class_obj.city_id
        )
        schedules.append(schedule)
        
        # 下一个日期
        ideal_next = scheduled_date + timedelta(days=Config.TARGET_INTERVAL_DAYS)
        current_date = find_next_available_saturday(ideal_next)
        
        # 同月检测：如果和本次课在同一日历月，推到下个月第一个可用周六
        if current_date.year == scheduled_date.year and current_date.month == scheduled_date.month:
            if scheduled_date.month == 12:
                next_month_1st = date_type(scheduled_date.year + 1, 1, 1)
            else:
                next_month_1st = date_type(scheduled_date.year, scheduled_date.month + 1, 1)
            current_date = find_next_available_saturday(next_month_1st)
            
        if (current_date - scheduled_date).days > getattr(Config, 'MAX_INTERVAL_DAYS', 42):
            earlier = current_date - timedelta(days=7)
            if earlier > scheduled_date and not is_holiday(earlier) \
               and not (earlier.year == scheduled_date.year and earlier.month == scheduled_date.month):
                current_date = earlier
    
    return {
        'schedules': schedules,
        'total': len(schedules),
        'conflict_count': len(conflicts),
        'conflicts': conflicts,
        'topic_swaps': [],
        'skipped_topics': 0
    }

