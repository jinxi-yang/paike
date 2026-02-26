# 北清商学院智能排课系统 - 代码审查与运行指南

## 一、代码完整性检查结果

### ✅ 数据库模型 (models.py) - 9张表

| 表名 | 功能 | 字段数 | 状态 |
|-----|------|-------|-----|
| `training_type` | 培训班类型 | 4 | ✅ 完整 |
| `topic` | 课题 | 6 | ✅ 完整 |
| `homeroom` | 班主任 | 5 | ✅ 完整 |
| `teacher` | 授课讲师 | 6 | ✅ 完整 |
| `course` | 课程 | 5 | ✅ 完整 |
| `teacher_course_combo` | 教-课组合 | 6 | ✅ 完整 |
| `class` | 班级 | 7 | ✅ 完整 |
| `class_schedule` | 班级课表 | 10 | ✅ 完整 |
| `monthly_plan` | 月度计划 | 5 | ✅ 完整 |

---

### ✅ API路由 (routes/) - 10个模块

| 文件 | API数量 | 核心功能 | 状态 |
|-----|--------|---------|-----|
| `training_type.py` | 5 | CRUD培训班类型 | ✅ |
| `topic.py` | 4 | CRUD课题 | ✅ |
| `homeroom.py` | 5 | CRUD班主任 | ✅ |
| `teacher.py` | 5 | CRUD讲师 | ✅ |
| `course.py` | 5 | CRUD课程 | ✅ |
| `combo.py` | 5 | CRUD教-课组合 | ✅ |
| `classes.py` | 6 | 班级管理+自动排课 | ✅ |
| `schedule.py` | 7 | 月度查询/调整/合班/发布 | ✅ |
| `ai.py` | 4 | 智能体接口/配置/Schema | ✅ |

---

### ✅ 核心业务逻辑检查

| 功能 | 实现文件 | 状态 | 说明 |
|-----|---------|-----|------|
| 自动排课（每4周一节） | `classes.py:auto_schedule_class` | ✅ | 含MIN_WEEKS_INTERVAL配置 |
| 节假日避开 | `schedule.py:is_holiday` | ✅ | 调用timor.tech API |
| 找下一个周六 | `schedule.py:find_next_available_saturday` | ✅ | |
| 班主任冲突检查 | `schedule.py:adjust_schedule` | ✅ | 调整时检查同日期冲突 |
| **讲师档期冲突检查** | `schedule.py:adjust_schedule` | ✅ | **新增：检测讲师同日其他课程** |
| 合班功能 | `schedule.py:merge_classes` | ✅ | 验证同课题后合并 |
| 取消合班 | `schedule.py:unmerge_class` | ✅ | |
| **删除课程** | `schedule.py:delete_schedule` | ✅ | **新增：支持单课删除** |
| 月度计划发布 | `schedule.py:publish_month` | ✅ | 更新状态为published |
| AI约束提取接口 | `ai.py:extract_constraints` | ✅ | 支持外部智能体转发 |
| **前端拖拽排课** | `index.html:initDragAndDrop` | ✅ | **新增：课程可拖拽到其他周** |

---

### ✅ 初始化数据 (init_data.py)

| 数据类型 | 数量 | 状态 |
|---------|-----|-----|
| 培训班类型 | 7种 | ✅ |
| 课题 | 56个 (7×8) | ✅ |
| 班主任 | 10人 | ✅ |
| 授课讲师 | 20人 | ✅ |
| 课程 | 30门 | ✅ |
| 教-课组合 | 约100个 | ✅ |
| 模拟班级 | 17个 | ✅ |
| 模拟课表 | 136条 | ✅ |

---

### ✅ 前端页面 (frontend/index.html)

| 功能模块 | 状态 | 说明 |
|---------|-----|------|
| 培训班类型卡片 | ✅ | 从API动态加载 |
| 培训班详情弹窗 | ✅ | 显示课题列表和班级管理 |
| 新增班级弹窗 | ✅ | 含班主任选择和日期选择 |
| 班级课表弹窗 | ✅ | 显示8节课安排 |
| 月度排课看板 | ✅ | 按周分组显示 |
| AI提示词输入 | ✅ | 调用/api/ai/extract-constraints |
| 课程调整弹窗 | ✅ | 含上一周/下一周按钮 |
| 基础数据管理 | ✅ | 班主任/讲师/课程CRUD |
| 发布月度计划 | ✅ | 调用/api/schedule/publish |

---

## 二、本次增强内容（基于原型对照）

基于原始HTML原型 `北清本体设计-沟通后-2026年2月3日.html` 的详细分析，已补充以下功能：

| 功能 | 来源 | 状态 |
|-----|-----|-----|
| 拖拽排课（周间移动） | 原型L1467-1510 | ✅ 已实现 |
| 按周分组显示课表 | 原型L1396-1460 | ✅ 已实现 |
| 讲师档期冲突检测 | 讨论约定 | ✅ 已实现 |
| 课程删除功能 | 原型L1562-1572 | ✅ 已实现 |

### ⚠️ 剩余可改进项（非阻塞）

| 问题 | 位置 | 建议 |
|-----|-----|------|
| 节假日缓存仅内存 | `schedule.py` | 可考虑文件/Redis缓存 |

---

## 三、运行与验证步骤

### 第1步：进入后端目录

```powershell
cd C:\Users\wzwwh\.gemini\antigravity\scratch\beiqing-scheduler\backend
```

### 第2步：确保MySQL数据库存在

在MySQL中执行（如果数据库不存在）：
```sql
CREATE DATABASE IF NOT EXISTS bqsxy CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

### 第3步：初始化数据

```powershell
python init_data.py
```

**预期输出**：
```
==================================================
北清商学院排课系统 - 数据初始化
==================================================
数据库: MySQL @ 10.156.195.35:3306/bqsxy
==================================================
✓ 数据库表创建成功
✓ 培训班类型和课题初始化完成
✓ 班主任初始化完成（10人）
✓ 授课讲师初始化完成（20人）
✓ 课程初始化完成（30门）
✓ 教-课组合初始化完成（约100个）
✓ 模拟班级初始化完成（17个班级，136个课表记录）

✓ 所有数据初始化完成！
```

### 第4步：启动后端服务

```powershell
python app.py
```

**预期输出**：
```
 * Running on http://0.0.0.0:5000
 * Debug mode: on
```

### 第5步：验证后端API

在浏览器或命令行中访问：

```powershell
# 测试健康检查
curl http://localhost:5000/api/health

# 测试获取培训班类型
curl http://localhost:5000/api/training-types

# 测试获取月度排课（2026年3月）
curl http://localhost:5000/api/schedule/month/2026/3
```

### 第6步：打开前端页面

用浏览器打开：
```
C:\Users\wzwwh\.gemini\antigravity\scratch\beiqing-scheduler\frontend\index.html
```

或使用简单的HTTP服务器：
```powershell
cd C:\Users\wzwwh\.gemini\antigravity\scratch\beiqing-scheduler\frontend
python -m http.server 8080
# 然后访问 http://localhost:8080
```

### 第7步：功能验证检查表

- [ ] 页面加载后显示7个培训班类型卡片
- [ ] 右上角显示"● 已连接"（绿色）
- [ ] 点击培训班卡片，弹出详情窗口
- [ ] 详情窗口显示8个课题和已有班级
- [ ] 点击"新增班级"，选择日期后创建
- [ ] 创建成功后显示8节课的自动排课
- [ ] 月度看板显示按周分组的课程卡片
- [ ] 点击课程卡片上的"调整"按钮可修改
- [ ] 切换到"基础数据管理"可增删班主任/讲师/课程

---

## 四、配置说明

### MySQL连接配置

文件：`backend/config.py`

```python
MYSQL_HOST = '10.156.195.35'
MYSQL_PORT = 3306
MYSQL_USER = 'root'
MYSQL_PASSWORD = '112233'
MYSQL_DATABASE = 'bqsxy'
```

如需修改，请编辑以上值后重启后端。

### AI智能体配置

如果你有外部AI智能体服务，可以在运行时配置：

```bash
curl -X POST http://localhost:5000/api/ai/config \
  -H "Content-Type: application/json" \
  -d '{"url": "https://your-ai-agent.com/extract"}'
```

---

## 五、项目文件清单

```
beiqing-scheduler/
├── README.md
├── backend/
│   ├── app.py              # Flask主应用
│   ├── config.py           # 配置（MySQL连接）
│   ├── models.py           # 9个数据库模型
│   ├── init_data.py        # 数据初始化+模拟数据
│   ├── requirements.txt    # Python依赖
│   └── routes/
│       ├── __init__.py     # 蓝图注册
│       ├── training_type.py
│       ├── topic.py
│       ├── homeroom.py
│       ├── teacher.py  
│       ├── course.py
│       ├── combo.py
│       ├── classes.py      # 含自动排课
│       ├── schedule.py     # 含节假日API集成
│       └── ai.py           # 智能体接口
└── frontend/
    └── index.html          # 完整前端页面
```

共计 **15个代码文件**，功能完整。
