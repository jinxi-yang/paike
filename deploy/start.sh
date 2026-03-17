#!/bin/bash
# 启动排课系统（前台运行，用于调试）
cd "$(dirname "$0")/../backend"

echo "========================================"
echo "  北清商学院排课系统 - 启动中..."
echo "========================================"

# 检查 Python
if ! command -v python3 &> /dev/null; then
    echo "❌ 未找到 python3，请先安装"
    exit 1
fi

# 检查依赖
if ! python3 -c "import flask" 2>/dev/null; then
    echo "📦 首次运行，安装依赖..."
    bash "$(dirname "$0")/install_deps.sh"
fi

# 启动（开发模式）
echo "🚀 启动服务: http://0.0.0.0:5000"
python3 app.py
