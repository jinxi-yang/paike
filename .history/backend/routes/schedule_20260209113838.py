"""
排课调度API - 含节假日检查、调整、合班功能
"""
from flask import Blueprint, jsonify, request
from datetime import date, datetime, timedelta
from models import db, ClassSchedule, Class, MonthlyPlan
import requests

schedule_bp = Blueprint('schedule', __name__)

# ==================== 节假日相关 ====================

_holiday_cache = {}

def is_holiday(check_date):
    """
    检查某日期是否为节假日
    使用 timor.tech API
    """
    if isinstance(check_date, str):
        check_date = date.fromisoformat(check_date)
    
    date_str = check_date.isoformat()
    
    # 检查缓存
    if date_str in _holiday_cache:
        return _holiday_cache[date_str]
    
    try:
        resp = requests.get(f"https://timor.tech/api/holiday/info/{date_str}", timeout=5)
        data = resp.json()
        
        if data.get('code') == 0:
            holiday_info = data.get('holiday')
            # holiday为True表示是节假日，False表示是工作日（包括调休工作日）
            is_hol = holiday_info.get('holiday', False) if holiday_info else False
            _holiday_cache[date_str] = is_hol
            return is_hol
    except Exception as e:
        print(f"节假日API调用失败: {e}")
        # API失败时，通过日期判断：周六日(5,6)默认休息
        is_weekend = check_date.weekday() >= 5
        _holiday_cache[date_str] = is_weekend
        return is_weekend
    
    # 默认周六日为非工作日
    _holiday_cache[date_str] = False
    return False

def find_next_available_saturday(start_date):
    """找到下一个周六"""
    if isinstance(start_date, str):
        start_date = date.fromisoformat(start_date)
    
    # 找到下一个周六 (weekday 5 = Saturday)
    days_until_saturday = (5 - start_date.weekday()) % 7
    if days_until_saturday == 0 and start_date.weekday() != 5:
        days_until_saturday = 7
    
    return start_date + timedelta(days=days_until_saturday)


# ==================== 月度排课查询 ====================

@schedule_bp.route('/month/<int:year>/<int:month>', methods=['GET'])
def get_month_schedule(year, month):
    """获取指定月份的所有排课"""
    # 计算月份的起止日期
    start_date = date(year, month, 1)
    if month == 12:
        end_date = date(year + 1, 1, 1)
    else:
        end_date = date(year, month + 1, 1)
    
    schedules = ClassSchedule.query.filter(
        ClassSchedule.scheduled_date >= start_date,
        ClassSchedule.scheduled_date < end_date
    ).order_by(ClassSchedule.scheduled_date).all()
    
    # 按周分组
    weeks = {}
    for s in schedules:
        # 计算周开始日期（周一）
        week_start = s.scheduled_date - timedelta(days=s.scheduled_date.weekday())
        week_key = week_start.isoformat()
        
        if week_key not in weeks:
            weeks[week_key] = {
                'week_start': week_key,
                'week_end': (week_start + timedelta(days=6)).isoformat(),
                'schedules': []
            }
        weeks[week_key]['schedules'].append(s.to_dict())
    
    # 获取月度计划状态
    plan = MonthlyPlan.query.filter_by(year=year, month=month).first()
    
    return jsonify({
        'year': year,
        'month': month,
        'plan_status': plan.status if plan else 'draft',
        'published_at': plan.published_at.isoformat() if plan and plan.published_at else None,
        'weeks': list(weeks.values())
    })


# ==================== 排课调整 ====================

@schedule_bp.route('/adjust', methods=['POST'])
def adjust_schedule():
    """调整单节课的日期或教-课组合"""
    data = request.get_json()
    schedule_id = data.get('schedule_id')
    
    schedule = ClassSchedule.query.get_or_404(schedule_id)
    
    # 调整日期
    if 'new_date' in data:
        new_date = date.fromisoformat(data['new_date'])
        
        # 检查是否是周六
        if new_date.weekday() != 5:
            return jsonify({'error': '排课日期必须是周六'}), 400
        
        # 检查节假日
        if is_holiday(new_date):
            return jsonify({
                'warning': '该日期是节假日',
                'holiday': True,
                'proceed': False
            }), 200
        
        # 检查班主任冲突
        class_obj = schedule.class_
        if class_obj and class_obj.homeroom_id:
            homeroom_conflicts = ClassSchedule.query.join(Class).filter(
                Class.homeroom_id == class_obj.homeroom_id,
                ClassSchedule.scheduled_date == new_date,
                ClassSchedule.id != schedule_id
            ).all()
            
            if homeroom_conflicts:
                return jsonify({
                    'error': '班主任在该日期已有其他课程',
                    'conflict_type': 'homeroom',
                    'conflicts': [c.to_dict() for c in homeroom_conflicts]
                }), 409
        
        # 检查讲师冲突（如果已分配教-课组合）
        if schedule.combo_id and schedule.combo:
            teacher_id = schedule.combo.teacher_id
            from models import TeacherCourseCombo
            teacher_conflicts = ClassSchedule.query.join(
                TeacherCourseCombo, ClassSchedule.combo_id == TeacherCourseCombo.id
            ).filter(
                TeacherCourseCombo.teacher_id == teacher_id,
                ClassSchedule.scheduled_date == new_date,
                ClassSchedule.id != schedule_id
            ).all()
            
            if teacher_conflicts:
                return jsonify({
                    'warning': f'讲师 {schedule.combo.teacher.name} 在该日期已有其他课程',
                    'conflict_type': 'teacher',
                    'conflicts': [c.to_dict() for c in teacher_conflicts],
                    'proceed': True  # 讲师冲突可以警告但允许继续
                }), 200
        
        schedule.scheduled_date = new_date
    
    # 调整教-课组合
    if 'combo_id' in data:
        new_combo_id = data['combo_id']
        # 检查新讲师是否有冲突
        if new_combo_id:
            from models import TeacherCourseCombo
            new_combo = TeacherCourseCombo.query.get(new_combo_id)
            if new_combo:
                teacher_conflicts = ClassSchedule.query.join(
                    TeacherCourseCombo, ClassSchedule.combo_id == TeacherCourseCombo.id
                ).filter(
                    TeacherCourseCombo.teacher_id == new_combo.teacher_id,
                    ClassSchedule.scheduled_date == schedule.scheduled_date,
                    ClassSchedule.id != schedule_id
                ).all()
                
                if teacher_conflicts:
                    return jsonify({
                        'warning': f'讲师 {new_combo.teacher.name} 在该日期已有其他课程',
                        'conflict_type': 'teacher',
                        'conflicts': [c.to_dict() for c in teacher_conflicts],
                        'proceed': True
                    }), 200
        
        schedule.combo_id = new_combo_id
    
    # 更新备注
    if 'notes' in data:
        schedule.notes = data['notes']
    
    db.session.commit()
    return jsonify(schedule.to_dict())


@schedule_bp.route('/move-week', methods=['POST'])
def move_to_week():
    """将课程移动到上一周或下一周"""
    data = request.get_json()
    schedule_id = data.get('schedule_id')
    direction = data.get('direction', 'next')  # 'next' or 'prev'
    
    schedule = ClassSchedule.query.get_or_404(schedule_id)
    
    if direction == 'next':
        new_date = schedule.scheduled_date + timedelta(weeks=1)
    else:
        new_date = schedule.scheduled_date - timedelta(weeks=1)
    
    # 确保是周六
    new_date = find_next_available_saturday(new_date - timedelta(days=1))
    
    schedule.scheduled_date = new_date
    db.session.commit()
    
    return jsonify(schedule.to_dict())


# ==================== 合班功能 ====================

@schedule_bp.route('/merge', methods=['POST'])
def merge_classes():
    """合班操作 - 多个班级同一课题合并上课"""
    data = request.get_json()
    schedule_ids = data.get('schedule_ids', [])
    merged_date = data.get('merged_date')
    
    if len(schedule_ids) < 2:
        return jsonify({'error': '合班至少需要两个课程'}), 400
    
    schedules = ClassSchedule.query.filter(ClassSchedule.id.in_(schedule_ids)).all()
    
    if len(schedules) != len(schedule_ids):
        return jsonify({'error': '部分课程不存在'}), 404
    
    # 验证是否为同一课题
    topic_ids = set(s.topic_id for s in schedules)
    if len(topic_ids) > 1:
        return jsonify({'error': '只能合并相同课题的课程'}), 400
    
    # 使用第一个作为主课表
    main_schedule = schedules[0]
    
    if merged_date:
        main_schedule.scheduled_date = date.fromisoformat(merged_date)
    
    # 标记其他课程为合班
    for s in schedules[1:]:
        s.merged_with = main_schedule.id
        s.scheduled_date = main_schedule.scheduled_date
        s.notes = f"合班至 {main_schedule.class_.name}" if main_schedule.class_ else "合班"
    
    db.session.commit()
    
    return jsonify({
        'main_schedule': main_schedule.to_dict(),
        'merged_schedules': [s.to_dict() for s in schedules[1:]]
    })


@schedule_bp.route('/unmerge/<int:schedule_id>', methods=['POST'])
def unmerge_class(schedule_id):
    """取消合班"""
    schedule = ClassSchedule.query.get_or_404(schedule_id)
    schedule.merged_with = None
    schedule.notes = None
    db.session.commit()
    return jsonify(schedule.to_dict())


# ==================== 月度计划发布 ====================

@schedule_bp.route('/publish', methods=['POST'])
def publish_month():
    """发布月度计划"""
    data = request.get_json()
    year = data.get('year')
    month = data.get('month')
    
    # 查找或创建月度计划
    plan = MonthlyPlan.query.filter_by(year=year, month=month).first()
    if not plan:
        plan = MonthlyPlan(year=year, month=month)
        db.session.add(plan)
    
    plan.status = 'published'
    plan.published_at = datetime.now()
    
    # 更新该月所有课程状态
    start_date = date(year, month, 1)
    if month == 12:
        end_date = date(year + 1, 1, 1)
    else:
        end_date = date(year, month + 1, 1)
    
    ClassSchedule.query.filter(
        ClassSchedule.scheduled_date >= start_date,
        ClassSchedule.scheduled_date < end_date,
        ClassSchedule.status == 'scheduled'
    ).update({'status': 'confirmed'}, synchronize_session=False)
    
    db.session.commit()
    
    return jsonify({
        'message': f'{year}年{month}月计划已发布',
        'plan': plan.to_dict()
    })


@schedule_bp.route('/check-holiday', methods=['GET'])
def check_holiday():
    """检查指定日期是否为节假日"""
    date_str = request.args.get('date')
    if not date_str:
        return jsonify({'error': '缺少date参数'}), 400
    
    result = is_holiday(date_str)
    return jsonify({
        'date': date_str,
        'is_holiday': result
    })


@schedule_bp.route('/<int:schedule_id>', methods=['DELETE'])
def delete_schedule(schedule_id):
    """删除单个课程安排"""
    schedule = ClassSchedule.query.get_or_404(schedule_id)
    
    # 如果是合班主课程，取消其他课程的合班标记
    merged_schedules = ClassSchedule.query.filter_by(merged_with=schedule_id).all()
    for ms in merged_schedules:
        ms.merged_with = None
    
    db.session.delete(schedule)
    db.session.commit()
    
    return jsonify({'message': '课程已删除', 'id': schedule_id})

