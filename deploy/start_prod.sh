#!/bin/bash
# 生产环境启动（gunicorn + 后台运行）
APP_DIR="$(cd "$(dirname "$0")/../backend" && pwd)"
LOG_DIR="$(cd "$(dirname "$0")" && pwd)/logs"
PID_FILE="$(cd "$(dirname "$0")" && pwd)/paike.pid"
VENV_DIR="$(cd "$(dirname "$0")/.." && pwd)/venv"

mkdir -p "$LOG_DIR"

# ---------- 虚拟环境 ----------
_activate_venv() {
    if [ -d "$VENV_DIR" ]; then
        source "$VENV_DIR/bin/activate"
    fi
}

# ---------- 工具函数 ----------
_kill_port() {
    local port=$1
    echo "🔍 正在检测并清理占用 ${port} 端口的进程..."

    # 1. 优先尝试 fuser (Linux 常用)
    if command -v fuser &> /dev/null; then
        fuser -k "${port}/tcp" 2>/dev/null && sleep 1
    fi

    # 2. 尝试 lsof
    if command -v lsof &> /dev/null; then
        lsof -ti:"$port" | xargs -r kill -9 2>/dev/null && sleep 1
    fi

    # 3. 尝试 netstat (精简系统常用)
    if command -v netstat &> /dev/null; then
        netstat -nlp 2>/dev/null | grep ":${port} " | awk '{print $7}' | cut -d/ -f1 | xargs -r kill -9 2>/dev/null && sleep 1
    fi

    # 4. 尝试 ss (现代系统常用)
    if command -v ss &> /dev/null; then
        ss -ltnp 2>/dev/null | grep ":${port} " | awk '{print $6}' | cut -d, -f2 | sed 's/pid=//' | xargs -r kill -9 2>/dev/null && sleep 1
    fi
}

# ---------- 函数 ----------
start() {
    if [ -f "$PID_FILE" ] && kill -0 "$(cat "$PID_FILE")" 2>/dev/null; then
        echo "⚠️  服务已在运行 (PID: $(cat "$PID_FILE"))"
        return 1
    fi

    # 检查端口占用
    if netstat -tuln 2>/dev/null | grep -q ":5000 " || ss -tuln 2>/dev/null | grep -q ":5000 "; then
        echo "⚠️  检测到 5000 端口已被占用，正在尝试清理..."
        _kill_port 5000
        sleep 1
    fi

    # 再次检查端口
    if netstat -tuln 2>/dev/null | grep -q ":5000 " || ss -tuln 2>/dev/null | grep -q ":5000 "; then
        echo "❌ 无法清理 5000 端口，请手动检查或使用 sudo 运行脚本。"
        return 1
    fi

    # 激活虚拟环境
    _activate_venv

    # 检查 gunicorn
    if ! command -v gunicorn &> /dev/null; then
        echo "📦 安装依赖..."
        bash "$(dirname "$0")/install_deps.sh"
    fi

    echo "🚀 启动排课系统（生产模式）..."
    cd "$APP_DIR"

    # 使用 gunicorn 自带的 --pid 确保 PID 准确
    # ⚠️ workers=1 + threads=2：
    #   - SQLite 不支持多进程并发写，多 worker 会导致 "database is locked" 崩溃
    #   - _task_store 是进程内 dict，多 worker 时异步任务状态轮询会 404
    #   - threads 模式让异步排课线程能与 HTTP 请求共享 _task_store
    # ⚠️ timeout=300：30轮排课算法可能需要几分钟，120s 会导致 worker 被杀
    gunicorn \
        --bind 0.0.0.0:5000 \
        --workers 1 \
        --threads 2 \
        --timeout 300 \
        --pid "$PID_FILE" \
        --daemon \
        --access-logfile "$LOG_DIR/access.log" \
        --error-logfile "$LOG_DIR/error.log" \
        "app:app"

    sleep 1

    if [ -f "$PID_FILE" ] && kill -0 "$(cat "$PID_FILE")" 2>/dev/null; then
        echo "✅ 启动成功 (PID: $(cat "$PID_FILE"))"
        echo "   访问地址: http://$(hostname -I 2>/dev/null | awk '{print $1}' || echo 'localhost'):5000"
        echo "   日志目录: $LOG_DIR"
    else
        echo "❌ 启动失败，查看日志: $LOG_DIR/error.log"
        rm -f "$PID_FILE"
        # 显示最后几行错误日志帮助排查
        if [ -f "$LOG_DIR/error.log" ]; then
            echo "--- 最近错误日志 ---"
            tail -10 "$LOG_DIR/error.log"
        fi
        return 1
    fi
}

stop() {
    # 检查是否作为 systemd 服务运行
    if command -v systemctl &>/dev/null && systemctl is-active --quiet paike 2>/dev/null; then
        echo "⚠️  警告：检测到 paike 服务正在通过 systemd 运行。"
        echo "💡 如果此脚本无法停止，请使用: sudo systemctl stop paike"
    fi

    if [ ! -f "$PID_FILE" ]; then
        echo "⚠️  PID文件不存在，尝试通过端口强力清理..."
        _kill_port 5000
        return 0
    fi
    PID=$(cat "$PID_FILE")
    echo "⏹️  正在停止服务 (PID: $PID)..."

    # 发送 TERM 信号让 gunicorn master 优雅关闭自身及所有 workers
    kill "$PID" 2>/dev/null
    # 等待最多 5 秒让进程优雅退出
    for i in $(seq 1 5); do
        if ! kill -0 "$PID" 2>/dev/null; then
            break
        fi
        sleep 1
    done

    # 若仍存活则强杀
    if kill -0 "$PID" 2>/dev/null; then
        echo "⚠️  进程未响应，尝试强制结束..."
        kill -9 "$PID" 2>/dev/null
        sleep 1
    fi
    rm -f "$PID_FILE"
    # 兜底：确认端口已释放
    _kill_port 5000
    echo "✅ 停止指令执行完毕"
}

restart() {
    stop
    sleep 1
    start
}

status() {
    if [ -f "$PID_FILE" ] && kill -0 "$(cat "$PID_FILE")" 2>/dev/null; then
        local pid=$(cat "$PID_FILE")
        echo "✅ 服务运行中 (PID: $pid)"
        # 显示 worker 信息
        local workers=$(pgrep -P "$pid" 2>/dev/null | wc -l)
        echo "   Workers: $workers"
        # 显示运行时间
        if [ -d "/proc/$pid" ]; then
            local uptime=$(ps -p "$pid" -o etime= 2>/dev/null | xargs)
            echo "   运行时间: $uptime"
        fi
        # 显示内存占用
        local mem=$(ps -p "$pid" -o rss= 2>/dev/null | xargs)
        if [ -n "$mem" ]; then
            echo "   内存占用: $((mem / 1024)) MB (master)"
        fi
    else
        echo "⏹️  服务未运行"
        rm -f "$PID_FILE" 2>/dev/null
    fi
}

logs() {
    local lines=${2:-50}
    if [ -f "$LOG_DIR/error.log" ]; then
        echo "--- 错误日志 (最近 $lines 行) ---"
        tail -n "$lines" "$LOG_DIR/error.log"
    else
        echo "暂无错误日志"
    fi
}

# ---------- 入口 ----------
case "${1:-start}" in
    start)   start   ;;
    stop)    stop    ;;
    restart) restart ;;
    status)  status  ;;
    logs)    logs "$@" ;;
    *)
        echo "用法: $0 {start|stop|restart|status|logs}"
        exit 1
        ;;
esac
