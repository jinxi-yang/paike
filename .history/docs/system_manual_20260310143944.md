# 北清商学院智能排课系统 — 系统说明书

> **文档版本**: v2.2 | **适用系统**: paike v1.2 | **更新日期**: 2026年3月8日

---

## 目录

1. [系统概述](#1-系统概述)
2. [技术架构](#2-技术架构)
3. [数据模型与数据字典](#3-数据模型与数据字典)
4. [业务概念与术语](#4-业务概念与术语)
5. [系统功能模块详解](#5-系统功能模块详解)
6. [核心业务流程](#6-核心业务流程)
7. [排课算法详解](#7-排课算法详解)
8. [API 接口参考](#8-api-接口参考)
9. [使用注意事项与约束](#9-使用注意事项与约束)
10. [已知问题与改进建议](#10-已知问题与改进建议)
11. [部署与维护](#11-部署与维护)

---

## 1. 系统概述

### 1.1 产品定位
北清商学院智能排课系统是一套面向商学院教务管理的自动化课程调度平台。系统围绕 **项目→课题→班级→课表** 的业务主线，实现从基础数据录入、自动排课、冲突检测、月度发布的全流程管理。

### 1.2 核心价值
| 能力 | 说明 |
|------|------|
| 自动排课 | 一键生成全月课表，4周间隔自动计算 |
| 冲突检测 | 实时检测节假日/讲师/班主任冲突 |
| AI约束提取 | 自然语言描述转结构化约束条件 |
| 合班管理 | 支持多班级同课题合并上课 |
| 月度发布 | 草稿→审核→发布的标准工作流 |

### 1.3 用户角色
- **教务管理员**: 系统的主要使用者，负责数据维护、排课、发布
- **技术管理员**: 负责系统部署、配置与维护

---

## 2. 技术架构

### 2.1 技术栈

```
┌──────────────────┐     ┌──────────────────┐     ┌──────────────────┐
│   前端 (SPA)      │────▶│   后端 (Flask)    │────▶│   数据库 (SQLite) │
│  HTML+JS+Tailwind│     │  Python 3.7+     │     │  scheduler.db    │
└──────────────────┘     └────────┬─────────┘     └──────────────────┘
                                  │
                    ┌─────────────┼─────────────┐
                    ▼                             ▼
          ┌──────────────────┐          ┌──────────────────┐
          │  节假日 API       │          │  AI 智能体 (Dify) │
          │  timor.tech      │          │  ai.isstech.com  │
          └──────────────────┘          └──────────────────┘
```

### 2.2 前端架构
- **单文件 SPA**: 所有功能在 `frontend/index.html`（约3600行）
- **三大主视图**: 智能课程编排 / 资源配置 / 系统初始化
- **6个弹窗**: 项目详情、新增班级、班级课表、调整课程、教课组合配置、发布预览
- **API基础地址**: `http://localhost:5000/api`（可在文件顶部修改）

### 2.3 后端架构
- **入口**: [app.py](file:///d:/学习/outputmsg/排课/paike/backend/app.py) — Flask应用初始化、蓝图注册
- **配置**: [config.py](file:///d:/学习/outputmsg/排课/paike/backend/config.py) — 数据库URI、API密钥、调度参数
- **模型**: [models.py](file:///d:/学习/outputmsg/排课/paike/backend/models.py) — 10个数据模型
- **路由**: `routes/` 目录下8个蓝图模块

### 2.4 关键配置项

| 配置 | 默认值 | 说明 |
|------|--------|------|
| `DATABASE_URL` | `sqlite:///scheduler.db` | 数据库连接 |
| `WEEKS_INTERVAL` | `4` | 相邻课题间隔周数 |
| `HOLIDAY_API_URL` | `https://timor.tech/api/holiday` | 节假日数据源 |
| `AI_AGENT_URL` | `https://ai.isstech.com/agent/v1/chat-messages` | AI服务地址 |
| `AI_AGENT_API_KEY` | 环境变量 | AI服务密钥 |

---

## 3. 数据模型与数据字典

### 3.1 实体关系图

```mermaid
erDiagram
    Project ||--o{ Topic : "has"
    Project ||--o{ Class : "has"
    Topic ||--o{ Course : "has"
    Topic ||--o{ TeacherCourseCombo : "has"
    Teacher ||--o{ TeacherCourseCombo : "teaches"
    Course ||--o{ TeacherCourseCombo : "uses"
    Homeroom ||--o{ Class : "manages"
    Class ||--o{ ClassSchedule : "has"
    TeacherCourseCombo ||--o{ ClassSchedule : "combo_id"
    TeacherCourseCombo ||--o{ ClassSchedule : "combo_id_2"
```

### 3.2 数据表详解

#### Project（项目）
| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| id | Integer PK | 自增 | 主键 |
| name | String(100) | ✅ | 项目名称，唯一 |
| description | String(500) | ❌ | 项目描述 |
| created_at | DateTime | 自动 | 创建时间 |

> **业务含义**: 最顶层组织单位，如"EMBA高级研修班"。每个项目下有固定的课题大纲和多个班级。

#### Topic（课题）
| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| id | Integer PK | 自增 | 主键 |
| project_id | Integer FK | ✅ | 所属项目 |
| name | String(100) | ✅ | 课题名称 |
| sequence | Integer | ✅ | 排课顺序 (1-8) |
| is_fixed | Boolean | ❌ | 固定课题标记（首尾课题） |

> **业务含义**: 项目大纲中的模块，标准为8个课题。`is_fixed=true` 的课题在自动排课时不会被交换顺序。

#### Teacher（讲师）
| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| id | Integer PK | 自增 | 主键 |
| name | String(50) | ✅ | 姓名 |
| title | String(50) | ❌ | 职称 |
| expertise | String(200) | ❌ | 擅长领域 |
| phone | String(20) | ❌ | 联系电话 |

#### Course（课程）
| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| id | Integer PK | 自增 | 主键 |
| topic_id | Integer FK | ❌ | 所属课题 |
| name | String(100) | ✅ | 课程名称 |
| description | String(500) | ❌ | 课程描述 |
| duration_days | Integer | ❌ | 课时天数，默认2 |

#### TeacherCourseCombo（教-课组合）
| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| id | Integer PK | 自增 | 主键 |
| topic_id | Integer FK | ✅ | 所属课题 |
| teacher_id | Integer FK | ✅ | 讲师 |
| course_id | Integer FK | ✅ | 课程 |
| priority | Integer | ❌ | 优先级（值越高越优先） |

> **关键概念**: 这是排课算法的核心输入。一个课题下可配置多个"讲师+课程"的组合，系统按优先级选取。

#### Homeroom（班主任）
| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| id | Integer PK | 自增 | 主键 |
| name | String(50) | ✅ | 姓名 |
| phone | String(20) | ❌ | 联系电话 |
| email | String(100) | ❌ | 邮箱 |

#### Class（班级）
| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| id | Integer PK | 自增 | 主键 |
| project_id | Integer FK | ✅ | 所属项目 |
| homeroom_id | Integer FK | ❌ | 班主任 |
| name | String(100) | ✅ | 班级名称 |
| start_date | Date | ❌ | 首次上课日期 |
| status | String(20) | ❌ | 状态：`planning`/`active`/`completed` |

#### ClassSchedule（班级课表）— ⭐核心表
| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| id | Integer PK | 自增 | 主键 |
| class_id | Integer FK | ✅ | 班级 |
| topic_id | Integer FK | ✅ | 课题 |
| combo_id | Integer FK | ❌ | **周六** 教-课组合 |
| combo_id_2 | Integer FK | ❌ | **周日** 教-课组合 |
| scheduled_date | Date | ✅ | 排课日期（**始终为周六**） |
| week_number | Integer | ❌ | 周次序号 |
| status | String(20) | ❌ | `planning`/`scheduled`/`confirmed`/`completed`/`conflict`/`cancelled` |
| merged_with | Integer | ❌ | 合班关联的另一条记录ID |
| notes | Text | ❌ | 备注（含冲突原因） |

> **⚠️ 重要**: `scheduled_date` 始终存储**周六**日期。周日课程日期 = 周六日期 + 1天，由前端计算显示。

#### MonthlyPlan（月度计划）
| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| id | Integer PK | 自增 | 主键 |
| year | Integer | ✅ | 年份 |
| month | Integer | ✅ | 月份 |
| status | String(20) | ❌ | `draft`/`published` |
| published_at | DateTime | ❌ | 发布时间 |

#### ScheduleConstraint（排课约束条件）
| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| id | Integer PK | 自增 | 主键 |
| year | Integer | ✅ | 适用年份 |
| month | Integer | ✅ | 适用月份 |
| constraint_type | String(50) | ❌ | 类型：`teacher_unavailable`/`blocked_dates`/`custom` |
| description | Text | ✅ | 约束描述 |
| constraint_data | Text(JSON) | ❌ | 结构化数据 |
| is_active | Boolean | ❌ | 是否生效 |

---

## 4. 业务概念与术语

| 术语 | 英文 | 含义 |
|------|------|------|
| 项目 | Project | 培训班类型，如"EMBA高管班"，定义课程大纲 |
| 课题 | Topic | 项目大纲中的一个模块，标准8个课题 |
| 教-课组合 | Combo | 一个讲师+一门课程的绑定关系 |
| 固定课题 | Fixed Topic | 排课时不可交换顺序的课题（通常是首尾） |
| 预排 | Planning | 自动生成但未确认的课表状态 |
| 三级降级 | Three-level Downgrade | 排课冲突时的三步处理策略 |
| 合班 | Merge | 多个班级同课题合并到同一周末上课 |
| 约束条件 | Constraint | 影响排课决策的规则（如教师请假） |

---

## 5. 系统功能模块详解

### 5.1 Tab 1: 智能课程编排（主工作区）

这是系统最核心的功能界面，分为三大区域：

#### 5.1.1 项目卡片栏（顶部）
- 展示所有项目的卡片，点击任意卡片打开**项目详情弹窗**
- 项目详情弹窗内可以：
  - 查看课题列表及其教-课组合配置
  - 为课题添加/删除教-课组合
  - 查看/创建/删除班级
  - 查看班级课表

#### 5.1.2 AI 排课助手（左侧面板）
- **排课策略选择**: `自动顺延`(默认) 或 `保留位置并标记`
- **约束条件列表**: 展示当前月份已保存的约束，可启用/禁用/删除
- **追加新约束**: 输入自然语言约束（如"王芳老师3月请假"）
- **"基于约束重新生成课表"按钮**: 触发完整的AI排课流程

> **AI排课流程**:
> 1. 收集当月所有已激活约束条件文本
> 2. 调用 AI 接口提取结构化约束（blocked_dates、teacher_unavailable等）
> 3. 将约束传入 `generate_schedule` 后端接口
> 4. 后端清除该月已有预排数据，重新生成全月课表

#### 5.1.3 月度排课看板（右侧主区域）
- **月份导航**: 前后月切换
- **状态徽章**: 显示"草稿"或"已发布"及时间信息
- **视图切换**: 周度视图 / 月度视图
- **合班模式**: 开启后可选择多条课程记录进行合班

**周度视图（默认）**: 表格形式，按单周显示，包含：
- 班级/课题列 + 周六讲师/课程列 + 周日讲师/课程列
- 冲突时红色高亮并展示冲突助手面板（原因 + 建议 + 快捷操作）
- 每行有"编辑"和"删除"按钮（已过期课程不可操作）
- 底部有"保存草稿"和"发布月度计划"按钮

**月度视图**: 展示全月所有周的排课表格，格式同上

**冲突助手**: 当 `status='conflict'` 时，自动显示：
- 冲突原因（来自 `notes` 字段）
- 基于原因的自动建议（节假日→顺延，请假→换讲师等）
- "去调整"和"顺延一周"快捷按钮

### 5.2 Tab 2: 资源配置（6面板）

3×2 网格布局，每个面板独立管理一类基础数据：

| 面板 | 颜色 | 功能 | 特殊说明 |
|------|------|------|----------|
| 📦 项目管理 | 紫色 | 增删查改项目 | 填写名称(必填)+描述 |
| 📋 课题管理 | 青色 | 增删查改课题 | 需先选择项目过滤，序号+固定标记 |
| 👩‍🏫 班主任管理 | 靛蓝 | 增删查改班主任 | 姓名+电话+邮箱，行内编辑 |
| 🎓 讲师管理 | 蓝色 | 增删查改讲师 | 姓名+职称+专长+电话，行内编辑 |
| 📚 课程管理 | 绿色 | 增删查改课程 | 二级筛选（项目→课题），分组展示 |
| 🔗 科教组合管理 | 琥珀 | 增删查改教-课组合 | 二级筛选（项目→课题），显示优先级 |

> **注意**: 删除操作有安全检查 — 如果讲师/课题/班主任有活跃的排课引用，后端会阻止删除并返回错误提示。

### 5.3 Tab 3: 系统初始化

用于为**已开课的存量班级**补录历史课程进度。

#### 左栏: 班级列表
- 选择项目 → 加载该项目下所有班级
- 显示班级状态（筹备中/进行中/已完成）和班主任信息
- 底部可快速添加新班级

#### 右栏: 课题进度表单
- 选择班级后加载其所有课题（按大纲顺序排列）
- 每个课题卡片展示：
  - **序号徽章**（绿色=已完成，蓝色=已排课，灰色=未排课）
  - **周六教-课组合选择** + 日期选择
  - **周日教-课组合选择** + 自动计算日期(+1天)
  - **固定课题标记**
- **拖拽排序**: 课题卡片支持拖拽重新排列顺序
- **日期模式**: 自动推算（从开课日期起每4周一次）或手动选择
- 底部操作栏：重置 / 确认保存

### 5.4 弹窗功能详解

#### 新增班级弹窗
- 输入：班级名称(必填)、首次上课日期(默认下周六)、班主任(下拉选择)
- **排班预检**: 自动调用 `/classes/precheck-plan` 接口
  - 预演未来20周的排课日期
  - 检测潜在的班主任冲突
  - 推荐班主任（按冲突次数从低到高排序，含评分）
  - 显示风险提示（如节假日冲突）
- 创建后自动生成全部8节课的预排课表（三级降级算法）
- 如检测到冲突，弹窗展示详细冲突报告

#### 调整课程弹窗
- 显示当前排课信息（班级、课题、当前周六/周日日期）
- 可修改：日期（仅周六）、周六教-课组合、周日教-课组合
- 快捷操作：上移一周 / 下移一周（带冲突确认）
- **日期校验**: 前端强制检查必须为周六

#### 发布预览弹窗
- 按周展示全月所有排课，分周六/周日两列
- 显示发布审核清单（来自 `/schedule/publish-checklist`）：
  - 🔴 **无法解决**: `status='conflict'` 的记录（默认阻止发布）
  - 🟡 **待确认**: `status='planning'/'scheduled'` 的记录
  - 🟢 **已解决**: 已完成的记录
- 存在冲突时：需勾选"允许强制发布" + 填写备注才能发布
- 无冲突时：直接可发布

---

## 6. 核心业务流程

### 6.1 标准排课全流程

```
1. 录入基础数据
   项目 → 课题(8个) → 讲师 → 课程 → 教-课组合
                                              ↓
2. 创建班级 ──→ 排班预检(预演+班主任推荐)
                        ↓
3. 自动预排课 ──→ 三级降级算法生成8节课预排
                        ↓
4. 月度排课 ──→ AI约束提取 → generate_schedule → 全月课表
                        ↓
5. 人工调整 ──→ 调整日期/讲师 / 合班 / 顺延处理
                        ↓
6. 保存草稿 ──→ 月度计划(draft)
                        ↓
7. 发布预览 ──→ 审核清单检查 → 强制/正常发布
                        ↓
8. 正式发布 ──→ scheduled→confirmed / 冲突+备注
```

### 6.2 排课时间规则
- **上课日**: 仅周六和周日（周六为主日期）
- **课程间隔**: 默认每4周安排下一节课题
- **节假日规避**: 自动跳过法定节假日和补班日
- **日期存储**: 数据库中 `scheduled_date` 始终为周六

### 6.3 班级生命周期

```
planning（筹备中）──→ active（进行中）──→ completed（已完成）
    ↑ 创建时默认          ↑ 初始化后自动           ↑ 所有课题完成
```

### 6.4 课表记录状态机

```
                    ┌──── conflict ◀──── 冲突检测失败
                    │
planning ──→ scheduled ──→ confirmed ──→ completed
  ↑ 自动生成     ↑ 月度生成     ↑ 发布确认      ↑ 标记完成
                                                    │
                              cancelled ◀──── 手动取消
```

---

## 7. 排课算法详解

### 7.1 班级创建时的预排课（三级降级算法）

**代码位置**: [classes.py](file:///d:/学习/outputmsg/排课/paike/backend/routes/classes.py) → `auto_schedule_class()`

当创建新班级且 `auto_generate=true` 时触发：

```
对该项目的每个课题（按sequence排序）:
  ├── 计算目标日期 = start_date + (index × 4周)
  ├── 跳过节假日 → 找到最近的可用周六
  │
  ├── 策略A: 寻找无冲突组合
  │   ├── 遍历该课题的所有combo（按priority排序）
  │   ├── 检查讲师当日是否已被其他班级占用
  │   ├── 检查班主任当日是否已有其他课程
  │   └── 找到无冲突combo → 写入ClassSchedule(status='planning') ✅
  │
  ├── 策略B: 交换课题顺序
  │   ├── 当前课题的所有combo都冲突
  │   ├── 尝试与后续的非固定课题(is_fixed=false)交换
  │   ├── 检查交换后是否能消除冲突
  │   └── 成功交换 → 按新顺序重新排课 ✅
  │
  └── 策略C: 标记冲突
      ├── 策略A和B均失败
      ├── 使用第一个combo强制分配
      └── 写入ClassSchedule(status='conflict', notes=冲突原因) ⚠️
```

### 7.2 月度排课生成

**代码位置**: [schedule.py](file:///d:/学习/outputmsg/排课/paike/backend/routes/schedule.py) → `generate_schedule()`

前端点击"基于约束重新生成课表"时触发：

```
1. 清除该月所有 status in ('scheduled','planning','conflict') 的记录
2. 遍历所有 active/planning 状态的班级
3. 为每个班级找到下一个未完成的课题
4. 选择该课题下的最优combo（优先级 + 无冲突）
5. 在该月的周六中寻找可用日期
6. 冲突检测:
   - 节假日/补班检查 (is_holiday)
   - 班主任同日冲突检查
   - 讲师同日冲突检查 (周六combo_id + 周日combo_id_2)
   - 约束条件检查 (blocked_dates, teacher_unavailable, homeroom_unavailable)
7. 冲突处理:
   - postpone模式: 顺延至下一周六
   - mark模式: 保留位置，status='conflict'
8. 所有周六都不可用: 标记为skipped，通知前端
```

### 7.3 节假日检查逻辑

**代码位置**: [schedule.py](file:///d:/学习/outputmsg/排课/paike/backend/routes/schedule.py) → `is_holiday()`

```
1. 按年份动态加载本地缓存 holidays_{year}.json（自动匹配当前检查日期的年份）
2. 判定规则:
   - holiday=true → 节假日 ✅
   - after=true → 补班日 ✅
   - 名称包含"补班" → 补班日 ✅
   - workday=true → 补班日 ✅
3. 缓存未命中: 调用 timor.tech API 实时查询
4. API失败: 默认为工作日（不阻止排课）
```

---

## 8. API 接口参考

### 8.1 基础CRUD接口

| 模块 | 端点 | 方法 | 说明 |
|------|------|------|------|
| 项目 | `/api/projects` | GET/POST | 列表/创建 |
| 项目 | `/api/projects/<id>` | GET/PUT/DELETE | 详情/更新/删除 |
| 课题 | `/api/topics` | GET/POST | 列表(可过滤project_id)/创建 |
| 讲师 | `/api/teachers` | GET/POST | 列表/创建 |
| 课程 | `/api/courses` | GET/POST | 列表(可过滤topic_id)/创建 |
| 组合 | `/api/combos` | GET/POST | 列表(可过滤topic_id)/创建 |
| 班主任 | `/api/homerooms` | GET/POST | 列表/创建 |
| 班级 | `/api/classes` | GET/POST | 列表(可过滤project_id)/创建 |

### 8.2 排课核心接口

| 端点 | 方法 | 说明 |
|------|------|------|
| `/api/schedule/month/<year>/<month>` | GET | 获取月度排课数据（按周分组） |
| `/api/schedule/generate` | POST | 生成月度课表（需传year/month/constraints/conflict_mode） |
| `/api/schedule/adjust` | POST | 调整单条排课（日期/combo/force） |
| `/api/schedule/move-week` | POST | 上移/下移一周（带direction/force） |
| `/api/schedule/merge` | POST | 合班（传schedule_ids数组） |
| `/api/schedule/unmerge/<id>` | POST | 拆分合班 |
| `/api/schedule/save-draft` | POST | 保存月度草稿 |
| `/api/schedule/publish` | POST | 发布月度计划（支持force_publish+force_note） |
| `/api/schedule/publish-checklist` | GET | 获取发布审核清单 |
| `/api/schedule/constraints` | GET/POST | 约束条件列表/创建 |
| `/api/schedule/constraints/<id>` | PUT/DELETE | 更新/删除约束 |

### 8.3 特殊接口

| 端点 | 方法 | 说明 |
|------|------|------|
| `/api/classes/precheck-plan` | POST | 排班预检（预演日期+班主任推荐） |
| `/api/classes/sync-status` | POST | 同步班级状态 |
| `/api/init/class-status/<id>` | GET | 获取班级初始化状态 |
| `/api/init/class-progress` | POST | 批量录入班级课程进度 |
| `/api/ai/extract-constraints` | POST | AI提取约束条件 |
| `/api/ai/config` | GET/PUT | AI配置查看/修改 |
| `/api/health` | GET | 健康检查 |

---

## 9. 使用注意事项与约束

### 9.1 数据录入顺序
> [!IMPORTANT]
> 必须遵循以下录入顺序，否则后续功能无法正常工作：
> **项目 → 课题 → 讲师 + 课程 → 教-课组合 → 班主任 → 班级**

### 9.2 排课日期规则
> [!WARNING]
> - 所有排课日期**必须为周六**，前端和后端均有校验
> - 课程间隔固定为**4周**（28天），由 `config.py` 中 `WEEKS_INTERVAL` 控制
> - 系统不支持非周末排课

### 9.3 课题数量
- 系统设计为每个项目标准**8个课题**
- 实际可配置其他数量，前端已动态显示

### 9.4 教-课组合要求
> [!CAUTION]
> - 每个课题**至少需要1个教-课组合**才能正常排课
> - 建议每个课题配置**2个以上**组合，以便在冲突时有备选
> - 没有组合的课题在排课时会被跳过或报错

### 9.5 节假日数据
- 系统按年份动态加载 `holidays_{year}.json` 缓存文件
- 当前内置了 2026 年的缓存，跨年使用需添加对应年份文件或确保 API 可用
- 补班日（如春节后调休上班）同样被标记为不可排课

### 9.6 AI 功能前提
- AI约束提取依赖外部 Dify 智能体服务
- 需配置正确的 `AI_AGENT_URL` 和 `AI_AGENT_API_KEY`
- AI 服务不可用时，可手动管理约束条件，不影响基本排课功能

### 9.7 合班操作注意
- 合班仅适用于**同一周末、同一课题**的不同班级
- 合班后两条记录通过 `merged_with` 字段互相关联
- 拆分合班时只需对其中一条记录操作

### 9.8 发布与冲突
- 存在 `conflict` 状态记录时，默认**阻止发布**
- 强制发布需要：勾选强制选项 + 填写备注说明
- 发布后 `scheduled` 状态变为 `confirmed`
- 已发布的月度计划可重新生成覆盖（生成时清除旧数据）

---

## 10. 已知问题与改进建议

### 10.1 已修复问题

> 以下问题均已修复。

#### v2.1 修复（代码级bug）
| # | 问题 | 修复方案 |
|---|------|----------|
| B1 | `adjust`接口讲师冲突误报 | 分离 Day1/Day2 检查 |
| B2 | `generate_schedule`课表清除不彻底 | 清除范围增加 `planning` 和 `conflict` 状态 |
| B3 | AI响应JSON解析脆弱 | 增加4种提取模式 + 尾随逗号修复 |
| B4 | 无事务回滚保护 | 已确认存在 `db.session.rollback()` |
| B5 | holidays缓存仅2026 | 按年份动态加载 `holidays_{year}.json` |
| F1 | 硬编码年月 | `new Date()` 自动定位当前月 |
| F2 | 课题数量硬编码 | 移除"共8节"硬编码文字 |
| F3 | 发布预览模板拼写错误 | 补全 `$` 前缀 |
| F4 | 顺延通知语言不一致 | 全部翻译为中文 |
| F5 | 拖拽警告转义异常 | 修复 `\\n` 双重转义 |
| F6 | 新增排课按钮指向错误 | 移除该按钮（3处） |

#### v2.2 修复（逻辑审计）
| # | 问题 | 修复方案 |
|---|------|----------|
| A1 | `move-week`缺少周日讲师冲突检查 | 增加 `combo_id_2` 冲突检查 |
| A2 | `publish`不处理`planning`状态 | 条件改为 `in_(['scheduled', 'planning'])` |
| A3 | `sync_class_statuses`遗漏`confirmed` | 条件改为 `in_(['scheduled', 'confirmed'])` |
| A4 | 合班主记录无标记 | 添加合班主记录备注 |
| A5 | `unmerge`清空所有备注 | 只清除合班相关备注 |
| A6 | 初始化跳过未选combo无提示 | 返回跳过列表给前端展示 |
| A7 | 初始化自动日期不检查节假日 | 异步检查并标红警告 |
| A8 | 月度看板无刷新按钮 | 月份导航增加刷新图标 |
| A9 | 初始化保存结果无跳过提示 | 展示后端返回的跳过详情 |
| A10 | 合班前端无同课题预检 | 勾选时检查 `topic_id` 一致性 |
| A11 | 已完成课程可通过API修改 | adjust/move/delete 增加状态保护 |

### 10.3 架构改进建议

| 建议 | 优先级 | 说明 |
|------|--------|------|
| 引入前端框架 | 低 | 3600行单文件难以维护，建议拆分为模块化组件 |
| 状态管理 | 中 | 当前靠全局变量管理状态，易出现不一致 |
| API错误统一处理 | 中 | 前端各函数独立处理错误，缺少统一机制 |
| 数据输入验证增强 | 中 | 后端对边界情况校验不够严格 |
| 操作日志 | 低 | 缺少操作审计记录 |
| 数据库迁移脚本 | 中 | 无Schema版本管理，升级风险高 |

---

## 11. 部署与维护

### 11.1 环境要求
- Python 3.7+、现代浏览器（Chrome/Firefox/Edge）
- 可选：网络连接（节假日API + AI服务）

### 11.2 快速启动

```bash
# 1. 安装依赖
cd backend
pip install -r requirements.txt

# 2. 初始化数据库 (首次运行自动创建)
python app.py

# 3. 访问前端
# 浏览器打开 frontend/index.html
```

### 11.3 环境变量

```bash
# 可选配置
export DATABASE_URL="sqlite:///scheduler.db"      # 数据库
export SECRET_KEY="your-secret-key"                 # Flask密钥
export AI_AGENT_URL="https://ai.isstech.com/..."    # AI服务
export AI_AGENT_API_KEY="your-api-key"              # AI密钥
```

### 11.4 日常维护
- **数据备份**: 定期备份 `scheduler.db` 文件
- **节假日更新**: 新年度需更新 `holidays_YYYY.json`
- **日志检查**: Flask开发服务器日志可在终端查看
- **数据清理**: 定期归档已完成班级的历史数据

---

> 本文档基于对系统全部代码（后端10个Python文件、前端3629行HTML/JS）和4份现有文档的深度分析自动生成。  
> 如需更新，请在系统代码变更后同步修改本文档。
