#!/bin/bash
# 安装 Python 依赖（兼容无法编译 greenlet 的服务器）
echo "📦 安装 Python 依赖..."

pip3 install sqlalchemy --no-deps -q
pip3 install typing-extensions -q
pip3 install flask flask-sqlalchemy flask-cors requests python-dateutil openpyxl gunicorn -q

echo ""
python3 -c "from flask import Flask; from flask_sqlalchemy import SQLAlchemy; print('✅ 依赖安装完成')" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "❌ 依赖检查失败，请查看上方错误信息"
    exit 1
fi
