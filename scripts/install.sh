#!/bin/bash
# tradecat 一键安装脚本
set -e

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[0;33m'
NC='\033[0m'

ROOT=$(cd "$(dirname "$0")" && pwd)
echo -e "${GREEN}🐱 tradecat 一键安装${NC}"
echo "安装目录: $ROOT"

# ========== 1. 检查系统依赖 ==========
echo -e "\n${YELLOW}[1/6] 检查系统依赖...${NC}"

check_cmd() {
    command -v "$1" &>/dev/null || { echo -e "${RED}❌ 未安装 $1${NC}"; return 1; }
    echo -e "  ✅ $1"
}

check_cmd python3 || { echo "请先安装 Python 3.10+"; exit 1; }
check_cmd pip3 || { echo "请先安装 pip"; exit 1; }

# 检查 Python 版本
PY_VER=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
if [[ $(echo "$PY_VER < 3.10" | bc -l) -eq 1 ]]; then
    echo -e "${RED}❌ Python 版本需要 3.10+，当前: $PY_VER${NC}"
    exit 1
fi
echo -e "  ✅ Python $PY_VER"

# ========== 2. 创建虚拟环境 ==========
echo -e "\n${YELLOW}[2/6] 创建虚拟环境...${NC}"

if [ ! -d "$ROOT/.venv" ]; then
    python3 -m venv "$ROOT/.venv"
    echo -e "  ✅ 虚拟环境已创建"
else
    echo -e "  ⏭️ 虚拟环境已存在"
fi

source "$ROOT/.venv/bin/activate"

# ========== 3. 安装 Python 依赖 ==========
echo -e "\n${YELLOW}[3/6] 安装 Python 依赖...${NC}"

pip install --upgrade pip -q

# data-service
echo "  📦 data-service..."
pip install -e "$ROOT/services/data-service" -q 2>/dev/null || \
pip install cryptofeed ccxt psycopg[binary] psycopg-pool requests python-dotenv -q

# trading-service
echo "  📦 trading-service..."
pip install -e "$ROOT/services/trading-service" -q 2>/dev/null || \
pip install pandas numpy ta-lib -q 2>/dev/null || pip install pandas numpy -q

# telegram-service
echo "  📦 telegram-service..."
pip install python-telegram-bot httpx aiohttp -q

echo -e "  ✅ Python 依赖安装完成"

# ========== 4. 配置环境变量 ==========
echo -e "\n${YELLOW}[4/6] 配置环境变量...${NC}"

setup_env() {
    local dir=$1
    local name=$2
    if [ -f "$dir/.env.example" ] && [ ! -f "$dir/.env" ]; then
        cp "$dir/.env.example" "$dir/.env"
        echo -e "  ✅ $name/.env 已创建（请编辑配置）"
    elif [ -f "$dir/.env" ]; then
        echo -e "  ⏭️ $name/.env 已存在"
    fi
}

setup_env "$ROOT/services/data-service" "data-service"
setup_env "$ROOT/services/trading-service" "trading-service"
setup_env "$ROOT/services/telegram-service" "telegram-service"

# ========== 5. 创建数据目录 ==========
echo -e "\n${YELLOW}[5/6] 创建数据目录...${NC}"

mkdir -p "$ROOT/services/data-service/logs"
mkdir -p "$ROOT/services/data-service/pids"
mkdir -p "$ROOT/services/trading-service/logs"
mkdir -p "$ROOT/services/telegram-service/logs"
mkdir -p "$ROOT/services/telegram-service/data/cache"
mkdir -p "$ROOT/libs/database/db/state"

echo -e "  ✅ 数据目录已创建"

# ========== 6. 检查数据库 ==========
echo -e "\n${YELLOW}[6/6] 检查数据库...${NC}"

if command -v psql &>/dev/null; then
    echo -e "  ✅ PostgreSQL 客户端已安装"
    echo -e "  ${YELLOW}⚠️ 请确保 TimescaleDB 已运行并导入 schema:${NC}"
    echo -e "     psql -h localhost -p 5433 -U opentd -d market_data -f libs/database/db/schema/001_timescaledb.sql"
else
    echo -e "  ${YELLOW}⚠️ 未检测到 psql，请手动安装 TimescaleDB${NC}"
fi

# ========== 完成 ==========
echo -e "\n${GREEN}✅ 安装完成！${NC}"
echo ""
echo "下一步："
echo "  1. 编辑配置文件:"
echo "     - services/data-service/.env"
echo "     - services/trading-service/.env"
echo "     - services/telegram-service/.env (设置 BOT_TOKEN)"
echo ""
echo "  2. 导入数据库 schema (如果是新数据库):"
echo "     cd libs/database/db/schema"
echo "     for f in *.sql; do psql -h localhost -p 5433 -U opentd -d market_data -f \$f; done"
echo ""
echo "  3. 启动服务:"
echo "     source .venv/bin/activate"
echo "     ./scripts/daemon.sh"
echo ""
echo "  4. 或单独启动:"
echo "     cd services/data-service && ./scripts/start.sh daemon"
echo "     cd services/telegram-service && python -m src.main"
