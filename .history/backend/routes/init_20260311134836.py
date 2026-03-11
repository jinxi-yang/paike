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
    
    # 自动完成：过去日期的 scheduled → completed
    from datetime import date as dt_date
    today = dt_date.today()
    auto_completed = ClassSchedule.query.filter(
        ClassSchedule.class_id == class_id,
        ClassSchedule.status == 'scheduled',
        ClassSchedule.scheduled_date < today
    ).update({ClassSchedule.status: 'completed'}, synchronize_session='fetch')
    
    # 反向纠正：未来日期的 completed → scheduled（数据修正）
    auto_fixed = ClassSchedule.query.filter(
        ClassSchedule.class_id == class_id,
        ClassSchedule.status == 'completed',
        ClassSchedule.scheduled_date >= today
    ).update({ClassSchedule.status: 'scheduled'}, synchronize_session='fetch')
    
    if auto_completed or auto_fixed:
        db.session.commit()
    
    # 获取该班级已有的排课记录
    existing = ClassSchedule.query.filter_by(class_id=class_id).all()
    existing_map = {}  # topic_id -> schedule_dict（保留最新日期的记录）
    for s in existing:
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
    
    created = []
    skipped = []
    for item in items:
        topic_id = item.get('topic_id')
        combo_id = item.get('combo_id')
        combo_id_2 = item.get('combo_id_2')
        date_str = item.get('date')
        
        if not topic_id or not combo_id or not date_str:
            # 记录跳过的条目而非静默忽略
            skipped.append({
                'topic_id': topic_id,
                'reason': '缺少必填信息' + ('（未选周六组合）' if not combo_id else '') + ('（未选日期）' if not date_str else '')
            })
            continue
        
        # 检查是否已有该课题的排课记录
        existing = ClassSchedule.query.filter_by(
            class_id=class_id, topic_id=topic_id
        ).first()
        
        if existing and not clear_existing:
            # 更新已有记录
            existing.combo_id = combo_id
            existing.combo_id_2 = combo_id_2 if combo_id_2 else None
            parsed_date = datetime.strptime(date_str, '%Y-%m-%d').date()
            existing.scheduled_date = parsed_date
            existing.status = 'completed' if parsed_date < today else 'scheduled'
            created.append(existing.to_dict())
        else:
            # 新建排课记录
            parsed_date = datetime.strptime(date_str, '%Y-%m-%d').date()
            record_status = 'completed' if parsed_date < today else 'scheduled'
            schedule = ClassSchedule(
                class_id=class_id,
                topic_id=topic_id,
                combo_id=combo_id,
                combo_id_2=combo_id_2 if combo_id_2 else None,
                scheduled_date=parsed_date,
                status=record_status,
                notes='系统初始化导入'
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
    
    # 检查班级是否所有课题已完成(仅在排课变更时触发)
    from .classes import check_class_completion
    check_class_completion(class_id)
    
    # reload status after potential update
    db.session.refresh(cls)
    
    return jsonify({
        'message': f'成功初始化 {len(created)} 个课题' + (f'，{len(skipped)} 个被跳过' if skipped else ''),
        'count': len(created),
        'skipped': skipped,
        'class_status': cls.status
    })
