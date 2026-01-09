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
            if [[ "${CODESPACES:-}" == "true" ]]; then
                echo "⚠️  Codespace 环境，跳过权限检查 ($file: $perm)"
            else
                echo "❌ 错误: $file 权限为 $perm，必须设为 600"
                echo "   执行: chmod 600 $file"
                exit 1
            fi
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
# 配置已统一到 config/.env

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

# 代理自检（重试3次+指数退避冷却）
check_proxy() {
    local proxy="${HTTP_PROXY:-${HTTPS_PROXY:-}}"
    [ -z "$proxy" ] && return 0
    
    local retries=3
    local delay=1
    local i=0
    
    while [ $i -lt $retries ]; do
        if curl -s --max-time 3 --proxy "$proxy" https://api.binance.com/api/v3/ping >/dev/null 2>&1; then
            echo "✓ 代理可用: $proxy"
            return 0
        fi
        ((i++))
        if [ $i -lt $retries ]; then
            echo "  代理检测失败，${delay}秒后重试 ($i/$retries)..."
            sleep $delay
            delay=$((delay * 2))  # 指数退避: 1s, 2s, 4s
        fi
    done
    
    echo "⚠️  代理不可用（重试${retries}次失败），已禁用: $proxy"
    unset HTTP_PROXY HTTPS_PROXY http_proxy https_proxy
}
check_proxy

# 组件定义
COMPONENTS=(backfill metrics ws)

# 启动命令
declare -A START_CMDS=(
[backfill]="python3 -c \"
import time, logging, sys
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(name)s - %(message)s')
logger = logging.getLogger('backfill.patrol')
from collectors.backfill import DataBackfiller, get_backfill_config, compute_lookback

mode, env_days, on_start, start_date = get_backfill_config()
lookback = compute_lookback(mode, env_days, start_date)

if lookback <= 0:
    logger.info('BACKFILL_MODE=none，跳过巡检')
    sys.exit(0)

logger.info('补齐巡检启动: mode=%s lookback=%d days', mode, lookback)
bf = DataBackfiller(lookback_days=lookback)

if on_start:
    try:
        logger.info('启动时执行一次全量补齐...')
        result = bf.run_all()
        logger.info('启动补齐完成: %s', result)
    except Exception as e:
        logger.error('启动补齐异常: %s', e, exc_info=True)

while True:
    try:
        logger.info('开始缺口巡检...')
        result = bf.run_all()
        klines = result.get('klines', {})
        metrics = result.get('metrics', {})
        logger.info('巡检完成: K线填充 %d 条, Metrics填充 %d 条, 5分钟后再次检查',
                    klines.get('filled', 0), metrics.get('filled', 0))
    except Exception as e:
        logger.error('巡检异常: %s', e, exc_info=True)
    time.sleep(300)
\""
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

# ==================== 守护进程 ====================
daemon_loop() {
    log "守护进程启动 (检查间隔: ${CHECK_INTERVAL}s)"
    while true; do
        for name in "${COMPONENTS[@]}"; do
            local pid=$(get_pid "$name")
            if ! is_running "$pid"; then
                log "检测到 $name 未运行，重启..."
                start_component "$name" >/dev/null
            fi
        done
        sleep "$CHECK_INTERVAL"
    done
}

cmd_daemon() {
    init_dirs
    
    # 检查是否已有守护进程
    if [ -f "$DAEMON_PID" ]; then
        local pid=$(cat "$DAEMON_PID")
        if is_running "$pid"; then
            echo "守护进程已运行 (PID: $pid)"
            return 0
        fi
    fi
    
    # 先启动所有服务
    echo "=== 启动守护模式 ==="
    for name in "${COMPONENTS[@]}"; do
        start_component "$name"
    done
    
    # 后台启动守护循环
    daemon_loop &
    echo $! > "$DAEMON_PID"
    log "守护进程已启动 (PID: $!)"
    echo "守护进程已启动 (PID: $!)"
}

cmd_stop() {
    echo "=== 停止全部服务 ==="
    
    # 先停守护进程
    if [ -f "$DAEMON_PID" ]; then
        local dpid=$(cat "$DAEMON_PID")
        if is_running "$dpid"; then
            kill "$dpid" 2>/dev/null
            log "STOP daemon (PID: $dpid)"
            echo "  daemon: 已停止"
        fi
        rm -f "$DAEMON_PID"
    fi
    
    for name in "${COMPONENTS[@]}"; do
        stop_component "$name"
    done
}

# ==================== 主命令 ====================
cmd_start() {
    # 默认就是守护模式
    cmd_daemon
}

cmd_status() {
    echo "=== 服务状态 ==="
    
    # 守护进程状态
    if [ -f "$DAEMON_PID" ]; then
        local dpid=$(cat "$DAEMON_PID")
        if is_running "$dpid"; then
            echo "  ✓ daemon: 运行中 (PID: $dpid)"
        else
            echo "  ✗ daemon: 未运行"
        fi
    else
        echo "  ✗ daemon: 未运行"
    fi
    
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
