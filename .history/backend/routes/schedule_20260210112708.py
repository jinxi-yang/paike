"""
排课调度API - 含节假日检查、调整、合班功能
"""
from flask import Blueprint, jsonify, request
from datetime import date, datetime, timedelta
from models import db, ClassSchedule, Class, MonthlyPlan, TeacherCourseCombo
import requests

schedule_bp = Blueprint('schedule', __name__)

# ==================== 节假日相关 ====================

import os
import json

# 加载本地节假日缓存
_local_holiday_data = {}
try:
    with open('holidays_2026.json', 'r', encoding='utf-8') as f:
        _local_holiday_data = json.load(f)
    print(f"Loaded {len(_local_holiday_data)} holiday records from local file")
except Exception as e:
    print(f"Warning: Could not load local holiday file: {e}")

_holiday_cache = {}

def is_holiday(check_date):
    """
    检查某日期是否为节假日
    优先使用本地 holidays_2026.json
    其次使用 timor.tech API
    最后兜底逻辑：默认为工作日（排课日）
    """
    if isinstance(check_date, str):
        check_date = date.fromisoformat(check_date)
    
    date_str = check_date.isoformat()
    mm_dd = date_str[5:] # MM-DD
    
    # 1. 检查内存缓存
    if date_str in _holiday_cache:
        return _holiday_cache[date_str]
    
    # 2. 检查本地文件缓存 (优先)
    # 尝试 YYYY-MM-DD
    if date_str in _local_holiday_data:
        record = _local_holiday_data[date_str]
        is_hol = record.get('holiday', False)
        _holiday_cache[date_str] = is_hol
        return is_hol
        
    # 尝试 MM-DD (holidays_2026.json 格式)
    if mm_dd in _local_holiday_data:
        record = _local_holiday_data[mm_dd]
        is_hol = record.get('holiday', False)
        # 注意：这里我们存入缓存的是完整日期
        _holiday_cache[date_str] = is_hol
        return is_hol

    # 3. 检查API (作为补充)
    try:
        resp = requests.get(f"https://timor.tech/api/holiday/info/{date_str}", timeout=2) # 缩短超时
        data = resp.json()
        
        if data.get('code') == 0:
            holiday_info = data.get('holiday')
            is_hol = holiday_info.get('holiday', False) if holiday_info else False
            _holiday_cache[date_str] = is_hol
            return is_hol
    except Exception as e:
        # print(f"节假日API调用失败: {e}") # 减少日志干扰
        pass
    
    # 4. 兜底逻辑
    # 商学院排课主要在周六日，所以默认这些天不是节假日（除非API已明确说是）
    # 只有API或本地文件明确说是holiday: true，才是节假日
    # 否则默认都是工作日（可以排课）
    is_hol = False
    _holiday_cache[date_str] = is_hol
    return is_hol

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
    
    # 生成该月所有周的结构
    weeks_data = []
    
    # 找到该月第一天所在的周一
    # weekday(): 0=Mon, 6=Sun
    curr_week_start = start_date - timedelta(days=start_date.weekday())
    
    while curr_week_start < end_date:
        week_end = curr_week_start + timedelta(days=6)
        week_key = curr_week_start.isoformat()
        
        # 查找该周的课程
        week_schedules = [s.to_dict() for s in schedules if curr_week_start <= s.scheduled_date <= week_end]
        
        weeks_data.append({
            'week_start': week_key,
            'week_end': week_end.isoformat(),
            'schedules': week_schedules
        })
        
        curr_week_start += timedelta(weeks=1)
    
    # week_start > end_date 时停止，但可能最后一周跨月，只要 week_start < end_date 就会包含
    
    # 获取月度计划状态
    plan = MonthlyPlan.query.filter_by(year=year, month=month).first()
    
    return jsonify({
        'year': year,
        'month': month,
        'plan_status': plan.status if plan else 'draft',
        'published_at': plan.published_at.isoformat() if plan and plan.published_at else None,
        'weeks': weeks_data
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


@schedule_bp.route('/<int:schedule_id>', methods=['GET'])
def get_schedule_detail(schedule_id):
    """获取单个排课详情"""
    schedule = ClassSchedule.query.get_or_404(schedule_id)
    return jsonify(schedule.to_dict())

@schedule_bp.route('/generate', methods=['POST'])
def generate_schedule():
    """根据约束条件生成/重新生成月度排课"""
    data = request.get_json()
    year = data.get('year')
    month = data.get('month')
    constraints = data.get('constraints', {})
    
    if not year or not month:
        return jsonify({'error': 'Missing year/month'}), 400
        
    try:
        # 1. 清除该月所有【草稿】状态的排课 (status='scheduled')
        # 已发布('confirmed')或已完成('completed')的不动
        start_date = date(year, month, 1)
        if month == 12:
            end_date = date(year + 1, 1, 1)
        else:
            end_date = date(year, month + 1, 1)
            
        ClassSchedule.query.filter(
            ClassSchedule.scheduled_date >= start_date,
            ClassSchedule.scheduled_date < end_date,
            ClassSchedule.status.in_(['scheduled', 'planning'])
        ).delete()
        
        # 2. 获取所有活跃班级
        # (简化逻辑：所有status='active'或'planning'的班级都尝试排一节课)
        active_classes = Class.query.filter(Class.status.in_(['active', 'planning'])).all()
        
        generated_count = 0
        
        # 获取月度所有周六
        saturdays = []
        d = start_date
        # 找到第一个周六
        while d.weekday() != 5:
            d += timedelta(days=1)
        while d < end_date:
            saturdays.append(d)
            d += timedelta(days=7)
            
        # 3. 为每个班级排课
        skipped_classes_info = []
        conflict_mode = data.get('conflict_mode', 'postpone') # 'postpone' (顺延) or 'mark' (标记冲突)

        for cls in active_classes:
            # 找到该班级下一个未上的课题
            # 获取已排的最大sequence (仅查找本月之前的)
            last_schedule = ClassSchedule.query.filter(
                ClassSchedule.class_id == cls.id,
                ClassSchedule.scheduled_date < start_date
            ).order_by(ClassSchedule.topic_id.desc()).first()
            
            # 获取所有topic按sequence排序
            # 注意: 这里假设topic.id和sequence有对应关系，严谨应查询Topic表
            # 简化：获取该班级对应training_type的所有topics
            all_topics = cls.training_type.topics.order_by("sequence").all()
            
            next_topic = None
            if not last_schedule:
                # 还没上过课，第一节
                if all_topics: 
                    next_topic = all_topics[0]
            else:
                # 找下一节
                current_seq = last_schedule.topic.sequence
                for t in all_topics:
                    if t.sequence > current_seq:
                        next_topic = t
                        break
            
            if not next_topic:
                continue # 该班级已结课
                
            if not next_topic:
                continue # 该班级已结课
                
            # 找到合适的 Combo (Teacher)
            # 获取该课题下的所有可用Combo，按ID倒序（最新）
            combos = TeacherCourseCombo.query.filter_by(topic_id=next_topic.id).order_by(TeacherCourseCombo.id.desc()).limit(2).all()
            
            combo1 = None
            combo2 = None
            teacher1_name = None
            teacher2_name = None
            
            if combos:
                if len(combos) >= 2:
                    # 有两个不同的组合，优先排不同的
                    combo1 = combos[0]
                    combo2 = combos[1]
                else:
                    # 只有一个组合，两天都排同一个
                    combo1 = combos[0]
                    combo2 = combos[0]
                    
            teacher1_name = combo1.teacher.name if combo1 and combo1.teacher else None
            teacher2_name = combo2.teacher.name if combo2 and combo2.teacher else None
            
            # 4. 寻找合适的档期 (从可用周六中找)
            assigned_date = None
            fail_reason = "无可用档期"
            final_status = 'scheduled'
            final_notes = 'AI自动排课'
            
            for sat in saturdays:
                sun = sat + timedelta(days=1)
                sat_str = sat.isoformat()
                sun_str = sun.isoformat()
                
                current_conflict_reason = None
                
                # A. 检查节假日 (2天都不能是节假日)
                if is_holiday(sat) or is_holiday(sun):
                    current_conflict_reason = "节假日冲突"
                    
                # B. 检查系统硬约束 (blocked_dates)
                if not current_conflict_reason: 
                    blocked = constraints.get('blocked_dates', [])
                    for b in blocked:
                        b_date = b.get('date') if isinstance(b, dict) else b
                        if b_date == sat_str or b_date == sun_str:
                            current_conflict_reason = f"日期被排除 ({b.get('reason', '人工约束')})" if isinstance(b, dict) else "日期被排除"
                            break
                    
                # C. 检查班主任档期 (Inherent Check)
                if not current_conflict_reason and cls.homeroom_id:
                    # 查找该班主任在当天的其他排课
                    # 注意：ClassSchedule 本身没有 homeroom_id，需关联 Class 表
                    # Join Class to filter by homeroom_id
                    homeroom_conflict = ClassSchedule.query.join(Class).filter(
                        Class.homeroom_id == cls.homeroom_id,
                        ClassSchedule.scheduled_date == sat
                    ).first()
                    
                    if homeroom_conflict:
                        current_conflict_reason = f"周六: 班主任撞课 ({homeroom_conflict.class_.name})"

                    # NEW: Check homeroom_unavailable constraint (AI Constraints)
                    if not current_conflict_reason:
                        homeroom_unavailable = constraints.get('homeroom_unavailable', [])
                        if cls.homeroom: # Ensure homeroom loaded
                             hrm_name = cls.homeroom.name
                             for u in homeroom_unavailable:
                                 # Flexible matching: exact match or partial match if needed (stick to exact for now)
                                 if u.get('homeroom_name') == hrm_name:
                                     if sat_str in u.get('dates', []):
                                         current_conflict_reason = f"周六: 班主任 {hrm_name} 请假/不可用"
                                     elif sun_str in u.get('dates', []):
                                         current_conflict_reason = f"周日: 班主任 {hrm_name} 请假/不可用"
                                     break

                # D. 检查讲师档期 (分别检查Day1和Day2)
                unavailable = constraints.get('teacher_unavailable', [])
                
                # Day 1 Teacher Check
                if not current_conflict_reason and teacher1_name:
                    for u in unavailable:
                        if u['teacher_name'] == teacher1_name and sat_str in u['dates']:
                            current_conflict_reason = f"周六: 讲师 {teacher1_name} 请假"
                            break
                            
                # Day 2 Teacher Check
                if not current_conflict_reason and teacher2_name:
                    for u in unavailable:
                        if u['teacher_name'] == teacher2_name and sun_str in u['dates']:
                            current_conflict_reason = f"周日: 讲师 {teacher2_name} 请假"
                            break
                
                # D. 冲突检查：同一个讲师同一天不能排两个班 
                # Day 1 Check
                if not current_conflict_reason and combo1:
                    conflict_schedule = ClassSchedule.query.join(TeacherCourseCombo, ClassSchedule.combo_id == TeacherCourseCombo.id).filter(
                        ClassSchedule.scheduled_date == sat,
                        TeacherCourseCombo.teacher_id == combo1.teacher_id
                    ).first()
                    # 还要检查作为Day2被占用的情况 (combo_id_2) -- 需 join combo_2 logic，较复杂，暂只查combo_id
                    # 严谨做法：Check if teacher1 is busy on Sat in ANY schedule (as Day1 or Day2)
                    # 简化：只查 scheduled_date == sat 的 combo_id (Day1) 和 scheduled_date == sat-1 的 combo_id_2 (Day2)
                    # 这里的 conflict_schedule 只查了 Day1 撞 Day1
                    if conflict_schedule:
                        current_conflict_reason = f"周六: 讲师 {teacher1_name} 撞课 ({conflict_schedule.class_.name})"

                # Day 2 Check (Sun)
                # 检查有没有其他课在周日上 (即 start_date == Sun, 不太可能，都是周六开课)
                # 或者 start_date == Sat 的课，其 Day2 (Sun) 用了这个老师
                if not current_conflict_reason and combo2:
                    # 查找同日期的其他排课 (都是周六开课)
                    # 检查他们的 combo_id_2 是否占用了 teacher2
                    # Aliasing needed for complex join, using simplified logic:
                    # Iterate all schedules on this Sat, check their combo_2's teacher
                    schedules_on_sat = ClassSchedule.query.filter(ClassSchedule.scheduled_date == sat).all()
                    for existing_s in schedules_on_sat:
                        if existing_s.combo_2 and existing_s.combo_2.teacher_id == combo2.teacher_id:
                            current_conflict_reason = f"周日: 讲师 {teacher2_name} 撞课 ({existing_s.class_.name})"
                            break

                # --- 决策逻辑 ---
                if current_conflict_reason:
                    if conflict_mode == 'mark':
                        # 允许冲突：直接使用此日期，并标记
                        assigned_date = sat
                        final_status = 'conflict'
                        final_notes = current_conflict_reason
                        break # 找到了（带冲突的）位置
                    else:
                        # 顺延模式：记录失败原因，继续找下一个日期
                        fail_reason = current_conflict_reason
                        continue
                else:
                    # 无冲突，完美
                    assigned_date = sat
                    final_status = 'scheduled'
                    final_notes = 'AI自动排课'
                    break
            
            if assigned_date:
                new_schedule = ClassSchedule(
                    class_id=cls.id,
                    topic_id=next_topic.id,
                    combo_id=combo1.id if combo1 else None,
                    combo_id_2=combo2.id if combo2 else None,
                    scheduled_date=assigned_date,
                    week_number=0, # 暂不计算
                    status=final_status,
                    notes=final_notes
                )
                db.session.add(new_schedule)
                generated_count += 1
            else:
                skipped_classes_info.append({
                    "class_name": cls.name,
                    "reason": fail_reason or "当月无可用周六"
                })
            
        db.session.commit()
        
        result_msg = f'已生成 {generated_count} 节课程安排'
        if skipped_classes_info:
            result_msg += f'。有 {len(skipped_classes_info)} 个班级未排课：' + '; '.join([f"{i['class_name']}({i['reason']})" for i in skipped_classes_info])
            
        return jsonify({
            'success': True, 
            'message': result_msg,
            'skipped': skipped_classes_info
        })
        
    except Exception as e:
        db.session.rollback()
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500
    schedule = ClassSchedule.query.get_or_404(schedule_id)
    return jsonify(schedule.to_dict())

