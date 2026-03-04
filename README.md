# 北清商学院智能排课系统

<p align="center">
  <img src="https://img.shields.io/badge/version-1.0-blue.svg" alt="Version">
  <img src="https://img.shields.io/badge/python-3.7%2B-green.svg" alt="Python Version">
  <img src="https://img.shields.io/badge/license-MIT-orange.svg" alt="License">
</p>

## 🎯 项目简介

北清商学院智能排课系统是一款基于人工智能技术的教学资源调度管理平台，专门解决商学院复杂的课程安排问题。通过智能化算法和自动化流程，显著提升教务管理效率，降低人工排课成本。

### 🔧 核心功能
- **智能排课引擎**: 基于约束满足问题(CSP)的自动排课算法
- **冲突检测预防**: 实时检测并解决时间、师资、场地等各类冲突
- **AI辅助决策**: 集成Dify平台提供智能决策支持
- **可视化管理**: 直观的Web界面，支持月/周视图切换
- **灵活调整**: 支持单课调整、批量操作、合班处理等功能

## 📚 文档导航

| 文档 | 用途 | 适合人群 |
|------|------|----------|
| [📘 产品说明书](docs/product_specification.md) | 详细介绍产品功能、架构、技术特点 | 产品经理、技术负责人 |
| [📖 用户手册](docs/user_manual.md) | 详细操作指南和使用说明 | 教务管理人员、最终用户 |
| [📝 实施计划](implementation_plan.md) | 技术实现方案和开发计划 | 开发团队 |
| [🔍 诊断文档](DIAGNOSIS.md) | 系统诊断和问题排查指南 | 运维人员 |
| [🚀 部署指南](DEPLOY.md) | 生产环境部署说明 | 系统管理员 |

## 🏗️ 系统架构

```
paike/
├── backend/           # 后端服务
│   ├── app.py        # Flask主应用
│   ├── models.py     # 数据模型
│   ├── config.py     # 配置管理
│   ├── routes/       # API路由模块
│   └── init_data.py  # 数据初始化
├── frontend/         # 前端界面
│   └── index.html    # 主页面
├── docs/             # 文档目录
│   ├── product_specification.md  # 产品说明书
│   └── user_manual.md           # 用户手册
└── scripts/          # 辅助脚本
```

## 🚀 快速开始

### 环境准备
```bash
# Python版本要求
python >= 3.7

# 安装依赖
cd backend
pip install -r requirements.txt
```

### 系统启动
```bash
# 1. 初始化数据库
python init_data.py

# 2. 启动后端服务
python app.py
# 默认访问地址: http://localhost:5000

# 3. 打开前端界面
# 直接在浏览器中打开 frontend/index.html
```

## 🎨 主要特性

### 智能化程度高
- 🤖 基于AI的自动排课算法
- ⚡ 智能冲突检测和解决
- 📊 数据驱动的决策支持

### 用户体验优秀
- 💻 响应式Web界面设计
- 🎯 直观的操作流程
- 🔄 实时状态反馈

### 扩展性强
- 🔧 模块化架构设计
- 📦 灵活的配置选项
- ☁️ 支持多种部署方式

## 👥 目标用户

- **教务管理人员**: 日常排课、调课、计划制定
- **教学组织者**: 课程资源协调、进度跟踪
- **系统管理员**: 平台维护、数据管理

## 📊 技术栈

- **前端**: HTML5 + JavaScript + Tailwind CSS
- **后端**: Python Flask + SQLAlchemy
- **数据库**: SQLite (支持MySQL扩展)
- **AI平台**: Dify智能体平台
- **部署**: 本地部署或云服务器

## 🤝 贡献指南

欢迎提交Issue和Pull Request来帮助改进项目：

1. Fork 项目仓库
2. 创建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情

## 📞 联系方式

- **项目主页**: [GitHub仓库地址]
- **问题反馈**: [Issues页面]
- **技术交流**: [讨论区]

---

<p align="center">
  Made with ❤️ for 北清商学院
</p>