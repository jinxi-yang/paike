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
    
    # 获取该班级已有的排课记录
    existing = ClassSchedule.query.filter_by(class_id=class_id).all()
    existing_map = {}  # topic_id -> schedule_dict
    for s in existing:
        existing_map[s.topic_id] = s.to_dict()
    
    # 构建课题列表（含combo选项 + 已有排课信息）
    topic_list = []
    for t in topics:
        combos = TeacherCourseCombo.query.filter_by(topic_id=t.id).all()
        topic_data = t.to_dict()
        topic_data['combos'] = [c.to_dict() for c in combos]
        topic_data['existing_schedule'] = existing_map.get(t.id, None)
        topic_list.append(topic_data)
    
    from config import Config
    
    return jsonify({
        'class': cls.to_dict(),
        'project_name': project.name if project else None,
        'topics': topic_list,
        'existing_count': len(existing),
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
    
    created = []
    for item in items:
        topic_id = item.get('topic_id')
        combo_id = item.get('combo_id')
        combo_id_2 = item.get('combo_id_2')
        date_str = item.get('date')
        
        if not topic_id or not combo_id or not date_str:
            continue
        
        # 检查是否已有该课题的排课记录
        existing = ClassSchedule.query.filter_by(
            class_id=class_id, topic_id=topic_id
        ).first()
        
        if existing and not clear_existing:
            # 更新已有记录
            existing.combo_id = combo_id
            existing.combo_id_2 = combo_id_2 if combo_id_2 else None
            existing.scheduled_date = datetime.strptime(date_str, '%Y-%m-%d').date()
            existing.status = 'completed'
            created.append(existing.to_dict())
        else:
            # 新建排课记录
            schedule = ClassSchedule(
                class_id=class_id,
                topic_id=topic_id,
                combo_id=combo_id,
                combo_id_2=combo_id_2 if combo_id_2 else None,
                scheduled_date=datetime.strptime(date_str, '%Y-%m-%d').date(),
                status='completed',
                notes='系统初始化导入'
            )
            db.session.add(schedule)
            created.append({'topic_id': topic_id, 'status': 'completed'})
    
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
    
    return jsonify({
        'message': f'成功初始化 {len(created)} 个课题',
        'count': len(created),
        'class_status': cls.status
    })
