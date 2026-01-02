#!/usr/bin/env bash
# tradecat 统一启动脚本
# 用法: ./scripts/start.sh {start|stop|status|restart}

set -uo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SERVICES=(data-service trading-service telegram-service)

start_all() {
    echo "=== 启动全部服务 ==="
    for svc in "${SERVICES[@]}"; do
        cd "$ROOT/services/$svc"
        ./scripts/start.sh start 2>&1 | sed "s/^/  [$svc] /"
    done
}

stop_all() {
    echo "=== 停止全部服务 ==="
    for svc in "${SERVICES[@]}"; do
        cd "$ROOT/services/$svc"
        ./scripts/start.sh stop 2>&1 | sed "s/^/  [$svc] /"
    done
}

status_all() {
    echo "=== 服务状态 ==="
    for svc in "${SERVICES[@]}"; do
        cd "$ROOT/services/$svc"
        ./scripts/start.sh status 2>&1 | sed "s/^/  [$svc] /"
        echo ""
    done
}

case "${1:-status}" in
    start)   start_all ;;
    stop)    stop_all ;;
    status)  status_all ;;
    restart) stop_all; sleep 2; start_all ;;
    *)
        echo "用法: $0 {start|stop|status|restart}"
        exit 1
        ;;
esac
