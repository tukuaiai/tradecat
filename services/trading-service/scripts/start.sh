#!/usr/bin/env bash
# trading-service 启动/守护脚本
# 用法: ./scripts/start.sh {start|stop|status|restart|daemon}

set -uo pipefail

# ==================== 配置区 ====================
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
SERVICE_DIR="$(dirname "$SCRIPT_DIR")"
PROJECT_ROOT="$(dirname "$(dirname "$SERVICE_DIR")")"
RUN_DIR="$SERVICE_DIR/pids"
LOG_DIR="$SERVICE_DIR/logs"
DAEMON_PID="$RUN_DIR/daemon.pid"
DAEMON_LOG="$LOG_DIR/daemon.log"
SERVICE_PID="$RUN_DIR/service.pid"
SERVICE_LOG="$LOG_DIR/service.log"
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

# 加载全局配置 → 服务配置
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

# 启动命令
MODE="${MODE:-simple}"
START_CMD="python3 -u src/simple_scheduler.py"
[ "$MODE" = "listener" ] && START_CMD="python3 -u src/kline_listener.py"

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

get_service_pid() {
    [ -f "$SERVICE_PID" ] && cat "$SERVICE_PID"
}

# ==================== 服务管理 ====================
start_service() {
    init_dirs
    local pid=$(get_service_pid)
    if is_running "$pid"; then
        echo "✓ 服务已运行 (PID: $pid)"
        return 0
    fi
    
    cd "$SERVICE_DIR"
    source .venv/bin/activate
    export PYTHONPATH=src
    nohup $START_CMD >> "$SERVICE_LOG" 2>&1 &
    local new_pid=$!
    echo "$new_pid" > "$SERVICE_PID"
    
    sleep 1
    if is_running "$new_pid"; then
        log "START 服务 (PID: $new_pid, MODE: $MODE)"
        echo "✓ 服务已启动 (PID: $new_pid, MODE: $MODE)"
        return 0
    else
        log "ERROR 服务启动失败"
        echo "✗ 服务启动失败"
        return 1
    fi
}

stop_service() {
    local pid=$(get_service_pid)
    if ! is_running "$pid"; then
        echo "服务未运行"
        rm -f "$SERVICE_PID"
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
        log "KILL 服务 (PID: $pid) 强制终止"
    else
        log "STOP 服务 (PID: $pid)"
    fi
    
    rm -f "$SERVICE_PID"
    echo "✓ 服务已停止"
}

status_service() {
    local pid=$(get_service_pid)
    if is_running "$pid"; then
        local uptime=$(ps -o etime= -p "$pid" 2>/dev/null | tr -d ' ')
        echo "✓ 服务运行中 (PID: $pid, 运行: $uptime)"
        echo ""
        echo "=== 最近日志 ==="
        tail -10 "$SERVICE_LOG" 2>/dev/null
    else
        echo "✗ 服务未运行"
    fi
}

# ==================== 入口 ====================
case "${1:-status}" in
    start)   start_service ;;
    stop)    stop_service ;;
    status)  status_service ;;
    restart) stop_service; sleep 2; start_service ;;
    *)
        echo "用法: $0 {start|stop|status|restart}"
        exit 1
        ;;
esac
