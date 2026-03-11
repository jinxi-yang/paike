"""
排课调度API - 含节假日检查、调整、合班功能
"""
from flask import Blueprint, jsonify, request
from datetime import date, datetime, timedelta
from models import db, ClassSchedule, Class, MonthlyPlan, TeacherCourseCombo, Topic, ScheduleConstraint
import requests
import json as _json

schedule_bp = Blueprint('schedule', __name__)


def _month_range(year, month):
    start_date = date(year, month, 1)
    if month == 12:
        end_date = date(year + 1, 1, 1)
    else:
        end_date = date(year, month + 1, 1)
    return start_date, end_date


def _guess_suggestion(reason):
    text = reason or ''
    if '节假日' in text:
        return '建议顺延到下一周周六/周日'
    if '请假' in text or '不可用' in text:
        return '建议改用同课题备选讲师，或顺延一周'
    if '班主任' in text:
        return '建议调整到班主任可到场的下一周末'
    if '撞课' in text:
        return '建议同周内错开班级，或调整到下一周'
    if '日期被排除' in text:
        return '建议改到最近可用周末'
    return '建议人工调整时间或师资后再发布'


def _build_publish_checklist(year, month):
    start_date, end_date = _month_range(year, month)
    month_schedules = ClassSchedule.query.filter(
        ClassSchedule.scheduled_date >= start_date,
        ClassSchedule.scheduled_date < end_date
    ).all()

    unresolved = []
    pending = []
    resolved = []

    for s in month_schedules:
        if s.status == 'conflict':
            reason = s.notes or '冲突原因未记录'
            same_day_count = ClassSchedule.query.filter(
                ClassSchedule.scheduled_date == s.scheduled_date
            ).count()
            unresolved.append({
                'schedule_id': s.id,
                'class_name': s.class_.name if s.class_ else None,
                'topic_name': s.topic.name if s.topic else None,
                'date': s.scheduled_date.isoformat() if s.scheduled_date else None,
                'reason': reason,
                'suggestion': _guess_suggestion(reason),
                'impact_scope': f'影响日期 {s.scheduled_date.isoformat()}，同日排课 {max(same_day_count - 1, 0)} 条'
            })
        elif s.status in ['scheduled']:
            # 只有真正需要关注的才放入 pending（缺讲师、缺日期等）
            needs_attention = False
            attention_reason = ''
            if not s.combo_id:
                needs_attention = True
                attention_reason = '未分配讲师（教-课组合）'
            elif not s.scheduled_date:
                needs_attention = True
                attention_reason = '未设定上课日期'

            if needs_attention:
                pending.append({
                    'schedule_id': s.id,
                    'class_name': s.class_.name if s.class_ else None,
                    'topic_name': s.topic.name if s.topic else None,
                    'date': s.scheduled_date.isoformat() if s.scheduled_date else None,
                    'reason': attention_reason,
                    'suggestion': '建议发布前补全信息',
                    'impact_scope': '仅影响当前班级'
                })
            else:
                resolved.append({
                    'schedule_id': s.id,
                    'class_name': s.class_.name if s.class_ else None,
                    'topic_name': s.topic.name if s.topic else None,
                    'date': s.scheduled_date.isoformat() if s.scheduled_date else None
                })
        else:
            resolved.append({
                'schedule_id': s.id,
                'class_name': s.class_.name if s.class_ else None,
                'topic_name': s.topic.name if s.topic else None,
                'date': s.scheduled_date.isoformat() if s.scheduled_date else None
            })

    return {
        'resolved': resolved,
        'pending': pending,
        'unresolved': unresolved
    }

# ==================== 节假日相关 ====================

import os
import json

# 加载本地节假日缓存（按年份动态查找 holidays_{year}.json）
_local_holiday_data = {}
_holiday_files_loaded = set()
_backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def _load_holiday_file(year):
    """按年份加载对应的节假日缓存文件"""
    if year in _holiday_files_loaded:
        return
    _holiday_files_loaded.add(year)
    local_path = os.path.join(_backend_dir, f'holidays_{year}.json')
    try:
        with open(local_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            _local_holiday_data.update(data)
            print(f"Loaded {len(data)} holiday records from: {local_path}")
    except FileNotFoundError:
        print(f"Info: No holiday file for {year}: {local_path}")
    except Exception as e:
        print(f"Warning: Could not load holiday file {local_path}: {e}")

# 启动时预加载当前年份
from datetime import datetime as _dt
_load_holiday_file(_dt.now().year)

_holiday_cache = {}

def is_holiday(check_date):
    """
    检查某日期是否为节假日
    优先使用本地 holidays_{year}.json（按年份自动加载）
    其次使用 timor.tech API
    最后兜底逻辑：默认为工作日（排课日）
    """
    if isinstance(check_date, str):
        check_date = date.fromisoformat(check_date)
    
    # 动态加载该年份的节假日缓存
    _load_holiday_file(check_date.year)
    
    date_str = check_date.isoformat()
    mm_dd = date_str[5:] # MM-DD
    
    # 1. 检查内存缓存
    if date_str in _holiday_cache:
        return _holiday_cache[date_str]
    
    # 2. 检查本地文件缓存 (优先)
    # 尝试 YYYY-MM-DD
    if date_str in _local_holiday_data:
        record = _local_holiday_data[date_str]
        # treat official holidays and any record that represents a make-up/adjusted workday as restricted
        is_makeup = ('after' in record) or ('补班' in (record.get('name') or '')) or record.get('workday', False)
        is_hol = bool(record.get('holiday', False) or is_makeup)
        _holiday_cache[date_str] = is_hol
        return is_hol

    # 尝试 MM-DD (holidays_2026.json 格式)
    if mm_dd in _local_holiday_data:
        record = _local_holiday_data[mm_dd]
        is_makeup = ('after' in record) or ('补班' in (record.get('name') or '')) or record.get('workday', False)
        is_hol = bool(record.get('holiday', False) or is_makeup)
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
        'last_saved_at': plan.updated_at.isoformat() if plan and plan.updated_at else None,
        'weeks': weeks_data
    })


# ==================== 排课调整 ====================

@schedule_bp.route('/adjust', methods=['POST'])
def adjust_schedule():
    """调整单节课的日期或教-课组合"""
    data = request.get_json()
    schedule_id = data.get('schedule_id')
    force = data.get('force', False)
    
    schedule = ClassSchedule.query.get_or_404(schedule_id)
    
    # 状态保护：已完成/已取消的课程不允许调整
    if schedule.status in ('completed', 'cancelled'):
        return jsonify({'error': f'该课程已{schedule.status}，无法调整'}), 400
    
    # 强制模式：跳过所有冲突检查，直接应用修改并标记为冲突
    if force:
        conflict_notes = []
        if 'new_date' in data:
            schedule.scheduled_date = date.fromisoformat(data['new_date'])
        if 'combo_id' in data:
            old_combo_id = schedule.combo_id
            schedule.combo_id = data['combo_id']
            new_combo = TeacherCourseCombo.query.get(data['combo_id']) if data['combo_id'] else None
            if new_combo:
                conflict_notes.append(f'周六讲师强制改为 {new_combo.teacher.name}')
        if 'combo_id_2' in data:
            schedule.combo_id_2 = data['combo_id_2']
            new_combo2 = TeacherCourseCombo.query.get(data['combo_id_2']) if data['combo_id_2'] else None
            if new_combo2:
                conflict_notes.append(f'周日讲师强制改为 {new_combo2.teacher.name}')
        schedule.status = 'conflict'
        schedule.notes = '手动强制调整: ' + '; '.join(conflict_notes) if conflict_notes else '手动强制调整'
        db.session.commit()
        return jsonify(schedule.to_dict())
    
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
        
        # 检查班主任冲突（周六及周日）
        class_obj = schedule.class_
        if class_obj and class_obj.homeroom_id:
            # check saturday
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
            # check sunday (since sunday is part of same record, treat as same new_date)
            sun = new_date + timedelta(days=1)
            homeroom_conflicts2 = ClassSchedule.query.join(Class).filter(
                Class.homeroom_id == class_obj.homeroom_id,
                ClassSchedule.scheduled_date == new_date,
                ClassSchedule.id != schedule_id
            ).all()
            # above query same as saturday because sunday is stored in same record; no extra check needed
        
        # 检查讲师冲突（如果已分配教-课组合，考虑两天）
        # 讲师冲突检查：combo_id=周六讲师, combo_id_2=周日讲师，不同天应分别检查
        if schedule.combo_id and schedule.combo:
            teacher_id = schedule.combo.teacher_id
            from models import TeacherCourseCombo
            # 周六讲师只与其他记录的周六讲师(combo_id)比较
            teacher_conflicts = ClassSchedule.query.join(
                TeacherCourseCombo, ClassSchedule.combo_id == TeacherCourseCombo.id
            ).filter(
                TeacherCourseCombo.teacher_id == teacher_id,
                ClassSchedule.scheduled_date == new_date,
                ClassSchedule.id != schedule_id
            ).all()

            if teacher_conflicts:
                return jsonify({
                    'warning': f'讲师 {schedule.combo.teacher.name} 在该周六已有其他课程',
                    'conflict_type': 'teacher',
                    'conflicts': [c.to_dict() for c in teacher_conflicts],
                    'proceed': True
                }), 200
        if schedule.combo_id_2 and schedule.combo_2:
            teacher2_id = schedule.combo_2.teacher_id
            from models import TeacherCourseCombo
            # 周日讲师只与其他记录的周日讲师(combo_id_2)比较
            teacher_conflicts2 = ClassSchedule.query.filter(
                ClassSchedule.combo_id_2.isnot(None),
                ClassSchedule.scheduled_date == new_date,
                ClassSchedule.id != schedule_id
            ).all()
            teacher_conflicts2 = [s for s in teacher_conflicts2 if s.combo_2 and s.combo_2.teacher_id == teacher2_id]
            if teacher_conflicts2:
                return jsonify({
                    'warning': f'讲师 {schedule.combo_2.teacher.name} 在该周日已有其他课程',
                    'conflict_type': 'teacher',
                    'conflicts': [c.to_dict() for c in teacher_conflicts2],
                    'proceed': True
                }), 200
        
        # optional: 如果必要，还可检查新星期天是否是节假日
        sun_date = new_date + timedelta(days=1)
        if is_holiday(sun_date):
            return jsonify({
                'warning': '新周日日期为节假日',
                'holiday': True,
                'proceed': False
            }), 200
        
        schedule.scheduled_date = new_date
    
    # 调整教-课组合（周六）
    if 'combo_id' in data:
        new_combo_id = data['combo_id']
        # 检查新周六讲师是否有冲突（只与其他记录的周六讲师比较）
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
                        'warning': f'讲师 {new_combo.teacher.name} 在该周六已有其他课程',
                        'conflict_type': 'teacher',
                        'conflicts': [c.to_dict() for c in teacher_conflicts],
                        'proceed': True
                    }), 200
        
        schedule.combo_id = new_combo_id
    # 调整教-课组合（周日）
    if 'combo_id_2' in data:
        new_combo2_id = data['combo_id_2']
        # 检查新周日讲师是否有冲突（只与其他记录的周日讲师比较）
        if new_combo2_id:
            from models import TeacherCourseCombo
            new_combo2 = TeacherCourseCombo.query.get(new_combo2_id)
            if new_combo2:
                teacher_conflicts2 = ClassSchedule.query.filter(
                    ClassSchedule.combo_id_2.isnot(None),
                    ClassSchedule.scheduled_date == schedule.scheduled_date,
                    ClassSchedule.id != schedule_id
                ).all()
                teacher_conflicts2 = [s for s in teacher_conflicts2 if s.combo_2 and s.combo_2.teacher_id == new_combo2.teacher_id]
                if teacher_conflicts2:
                    return jsonify({
                        'warning': f'讲师 {new_combo2.teacher.name} 在该周日已有其他课程',
                        'conflict_type': 'teacher',
                        'conflicts': [c.to_dict() for c in teacher_conflicts2],
                        'proceed': True
                    }), 200
        schedule.combo_id_2 = new_combo2_id
    
    # 更新备注
    if 'notes' in data:
        schedule.notes = data['notes']
    
    db.session.commit()
    return jsonify(schedule.to_dict())


@schedule_bp.route('/move-week', methods=['POST'])
def move_to_week():
    """将课程移动到上一周或下一周（含冲突/节假日检测）"""
    data = request.get_json()
    schedule_id = data.get('schedule_id')
    direction = data.get('direction', 'next')  # 'next' or 'prev'
    force = data.get('force', False)  # 前端确认后强制移动
    
    schedule = ClassSchedule.query.get_or_404(schedule_id)
    
    # 状态保护
    if schedule.status in ('completed', 'cancelled'):
        return jsonify({'error': f'该课程已{schedule.status}，无法移动'}), 400
    
    if direction == 'next':
        new_date = schedule.scheduled_date + timedelta(weeks=1)
    else:
        new_date = schedule.scheduled_date - timedelta(weeks=1)
    
    # 确保是周六
    new_date = find_next_available_saturday(new_date - timedelta(days=1))
    
    # 检查目标日期的冲突
    warnings = []
    
    # 检查节假日
    if is_holiday(new_date):
        warnings.append(f'{new_date.isoformat()} 为节假日')
    
    # 检查班主任冲突
    if schedule.class_ and schedule.class_.homeroom_id:
        homeroom_conflict = ClassSchedule.query.join(Class).filter(
            Class.homeroom_id == schedule.class_.homeroom_id,
            ClassSchedule.scheduled_date == new_date,
            ClassSchedule.class_id != schedule.class_id
        ).first()
        if homeroom_conflict:
            warnings.append(f'班主任与 {homeroom_conflict.class_.name} 撞课')
    
    # 检查讲师冲突（周六）
    if schedule.combo:
        teacher_conflict = ClassSchedule.query.filter(
            ClassSchedule.scheduled_date == new_date,
            ClassSchedule.combo_id.isnot(None),
            ClassSchedule.id != schedule.id
        ).all()
        for tc in teacher_conflict:
            if tc.combo and tc.combo.teacher_id == schedule.combo.teacher_id:
                warnings.append(f'周六讲师 {schedule.combo.teacher.name} 与 {tc.class_.name} 撞课')
                break
    
    # 检查讲师冲突（周日）
    if schedule.combo_2:
        teacher_conflict_2 = ClassSchedule.query.filter(
            ClassSchedule.scheduled_date == new_date,
            ClassSchedule.combo_id_2.isnot(None),
            ClassSchedule.id != schedule.id
        ).all()
        for tc in teacher_conflict_2:
            if tc.combo_2 and tc.combo_2.teacher_id == schedule.combo_2.teacher_id:
                warnings.append(f'周日讲师 {schedule.combo_2.teacher.name} 与 {tc.class_.name} 撞课')
                break
    
    # 如果有警告且未强制，返回警告让前端确认
    if warnings and not force:
        return jsonify({
            'confirm_required': True,
            'new_date': new_date.isoformat(),
            'warnings': warnings,
            'message': '移动目标日期存在以下问题，是否仍要移动？'
        })
    
    schedule.scheduled_date = new_date
    # 如果强制移动到有冲突的位置，更新状态
    if warnings:
        schedule.status = 'conflict'
        schedule.conflict_type = 'teacher' if '讲师' in str(warnings) else 'homeroom'
        schedule.notes = '手动移动: ' + '; '.join(warnings)
    db.session.commit()
    
    return jsonify(schedule.to_dict())


# ==================== 合班功能 ====================

@schedule_bp.route('/merge-info', methods=['POST'])
def merge_info():
    """获取合班可选项（日期、讲师组合、班主任）供前端弹窗展示"""
    data = request.get_json()
    schedule_ids = data.get('schedule_ids', [])
    
    schedules = ClassSchedule.query.filter(ClassSchedule.id.in_(schedule_ids)).all()
    if len(schedules) < 2:
        return jsonify({'error': '至少需要两条记录'}), 400
    
    # 收集可选日期
    dates = list(set(s.scheduled_date.isoformat() for s in schedules if s.scheduled_date))
    dates.sort()
    
    # 收集可选周六组合
    combos_day1 = []
    seen_combo1 = set()
    for s in schedules:
        if s.combo and s.combo_id not in seen_combo1:
            seen_combo1.add(s.combo_id)
            combos_day1.append({
                'combo_id': s.combo_id,
                'label': f'{s.combo.teacher.name} - {s.combo.course.name}' if s.combo.teacher and s.combo.course else f'组合#{s.combo_id}',
                'from_class': s.class_.name if s.class_ else ''
            })
    
    # 收集可选周日组合
    combos_day2 = []
    seen_combo2 = set()
    for s in schedules:
        if s.combo_2 and s.combo_id_2 not in seen_combo2:
            seen_combo2.add(s.combo_id_2)
            combos_day2.append({
                'combo_id': s.combo_id_2,
                'label': f'{s.combo_2.teacher.name} - {s.combo_2.course.name}' if s.combo_2.teacher and s.combo_2.course else f'组合#{s.combo_id_2}',
                'from_class': s.class_.name if s.class_ else ''
            })
    
    # 收集可选班主任
    homerooms = []
    seen_hr = set()
    for s in schedules:
        if s.class_ and s.class_.homeroom and s.class_.homeroom_id not in seen_hr:
            seen_hr.add(s.class_.homeroom_id)
            homerooms.append({
                'homeroom_id': s.class_.homeroom_id,
                'name': s.class_.homeroom.name,
                'from_class': s.class_.name
            })
    
    return jsonify({
        'dates': dates,
        'combos_day1': combos_day1,
        'combos_day2': combos_day2,
        'homerooms': homerooms,
        'schedules': [s.to_dict() for s in schedules]
    })


@schedule_bp.route('/merge', methods=['POST'])
def merge_classes():
    """合班操作 - 多个班级同一课题合并上课，统一讲师和日期"""
    import json
    data = request.get_json()
    schedule_ids = data.get('schedule_ids', [])
    merged_date = data.get('merged_date')
    merged_combo_id = data.get('merged_combo_id')
    merged_combo_id_2 = data.get('merged_combo_id_2')
    lead_homeroom = data.get('lead_homeroom_name', '')
    
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
    class_names = [s.class_.name for s in schedules if s.class_]
    
    # 统一日期
    if merged_date:
        unified_date = date.fromisoformat(merged_date)
    else:
        unified_date = main_schedule.scheduled_date
    
    # 合班前保存每条记录的快照（拆分时用于恢复）
    for s in schedules:
        snapshot = {
            'scheduled_date': s.scheduled_date.isoformat() if s.scheduled_date else None,
            'combo_id': s.combo_id,
            'combo_id_2': s.combo_id_2,
            'status': s.status,
            'conflict_type': s.conflict_type,
            'notes': s.notes
        }
        s.merge_snapshot = json.dumps(snapshot, ensure_ascii=False)
    
    # 更新所有记录的统一信息
    for s in schedules:
        s.scheduled_date = unified_date
        s.status = 'merged'
        if merged_combo_id:
            s.combo_id = int(merged_combo_id)
        if merged_combo_id_2:
            s.combo_id_2 = int(merged_combo_id_2)
    
    # 设置合班关联
    for s in schedules[1:]:
        s.merged_with = main_schedule.id
        s.notes = f'合班至 {main_schedule.class_.name}' + (f'（带班: {lead_homeroom}）' if lead_homeroom else '')
    
    main_schedule.notes = f'合班主记录（含 {", ".join(class_names[1:])}）' + (f'（带班: {lead_homeroom}）' if lead_homeroom else '')
    
    db.session.commit()
    
    return jsonify({
        'main_schedule': main_schedule.to_dict(),
        'merged_schedules': [s.to_dict() for s in schedules[1:]]
    })


@schedule_bp.route('/unmerge/<int:schedule_id>', methods=['POST'])
def unmerge_class(schedule_id):
    """取消合班 - 级联清除所有相关合班记录，并从快照恢复原始状态"""
    import json
    schedule = ClassSchedule.query.get_or_404(schedule_id)
    
    def _restore_from_snapshot(record):
        """从 merge_snapshot 恢复记录的原始状态"""
        if not record.merge_snapshot:
            return
        try:
            snap = json.loads(record.merge_snapshot)
            if snap.get('scheduled_date'):
                record.scheduled_date = date.fromisoformat(snap['scheduled_date'])
            if 'combo_id' in snap:
                record.combo_id = snap['combo_id']
            if 'combo_id_2' in snap:
                record.combo_id_2 = snap['combo_id_2']
            record.status = snap.get('status', 'scheduled')
            record.conflict_type = snap.get('conflict_type')
            record.notes = snap.get('notes')
        except (json.JSONDecodeError, ValueError):
            pass
        record.merge_snapshot = None
        record.merged_with = None
    
    # 情况1: 如果是主记录（被其他记录引用），同时恢复所有次记录
    secondary_records = ClassSchedule.query.filter_by(merged_with=schedule_id).all()
    for sec in secondary_records:
        _restore_from_snapshot(sec)
    
    # 情况2: 如果是次记录（引用其他主记录），也检查主记录
    if schedule.merged_with:
        main_record = ClassSchedule.query.get(schedule.merged_with)
        if main_record:
            # 检查主记录下还有没有其他次记录
            remaining = ClassSchedule.query.filter(
                ClassSchedule.merged_with == schedule.merged_with,
                ClassSchedule.id != schedule_id
            ).count()
            if remaining == 0:
                # 没有其他次记录了，主记录也恢复
                _restore_from_snapshot(main_record)
    
    # 恢复当前记录
    _restore_from_snapshot(schedule)
    
    db.session.commit()
    return jsonify({'message': '拆分成功，已恢复原始状态', 'schedule': schedule.to_dict()})


# ==================== 月度计划发布 ====================

@schedule_bp.route('/publish-checklist', methods=['GET'])
def publish_checklist():
    """发布前冲突处置清单"""
    year = request.args.get('year', type=int)
    month = request.args.get('month', type=int)
    if not year or not month:
        return jsonify({'error': 'Missing year/month'}), 400

    checklist = _build_publish_checklist(year, month)
    return jsonify({
        'year': year,
        'month': month,
        'checklist': checklist
    })


@schedule_bp.route('/publish', methods=['POST'])
def publish_month():
    """发布月度计划"""
    data = request.get_json()
    year = data.get('year')
    month = data.get('month')
    force_publish = bool(data.get('force_publish', False))
    force_note = (data.get('force_note') or '').strip()

    checklist = _build_publish_checklist(year, month)
    unresolved = checklist.get('unresolved', [])
    if unresolved and not force_publish:
        return jsonify({
            'error': '存在无法自动解决的冲突，默认阻止发布',
            'code': 'UNRESOLVED_CONFLICTS',
            'checklist': checklist
        }), 409

    if force_publish and unresolved and not force_note:
        return jsonify({
            'error': '强制发布必须填写备注',
            'code': 'FORCE_NOTE_REQUIRED'
        }), 400

    # find or create monthly plan
    plan = MonthlyPlan.query.filter_by(year=year, month=month).first()
    if not plan:
        plan = MonthlyPlan(year=year, month=month)
        db.session.add(plan)

    plan.status = 'published'
    plan.published_at = datetime.now()

    # update month schedules
    start_date, end_date = _month_range(year, month)

    ClassSchedule.query.filter(
        ClassSchedule.scheduled_date >= start_date,
        ClassSchedule.scheduled_date < end_date,
        ClassSchedule.status.in_(['scheduled', 'planning'])
    ).update({'status': 'confirmed'}, synchronize_session=False)

    if force_publish and unresolved:
        for item in unresolved:
            sid = item.get('schedule_id')
            schedule = ClassSchedule.query.get(sid)
            if schedule:
                schedule.notes = f"{schedule.notes or ''}\n[强制发布备注] {force_note}".strip()

    db.session.commit()

    return jsonify({
        'message': f'{year}年{month}月计划已发布',
        'plan': plan.to_dict(),
        'forced': force_publish,
        'forced_conflict_count': len(unresolved) if force_publish else 0
    })


# ==================== 草稿保存 ====================

@schedule_bp.route('/save-draft', methods=['POST'])
def save_draft():
    """保存当前月度课表为草稿"""
    data = request.get_json()
    year = data.get('year')
    month = data.get('month')
    
    if not year or not month:
        return jsonify({'error': '缺少 year/month'}), 400
    
    plan = MonthlyPlan.query.filter_by(year=year, month=month).first()
    if not plan:
        plan = MonthlyPlan(year=year, month=month, status='draft')
        db.session.add(plan)
    
    plan.updated_at = datetime.now()
    # 如果已发布，不允许再存草稿（需要先解除发布）
    if plan.status == 'published':
        return jsonify({'error': '该月计划已发布，无法保存草稿'}), 400
    
    db.session.commit()
    
    return jsonify({
        'message': '草稿已保存',
        'plan': plan.to_dict()
    })


# ==================== 约束条件管理 ====================

def _get_or_create_plan(year, month):
    """获取或创建月度计划（辅助函数）"""
    plan = MonthlyPlan.query.filter_by(year=year, month=month).first()
    if not plan:
        plan = MonthlyPlan(year=year, month=month, status='draft')
        db.session.add(plan)
        db.session.flush()  # 获取 ID
    return plan


@schedule_bp.route('/constraints', methods=['GET'])
def get_constraints():
    """获取指定月份的所有约束条件"""
    year = request.args.get('year', type=int)
    month = request.args.get('month', type=int)
    
    if not year or not month:
        return jsonify({'error': '缺少 year/month'}), 400
    
    plan = MonthlyPlan.query.filter_by(year=year, month=month).first()
    if not plan:
        return jsonify([])
    
    constraints = ScheduleConstraint.query.filter_by(
        monthly_plan_id=plan.id
    ).order_by(ScheduleConstraint.created_at).all()
    
    return jsonify([c.to_dict() for c in constraints])


@schedule_bp.route('/constraints', methods=['POST'])
def add_constraint():
    """添加约束条件"""
    data = request.get_json()
    year = data.get('year')
    month = data.get('month')
    description = data.get('description', '').strip()
    
    if not year or not month:
        return jsonify({'error': '缺少 year/month'}), 400
    if not description:
        return jsonify({'error': '约束描述不能为空'}), 400
    
    plan = _get_or_create_plan(year, month)
    
    constraint = ScheduleConstraint(
        monthly_plan_id=plan.id,
        constraint_type=data.get('constraint_type', 'custom'),
        description=description,
        parsed_data=_json.dumps(data.get('parsed_data')) if data.get('parsed_data') else None,
        is_active=True
    )
    db.session.add(constraint)
    db.session.commit()
    
    return jsonify(constraint.to_dict()), 201


@schedule_bp.route('/constraints/<int:constraint_id>', methods=['PUT'])
def update_constraint(constraint_id):
    """更新约束条件（主要用于切换启用/禁用）"""
    c = ScheduleConstraint.query.get_or_404(constraint_id)
    data = request.get_json()
    
    if 'is_active' in data:
        c.is_active = data['is_active']
    if 'description' in data:
        c.description = data['description']
    if 'constraint_type' in data:
        c.constraint_type = data['constraint_type']
    if 'parsed_data' in data:
        c.parsed_data = _json.dumps(data['parsed_data']) if data['parsed_data'] else None
    
    db.session.commit()
    return jsonify(c.to_dict())


@schedule_bp.route('/constraints/<int:constraint_id>', methods=['DELETE'])
def delete_constraint(constraint_id):
    """删除约束条件"""
    c = ScheduleConstraint.query.get_or_404(constraint_id)
    db.session.delete(c)
    db.session.commit()
    return jsonify({'message': '约束已删除'})




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
    
    # 状态保护：已完成的课程不允许删除
    if schedule.status == 'completed':
        return jsonify({'error': '已完成的课程不能删除'}), 400
    
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
            ClassSchedule.status.in_(['scheduled', 'planning', 'conflict'])
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
            ).order_by(ClassSchedule.scheduled_date.desc()).first()
            
            # 获取所有topic按sequence排序
            # 获取该班级对应项目的所有课题
            all_topics = cls.project.topics.order_by("sequence").all()
            
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
                continue  # 该班级已结课
                
            # 找到合适的 Combo (Teacher) — 增强版：遍历所有combo，优先选不同讲师
            all_combos = TeacherCourseCombo.query.filter_by(topic_id=next_topic.id)\
                .order_by(TeacherCourseCombo.priority.desc(), TeacherCourseCombo.id.desc()).all()
            
            combo1 = None
            combo2 = None
            teacher1_name = None
            teacher2_name = None
            
            if all_combos:
                combo1 = all_combos[0]  # 优先级最高的
                # 周日：优先选不同讲师的combo
                combo2 = combo1  # 默认兜底
                for c in all_combos:
                    if c.teacher_id != combo1.teacher_id:
                        combo2 = c
                        break
                    
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
                    # 查找该班主任在当天的其他排课（排除当前班级自身）
                    homeroom_conflict = ClassSchedule.query.join(Class).filter(
                        Class.homeroom_id == cls.homeroom_id,
                        ClassSchedule.scheduled_date == sat,
                        ClassSchedule.class_id != cls.id
                    ).first()
                    
                    if homeroom_conflict:
                        current_conflict_reason = f"周六: 班主任撞课 ({homeroom_conflict.class_.name})"

                    # NEW: Check homeroom_unavailable constraint (AI Constraints)
                    if not current_conflict_reason:
                        homeroom_unavailable = constraints.get('homeroom_unavailable', [])
                        if cls.homeroom: # Ensure homeroom loaded
                            hrm_name = cls.homeroom.name
                            # Determine week range for candidate Saturday (Mon..Sun)
                            week_monday = sat - timedelta(days=5)
                            week_sunday = week_monday + timedelta(days=6)

                            for u in homeroom_unavailable:
                                if u.get('homeroom_name') != hrm_name:
                                    continue

                                # u['dates'] may be a list of ISO dates or date ranges; handle common formats
                                dates = u.get('dates', [])
                                parsed = []
                                for item in dates:
                                    if isinstance(item, str):
                                        # single date
                                        try:
                                            parsed.append(date.fromisoformat(item))
                                        except Exception:
                                            # try to parse ranges like '2026-04-13~2026-04-17'
                                            if '~' in item:
                                                parts = item.split('~')
                                                try:
                                                    d1 = date.fromisoformat(parts[0])
                                                    d2 = date.fromisoformat(parts[1])
                                                    # expand range (inclusive)
                                                    d = d1
                                                    while d <= d2:
                                                        parsed.append(d)
                                                        d = d + timedelta(days=1)
                                                except Exception:
                                                    pass
                                    elif isinstance(item, dict):
                                        # permissive: {from: 'YYYY-MM-DD', to: 'YYYY-MM-DD'}
                                        f = item.get('from') or item.get('start')
                                        t = item.get('to') or item.get('end')
                                        try:
                                            d1 = date.fromisoformat(f)
                                            d2 = date.fromisoformat(t)
                                            d = d1
                                            while d <= d2:
                                                parsed.append(d)
                                                d = d + timedelta(days=1)
                                        except Exception:
                                            pass

                                # If any parsed date falls within the candidate week, block this weekend
                                for pd in parsed:
                                    if week_monday <= pd <= week_sunday:
                                        current_conflict_reason = f"周末: 班主任 {hrm_name} 在同一周请假/不可用"
                                        break
                                if current_conflict_reason:
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
                        TeacherCourseCombo.teacher_id == combo1.teacher_id,
                        ClassSchedule.class_id != cls.id
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
                    schedules_on_sat = ClassSchedule.query.filter(
                        ClassSchedule.scheduled_date == sat,
                        ClassSchedule.class_id != cls.id
                    ).all()
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
                # 设置冲突类型
                conflict_type_val = None
                if final_status == 'conflict':
                    if '班主任' in (final_notes or ''):
                        conflict_type_val = 'homeroom'
                    elif '讲师' in (final_notes or ''):
                        conflict_type_val = 'teacher'
                    elif '节假日' in (final_notes or ''):
                        conflict_type_val = 'holiday'

                new_schedule = ClassSchedule(
                    class_id=cls.id,
                    topic_id=next_topic.id,
                    combo_id=combo1.id if combo1 else None,
                    combo_id_2=combo2.id if combo2 else None,
                    scheduled_date=assigned_date,
                    week_number=0,
                    status=final_status,
                    conflict_type=conflict_type_val,
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
        
        # 自动创建/更新月度计划为草稿
        plan = MonthlyPlan.query.filter_by(year=year, month=month).first()
        if not plan:
            plan = MonthlyPlan(year=year, month=month, status='draft')
            db.session.add(plan)
        plan.updated_at = datetime.now()
        db.session.commit()
        
        result_msg = f'已生成 {generated_count} 节课程安排'
        if skipped_classes_info:
            result_msg += f'。有 {len(skipped_classes_info)} 个班级未排课：' + '; '.join([f"{i['class_name']}({i['reason']})" for i in skipped_classes_info])
            
        return jsonify({
            'success': True, 
            'message': result_msg,
            'skipped': skipped_classes_info,
            'plan': plan.to_dict()
        })
        
    except Exception as e:
        db.session.rollback()
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500
