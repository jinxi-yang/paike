#!/bin/bash
# 安装 Python 依赖（支持 venv，兼容无法编译 greenlet 的服务器）
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
VENV_DIR="$(cd "$SCRIPT_DIR/.." && pwd)/venv"

# 如果存在 venv 则激活
if [ -d "$VENV_DIR" ]; then
    echo "🐍 检测到虚拟环境: $VENV_DIR"
    source "$VENV_DIR/bin/activate"
elif command -v python3 &>/dev/null && python3 -m venv --help &>/dev/null; then
    echo "🐍 创建虚拟环境: $VENV_DIR"
    python3 -m venv "$VENV_DIR"
    source "$VENV_DIR/bin/activate"
    pip install --upgrade pip -q
else
    echo "⚠️  无法创建虚拟环境，将使用系统 Python"
fi

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
