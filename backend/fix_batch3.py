"""批次3: EMBA133(宁夏)/135/138/136(太原)/139"""
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
    if not s: print(f"  [SKIP] {ds}"); return None
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
    empty = sum(1 for s in ss if not s.combo)
    ok = not issues and not dups and empty==0
    print(f"  [{'OK' if ok else '!!'}] {name}: 空={empty} 重复={len(dups)} 错配={len(issues)}")
    if dups: print(f"       {dups}")
    if issues: print(f"       {issues}")

with app.app_context():
    def st(cid, ds):
        y,m,d=map(int,ds.split('-'))
        s=ClassSchedule.query.filter_by(class_id=cid,scheduled_date=date(y,m,d)).first()
        return s.topic_id if s else None

    # === EMBA133 宁夏 (ID=11) ===
    print("="*60); print("EMBA133 宁夏 (ID=11)"); print("="*60)
    print("  [NOTE] 1/17-18峰会(宏观经济)不在DB中")
    fix(11,'2026-04-18',1,st(11,'2026-04-18'),'霍振先','总裁决策者财税思维')
    fix(11,'2026-04-18',2,st(11,'2026-04-18'),'霍振先','总裁决策者财税思维')
    fix(11,'2026-05-23',1,st(11,'2026-05-23'),'李江涛','AI时代企业战略管理')
    fix(11,'2026-05-23',2,st(11,'2026-05-23'),'李江涛','AI时代企业战略管理')
    fix(11,'2026-06-27',1,st(11,'2026-06-27'),'刘春华','AI时代下的新营销九段法')
    fix(11,'2026-06-27',2,st(11,'2026-06-27'),'刘春华','AI时代下的新营销九段法')
    fix(11,'2026-10-17',1,st(11,'2026-10-17'),'陈晋蓉','资本财务思维')
    fix(11,'2026-10-17',2,st(11,'2026-10-17'),'陈晋蓉','资本财务思维')
    fix(11,'2026-12-26',2,st(11,'2026-12-26'),'杨波','领导力赋能组织活力')
    auto_fix(11,"EMBA133")

    # === EMBA135 (ID=12) ===
    print("\n"+"="*60); print("EMBA135 (ID=12)"); print("="*60)
    fix(12,'2025-12-13',1,st(12,'2025-12-13'),'刘春华','AI时代下的新营销九段法')
    fix(12,'2025-12-13',2,st(12,'2025-12-13'),'刘春华','AI时代下的新营销九段法')
    fix(12,'2026-09-19',2,st(12,'2026-09-19'),'董俊豪','企业AI Deepseek战略课')
    fix(12,'2026-10-24',1,st(12,'2026-10-24'),'罗毅','股权设计与股权激励')
    fix(12,'2026-10-24',2,st(12,'2026-10-24'),'罗毅','股权设计与股权激励')
    auto_fix(12,"EMBA135")

    # === EMBA138 (ID=13) ===
    print("\n"+"="*60); print("EMBA138 (ID=13)"); print("="*60)
    fix(13,'2025-12-27',1,st(13,'2025-12-27'),'刘春华','AI时代下的新营销九段法')
    fix(13,'2025-12-27',2,st(13,'2025-12-27'),'刘春华','AI时代下的新营销九段法')
    fix(13,'2026-03-07',2,st(13,'2026-03-07'),'刘钰','赢在顶层设计—企业持续成功的底层逻辑')
    fix(13,'2026-04-25',2,st(13,'2026-04-25'),'张晓丽','资本趋势破解：经济周期研判与思维重构')
    fix(13,'2026-07-18',1,st(13,'2026-07-18'),'吴子敬','股权设计、股权合伙与激励')
    fix(13,'2026-07-18',2,st(13,'2026-07-18'),'吴子敬','股权设计、股权合伙与激励')
    fix(13,'2026-09-12',2,st(13,'2026-09-12'),'董俊豪','企业AI Deepseek战略课')
    auto_fix(13,"EMBA138")

    # === EMBA136 太原 (ID=14) ===
    print("\n"+"="*60); print("EMBA136 太原 (ID=14)"); print("="*60)
    fix(14,'2025-11-22',1,st(14,'2025-11-22'),'刘春华','AI时代下的新营销九段法')
    fix(14,'2025-11-22',2,st(14,'2025-11-22'),'刘春华','AI时代下的新营销九段法')
    fix(14,'2026-03-14',2,st(14,'2026-03-14'),'韩铁林','企业战略规划与制定')
    fix(14,'2026-09-12',1,st(14,'2026-09-12'),'霍振先','总裁决策者财税思维')
    fix(14,'2026-09-12',2,st(14,'2026-09-12'),'霍振先','总裁决策者财税思维')
    fix(14,'2026-11-14',1,st(14,'2026-11-14'),'董俊豪','企业AI Deepseek战略课')
    fix(14,'2026-11-14',2,st(14,'2026-11-14'),'梁培霖','战略洞察力提升实战')
    fix(14,'2027-01-15',2,st(14,'2027-01-15'),'沈佳','企业家卓越领导能力构建')
    auto_fix(14,"EMBA136")

    # === EMBA139 (ID=15) ===
    print("\n"+"="*60); print("EMBA139 (ID=15)"); print("="*60)
    fix(15,'2026-03-07',2,st(15,'2026-03-07'),'陈晋蓉','经营管理与财务分析')
    fix(15,'2026-07-18',1,st(15,'2026-07-18'),'李继延','企业战略规划与制定')
    fix(15,'2026-07-18',2,st(15,'2026-07-18'),'李继延','企业战略规划与制定')
    fix(15,'2026-10-10',1,st(15,'2026-10-10'),'董俊豪','企业AI Deepseek战略课')
    fix(15,'2026-10-10',2,st(15,'2026-10-10'),'曲融','投资视角下的行业研究体系分析')
    fix(15,'2026-11-14',2,st(15,'2026-11-14'),'尚旭','企业布局的财富智慧')
    auto_fix(15,"EMBA139")

    db.session.commit()
    print("\n"+"="*60); print("最终验证"); print("="*60)
    for cid,n in [(11,"EMBA133"),(12,"EMBA135"),(13,"EMBA138"),(14,"EMBA136"),(15,"EMBA139")]:
        verify(cid,n)
    print("\n全部完成!")
