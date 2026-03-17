#!/bin/bash
# 生产环境启动（gunicorn + 后台运行）
APP_DIR="$(cd "$(dirname "$0")/../backend" && pwd)"
LOG_DIR="$(cd "$(dirname "$0")" && pwd)/logs"
PID_FILE="$(cd "$(dirname "$0")" && pwd)/paike.pid"

mkdir -p "$LOG_DIR"

# ---------- 函数 ----------
start() {
    if [ -f "$PID_FILE" ] && kill -0 "$(cat "$PID_FILE")" 2>/dev/null; then
        echo "⚠️  服务已在运行 (PID: $(cat "$PID_FILE"))"
        return 1
    fi

    # 检查 gunicorn
    if ! command -v gunicorn &> /dev/null; then
        echo "📦 安装 gunicorn..."
        pip3 install gunicorn
    fi

    echo "🚀 启动排课系统（生产模式）..."
    cd "$APP_DIR"
    nohup gunicorn \
        --bind 0.0.0.0:5000 \
        --workers 2 \
        --timeout 120 \
        --access-logfile "$LOG_DIR/access.log" \
        --error-logfile "$LOG_DIR/error.log" \
        "app:app" \
        > "$LOG_DIR/stdout.log" 2>&1 &

    echo $! > "$PID_FILE"
    sleep 1

    if kill -0 "$(cat "$PID_FILE")" 2>/dev/null; then
        echo "✅ 启动成功 (PID: $(cat "$PID_FILE"))"
        echo "   访问地址: http://$(hostname -I | awk '{print $1}'):5000"
        echo "   日志目录: $LOG_DIR"
    else
        echo "❌ 启动失败，查看日志: $LOG_DIR/error.log"
        rm -f "$PID_FILE"
        return 1
    fi
}

stop() {
    if [ ! -f "$PID_FILE" ]; then
        echo "⚠️  PID文件不存在，服务可能未在运行"
        return 1
    fi
    PID=$(cat "$PID_FILE")
    echo "⏹️  停止服务 (PID: $PID)..."
    kill "$PID" 2>/dev/null
    sleep 2
    kill -9 "$PID" 2>/dev/null
    rm -f "$PID_FILE"
    echo "✅ 已停止"
}

restart() {
    stop
    sleep 1
    start
}

status() {
    if [ -f "$PID_FILE" ] && kill -0 "$(cat "$PID_FILE")" 2>/dev/null; then
        echo "✅ 服务运行中 (PID: $(cat "$PID_FILE"))"
    else
        echo "⏹️  服务未运行"
        rm -f "$PID_FILE" 2>/dev/null
    fi
}

# ---------- 入口 ----------
case "${1:-start}" in
    start)   start   ;;
    stop)    stop    ;;
    restart) restart ;;
    status)  status  ;;
    *)
        echo "用法: $0 {start|stop|restart|status}"
        exit 1
        ;;
esac
