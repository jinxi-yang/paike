"""批次4(最终): 北清151/152/153/155/156深圳"""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
from datetime import date
from collections import Counter
from app import app
from models import db, ClassSchedule, TeacherCourseCombo, Teacher, Topic

def fot(name):
    t = Teacher.query.filter_by(name=name).first()
    if not t:
        t = Teacher(name=name); db.session.add(t); db.session.flush()
        print(f"  [NEW TEACHER] {name} (id={t.id})")
    return t

def foc(topic_id, teacher_name, course_name):
    teacher = fot(teacher_name)
    c = TeacherCourseCombo.query.filter_by(topic_id=topic_id, teacher_id=teacher.id, course_name=course_name).first()
    if not c:
        c = TeacherCourseCombo(topic_id=topic_id, teacher_id=teacher.id, course_name=course_name)
        db.session.add(c); db.session.flush()
        print(f"  [NEW COMBO] id={c.id}: {teacher_name}/{course_name}")
    return c

def fix(cid, ds, day, tid, tn, cn):
    y,m,d = map(int, ds.split('-'))
    s = ClassSchedule.query.filter_by(class_id=cid, scheduled_date=date(y,m,d)).first()
    if not s: print(f"  [SKIP] {ds} not found for class {cid}"); return None
    c = foc(tid, tn, cn)
    if day==1: s.combo_id=c.id
    else: s.combo_id_2=c.id
    print(f"  [FIX D{day}] {ds} {tn}/{cn}")
    return s

def foc_under(tid, teacher_id, cn):
    c = TeacherCourseCombo.query.filter_by(topic_id=tid, teacher_id=teacher_id, course_name=cn).first()
    if not c:
        c = TeacherCourseCombo(topic_id=tid, teacher_id=teacher_id, course_name=cn)
        db.session.add(c); db.session.flush()
    return c

def nat_topic(combo):
    if not combo: return None
    e = TeacherCourseCombo.query.filter_by(teacher_id=combo.teacher_id, course_name=combo.course_name).order_by(TeacherCourseCombo.id).first()
    return e.topic_id if e else combo.topic_id

def auto_fix(cid, name):
    print(f"\n  [TOPIC FIX] {name}")
    ss = ClassSchedule.query.filter(ClassSchedule.class_id==cid, ClassSchedule.status!='cancelled').order_by(ClassSchedule.scheduled_date).all()
    cls = ss[0].class_
    ct = Topic.query.filter_by(project_id=cls.project_id).filter(Topic.is_other!=True).order_by(Topic.sequence).all()
    ci = {t.id for t in ct}
    ot = Topic.query.filter_by(project_id=cls.project_id, is_other=True).first()
    core = ss[:8]; extra = ss[8:]
    for s in extra:
        if s.topic_id != ot.id:
            old = s.topic.name; s.topic_id = ot.id
            if s.combo: s.combo_id = foc_under(ot.id, s.combo.teacher_id, s.combo.course_name).id
            if s.combo_2: s.combo_id_2 = foc_under(ot.id, s.combo_2.teacher_id, s.combo_2.course_name).id
            print(f"    {s.scheduled_date} [{old}] -> [其他]")
    asgn={}; conf=[]
    for s in core:
        n = nat_topic(s.combo) if s.combo else s.topic_id
        if n in ci and n not in asgn: asgn[n]=s
        else: conf.append(s)
    miss = [t.id for t in ct if t.id not in asgn]
    for s,tid in zip(conf, miss): asgn[tid]=s
    for tid,s in asgn.items():
        if s.topic_id != tid:
            old=s.topic.name; nt=db.session.get(Topic,tid); s.topic_id=tid
            if s.combo: s.combo_id=foc_under(tid,s.combo.teacher_id,s.combo.course_name).id
            if s.combo_2: s.combo_id_2=foc_under(tid,s.combo_2.teacher_id,s.combo_2.course_name).id
            print(f"    {s.scheduled_date} [{old}] -> [{nt.name}]")

def verify(cid, name):
    ss = ClassSchedule.query.filter(ClassSchedule.class_id==cid, ClassSchedule.status!='cancelled').all()
    issues = []
    for s in ss:
        if s.combo and s.combo.topic_id != s.topic_id: issues.append(f"D1:{s.scheduled_date}")
        if s.combo_2 and s.combo_2.topic_id != s.topic_id: issues.append(f"D2:{s.scheduled_date}")
    tc = Counter(s.topic.name for s in ss if not s.topic.is_other)
    dups = {k:v for k,v in tc.items() if v>1}
    empty_d1 = sum(1 for s in ss if not s.combo)
    ct_all = {t.name for t in Topic.query.filter_by(project_id=ss[0].class_.project_id).filter(Topic.is_other!=True)}
    used = {s.topic.name for s in ss if not s.topic.is_other}
    miss = ct_all - used
    ok = not issues and not dups and empty_d1==0 and not miss
    print(f"  [{'OK' if ok else '!!'}] {name}: 空D1={empty_d1} 重复={len(dups)} 错配={len(issues)} 缺课题={len(miss)}")
    if dups: print(f"       重复: {dups}")
    if issues: print(f"       错配: {issues}")
    if miss: print(f"       缺: {miss}")

with app.app_context():
    def st(cid, ds):
        y,m,d=map(int,ds.split('-'))
        s=ClassSchedule.query.filter_by(class_id=cid,scheduled_date=date(y,m,d)).first()
        return s.topic_id if s else None

    # === 北清151 (ID=16) ===
    print("="*60); print("北清151 (ID=16)"); print("="*60)
    # 开学D1已有院长, 需检查
    fix(16,'2025-04-11',2,st(16,'2025-04-11'),'刘钰','股权设计和资本路径')
    fix(16,'2025-08-15',2,st(16,'2025-08-15'),'宗英涛','稻盛和夫的经营哲学')
    fix(16,'2025-12-12',2,st(16,'2025-12-12'),'沈佳','企业家卓越领导能力构建')
    auto_fix(16,"北清151")

    # === 北清152 (ID=17) ===
    print("\n"+"="*60); print("北清152 (ID=17)"); print("="*60)
    fix(17,'2025-05-30',1,st(17,'2025-05-30'),'刘春华','AI时代下的新营销九段法')
    fix(17,'2025-05-30',2,st(17,'2025-05-30'),'刘春华','AI时代下的新营销九段法')
    fix(17,'2026-02-27',2,st(17,'2026-02-27'),'苏伟','企业家信念管理')
    auto_fix(17,"北清152")

    # === 北清153 (ID=18) ===
    print("\n"+"="*60); print("北清153 (ID=18)"); print("="*60)
    fix(18,'2025-07-11',2,st(18,'2025-07-11'),'董俊豪','企业AI Deepseek战略课')
    fix(18,'2025-09-12',1,st(18,'2025-09-12'),'刘春华','AI时代下的新营销九段法')
    fix(18,'2025-09-12',2,st(18,'2025-09-12'),'刘春华','AI时代下的新营销九段法')
    fix(18,'2026-01-16',1,st(18,'2026-01-16'),'刘钰','股权设计与资本路径')
    fix(18,'2026-01-16',2,st(18,'2026-01-16'),'龙平敬','企业资本价值倍增之道')
    auto_fix(18,"北清153")

    # === 北清155 (ID=19) ===
    print("\n"+"="*60); print("北清155 (ID=19)"); print("="*60)
    fix(19,'2025-08-15',1,st(19,'2025-08-15'),'刘春华','AI时代下的新营销九段法')
    fix(19,'2025-08-15',2,st(19,'2025-08-15'),'刘春华','AI时代下的新营销九段法')
    fix(19,'2025-10-17',2,st(19,'2025-10-17'),'龙平敬','企业资本价值倍增之道')
    fix(19,'2026-01-23',2,st(19,'2026-01-23'),'黄宏','商业模式创新与落地')
    fix(19,'2026-03-20',2,st(19,'2026-03-20'),'易正','中国古法姓名学')
    auto_fix(19,"北清155")

    # === 北清156 深圳 (ID=20) ===
    print("\n"+"="*60); print("北清156 深圳 (ID=20)"); print("="*60)
    fix(20,'2025-04-25',1,st(20,'2025-04-25'),'刘钰','股权设计与资本路径')
    fix(20,'2025-04-25',2,st(20,'2025-04-25'),'刘钰','股权设计与资本路径')
    fix(20,'2025-08-22',1,st(20,'2025-08-22'),'刘春华','AI时代下的新营销九段法')
    fix(20,'2025-08-22',2,st(20,'2025-08-22'),'刘春华','AI时代下的新营销九段法')
    fix(20,'2025-10-10',2,st(20,'2025-10-10'),'董俊豪','企业AI战略课')
    fix(20,'2026-01-15',2,st(20,'2026-01-15'),'宗英涛','稻盛和夫的经营哲学')
    fix(20,'2026-03-13',2,st(20,'2026-03-13'),'易正','易经智慧与财富幸福')
    auto_fix(20,"北清156")

    db.session.commit()
    print("\n"+"="*60); print("最终验证"); print("="*60)
    for cid,n in [(16,"北清151"),(17,"北清152"),(18,"北清153"),(19,"北清155"),(20,"北清156")]:
        verify(cid,n)
    print("\n全部完成!")
