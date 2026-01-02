#!/usr/bin/env bash
# data-service 启动/守护脚本
# 用法: ./scripts/start.sh {start|stop|status|restart}

set -uo pipefail

# ==================== 配置区 ====================
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
SERVICE_DIR="$(dirname "$SCRIPT_DIR")"
PROJECT_ROOT="$(dirname "$(dirname "$SERVICE_DIR")")"
RUN_DIR="$SERVICE_DIR/pids"
LOG_DIR="$SERVICE_DIR/logs"
DAEMON_PID="$RUN_DIR/daemon.pid"
DAEMON_LOG="$LOG_DIR/daemon.log"
CHECK_INTERVAL="${CHECK_INTERVAL:-30}"
STOP_TIMEOUT=10

# 安全加载 .env（只读键值解析，拒绝危险行）
safe_load_env() {
    local file="$1"
    [ -f "$file" ] || return 0
    
    # 检查权限（生产环境强制 600）
    if [[ "$file" == *"config/.env" ]] && [[ ! "$file" == *".example" ]]; then
        local perm=$(stat -c %a "$file" 2>/dev/null)
        if [[ "$perm" != "600" && "$perm" != "400" ]]; then
            echo "❌ 错误: $file 权限为 $perm，必须设为 600"
            echo "   执行: chmod 600 $file"
            exit 1
        fi
    fi
    
    while IFS= read -r line || [[ -n "$line" ]]; do
        [[ -z "$line" || "$line" =~ ^[[:space:]]*# ]] && continue
        [[ "$line" =~ ^[[:space:]]*export ]] && continue
        [[ "$line" =~ \$\( ]] && continue
        [[ "$line" =~ \` ]] && continue
        if [[ "$line" =~ ^([A-Za-z_][A-Za-z0-9_]*)=(.*)$ ]]; then
            local key="${BASH_REMATCH[1]}"
            local val="${BASH_REMATCH[2]}"
            val="${val#\"}" && val="${val%\"}"
            val="${val#\'}" && val="${val%\'}"
            export "$key=$val"
        fi
    done < "$file"
}

# 加载全局配置 → 服务配置（后者覆盖）
safe_load_env "$PROJECT_ROOT/config/.env"
safe_load_env "$SERVICE_DIR/config/.env"

# 校验 SYMBOLS_* 格式
validate_symbols() {
    local errors=0
    for var in $(env | grep -E '^SYMBOLS_(GROUP_|EXTRA|EXCLUDE)' | cut -d= -f1); do
        local val="${!var}"
        [ -z "$val" ] && continue
        for sym in ${val//,/ }; do
            sym="${sym^^}"
            if [[ ! "$sym" =~ ^[A-Z0-9]+USDT$ ]]; then
                echo "❌ 无效币种 $var: $sym"
                errors=1
            fi
        done
    done
    [ $errors -eq 1 ] && exit 1
}
validate_symbols

# 代理自检（同时检测 HTTP_PROXY 和 HTTPS_PROXY）
check_proxy() {
    local proxy="${HTTP_PROXY:-${HTTPS_PROXY:-}}"
    [ -z "$proxy" ] && return 0
    
    if curl -s --max-time 3 --proxy "$proxy" https://api.binance.com/api/v3/ping >/dev/null 2>&1; then
        echo "✓ 代理可用: $proxy"
    else
        echo "⚠️  代理不可用，已禁用: $proxy"
        unset HTTP_PROXY HTTPS_PROXY http_proxy https_proxy
    fi
}
check_proxy

# 组件定义
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
    c.run_once()
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

is_running() {
    local pid=$1
    [ -n "$pid" ] && kill -0 "$pid" 2>/dev/null
}

get_pid() {
    local name=$1
    local pid_file="$RUN_DIR/${name}.pid"
    [ -f "$pid_file" ] && cat "$pid_file"
}

# ==================== 组件管理 ====================
start_component() {
    local name=$1
    local pid_file="$RUN_DIR/${name}.pid"
    local log_file="$LOG_DIR/${name}.log"
    
    local pid=$(get_pid "$name")
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
        return 1
    fi
}

stop_component() {
    local name=$1
    local pid_file="$RUN_DIR/${name}.pid"
    local pid=$(get_pid "$name")
    
    if ! is_running "$pid"; then
        echo "  $name: 未运行"
        rm -f "$pid_file"
        return 0
    fi
    
    kill "$pid" 2>/dev/null
    local waited=0
    while is_running "$pid" && [ $waited -lt $STOP_TIMEOUT ]; do
        sleep 1
        ((waited++))
    done
    
    if is_running "$pid"; then
        kill -9 "$pid" 2>/dev/null
        log "KILL $name (PID: $pid) 强制终止"
    else
        log "STOP $name (PID: $pid)"
    fi
    
    rm -f "$pid_file"
    echo "  $name: 已停止"
}

status_component() {
    local name=$1
    local pid=$(get_pid "$name")
    
    if is_running "$pid"; then
        local uptime=$(ps -o etime= -p "$pid" 2>/dev/null | tr -d ' ')
        echo "  ✓ $name: 运行中 (PID: $pid, 运行: $uptime)"
    else
        echo "  ✗ $name: 未运行"
    fi
}

# ==================== 主命令 ====================
cmd_start() {
    init_dirs
    echo "=== 启动全部服务 ==="
    for name in "${COMPONENTS[@]}"; do
        start_component "$name"
    done
}

cmd_stop() {
    echo "=== 停止全部服务 ==="
    for name in "${COMPONENTS[@]}"; do
        stop_component "$name"
    done
}

cmd_status() {
    echo "=== 服务状态 ==="
    for name in "${COMPONENTS[@]}"; do
        status_component "$name"
    done
}

cmd_restart() {
    cmd_stop
    sleep 2
    cmd_start
}

# ==================== 入口 ====================
case "${1:-status}" in
    start)   cmd_start ;;
    stop)    cmd_stop ;;
    status)  cmd_status ;;
    restart) cmd_restart ;;
    *)
        echo "用法: $0 {start|stop|status|restart}"
        exit 1
        ;;
esac
