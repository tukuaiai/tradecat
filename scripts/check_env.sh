#!/usr/bin/env bash
# tradecat 环境检查脚本
# 用法: ./scripts/check_env.sh
# 检查所有运行依赖，确保"安装即运行"

set -e

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

# ==================== 工具函数 ====================
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m'

success() { echo -e "${GREEN}✓${NC} $1"; }
fail() { echo -e "${RED}✗${NC} $1"; ERRORS=$((ERRORS + 1)); }
warn() { echo -e "${YELLOW}⚠${NC} $1"; WARNINGS=$((WARNINGS + 1)); }
info() { echo -e "${BLUE}→${NC} $1"; }

ERRORS=0
WARNINGS=0

# ==================== 1. Python 环境 ====================
check_python() {
    echo ""
    echo "=== Python 环境 ==="
    
    # Python 版本
    if command -v python3 &>/dev/null; then
        local py_ver=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}')")
        local py_major=$(python3 -c "import sys; print(sys.version_info.major)")
        local py_minor=$(python3 -c "import sys; print(sys.version_info.minor)")
        
        if [ "$py_major" -ge 3 ] && [ "$py_minor" -ge 10 ]; then
            success "Python: $py_ver"
        else
            fail "Python 版本需要 3.10+，当前: $py_ver"
        fi
    else
        fail "Python3 未安装"
        return 1
    fi
    
    # pip
    if python3 -m pip --version &>/dev/null; then
        local pip_ver=$(python3 -m pip --version | cut -d' ' -f2)
        success "pip: $pip_ver"
    else
        fail "pip 未安装"
    fi
    
    # venv
    if python3 -m venv --help &>/dev/null; then
        success "venv: 可用"
    else
        fail "venv 模块不可用，请安装: sudo apt install python3-venv"
    fi
}

# ==================== 2. 系统依赖 ====================
check_system_deps() {
    echo ""
    echo "=== 系统依赖 ==="
    
    # Git
    if command -v git &>/dev/null; then
        success "git: $(git --version | cut -d' ' -f3)"
    else
        warn "git 未安装 (版本控制不可用)"
    fi
    
    # PostgreSQL client
    if command -v psql &>/dev/null; then
        success "psql: $(psql --version 2>&1 | head -1 | grep -oP '\d+\.\d+')"
    else
        warn "psql 未安装 (数据库操作受限)"
        echo "      安装: sudo apt install postgresql-client"
    fi
    
    # curl
    if command -v curl &>/dev/null; then
        success "curl: 已安装"
    else
        fail "curl 未安装"
    fi
    
    # TA-Lib (可选)
    if python3 -c "import talib" 2>/dev/null; then
        success "TA-Lib: 已安装"
    else
        info "TA-Lib: 未安装 (K线形态检测不可用)"
    fi
}

# ==================== 3. 虚拟环境 ====================
check_venvs() {
    echo ""
    echo "=== 虚拟环境 ==="
    
    local services=(data-service trading-service telegram-service ai-service signal-service)
    
    for svc in "${services[@]}"; do
        local svc_dir="$ROOT/services/$svc"
        if [ -d "$svc_dir/.venv" ] && [ -f "$svc_dir/.venv/bin/python" ]; then
            success "$svc: .venv 存在"
        else
            if [ -d "$svc_dir" ]; then
                fail "$svc: .venv 缺失 (运行 ./scripts/init.sh $svc)"
            else
                info "$svc: 服务目录不存在"
            fi
        fi
    done
}

# ==================== 4. 配置文件 ====================
check_config() {
    echo ""
    echo "=== 配置文件 ==="
    
    local config_file="$ROOT/config/.env"
    
    if [ -f "$config_file" ]; then
        # 权限检查
        local perms=$(stat -c %a "$config_file" 2>/dev/null || stat -f %Lp "$config_file" 2>/dev/null)
        if [ "$perms" = "600" ] || [ "$perms" = "400" ]; then
            success "config/.env: 权限 $perms"
        else
            warn "config/.env: 权限 $perms (建议 600)"
        fi
        
        # 必填字段检查
        local required_keys=(BOT_TOKEN DATABASE_URL)
        for key in "${required_keys[@]}"; do
            local value=$(grep "^${key}=" "$config_file" | cut -d= -f2- | tr -d '"' | tr -d "'")
            if [ -n "$value" ] && [ "$value" != "your_token_here" ]; then
                success "$key: 已配置"
            else
                fail "$key: 未配置或为默认值"
            fi
        done
        
        # 代理配置
        local http_proxy=$(grep "^HTTP_PROXY=" "$config_file" | cut -d= -f2- | tr -d '"' | tr -d "'")
        if [ -n "$http_proxy" ]; then
            if curl -s --connect-timeout 3 -x "$http_proxy" https://api.telegram.org -o /dev/null 2>/dev/null; then
                success "HTTP_PROXY: $http_proxy (可用)"
            else
                warn "HTTP_PROXY: $http_proxy (连接失败)"
            fi
        else
            info "HTTP_PROXY: 未配置"
        fi

        # 信号服务新鲜度/冷却（可选）
        local signal_age=$(grep "^SIGNAL_DATA_MAX_AGE=" "$config_file" | cut -d= -f2- | tr -d '"' | tr -d "'")
        if [ -n "$signal_age" ]; then
            success "SIGNAL_DATA_MAX_AGE: $signal_age 秒"
        else
            warn "SIGNAL_DATA_MAX_AGE: 未配置，默认 600 秒"
        fi

        local pg_cooldown=$(grep "^COOLDOWN_SECONDS=" "$config_file" | cut -d= -f2- | tr -d '"' | tr -d "'")
        if [ -n "$pg_cooldown" ]; then
            success "COOLDOWN_SECONDS: $pg_cooldown 秒"
        else
            info "COOLDOWN_SECONDS: 未配置，使用代码默认值"
        fi
    else
        fail "config/.env 不存在"
        echo "      创建: cp config/.env.example config/.env && chmod 600 config/.env"
    fi
}

# ==================== 5. 数据库连接 ====================
check_database() {
    echo ""
    echo "=== 数据库连接 ==="
    
    local config_file="$ROOT/config/.env"
    if [ ! -f "$config_file" ]; then
        info "跳过 (config/.env 不存在)"
        return 0
    fi
    
    local db_url=$(grep "^DATABASE_URL=" "$config_file" | cut -d= -f2- | tr -d '"' | tr -d "'")
    if [ -z "$db_url" ]; then
        fail "DATABASE_URL 未配置"
        return 1
    fi
    
    # 解析连接信息
    local db_host=$(echo "$db_url" | sed -n 's|.*@\([^:/]*\).*|\1|p')
    local db_port=$(echo "$db_url" | grep -oP ':\K\d+(?=/)' || echo "5432")
    local db_name=$(echo "$db_url" | grep -oP '/\K[^?]+' || echo "market_data")
    
    [ -z "$db_host" ] && db_host="localhost"
    
    info "连接: $db_host:$db_port/$db_name"
    
    # pg_isready 检查
    if command -v pg_isready &>/dev/null; then
        if pg_isready -h "$db_host" -p "$db_port" -q 2>/dev/null; then
            success "PostgreSQL: 服务可达"
        else
            fail "PostgreSQL: $db_host:$db_port 无法连接"
            return 1
        fi
    else
        warn "pg_isready 不可用，跳过连接检查"
        return 0
    fi
    
    # 表检查
    local db_user=$(echo "$db_url" | sed -n 's|.*//\([^:]*\):.*|\1|p')
    local db_pass=$(echo "$db_url" | sed -n 's|.*:\([^@]*\)@.*|\1|p')
    
    if [ -n "$db_user" ] && [ -n "$db_pass" ]; then
        if PGPASSWORD="$db_pass" psql -h "$db_host" -p "$db_port" -U "$db_user" -d "$db_name" \
            -c "SELECT 1 FROM market_data.candles_1m LIMIT 1" -q 2>/dev/null; then
            success "数据表: candles_1m 存在"
        else
            warn "数据表: candles_1m 不存在或无数据"
            echo "      请导入 schema: psql -f libs/database/db/schema/*.sql"
        fi
    fi
}

# ==================== 6. 网络连接 ====================
check_network() {
    echo ""
    echo "=== 网络连接 ==="
    
    local config_file="$ROOT/config/.env"
    local proxy=""
    
    if [ -f "$config_file" ]; then
        proxy=$(grep "^HTTP_PROXY=" "$config_file" | cut -d= -f2- | tr -d '"' | tr -d "'")
    fi
    
    local curl_opts="-s --connect-timeout 5"
    [ -n "$proxy" ] && curl_opts="$curl_opts -x $proxy"
    
    # Telegram API
    if eval "curl $curl_opts https://api.telegram.org -o /dev/null" 2>/dev/null; then
        success "Telegram API: 可达"
    else
        fail "Telegram API: 无法连接 (检查代理配置)"
    fi
    
    # Binance API
    if eval "curl $curl_opts https://api.binance.com/api/v3/ping -o /dev/null" 2>/dev/null; then
        success "Binance API: 可达"
    else
        warn "Binance API: 无法连接"
    fi
}

# ==================== 7. 数据目录 ====================
check_data_dirs() {
    echo ""
    echo "=== 数据目录 ==="
    
    local dirs=(
        "$ROOT/libs/database/services/telegram-service"
        "$ROOT/services/telegram-service/data/cache"
        "$ROOT/services/data-service/logs"
        "$ROOT/services/trading-service/logs"
        "$ROOT/services/telegram-service/logs"
    )
    
    for dir in "${dirs[@]}"; do
        if [ -d "$dir" ]; then
            success "$(basename $(dirname $dir))/$(basename $dir): 存在"
        else
            warn "$dir: 不存在"
        fi
    done
    
    # SQLite 数据库
    local sqlite_db="$ROOT/libs/database/services/telegram-service/market_data.db"
    if [ -f "$sqlite_db" ]; then
        local size=$(du -h "$sqlite_db" | cut -f1)
        success "market_data.db: $size"
    else
        info "market_data.db: 不存在 (首次启动会创建)"
    fi
}

# ==================== 8. 磁盘空间 ====================
check_disk_space() {
    echo ""
    echo "=== 磁盘空间 ==="
    
    local available=$(df -h "$ROOT" | tail -1 | awk '{print $4}')
    local used_pct=$(df -h "$ROOT" | tail -1 | awk '{print $5}' | tr -d '%')
    
    if [ "$used_pct" -lt 90 ]; then
        success "可用空间: $available (使用率: $used_pct%)"
    else
        warn "磁盘空间不足: $available (使用率: $used_pct%)"
    fi
}

# ==================== 主程序 ====================
main() {
    echo "=========================================="
    echo "  TradeCat 环境检查"
    echo "=========================================="
    echo "  项目路径: $ROOT"
    echo "  检查时间: $(date '+%Y-%m-%d %H:%M:%S')"
    
    check_python
    check_system_deps
    check_venvs
    check_config
    check_database
    check_network
    check_data_dirs
    check_disk_space
    
    echo ""
    echo "=========================================="
    if [ $ERRORS -gt 0 ]; then
        echo -e "${RED}检查完成: $ERRORS 个错误, $WARNINGS 个警告${NC}"
        echo "请修复上述错误后再启动服务"
        exit 1
    elif [ $WARNINGS -gt 0 ]; then
        echo -e "${YELLOW}检查完成: $WARNINGS 个警告${NC}"
        echo "建议修复警告项以获得最佳体验"
        exit 0
    else
        echo -e "${GREEN}检查完成: 所有项目通过${NC}"
        echo "可以启动服务: ./scripts/start.sh start"
        exit 0
    fi
}

main "$@"
