import os

file_path = r"backend\routes\schedule.py"
with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

# 1. Add _recalculate_assignments_conflicts
recalc_func = '''
def _recalculate_assignments_conflicts(assignments, constraints, homeroom_overrides=None):
    """
    全量 O(N^2) 重新检测所有已分配的组合冲突，确保冲突计数对称。
    """
    if homeroom_overrides is None:
        homeroom_overrides = {}
        
    assigned_map = {}
    for a in assignments:
        if a.get('is_merged_target'): continue
        if not a.get('assigned_date'): continue
        cls_id = a['class_id']
        combo1_teacher_id = None
        combo2_teacher_id = None
        if a.get('combo_id'):
            from models import TeacherCourseCombo
            c1 = TeacherCourseCombo.query.get(a['combo_id'])
            if c1: combo1_teacher_id = c1.teacher_id
        if a.get('combo_id_2'):
            from models import TeacherCourseCombo
            c2 = TeacherCourseCombo.query.get(a['combo_id_2'])
            if c2: combo2_teacher_id = c2.teacher_id
            
        from models import Class
        cls_obj = Class.query.get(cls_id)
        
        from datetime import date
        assigned_map[cls_id] = {
            'date': date.fromisoformat(a['assigned_date']),
            'combo1_teacher_id': combo1_teacher_id,
            'combo2_teacher_id': combo2_teacher_id,
            'topic_id': a.get('topic_id'),
            'city_id': cls_obj.city_id if cls_obj else None
        }

    for a in assignments:
        if a.get('is_merged_target') or not a.get('assigned_date'):
            continue
            
        cls_id = a['class_id']
        from models import Class, TeacherCourseCombo
        cls = Class.query.get(cls_id)
        if not cls: continue
        
        from datetime import date
        sat = date.fromisoformat(a['assigned_date'])
        last_date = date.fromisoformat(a['last_date']) if a.get('last_date') else None
        
        combo1 = TeacherCourseCombo.query.get(a['combo_id']) if a.get('combo_id') else None
        combo2 = TeacherCourseCombo.query.get(a['combo_id_2']) if a.get('combo_id_2') else None
        
        # 构建不含自身的 assigned_map
        other_map = {k: v for k, v in assigned_map.items() if k != cls_id}
        
        score, is_hard, conflict_reasons, merge_suggestions = _score_candidate(
            cls, sat, last_date, combo1, combo2,
            other_map, constraints, homeroom_overrides
        )
        
        a['conflicts'] = conflict_reasons
        conflict_text = '；'.join(conflict_reasons) if conflict_reasons else ""
        if '班主任' in conflict_text:
            a['conflict_type'] = 'homeroom'
        elif '讲师' in conflict_text:
            a['conflict_type'] = 'teacher'
        elif '节假日' in conflict_text:
            a['conflict_type'] = 'holiday'
        elif conflict_text:
            a['conflict_type'] = 'other'
        else:
            a['conflict_type'] = None
            
        a['score'] = score
        a['merge_suggestions'] = merge_suggestions
'''
if "def _recalculate_assignments_conflicts" not in content:
    content = content.replace("def _find_best_combo_for_saturday", recalc_func + "\n\ndef _find_best_combo_for_saturday")

# 2. Modify _run_best_of_n
# Find Phase 1 end
ph1_old = """
        # Phase 1: 贪心打底
        assignments = _run_scheduling_algorithm(
            year, month, constraints, conflict_mode, overrides, skip_class_ids, homeroom_overrides, combo_overrides, shuffle_seed=i,
            precomputed=precomputed)"""
ph1_new = ph1_old + """
        _recalculate_assignments_conflicts(assignments, constraints, homeroom_overrides)"""

content = content.replace(ph1_old, ph1_new)

ph2_old = """        _optimize_combos_per_day(assignments_copy, constraints)
        quality = _build_quality_report(assignments_copy)"""
ph2_new = """        _optimize_combos_per_day(assignments_copy, constraints)
        _recalculate_assignments_conflicts(assignments_copy, constraints, homeroom_overrides)
        quality = _build_quality_report(assignments_copy)"""
content = content.replace(ph2_old, ph2_new)

# 3. Add evaluate_preview
eval_prev = '''
@schedule_bp.route('/evaluate-preview', methods=['POST'])
def evaluate_preview():
    """
    轻量评估预览：不重新排课，只重新检测冲突和计算评分。
    前端在调整日期/组合/班主任后调用此接口，避免完整重排。
    """
    data = request.get_json()
    assignments_raw = data.get('assignments', [])
    constraints = data.get('constraints', {})
    raw_hr_overrides = data.get('homeroom_overrides', {})
    homeroom_overrides = {int(k): v for k, v in raw_hr_overrides.items()} if raw_hr_overrides else {}

    all_dates_for_month = [a['assigned_date'] for a in assignments_raw if a.get('assigned_date')]
    if all_dates_for_month:
        first_date = date.fromisoformat(min(all_dates_for_month))
        db_constraints = _load_db_constraints(first_date.year, first_date.month)
        if db_constraints:
            constraints = _merge_constraints(constraints, db_constraints)

    if not assignments_raw:
        return jsonify({'error': 'No assignments to evaluate'}), 400

    try:
        # 重计算前清除测试范围的db状态，类似generate
        all_dates = [a['assigned_date'] for a in assignments_raw if a.get('assigned_date')]
        if all_dates:
            min_date = date.fromisoformat(min(all_dates))
            max_date = date.fromisoformat(max(all_dates))
            start_d = date(min_date.year, min_date.month, 1)
            end_month = max_date.month + 1 if max_date.month < 12 else 1
            end_year = max_date.year if max_date.month < 12 else max_date.year + 1
            end_d = date(end_year, end_month, 1)

            ClassSchedule.query.filter(
                ClassSchedule.scheduled_date >= start_d,
                ClassSchedule.scheduled_date < end_d,
                ClassSchedule.status.in_(['scheduled'])
            ).delete(synchronize_session='fetch')
            db.session.flush()

        # 利用提取的完全对称重算逻辑
        _recalculate_assignments_conflicts(assignments_raw, constraints, homeroom_overrides)
        
        # 构建 homeroom_availability 特征（被前端需要用）
        all_hr = Homeroom.query.all()
        for a in assignments_raw:
            if a.get('is_merged_target') or not a.get('assigned_date'): continue
            assigned_date_str = a['assigned_date']
            busy_homerooms = {}
            for other_a in assignments_raw:
                if other_a.get('class_id') == a['class_id'] or other_a.get('is_merged_target'):
                    continue
                if other_a.get('assigned_date') == assigned_date_str:
                    if other_a.get('homeroom_id'):
                        busy_homerooms[other_a.get('homeroom_id')] = other_a.get('class_name', '?')
            a['homeroom_availability'] = [
                {
                    'id': h.id,
                    'name': h.name,
                    'busy': h.id in busy_homerooms,
                    'busy_class': busy_homerooms.get(h.id)
                } for h in all_hr
            ]

        db.session.rollback()
        
        non_merged = [a for a in assignments_raw if not a.get('is_merged_target')]
        quality_report = _build_quality_report(non_merged)
        return jsonify({'success': True, 'preview': assignments_raw, 'quality_report': quality_report})
    except Exception as e:
        db.session.rollback()
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500
'''
if "def evaluate_preview():" not in content:
    content = content.replace("def _get_candidate_saturdays", eval_prev + "\n\ndef _get_candidate_saturdays")

# 4. Modify _score_candidate (City check)
score_old = """    assigned_count = sum(1 for info in assigned_map.values() if info['date'] == sat)
    total_on_sat = db_count + assigned_count

    # 教室硬上限：超过最大教室数直接拒绝
    from config import Config as _cfg_cls
    max_rooms = getattr(_cfg_cls, 'MAX_CLASSES_PER_SATURDAY', 7)
    if total_on_sat >= max_rooms:
        return (0.0, True, [f'教室已满({total_on_sat}/{max_rooms})'], [])"""

score_new = """    cls_city_id = cls.city_id
    if cls_city_id:
        db_count = _rc_city.get((sat, cls_city_id), 0) if '_rc_city' in locals() else ClassSchedule.query.filter(
            ClassSchedule.scheduled_date == sat,
            ClassSchedule.status.in_(['scheduled', 'completed']),
            ClassSchedule.merged_with.is_(None)
        ).join(Class).filter(Class.city_id == cls_city_id).count()
    else:
        db_count = _rc_all.get(sat, 0) if '_rc_all' in locals() else ClassSchedule.query.filter(
            ClassSchedule.scheduled_date == sat,
            ClassSchedule.status.in_(['scheduled', 'completed']),
            ClassSchedule.merged_with.is_(None)
        ).count()

    assigned_count = 0
    for a_cls_id, info in assigned_map.items():
        if info['date'] == sat:
            if cls_city_id and info.get('city_id') != cls_city_id:
                continue
            assigned_count += 1
            
    total_on_sat = db_count + assigned_count

    city = cls.city_ref if cls.city_id else None
    city_name = city.name if city else '未知'
    max_rooms = city.max_classrooms if city else 99
    
    if total_on_sat >= max_rooms:
        return (0.0, True, [f'{city_name}教室已满({total_on_sat}/{max_rooms})'], [])"""

if "cls_city_id = cls.city_id" not in content and score_old in content:
    content = content.replace(score_old, score_new)

# 5. Modify update_schedule constraint relaxation
# (Saturdays -> Warnings)
update_old = """            # 检查是否是周六
            if new_date.weekday() != 5:
                return jsonify({'error': '排课日期必须是周六'}), 400"""
update_new = """            date_actually_changed = (schedule.scheduled_date != new_date)
            # 检查是否是周六 (现在是警告不是报错)
            if date_actually_changed and new_date.weekday() != 5:
                pass # 允许前端安排在非周末"""
if update_old in content:
    content = content.replace(update_old, update_new)

# Write back
with open(file_path, "w", encoding="utf-8") as f:
    f.write(content)

print("Patch applied.")
