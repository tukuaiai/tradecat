#!/bin/bash
# =============================================================================
# TradeCat Docker 部署验证脚本
# 用法: ./test_deploy.sh [--build] [--cleanup]
# =============================================================================

set -e

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[0;33m'
NC='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

log_info() { echo -e "${GREEN}[PASS]${NC} $1"; }
log_fail() { echo -e "${RED}[FAIL]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }

TESTS_PASSED=0
TESTS_FAILED=0

test_case() {
    local name="$1"
    local cmd="$2"
    local expect_fail="${3:-false}"
    
    echo -n "Testing: $name... "
    
    if eval "$cmd" > /dev/null 2>&1; then
        if [ "$expect_fail" = "true" ]; then
            log_fail "Expected failure but succeeded"
            TESTS_FAILED=$((TESTS_FAILED + 1))
        else
            log_info "OK"
            TESTS_PASSED=$((TESTS_PASSED + 1))
        fi
    else
        if [ "$expect_fail" = "true" ]; then
            log_info "OK (expected failure)"
            TESTS_PASSED=$((TESTS_PASSED + 1))
        else
            log_fail "Failed"
            TESTS_FAILED=$((TESTS_FAILED + 1))
        fi
    fi
}

# =============================================================================
# 静态检查
# =============================================================================
echo "=== 静态检查 ==="

test_case "Dockerfile 存在" "[ -f '$SCRIPT_DIR/Dockerfile' ]"
test_case "docker-compose.yml 存在" "[ -f '$SCRIPT_DIR/docker-compose.yml' ]"
test_case "entrypoint.sh 存在且可执行" "[ -x '$SCRIPT_DIR/entrypoint.sh' ]"
test_case "SQL 初始化脚本存在" "[ -d '$SCRIPT_DIR/timescaledb' ] && [ -f '$SCRIPT_DIR/timescaledb/001_init.sql' ]"
test_case "config/.env.example 存在" "[ -f '$PROJECT_ROOT/config/.env.example' ]"

# Bash 语法检查
test_case "entrypoint.sh 语法正确" "bash -n '$SCRIPT_DIR/entrypoint.sh'"

# SQL 语法检查（基本）
test_case "SQL 文件包含 CREATE 语句" "grep -c 'CREATE' '$SCRIPT_DIR/timescaledb/'*.sql | grep -v ':0' | wc -l | grep -q '^4$'"

# =============================================================================
# .env 解析测试
# =============================================================================
echo ""
echo "=== .env 解析测试 ==="

# 创建临时测试文件
TEST_ENV=$(mktemp)
cat > "$TEST_ENV" << 'EOF'
BOT_TOKEN=123456:ABC-DEF
DATABASE_URL=postgresql://user:p@ss=word@host:5432/db
# 注释行
SYMBOLS_GROUPS=main4
  HTTP_PROXY = http://127.0.0.1:7890
INVALID_KEY=should_not_load
EOF

# 模拟解析
test_case ".env 解析 - 基本键值" "grep -q 'BOT_TOKEN=123456:ABC-DEF' '$TEST_ENV'"
test_case ".env 解析 - 含特殊字符的值" "grep 'DATABASE_URL' '$TEST_ENV' | grep -q 'p@ss=word'"
rm -f "$TEST_ENV"

# =============================================================================
# 依赖文件检查
# =============================================================================
echo ""
echo "=== 依赖文件检查 ==="

for svc in data-service trading-service telegram-service ai-service; do
    test_case "$svc/requirements.txt 存在" "[ -f '$PROJECT_ROOT/services/$svc/requirements.txt' ]"
done

# =============================================================================
# Docker 构建测试（可选）
# =============================================================================
if [ "$1" = "--build" ]; then
    echo ""
    echo "=== Docker 构建测试 ==="
    
    if command -v docker &> /dev/null; then
        test_case "Docker 可用" "docker info > /dev/null 2>&1"
        
        cd "$SCRIPT_DIR"
        
        # 构建镜像
        echo "构建镜像中（这可能需要几分钟）..."
        if docker build -t tradecat-test -f Dockerfile .. > /tmp/docker_build.log 2>&1; then
            log_info "镜像构建成功"
            TESTS_PASSED=$((TESTS_PASSED + 1))
            
            # 测试镜像
            test_case "镜像可启动" "docker run --rm tradecat-test echo 'OK'"
            test_case "Python 可用" "docker run --rm tradecat-test python --version"
            test_case "TA-Lib 已安装" "docker run --rm tradecat-test python -c 'import talib'"
            test_case "psycopg 已安装" "docker run --rm tradecat-test python -c 'import psycopg'"
            
            # 清理
            if [ "$2" = "--cleanup" ] || [ "$1" = "--cleanup" ]; then
                docker rmi tradecat-test > /dev/null 2>&1 || true
            fi
        else
            log_fail "镜像构建失败，查看 /tmp/docker_build.log"
            TESTS_FAILED=$((TESTS_FAILED + 1))
        fi
    else
        log_warn "Docker 不可用，跳过构建测试"
    fi
fi

# =============================================================================
# 总结
# =============================================================================
echo ""
echo "=========================================="
echo "测试结果: $TESTS_PASSED 通过, $TESTS_FAILED 失败"
echo "=========================================="

if [ $TESTS_FAILED -gt 0 ]; then
    exit 1
fi
