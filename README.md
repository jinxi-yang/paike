# 北清商学院智能排课系统

## 项目结构

```
beiqing-scheduler/
├── backend/          # Flask后端
│   ├── app.py        # 主应用入口
│   ├── config.py     # 配置文件
│   ├── models.py     # 数据库模型
│   ├── init_data.py  # 数据初始化脚本
│   └── routes/       # API路由
├── frontend/         # 前端页面
│   └── index.html    # 改造后的排课页面
└── README.md
```

## 快速开始

### 1. 安装依赖

```bash
cd beiqing-scheduler/backend
pip install -r requirements.txt
```

### 2. 初始化数据库

```bash
python init_data.py
```

### 3. 启动后端

```bash
python app.py
```

后端将在 http://localhost:5000 启动

### 4. 打开前端

用浏览器直接打开 `frontend/index.html`，或使用 VS Code Live Server。

## API文档

详见 `implementation_plan.md`
