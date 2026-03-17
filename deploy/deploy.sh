#!/bin/bash
# ============================================================
#  一键部署脚本（从本地 Windows 机器通过 SSH 执行）
#
#  用法:
#    bash deploy.sh <服务器IP> [用户名] [远程目录]
#
#  示例:
#    bash deploy.sh 192.168.1.100                    # 默认 root, /opt/paike
#    bash deploy.sh 192.168.1.100 ubuntu /home/ubuntu/paike
# ============================================================

set -e

SERVER=${1:?"请提供服务器IP，例如: bash deploy.sh 192.168.1.100"}
USER=${2:-root}
REMOTE_DIR=${3:-/opt/paike}

PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"

echo "========================================"
echo "  部署排课系统到 $USER@$SERVER:$REMOTE_DIR"
echo "========================================"

# 1. 在服务器上创建目录
echo "📁 创建远程目录..."
ssh "$USER@$SERVER" "mkdir -p $REMOTE_DIR"

# 2. 同步代码（排除不需要的文件）
echo "📤 同步代码..."
rsync -avz --progress \
    --exclude '.git/' \
    --exclude '.history/' \
    --exclude '.vscode/' \
    --exclude '__pycache__/' \
    --exclude '*.pyc' \
    --exclude 'scheduler.db'        \
    --exclude 'scheduler.db.*'      \
    --exclude 'deploy/logs/'        \
    --exclude 'deploy/*.pid'        \
    "$PROJECT_ROOT/" "$USER@$SERVER:$REMOTE_DIR/"

# 3. 远程安装依赖 + 启动
echo "🔧 安装依赖并启动..."
ssh "$USER@$SERVER" << REMOTE_SCRIPT
cd $REMOTE_DIR
chmod +x deploy/*.sh
bash deploy/install_deps.sh
# 重启服务
bash deploy/start_prod.sh restart
REMOTE_SCRIPT

echo ""
echo "✅ 部署完成！"
echo "   直连地址: http://$SERVER:5000"
echo "   nginx代理: http://$SERVER/paike/"
echo "   管理员登录: admin / admin123"
echo "   查看者登录: viewer / viewer123"
