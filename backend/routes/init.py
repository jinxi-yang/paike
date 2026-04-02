"""
系统初始化API - 班级进度初始化向导
"""
from flask import Blueprint, jsonify, request
from models import db, Project, Topic, Class, ClassSchedule, TeacherCourseCombo
from .schedule import _resequence_topics_by_date
from datetime import datetime, timedelta

init_bp = Blueprint('init', __name__)


@init_bp.route('/class-status/<int:class_id>', methods=['GET'])
def class_status(class_id):
    """获取班级初始化状态：班级信息 + 课题(含combo) + 已有排课"""
    cls = Class.query.get_or_404(class_id)
    project = Project.query.get(cls.project_id)
    
    # 获取该项目的所有课题（按序号排列）
    topics = Topic.query.filter_by(project_id=cls.project_id).order_by(Topic.id).all()
    
    # #21: 删除重复的状态自动转换，统一由 classes.py 的 sync_class_statuses 处理
    # （GET classes 列表时已自动触发 sync_class_statuses）
    
    # 获取该班级已有的排课记录
    existing = ClassSchedule.query.filter_by(class_id=class_id).all()
    existing_map = {}  # topic_id -> list of schedule_dict
    
    for s in existing:
        if s.topic_id not in existing_map:
            existing_map[s.topic_id] = []
        existing_map[s.topic_id].append(s.to_dict())
    
    for tid in existing_map:
        existing_map[tid].sort(key=lambda x: x.get('scheduled_date') or '')
    
    # 构建课题列表（含combo选项 + 已有排课信息）
    topic_list = []
    for t in topics:
        combos = TeacherCourseCombo.query.filter_by(topic_id=t.id).all()
        topic_data = t.to_dict()
        topic_data['combos'] = [c.to_dict() for c in combos]
        topic_data['existing_schedules'] = existing_map.get(t.id, [])
        topic_list.append(topic_data)
    
    # 按上课时间排序：有排课日期的按日期升序，无排课日期的放最后
    def _sort_key(item):
        schedules = item.get('existing_schedules', [])
        if schedules:
            dates = [s.get('scheduled_date', '') for s in schedules if s.get('scheduled_date')]
            if dates:
                return (0, min(dates))  # 有日期排前面
        return (1, '')  # 无日期排后面
    topic_list.sort(key=_sort_key)
    
    from config import Config
    
    # Count topics with completed status specifically
    completed_count = sum(1 for s in existing if s.status == 'completed')
    
    return jsonify({
        'class': cls.to_dict(),
        'project_name': project.name if project else None,
        'topics': topic_list,
        'existing_count': len(existing_map),
        'completed_count': completed_count,
        'total_topics': len(topics),
        'weeks_interval': getattr(Config, 'MIN_WEEKS_INTERVAL', 4)
    })


@init_bp.route('/class-progress', methods=['POST'])
def init_class_progress():
    """批量初始化班级进度"""
    data = request.json
    class_id = data.get('class_id')
    items = data.get('items', [])
    clear_existing = data.get('clear_existing', False)
    
    if not class_id or not items:
        return jsonify({'error': '缺少必要参数'}), 400
    
    cls = Class.query.get_or_404(class_id)
    
    # 如果要清空已有记录
    if clear_existing:
        ClassSchedule.query.filter_by(class_id=class_id).delete()
        db.session.flush()
    
    from datetime import date as dt_date
    today = dt_date.today()
    
    # #4: 不再修改 topic.sequence（拖拽排序仅作为本次提交的顺序，不影响项目级课题排列）
    
    # Group items by topic_id to properly handle duplicates
    created = []
    skipped = []
    from collections import defaultdict
    topic_items = defaultdict(list)
    for item in items:
        topic_id = item.get('topic_id')
        combo_id = item.get('combo_id')
        date_str = item.get('date')
        if not topic_id or not combo_id or not date_str:
            skipped.append({
                'topic_id': topic_id,
                'reason': '缺少必填信息' + ('（未选周六组合）' if not combo_id else '') + ('（未选日期）' if not date_str else '')
            })
            continue
        topic_items[topic_id].append(item)
    
    for topic_id, t_items in topic_items.items():
        all_existing = ClassSchedule.query.filter_by(
            class_id=class_id, topic_id=topic_id
        ).all()
        
        normal_records = [r for r in all_existing if not r.merged_with]
        # Sort by scheduled_date to align predictably with UI's index
        normal_records.sort(key=lambda r: (r.scheduled_date is None, r.scheduled_date))
        
        for i, item in enumerate(t_items):
            combo_id = item.get('combo_id')
            combo_id_2 = item.get('combo_id_2')
            date_str = item.get('date')
            sequence = item.get('sequence')
            has_opening = item.get('has_opening', False)
            has_team_building = item.get('has_team_building', False)
            has_closing = item.get('has_closing', False)
            parsed_date = datetime.strptime(date_str, '%Y-%m-%d').date()
            record_status = 'completed' if parsed_date < today else 'scheduled'
            
            if not clear_existing and i < len(normal_records):
                keep = normal_records[i]
                keep.combo_id = combo_id
                keep.combo_id_2 = combo_id_2 if combo_id_2 else None
                keep.scheduled_date = parsed_date
                keep.status = record_status
                if sequence:
                    keep.week_number = sequence
                keep.has_opening = has_opening
                keep.has_team_building = has_team_building
                keep.has_closing = has_closing
                created.append(keep.to_dict())
            else:
                schedule = ClassSchedule(
                    class_id=class_id,
                    topic_id=topic_id,
                    combo_id=combo_id,
                    combo_id_2=combo_id_2 if combo_id_2 else None,
                    scheduled_date=parsed_date,
                    week_number=sequence,
                    status=record_status,
                    notes='课程录入导入',
                    has_opening=has_opening,
                    has_team_building=has_team_building,
                    has_closing=has_closing,
                    location_id=cls.city_id
                )
                db.session.add(schedule)
                created.append({'topic_id': topic_id, 'status': record_status})
        
        # Delete any excess normal records from database that were removed in the UI but not explicitly deleted
        if not clear_existing and len(normal_records) > len(t_items):
            for dup in normal_records[len(t_items):]:
                db.session.delete(dup)
    
    # 更新班级状态
    if cls.status == 'planning':
        cls.status = 'active'
    
    # 如果班级没有 start_date，用最早的日期
    if not cls.start_date and items:
        dates = [datetime.strptime(i['date'], '%Y-%m-%d').date() 
                 for i in items if i.get('date')]
        if dates:
            cls.start_date = min(dates)
    
    db.session.commit()
    
    # 重算 week_number，确保所有排课记录有正确的课次序号
    _resequence_topics_by_date(class_id)
    
    # 检查班级是否所有课题已完成(仅在排课变更时触发)
    from .classes import check_class_completion
    check_class_completion(class_id)
    
    # reload status after potential update
    db.session.refresh(cls)
    
    # #17: 保存后执行冲突检测
    conflicts = _check_init_conflicts(class_id)
    
    return jsonify({
        'message': f'成功保存 {len(created)} 个课题' + (f'，{len(skipped)} 个被跳过' if skipped else ''),
        'count': len(created),
        'skipped': skipped,
        'class_status': cls.status,
        'conflicts': conflicts  # #17: 返回冲突列表
    })


def _check_init_conflicts(class_id):
    """#17: 检查保存后的冲突（讲师冲突、班主任冲突）"""
    conflicts = []
    cls = Class.query.get(class_id)
    if not cls:
        return conflicts
    
    schedules = ClassSchedule.query.filter_by(class_id=class_id).filter(
        ClassSchedule.status.notin_(['completed', 'cancelled'])
    ).all()
    
    for s in schedules:
        if not s.scheduled_date:
            continue
        
        # 讲师冲突检查
        if s.combo_id:
            combo = TeacherCourseCombo.query.get(s.combo_id)
            if combo:
                teacher_conflict = ClassSchedule.query.join(
                    TeacherCourseCombo,
                    db.or_(
                        ClassSchedule.combo_id == TeacherCourseCombo.id,
                        ClassSchedule.combo_id_2 == TeacherCourseCombo.id
                    )
                ).filter(
                    TeacherCourseCombo.teacher_id == combo.teacher_id,
                    ClassSchedule.scheduled_date == s.scheduled_date,
                    ClassSchedule.id != s.id,
                    ClassSchedule.status.notin_(['cancelled'])
                ).first()
                
                if teacher_conflict:
                    conflicts.append({
                        'type': 'teacher',
                        'topic_name': s.topic.name if s.topic else '?',
                        'date': s.scheduled_date.isoformat(),
                        'detail': f'讲师 {combo.teacher.name} 在 {s.scheduled_date} 与 {teacher_conflict.class_.name} 冲突'
                    })
        
        # 班主任冲突检查
        if cls.homeroom_id:
            homeroom_conflict = ClassSchedule.query.join(
                Class, Class.id == ClassSchedule.class_id
            ).filter(
                Class.homeroom_id == cls.homeroom_id,
                ClassSchedule.scheduled_date == s.scheduled_date,
                ClassSchedule.class_id != class_id,
                ClassSchedule.status.notin_(['cancelled'])
            ).first()
            
            if homeroom_conflict:
                conflicts.append({
                    'type': 'homeroom',
                    'topic_name': s.topic.name if s.topic else '?',
                    'date': s.scheduled_date.isoformat(),
                    'detail': f'班主任在 {s.scheduled_date} 与 {homeroom_conflict.class_.name} 冲突'
                })
    
    return conflicts
