"""
系统初始化API - 班级进度初始化向导
"""
from flask import Blueprint, jsonify, request
from models import db, Project, Topic, Class, ClassSchedule, TeacherCourseCombo
from datetime import datetime, timedelta

init_bp = Blueprint('init', __name__)


@init_bp.route('/class-status/<int:class_id>', methods=['GET'])
def class_status(class_id):
    """获取班级初始化状态：班级信息 + 课题(含combo) + 已有排课"""
    cls = Class.query.get_or_404(class_id)
    project = Project.query.get(cls.project_id)
    
    # 获取该项目的所有课题（按序号排列）
    topics = Topic.query.filter_by(project_id=cls.project_id).order_by(Topic.sequence).all()
    
    # #21: 删除重复的状态自动转换，统一由 classes.py 的 sync_class_statuses 处理
    # （GET classes 列表时已自动触发 sync_class_statuses）
    
    # 获取该班级已有的排课记录
    existing = ClassSchedule.query.filter_by(class_id=class_id).all()
    existing_map = {}  # topic_id -> schedule_dict（保留最新日期的记录）
    duplicate_warnings = []  # #2: 记录有多条记录的课题
    topic_record_counts = {}
    
    for s in existing:
        topic_record_counts[s.topic_id] = topic_record_counts.get(s.topic_id, 0) + 1
        if s.topic_id not in existing_map or (s.scheduled_date and (
            not existing_map[s.topic_id].get('_raw_date') or 
            s.scheduled_date > existing_map[s.topic_id]['_raw_date']
        )):
            d = s.to_dict()
            d['_raw_date'] = s.scheduled_date  # 临时字段用于比较
            existing_map[s.topic_id] = d
    
    # 清理临时字段
    for v in existing_map.values():
        v.pop('_raw_date', None)
    
    # #2: 构建重复记录警告
    for tid, count in topic_record_counts.items():
        if count > 1:
            topic = Topic.query.get(tid)
            duplicate_warnings.append({
                'topic_id': tid,
                'topic_name': topic.name if topic else str(tid),
                'record_count': count
            })
    
    # 构建课题列表（含combo选项 + 已有排课信息）
    topic_list = []
    for t in topics:
        combos = TeacherCourseCombo.query.filter_by(topic_id=t.id).all()
        topic_data = t.to_dict()
        topic_data['combos'] = [c.to_dict() for c in combos]
        topic_data['existing_schedule'] = existing_map.get(t.id, None)
        topic_list.append(topic_data)
    
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
        'weeks_interval': getattr(Config, 'MIN_WEEKS_INTERVAL', 4),
        'duplicate_warnings': duplicate_warnings  # #2
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
    
    created = []
    skipped = []
    for item in items:
        topic_id = item.get('topic_id')
        combo_id = item.get('combo_id')
        combo_id_2 = item.get('combo_id_2')
        date_str = item.get('date')
        sequence = item.get('sequence')
        
        if not topic_id or not combo_id or not date_str:
            # 记录跳过的条目而非静默忽略
            skipped.append({
                'topic_id': topic_id,
                'reason': '缺少必填信息' + ('（未选周六组合）' if not combo_id else '') + ('（未选日期）' if not date_str else '')
            })
            continue
        
        # #3: 检查是否已有该课题的排课记录（排除合班子记录）
        all_existing = ClassSchedule.query.filter_by(
            class_id=class_id, topic_id=topic_id
        ).all()
        
        # 分离：普通记录 vs 合班记录
        normal_records = [r for r in all_existing if not r.merged_with]
        merged_records = [r for r in all_existing if r.merged_with]
        
        if normal_records and not clear_existing:
            # 更新第一条普通记录，删除多余的普通重复记录（保留合班记录不动）
            keep = normal_records[0]
            for dup in normal_records[1:]:
                db.session.delete(dup)
            
            keep.combo_id = combo_id
            keep.combo_id_2 = combo_id_2 if combo_id_2 else None
            parsed_date = datetime.strptime(date_str, '%Y-%m-%d').date()
            keep.scheduled_date = parsed_date
            keep.status = 'completed' if parsed_date < today else 'scheduled'
            # #1: 设置 week_number
            if sequence:
                keep.week_number = sequence
            # #18: 保留已有的 notes，不覆盖
            # #19: 保留已有的 homeroom_override_id，不清除
            created.append(keep.to_dict())
        elif not all_existing or clear_existing:
            # 新建排课记录（没有任何已有记录，或 clear_existing 模式）
            parsed_date = datetime.strptime(date_str, '%Y-%m-%d').date()
            record_status = 'completed' if parsed_date < today else 'scheduled'
            schedule = ClassSchedule(
                class_id=class_id,
                topic_id=topic_id,
                combo_id=combo_id,
                combo_id_2=combo_id_2 if combo_id_2 else None,
                scheduled_date=parsed_date,
                week_number=sequence,  # #1: 设置 week_number
                status=record_status,
                notes='课程录入导入'  # #18: 更准确的描述
            )
            db.session.add(schedule)
            created.append({'topic_id': topic_id, 'status': record_status})
        else:
            # 只有合班记录，没有普通记录 → 新建一条普通记录
            parsed_date = datetime.strptime(date_str, '%Y-%m-%d').date()
            record_status = 'completed' if parsed_date < today else 'scheduled'
            schedule = ClassSchedule(
                class_id=class_id,
                topic_id=topic_id,
                combo_id=combo_id,
                combo_id_2=combo_id_2 if combo_id_2 else None,
                scheduled_date=parsed_date,
                week_number=sequence,
                status=record_status,
                notes='课程录入导入'
            )
            db.session.add(schedule)
            created.append({'topic_id': topic_id, 'status': record_status})
    
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
    
    # 按日期重排课题 sequence，确保序号和日期顺序一致
    from .schedule import _resequence_topics_by_date
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
