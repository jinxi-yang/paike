# 🎓 北清商学院智能排课系统

[![Python](https://img.shields.io/badge/Python-3.7+-blue.svg)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-2.0+-red.svg)](https://flask.palletsprojects.com/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

基于AI技术的智能排课系统，通过算法优化实现课程、教师、班级、时间等资源的智能化调度，显著提升教务管理效率。

## 🌟 核心功能

- **AI智能排课** - 基于规则引擎与AI模型生成最优课表
- **多维度管理** - 教师信息、课程配置、班级管理一体化
- **灵活排课模式** - 支持行政班与走班制混合管理
- **节假日智能处理** - 自动规避节假日，避免排课冲突
- **可视化界面** - 直观的前端操作界面

## 🏗️ 技术架构

```
paike/
├── backend/              # Flask后端服务
│   ├── app.py           # 应用主入口
│   ├── config.py        # 系统配置
│   ├── models.py        # 数据库模型
│   ├── init_data.py     # 初始化数据脚本
│   ├── routes/          # RESTful API路由
│   │   ├── schedule.py  # 排课核心逻辑
│   │   ├── teacher.py   # 教师管理API
│   │   ├── course.py    # 课程管理API
│   │   └── ...          # 其他业务模块
│   └── requirements.txt # Python依赖包
├── frontend/            # 前端界面
│   └── index.html       # 主页面（SPA）
├── docs/                # 技术文档
│   └── SCHEDULING_ALGORITHM.md  # 排课算法详解
└── README.md
```

## 🚀 快速开始

### 环境要求
- Python 3.7+
- pip 包管理器
- 现代浏览器

### 安装部署

1. **克隆项目**
```bash
git clone https://github.com/your-username/paike.git
cd paike
```

2. **安装后端依赖**
```bash
cd backend
pip install -r requirements.txt
```

3. **初始化数据库**
```bash
python init_data.py
```

4. **启动服务**
```bash
python app.py
```
后端服务将在 `http://localhost:5000` 启动

5. **访问前端**
直接用浏览器打开 `frontend/index.html` 文件

## 🔧 API接口

主要API端点：
- `GET /api/teachers` - 获取教师列表
- `GET /api/courses` - 获取课程信息  
- `POST /api/schedule/generate` - 生成排课方案
- `GET /api/classes` - 获取班级信息

详细接口文档请参考 [API文档](docs/API_DOCUMENTATION.md)

## 📖 文档资料

- [排课算法详解](docs/SCHEDULING_ALGORITHM.md)
- [部署指南](DEPLOY.md)
- [系统诊断](DIAGNOSIS.md)
- [实施计划](implementation_plan.md)

## 🤝 贡献指南

欢迎提交Issue和Pull Request来改进项目！

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情

## 📞 联系方式

如有问题，请提交Issue或联系项目维护者。