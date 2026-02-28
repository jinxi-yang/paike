# 北清商学院智能排课系统 - 部署指南

恭喜！系统开发工作已全部完成，现在可以开始部署和测试。

本文档包含 **本地测试 (Windows)** 和 **生产环境部署 (Linux)** 的详细步骤。

---

## 一、部署前准备 (通用)

### 1. 核心依赖
不管是在windows还是Linux，都需要以下环境：
- **Python 3.8+**
- **MySQL 5.7+ 或 8.0+**
- **PIP 包管理器**

### 2. 数据库准备
确保你有一个可用的 MySQL 数据库。在数据库中执行以下SQL初始化库（如果不手动创建，初始化脚本也会尝试连接）：
```sql
CREATE DATABASE IF NOT EXISTS bqsxy CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

---

## 二、本地测试 (Windows)

### 1. 源码目录
假设源码在 `C:\Users\username\beiqing-scheduler`。

### 2. 安装依赖
打开 PowerShell 或 CMD，进入 `backend` 目录：
```powershell
cd backend
pip install -r requirements.txt
# 如果没有 requirements.txt，安装以下核心包：
# pip install flask flask-sqlalchemy flask-cors pymysql requests
```

### 3. 配置数据库
编辑 `backend/config.py`，修改 MySQL 连接信息：
```python
MYSQL_HOST = 'localhost'  # 或你的数据库IP
MYSQL_PORT = 3306
MYSQL_USER = 'root'
MYSQL_PASSWORD = 'your_password'
MYSQL_DATABASE = 'bqsxy'
```

### 4. 初始化数据
**首次运行前必须执行**，用于创建表和生成模拟数据：
```powershell
python init_data.py
```
> 如果看到 "所有数据初始化完成！" 即表示成功。

### 5. 启动后端
```powershell
python app.py
```
默认运行在 `http://127.0.0.1:5000`。

### 6. 前端访问
直接双击打开 `frontend/index.html`，或者为了更好的体验（避免跨域问题），在前端目录启动一个简单服务器：
```powershell
cd ../frontend
python -m http.server 8080
# 浏览器访问 http://localhost:8080
```

---

## 三、生产环境部署 (Linux - CentOS/Ubuntu)

### 1. 上传代码
将 `beiqing-scheduler` 文件夹上传到服务器，例如 `/opt/beiqing-scheduler`。

### 2. 安装环境
```bash
# Ubuntu
sudo apt update
sudo apt install python3-pip python3-venv mysql-server

# CentOS
sudo Inyum install python3-pip mysql-server
```

### 3. 创建虚拟环境 (推荐)
```bash
cd /opt/beiqing-scheduler/backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install gunicorn  # 生产环境推荐使用 Gunicorn
```

### 4. 配置与初始化
1.  修改 `backend/config.py` 中的数据库配置。
2.  初始化数据：
    ```bash
    python init_data.py
    ```

### 5. 使用 Gunicorn 启动后端
不要直接用 `python app.py`，使用 Gunicorn 后台运行：
```bash
# 启动 4 个 worker 进程，绑定到 5000 端口
nohup gunicorn -w 4 -b 0.0.0.0:5000 app:app > access.log 2>&1 &
```

### 6. 配置 Nginx (作为反向代理)
安装 Nginx 并配置：`sudo nano /etc/nginx/sites-available/scheduler`

```nginx
server {
    listen 80;
    server_name your_domain_or_ip;

    # 前端静态文件
    location / {
        root /opt/beiqing-scheduler/frontend;
        index index.html;
        try_files $uri $uri/ =404;
    }

    # 后端 API 代理
    location /api {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```
启用配置并重启 Nginx：
```bash
sudo ln -s /etc/nginx/sites-available/scheduler /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

### 7. 访问
你可以直接通过 `http://your_domain_or_ip` 访问系统了！

---

## 四、常见问题排查

1.  **数据库连接失败**：检查 `config.py` 中的 IP/端口/密码，确保防火墙开放了 3306 端口。
2.  **API 请求 404**：检查前端 `index.html` 中的 `API_BASE` 变量。如果在 Linux 配合 Nginx 使用，可以改为 `const API_BASE = '/api';` (相对路径)。
3.  **智能体无响应**：检查服务器能否访问外网（`https://ai.isstech.com`）。

祝部署顺利！🚀
