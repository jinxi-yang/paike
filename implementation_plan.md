# 北清商学院智能排课系统 - 实施方案

## 项目概述

将现有HTML原型改造为功能完整的排课系统，支持7种培训班的课程编排、班级管理、教-课组合配置及月度计划发布。

---

## 技术选型

| 层级 | 技术 | 理由 |
|-----|------|-----|
| **后端** | Python Flask + MySQL | 使用现有MySQL，支持高并发 |
| **前端** | 原有HTML + Tailwind + 原生JS | 复用现有原型，减少改动 |
| **节假日** | 中国节假日公共API | 自动避开法定节假日 |
| **数据迁移** | Python脚本 | 一键初始化全部数据 |

> [!NOTE]
> 后端使用Flask-SQLAlchemy ORM，支持MySQL连接。你只需在配置文件中填写MySQL连接信息即可。

---

## 数据库设计

### ER关系图

```mermaid
erDiagram
    TRAINING_TYPE ||--o{ TOPIC : has
    TRAINING_TYPE ||--o{ CLASS : has
    TOPIC ||--o{ TEACHER_COURSE_COMBO : configured_for
    TEACHER ||--o{ TEACHER_COURSE_COMBO : teaches
    COURSE ||--o{ TEACHER_COURSE_COMBO : contains
    HOMEROOM ||--o{ CLASS : manages
    CLASS ||--o{ CLASS_SCHEDULE : has
    TOPIC ||--o{ CLASS_SCHEDULE : uses
    TEACHER_COURSE_COMBO ||--o{ CLASS_SCHEDULE : selected
```

### 核心表结构

#### 1. 培训班类型表 `training_type`
| 字段 | 类型 | 说明 |
|-----|------|-----|
| id | INTEGER PK | 主键 |
| name | VARCHAR(100) | 培训班名称 |
| description | TEXT | 班型描述 |
| created_at | DATETIME | 创建时间 |

#### 2. 课题表 `topic`
| 字段 | 类型 | 说明 |
|-----|------|-----|
| id | INTEGER PK | 主键 |
| training_type_id | INTEGER FK | 关联培训班类型 |
| sequence | INTEGER | 课题顺序(1-8) |
| name | VARCHAR(200) | 课题名称 |
| is_fixed | BOOLEAN | 是否固定(首尾) |
| description | TEXT | 课题描述 |

#### 3. 班主任表 `homeroom`
| 字段 | 类型 | 说明 |
|-----|------|-----|
| id | INTEGER PK | 主键 |
| name | VARCHAR(50) | 姓名 |
| phone | VARCHAR(20) | 联系电话 |
| email | VARCHAR(100) | 邮箱 |

#### 4. 授课讲师表 `teacher`
| 字段 | 类型 | 说明 |
|-----|------|-----|
| id | INTEGER PK | 主键 |
| name | VARCHAR(50) | 姓名 |
| title | VARCHAR(50) | 职称 |
| expertise | TEXT | 擅长领域 |
| phone | VARCHAR(20) | 联系电话 |

#### 5. 课程表 `course`
| 字段 | 类型 | 说明 |
|-----|------|-----|
| id | INTEGER PK | 主键 |
| name | VARCHAR(200) | 课程名称 |
| description | TEXT | 课程描述 |
| duration_days | INTEGER | 时长(天)，默认2 |

#### 6. 教-课组合表 `teacher_course_combo`
| 字段 | 类型 | 说明 |
|-----|------|-----|
| id | INTEGER PK | 主键 |
| topic_id | INTEGER FK | 关联课题 |
| teacher_id | INTEGER FK | 关联讲师 |
| course_id | INTEGER FK | 关联课程 |
| priority | INTEGER | 优先级(用于推荐) |

#### 7. 班级表 `class`
| 字段 | 类型 | 说明 |
|-----|------|-----|
| id | INTEGER PK | 主键 |
| training_type_id | INTEGER FK | 关联培训班类型 |
| name | VARCHAR(100) | 班级名称 |
| homeroom_id | INTEGER FK | 班主任 |
| start_date | DATE | 首次开课日期 |
| status | VARCHAR(20) | 状态(planning/active/completed) |

#### 8. 班级课表 `class_schedule`
| 字段 | 类型 | 说明 |
|-----|------|-----|
| id | INTEGER PK | 主键 |
| class_id | INTEGER FK | 关联班级 |
| topic_id | INTEGER FK | 关联课题 |
| combo_id | INTEGER FK | 选用的教-课组合 |
| scheduled_date | DATE | 排课日期(周六) |
| week_number | INTEGER | 第几周 |
| status | VARCHAR(20) | 状态(scheduled/completed/cancelled) |
| notes | TEXT | 备注 |

#### 9. 月度计划表 `monthly_plan`
| 字段 | 类型 | 说明 |
|-----|------|-----|
| id | INTEGER PK | 主键 |
| year | INTEGER | 年份 |
| month | INTEGER | 月份 |
| status | VARCHAR(20) | 状态(draft/published) |
| published_at | DATETIME | 发布时间 |

---

## 7种培训班的8个课题设计

### 一、领袖增长本科班

| 序号 | 课题名称 | 固定 |
|-----|---------|-----|
| 1 | 开班仪式与宏观经济形势分析 | ✅ |
| 2 | 战略思维与商业模式创新 | |
| 3 | 组织管理与团队领导力 | |
| 4 | 财务管理与资本运作基础 | |
| 5 | 市场营销与品牌建设 | |
| 6 | 数字化转型与科技创新 | |
| 7 | 企业法务与风险管理 | |
| 8 | 结课典礼与领袖成长路演 | ✅ |

### 二、领袖增长硕士班

| 序号 | 课题名称 | 固定 |
|-----|---------|-----|
| 1 | 开班仪式与宏观经济趋势研判 | ✅ |
| 2 | 战略规划与竞争优势构建 | |
| 3 | 组织变革与人才梯队建设 | |
| 4 | 资本市场与投融资实务 | |
| 5 | 全球化视野与跨国经营 | |
| 6 | 产业生态与平台战略 | |
| 7 | 企业传承与基业长青 | |
| 8 | 结课典礼与战略突破路演 | ✅ |

### 三、国学班

| 序号 | 课题名称 | 固定 |
|-----|---------|-----|
| 1 | 开班仪式与易经智慧概论 | ✅ |
| 2 | 儒家思想与修身齐家 | |
| 3 | 道家哲学与无为而治 | |
| 4 | 兵法谋略与竞争智慧 | |
| 5 | 禅宗心法与企业家心性修炼 | |
| 6 | 史学经典与历史镜鉴 | |
| 7 | 中医养生与身心平衡 | |
| 8 | 结课典礼与国学智慧分享 | ✅ |

### 四、数字化转型总裁班

| 序号 | 课题名称 | 固定 |
|-----|---------|-----|
| 1 | 开班仪式与数字经济宏观解读 | ✅ |
| 2 | 数字化战略规划与转型路径 | |
| 3 | 数据中台与智能决策 | |
| 4 | 人工智能与业务场景融合 | |
| 5 | 数字营销与客户体验重塑 | |
| 6 | 组织敏捷与数字化人才培养 | |
| 7 | 网络安全与数据合规 | |
| 8 | 结课典礼与数字化转型成果展示 | ✅ |

### 五、EMBA创新实验班

| 序号 | 课题名称 | 固定 |
|-----|---------|-----|
| 1 | 开班仪式与创新经济学导论 | ✅ |
| 2 | 创新思维与设计思维方法论 | |
| 3 | 商业模式创新与颠覆式创新 | |
| 4 | 创新组织与创业生态构建 | |
| 5 | 技术前沿与产业创新趋势 | |
| 6 | 创新资本与风险投资策略 | |
| 7 | 创新实践与项目孵化 | |
| 8 | 结课典礼与创新项目路演 | ✅ |

### 六、女性领导力研修营

| 序号 | 课题名称 | 固定 |
|-----|---------|-----|
| 1 | 开班仪式与女性领导力觉醒 | ✅ |
| 2 | 自我认知与个人品牌塑造 | |
| 3 | 沟通艺术与影响力提升 | |
| 4 | 职业发展与事业家庭平衡 | |
| 5 | 财务独立与财富管理 | |
| 6 | 团队建设与赋能型领导 | |
| 7 | 健康管理与优雅生活美学 | |
| 8 | 结课典礼与女性力量分享 | ✅ |

### 七、医疗产业实战班

| 序号 | 课题名称 | 固定 |
|-----|---------|-----|
| 1 | 开班仪式与医疗产业宏观政策解读 | ✅ |
| 2 | 医疗机构运营与精细化管理 | |
| 3 | 医药研发与创新药物开发 | |
| 4 | 医疗器械与智能医疗设备 | |
| 5 | 医疗投融资与并购重组 | |
| 6 | 互联网医疗与数字健康 | |
| 7 | 医疗合规与医保政策应对 | |
| 8 | 结课典礼与医疗产业创新路演 | ✅ |

---

## 项目结构

```
beiqing-scheduler/
├── backend/
│   ├── app.py              # Flask主应用
│   ├── models.py           # SQLAlchemy模型
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── training_type.py
│   │   ├── topic.py
│   │   ├── homeroom.py
│   │   ├── teacher.py
│   │   ├── course.py
│   │   ├── combo.py
│   │   ├── classes.py
│   │   └── schedule.py
│   ├── init_data.py        # 数据初始化脚本
│   ├── requirements.txt
│   └── beiqing.db          # SQLite数据库文件
├── frontend/
│   └── index.html          # 改造后的前端页面
└── README.md
```

---

## Proposed Changes

### [NEW] 后端项目

#### [NEW] [app.py](file:///C:/Users/wzwwh/.gemini/antigravity/scratch/beiqing-scheduler/backend/app.py)
Flask主应用入口，配置CORS、路由注册、数据库初始化。

#### [NEW] [models.py](file:///C:/Users/wzwwh/.gemini/antigravity/scratch/beiqing-scheduler/backend/models.py)
SQLAlchemy ORM模型定义，包含上述8张表的完整定义。

#### [NEW] [routes/](file:///C:/Users/wzwwh/.gemini/antigravity/scratch/beiqing-scheduler/backend/routes/)
RESTful API路由模块，每个资源独立一个文件。

#### [NEW] [init_data.py](file:///C:/Users/wzwwh/.gemini/antigravity/scratch/beiqing-scheduler/backend/init_data.py)
数据初始化脚本，包含：
- 7种培训班类型 + 56个课题
- 10个班主任
- 20个授课讲师
- 若干课程和教-课组合

---

### [MODIFY] 前端页面

#### [MODIFY] [index.html](file:///C:/Users/wzwwh/.gemini/antigravity/scratch/beiqing-scheduler/frontend/index.html)
基于现有原型改造：

1. **页面上半部分改造**
   - 项目卡片从硬编码改为从API动态加载
   - 点击培训班类型后弹出班级创建/预排界面
   - 添加课题顺序调整功能（首尾固定，中间可拖拽）
   - 班主任选择从API加载

2. **页面下半部分改造**
   - 周末排课区域显示当前选中月份的课程
   - 每门课显示教-课组合选择下拉
   - 实现"上一周/下一周"调整
   - 实现"合班"功能
   - Prompt提示词区域连接后端（预留AI接口）

3. **新增功能**
   - 已完成课程标记显示
   - 月度计划发布与同步

---

## 核心API设计

### 培训班类型

| 端点 | 方法 | 说明 |
|-----|------|-----|
| `/api/training-types` | GET | 获取所有培训班类型 |
| `/api/training-types/{id}` | GET | 获取单个培训班详情（含课题列表） |

### 班级管理

| 端点 | 方法 | 说明 |
|-----|------|-----|
| `/api/classes` | GET | 获取所有班级 |
| `/api/classes` | POST | 创建班级（含自动排课） |
| `/api/classes/{id}` | GET | 获取班级课表 |
| `/api/classes/{id}/schedule` | PUT | 调整班级课表 |

### 排课调度

| 端点 | 方法 | 说明 |
|-----|------|-----|
| `/api/schedule/month/{year}/{month}` | GET | 获取月度排课 |
| `/api/schedule/adjust` | POST | 调整单节课（换周/换组合）。请求体可包含 `combo_id` 和/或 `combo_id_2`，后者用于周日第二天安排。 |
| `/api/schedule/merge` | POST | 合班操作 |
| `/api/schedule/publish` | POST | 发布月度计划 |

---

## 排课算法逻辑

### Step 1: 创建班级时自动预排

```python
def auto_schedule_class(class_id, start_date):
    """
    1. 获取该班级对应培训班类型的8个课题
    2. 从start_date开始，按每4周一节排课
    3. 自动找下一个周六
    4. 避开节假日（调用节假日API）
    5. 检查班主任档期冲突
    6. 为每个课题预设一个默认教-课组合
    """
```

### Step 2: 月度排课调整

```python
def adjust_schedule(schedule_id, target_week):
    """
    1. 验证目标周是否可用（>=4周间隔）
    2. 检查讲师/班主任冲突
    3. 更新scheduled_date
    """

def merge_classes(schedule_ids, merged_date):
    """
    1. 验证多个班级同一课题
    2. 创建合班记录
    3. 更新各班schedule指向合班
    """
```

---

## Verification Plan

### 自动化测试

> [!IMPORTANT]
> 由于这是新项目，我将编写基础的API测试脚本。

#### [NEW] 测试脚本 `backend/test_api.py`

```bash
# 运行测试
cd beiqing-scheduler/backend
python -m pytest test_api.py -v
```

测试覆盖：
- 培训班类型CRUD
- 班级创建与自动排课
- 排课调整
- 冲突检测

### 手动验证

#### 验证1: 后端启动与数据初始化

1. 打开终端，进入 `beiqing-scheduler/backend` 目录
2. 运行 `pip install -r requirements.txt`
3. 运行 `python init_data.py` 初始化数据
4. 运行 `python app.py` 启动后端
5. 访问 `http://localhost:5000/api/training-types`
6. **预期结果**: 返回7种培训班类型的JSON列表

#### 验证2: 前端页面加载

1. 确保后端在5000端口运行
2. 用浏览器打开 `frontend/index.html`
3. 点击"智能课程编排"标签
4. **预期结果**: 页面上半部分显示7个培训班类型卡片

#### 验证3: 创建班级与自动排课

1. 点击"领袖增长本科班"卡片
2. 点击"新增班级"
3. 输入班级名称，选择班主任，选择开始日期
4. 点击"创建并生成课表"
5. **预期结果**: 系统自动生成8节课的预排课表，显示在班级课表中

#### 验证4: 月度排课调整

1. 在页面下半部分选择某个月份
2. 查看该月的排课
3. 将某节课拖拽到下一周
4. **预期结果**: 课程日期更新，界面刷新显示新日期

#### 验证5: 发布月度计划

1. 安排好某月的课程
2. 点击"发布月度计划"
3. **预期结果**: 提示发布成功，课程状态更新

---

## 部署说明

### 开发环境启动

```bash
# 1. 后端
cd beiqing-scheduler/backend
pip install -r requirements.txt
python init_data.py  # 首次运行初始化数据
python app.py        # 启动 Flask @ http://localhost:5000

# 2. 前端
# 直接用浏览器打开 frontend/index.html
# 或用 VS Code Live Server 启动
```

### 生产部署（可选）

```bash
# 使用 gunicorn 部署
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

---

## 节假日API集成

### 接口选择

使用免费的中国节假日API：`https://timor.tech/api/holiday`

```python
# 调用示例
import requests

def is_holiday(date_str: str) -> bool:
    """检查某日期是否为节假日
    Args:
        date_str: 日期字符串，格式 YYYY-MM-DD
    Returns:
        True 如果是节假日/周末，False 如果是工作日
    """
    resp = requests.get(f"https://timor.tech/api/holiday/info/{date_str}")
    data = resp.json()
    if data.get('code') == 0:
        holiday = data.get('holiday', {})
        return holiday.get('holiday', False) if holiday else False
    return False

def get_next_workday_weekend(start_date, min_weeks=4):
    """获取下一个可用的周末（非节假日周末）"""
    # 跳过min_weeks周，然后找最近的周六
    # 如果该周六是节假日调休工作日，则继续向后找
    pass
```

### 排课时的节假日处理

1. **自动预排时**：系统自动跳过节假日周末
2. **手动调整时**：如果目标日期是节假日，前端弹出警告
3. **节假日缓存**：每天首次调用时缓存当年节假日数据

---

## AI智能体接口规范

### 接口设计

前端Prompt Center输入的提示词将发送到你的智能体，智能体需返回结构化的排课约束参数。

#### 请求接口

```
POST /api/ai/extract-constraints
Content-Type: application/json

{
    "prompt": "用户输入的自然语言提示词",
    "context": {
        "current_month": "2026-03",
        "classes": ["领袖增长营1班", "领袖增长营2班"],
        "teachers": ["王芳", "刘杰", ...]
    }
}
```

#### 响应格式（智能体需返回）

```json
{
    "success": true,
    "constraints": {
        "blocked_dates": [
            {
                "date": "2026-03-15",
                "reason": "北京医疗峰会",
                "affected_classes": ["医疗产业实战班1班"]
            }
        ],
        "teacher_unavailable": [
            {
                "teacher_name": "王芳",
                "dates": ["2026-03-21", "2026-03-22"],
                "reason": "请假"
            }
        ],
        "preferred_dates": [
            {
                "class_name": "领袖增长营1班",
                "preferred_date": "2026-03-28",
                "reason": "与校友活动配合"
            }
        ],
        "merge_suggestions": [
            {
                "classes": ["领袖增长营1班", "领袖增长营2班"],
                "topic": "数字化转型底层逻辑",
                "suggested_date": "2026-03-14"
            }
        ],
        "special_notes": "建议避开3月下旬的财报季"
    }
}
```

### 智能体提取参数说明

| 参数 | 类型 | 必填 | 说明 |
|-----|------|-----|------|
| `blocked_dates` | Array | 否 | 需要避开的日期列表 |
| `blocked_dates[].date` | String | 是 | 日期，格式YYYY-MM-DD |
| `blocked_dates[].reason` | String | 是 | 避开原因 |
| `blocked_dates[].affected_classes` | Array | 否 | 受影响的班级，空表示所有班级 |
| `teacher_unavailable` | Array | 否 | 教师请假/不可用信息 |
| `teacher_unavailable[].teacher_name` | String | 是 | 教师姓名 |
| `teacher_unavailable[].dates` | Array | 是 | 不可用日期列表 |
| `teacher_unavailable[].reason` | String | 否 | 原因 |
| `preferred_dates` | Array | 否 | 优先排课日期建议 |
| `merge_suggestions` | Array | 否 | 合班建议 |
| `special_notes` | String | 否 | 其他备注信息 |

### 示例提示词 → 参数提取

**用户输入**:
> "3月25日北京有大型医疗峰会，医疗班那天不能上课。王芳老师3月21-22日请假了。"

**智能体应返回**:
```json
{
    "success": true,
    "constraints": {
        "blocked_dates": [
            {
                "date": "2026-03-25",
                "reason": "北京大型医疗峰会",
                "affected_classes": ["医疗产业实战班"]
            }
        ],
        "teacher_unavailable": [
            {
                "teacher_name": "王芳",
                "dates": ["2026-03-21", "2026-03-22"],
                "reason": "请假"
            }
        ]
    }
}
```

---

## 时间估算

| 阶段 | 预计时间 |
|-----|---------|
| 后端框架 + 数据模型 | 30分钟 |
| API开发 | 45分钟 |
| 数据初始化脚本 | 20分钟 |
| 前端改造 | 60分钟 |
| 联调测试 | 30分钟 |
| **总计** | **约3小时** |

---

## User Review Required

> [!IMPORTANT]
> 请确认以下关键设计决策：

1. **技术栈**: Python Flask + SQLite + 原有前端改造，是否可接受？
2. **课题内容**: 上述7种培训班的8个课题设计是否符合预期？如需调整请说明。
3. **排课间隔**: 默认4周一节，可延长至5周，这个逻辑是否正确？
4. **节假日**: 是否需要集成公共节假日API？还是手动维护节假日表？
5. **AI提示词**: Prompt Center是否需要实际连接LLM？还是先做成静态提示？

