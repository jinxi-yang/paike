import re

with open(r"backend\routes\schedule.py", "r", encoding="utf-8") as f:
    content = f.read()

# 1. Add evaluate_preview before _get_candidate_saturdays
if "def evaluate_preview" not in content:
    eval_prev = """
@schedule_bp.route('/evaluate-preview', methods=['POST'])
def evaluate_preview():
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

        _recalculate_assignments_conflicts(assignments_raw, constraints, homeroom_overrides)
        
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

"""
    content = re.sub(r'def _get_candidate_saturdays', eval_prev + r'def _get_candidate_saturdays', content)

# 2. _recalculate_assignments_conflicts
if "def _recalculate_assignments_conflicts" not in content:
    recalc = """
def _recalculate_assignments_conflicts(assignments, constraints, homeroom_overrides=None):
    if homeroom_overrides is None: homeroom_overrides = {}
    assigned_map = {}
    for a in assignments:
        if a.get('is_merged_target'): continue
        if not a.get('assigned_date'): continue
        cls_id = a['class_id']
        combo1_teacher_id = None
        combo2_teacher_id = None
        if a.get('combo_id'):
            c1 = TeacherCourseCombo.query.get(a['combo_id'])
            if c1: combo1_teacher_id = c1.teacher_id
        if a.get('combo_id_2'):
            c2 = TeacherCourseCombo.query.get(a['combo_id_2'])
            if c2: combo2_teacher_id = c2.teacher_id
        cls_obj = Class.query.get(cls_id)
        assigned_map[cls_id] = {
            'date': date.fromisoformat(a['assigned_date']),
            'combo1_teacher_id': combo1_teacher_id,
            'combo2_teacher_id': combo2_teacher_id,
            'topic_id': a.get('topic_id'),
            'city_id': cls_obj.city_id if cls_obj else None
        }

    for a in assignments:
        if a.get('is_merged_target') or not a.get('assigned_date'): continue
        cls_id = a['class_id']
        cls = Class.query.get(cls_id)
        if not cls: continue
        
        sat = date.fromisoformat(a['assigned_date'])
        last_date = date.fromisoformat(a['last_date']) if a.get('last_date') else None
        combo1 = TeacherCourseCombo.query.get(a['combo_id']) if a.get('combo_id') else None
        combo2 = TeacherCourseCombo.query.get(a['combo_id_2']) if a.get('combo_id_2') else None
        
        other_map = {k: v for k, v in assigned_map.items() if k != cls_id}
        
        score, is_hard, conflict_reasons, merge_suggestions = _score_candidate(
            cls, sat, last_date, combo1, combo2, other_map, constraints, homeroom_overrides
        )
        
        a['conflicts'] = conflict_reasons
        conflict_text = '；'.join(conflict_reasons) if conflict_reasons else ""
        if '班主任' in conflict_text: a['conflict_type'] = 'homeroom'
        elif '讲师' in conflict_text: a['conflict_type'] = 'teacher'
        elif '节假日' in conflict_text: a['conflict_type'] = 'holiday'
        elif conflict_text: a['conflict_type'] = 'other'
        else: a['conflict_type'] = None
        a['score'] = score
        a['merge_suggestions'] = merge_suggestions

"""
    content = re.sub(r'def _find_best_combo_for_saturday', recalc + r'def _find_best_combo_for_saturday', content)


# 3. Call it in _run_best_of_n
if "_recalculate_assignments_conflicts(assignments," not in content:
    content = re.sub(
        r'(assignments = _run_scheduling_algorithm\([\s\S]*?precomputed=precomputed\))',
        r'\1\n        _recalculate_assignments_conflicts(assignments, constraints, homeroom_overrides)',
        content
    )

if "_recalculate_assignments_conflicts(assignments_copy," not in content:
    content = re.sub(
        r'(_optimize_combos_per_day\(assignments_copy, constraints\))',
        r'\1\n        _recalculate_assignments_conflicts(assignments_copy, constraints, homeroom_overrides)',
        content
    )


# 4. _score_candidate fix city
score_pat = r"assigned_count = sum.*?max_rooms = getattr\(_cfg_cls, 'MAX_CLASSES_PER_SATURDAY', 7\)\s*if total_on_sat >= max_rooms:.*?\], \[\]\)"
score_new = """cls_city_id = cls.city_id
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
            if cls_city_id and info.get('city_id') != cls_city_id: continue
            assigned_count += 1
            
    total_on_sat = db_count + assigned_count

    city = cls.city_ref if cls.city_id else None
    city_name = city.name if city else '未知'
    max_rooms = city.max_classrooms if city else 99
    
    if total_on_sat >= max_rooms:
        return (0.0, True, [f'{city_name}教室已满({total_on_sat}/{max_rooms})'], [])"""
if "cls_city_id = cls.city_id" not in content:
    content = re.sub(score_pat, score_new, content, flags=re.DOTALL)


# 5. adjust_schedule fix restrictions
adj_pat = r"(if 'new_date' in data:[\s\S]*?new_date = date\.fromisoformat\(data\['new_date'\]\)\s*)# 检查是否是周六\s*if new_date\.weekday\(\) != 5:\s*return jsonify\(\{'error': '排课日期必须是周六'\}\), 400"
adj_new = r"\1date_actually_changed = (schedule.scheduled_date != new_date)\n            if date_actually_changed and new_date.weekday() != 5:\n                pass # Allow non-saturday as warning but not error"
if "date_actually_changed" not in content:
    content = re.sub(adj_pat, adj_new, content, count=1)


with open(r"backend\routes\schedule.py", "w", encoding="utf-8") as f:
    f.write(content)

print("Patch 2 applied.")
