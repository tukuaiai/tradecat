#!/usr/bin/env bash
# data-service 启动/守护一体脚本
# 用法: ./scripts/start.sh {start|stop|status|daemon}

set -uo pipefail

# ==================== 配置区 ====================
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
SERVICE_DIR="$(dirname "$SCRIPT_DIR")"
RUN_DIR="$SERVICE_DIR/pids"
LOG_DIR="$SERVICE_DIR/logs"
DAEMON_PID="$RUN_DIR/daemon.pid"
DAEMON_LOG="$LOG_DIR/daemon.log"
CHECK_INTERVAL="${CHECK_INTERVAL:-30}"
STOP_TIMEOUT=10

# 加载环境变量
if [ -f "$SERVICE_DIR/config/.env" ]; then
    set -a
    source "$SERVICE_DIR/config/.env"
    set +a
fi

# 服务组件
COMPONENTS=(backfill metrics ws)

# 启动命令
declare -A START_CMDS=(
    [backfill]="python3 -m collectors.backfill --all --lookback 7"
    [metrics]="python3 -c \"
import time, logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
from collectors.metrics import MetricsCollector
c = MetricsCollector()
while True:
    try:
        c.run_once()
    except Exception as e:
        logging.error('Metrics error: %s', e)
    time.sleep(300)
\""
    [ws]="python3 -m collectors.ws"
)

# ==================== 工具函数 ====================
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" | tee -a "$DAEMON_LOG"
}

init_dirs() {
    mkdir -p "$RUN_DIR" "$LOG_DIR"
}

read_pid() {
    local pid_file="$1"
    [ -f "$pid_file" ] && cat "$pid_file" || echo ""
}

is_running() {
    local pid="$1"
    [ -n "$pid" ] && kill -0 "$pid" 2>/dev/null
}

get_uptime() {
    local pid="$1"
    if is_running "$pid"; then
        local start_time=$(ps -o lstart= -p "$pid" 2>/dev/null)
        if [ -n "$start_time" ]; then
            local start_sec=$(date -d "$start_time" +%s 2>/dev/null)
            local now_sec=$(date +%s)
            local diff=$((now_sec - start_sec))
            printf "%dd %dh %dm" $((diff/86400)) $((diff%86400/3600)) $((diff%3600/60))
        fi
    fi
}

# ==================== 服务控制 ====================
start_component() {
    local name="$1"
    local pid_file="$RUN_DIR/${name}.pid"
    local log_file="$LOG_DIR/${name}.log"
    local pid=$(read_pid "$pid_file")
    
    if is_running "$pid"; then
        echo "  $name: 已运行 (PID: $pid)"
        return 0
    fi
    
    cd "$SERVICE_DIR"
    source .venv/bin/activate
    export PYTHONPATH=src
    nohup bash -c "${START_CMDS[$name]}" >> "$log_file" 2>&1 &
    local new_pid=$!
    echo "$new_pid" > "$pid_file"
    
    sleep 1
    if is_running "$new_pid"; then
        log "START $name (PID: $new_pid)"
        echo "  $name: 已启动 (PID: $new_pid)"
        return 0
    else
        log "ERROR $name 启动失败"
        echo "  $name: 启动失败"
        rm -f "$pid_file"
        return 1
    fi
}

stop_component() {
    local name="$1"
    local pid_file="$RUN_DIR/${name}.pid"
    local pid=$(read_pid "$pid_file")
    
    if ! is_running "$pid"; then
        rm -f "$pid_file"
        echo "  $name: 未运行"
        return 0
    fi
    
    # 优雅停止
    kill -TERM "$pid" 2>/dev/null
    local waited=0
    while is_running "$pid" && [ $waited -lt $STOP_TIMEOUT ]; do
        sleep 1
        ((waited++))
    done
    
    # 强制停止
    if is_running "$pid"; then
        kill -KILL "$pid" 2>/dev/null
        log "KILL $name (PID: $pid) 强制终止"
    else
        log "STOP $name (PID: $pid)"
    fi
    
    rm -f "$pid_file"
    echo "  $name: 已停止"
}

# ==================== 批量操作 ====================
start_all() {
    echo "=== 启动全部服务 ==="
    for name in "${COMPONENTS[@]}"; do
        start_component "$name"
    done
}

stop_all() {
    echo "=== 停止全部服务 ==="
    for name in "${COMPONENTS[@]}"; do
        stop_component "$name"
    done
}

status_all() {
    echo "=== 服务状态 ==="
    for name in "${COMPONENTS[@]}"; do
        local pid_file="$RUN_DIR/${name}.pid"
        local pid=$(read_pid "$pid_file")
        if is_running "$pid"; then
            local uptime=$(get_uptime "$pid")
            echo "  ✓ $name: 运行中 (PID: $pid, 运行: $uptime)"
        else
            [ -f "$pid_file" ] && rm -f "$pid_file"
            echo "  ✗ $name: 未运行"
        fi
    done
}

# ==================== 守护进程 ====================
monitor_loop() {
    log "=== 守护进程启动 (间隔: ${CHECK_INTERVAL}s) ==="
    while true; do
        for name in "${COMPONENTS[@]}"; do
            local pid_file="$RUN_DIR/${name}.pid"
            local pid=$(read_pid "$pid_file")
            if ! is_running "$pid"; then
                [ -f "$pid_file" ] && rm -f "$pid_file"
                log "CHECK $name 未运行，重启..."
                start_component "$name" > /dev/null
            fi
        done
        sleep "$CHECK_INTERVAL"
    done
}

daemon_start() {
    local pid=$(read_pid "$DAEMON_PID")
    if is_running "$pid"; then
        echo "守护进程已运行 (PID: $pid)"
        return 0
    fi
    
    init_dirs
    start_all
    
    nohup "$0" _monitor >> "$DAEMON_LOG" 2>&1 &
    echo $! > "$DAEMON_PID"
    echo "守护进程已启动 (PID: $!)"
}

daemon_stop() {
    local pid=$(read_pid "$DAEMON_PID")
    if is_running "$pid"; then
        kill -TERM "$pid" 2>/dev/null
        rm -f "$DAEMON_PID"
        log "STOP 守护进程 (PID: $pid)"
        echo "守护进程已停止"
    else
        rm -f "$DAEMON_PID"
        echo "守护进程未运行"
    fi
    stop_all
}

daemon_status() {
    local pid=$(read_pid "$DAEMON_PID")
    if is_running "$pid"; then
        local uptime=$(get_uptime "$pid")
        echo "守护进程: 运行中 (PID: $pid, 运行: $uptime)"
    else
        [ -f "$DAEMON_PID" ] && rm -f "$DAEMON_PID"
        echo "守护进程: 未运行"
    fi
    status_all
}

# ==================== 入口 ====================
init_dirs
cd "$SERVICE_DIR"

case "${1:-help}" in
    start)    start_all ;;
    stop)     stop_all ;;
    status)   status_all ;;
    restart)  stop_all; sleep 1; start_all ;;
    daemon)   daemon_start ;;
    daemon-stop) daemon_stop ;;
    daemon-status) daemon_status ;;
    _monitor) monitor_loop ;;
    backfill|metrics|ws) start_component "$1" ;;
    *)
        echo "用法: $0 {start|stop|status|restart|daemon|daemon-stop|daemon-status}"
        echo ""
        echo "  start         启动全部服务"
        echo "  stop          停止全部服务"
        echo "  status        查看状态"
        echo "  restart       重启全部"
        echo "  daemon        启动 + 守护（自动重启挂掉的服务）"
        echo "  daemon-stop   停止守护 + 全部服务"
        echo "  daemon-status 查看守护进程和服务状态"
        echo ""
        echo "单独启动: $0 {backfill|metrics|ws}"
        exit 1
        ;;
esac
