#!/bin/bash
# ============================================================
# TradeCat 全市场数据库初始化脚本
# 用法: ./init_market_db.sh [host] [port] [database]
# ============================================================

set -e

HOST=${1:-localhost}
PORT=${2:-5434}
DATABASE=${3:-market_data}
USER=${PGUSER:-postgres}
PASSWORD=${PGPASSWORD:-postgres}

DDL_DIR="$(dirname "$0")/ddl"

echo "=============================================="
echo "TradeCat 数据库初始化"
echo "=============================================="
echo "Host: $HOST:$PORT"
echo "Database: $DATABASE"
echo "DDL Dir: $DDL_DIR"
echo "=============================================="

# 检查连接
echo "[1/9] 检查数据库连接..."
PGPASSWORD=$PASSWORD psql -h $HOST -p $PORT -U $USER -d $DATABASE -c "SELECT 1" > /dev/null 2>&1 || {
    echo "❌ 无法连接数据库"
    exit 1
}
echo "✅ 数据库连接正常"

# 执行 DDL
for i in 01 02 03 04 05 06 07 08; do
    SQL_FILE="$DDL_DIR/${i}_*.sql"
    SQL_FILE=$(ls $SQL_FILE 2>/dev/null | head -1)
    if [ -f "$SQL_FILE" ]; then
        echo "[$(($i+1))/9] 执行 $(basename $SQL_FILE)..."
        PGPASSWORD=$PASSWORD psql -h $HOST -p $PORT -U $USER -d $DATABASE -f "$SQL_FILE" > /dev/null 2>&1 || {
            echo "❌ 执行失败: $SQL_FILE"
            PGPASSWORD=$PASSWORD psql -h $HOST -p $PORT -U $USER -d $DATABASE -f "$SQL_FILE" 2>&1 | tail -20
            exit 1
        }
        echo "✅ 完成"
    fi
done

echo ""
echo "=============================================="
echo "✅ 数据库初始化完成!"
echo "=============================================="

# 验证
echo ""
echo "验证结果:"
PGPASSWORD=$PASSWORD psql -h $HOST -p $PORT -U $USER -d $DATABASE -c "
SELECT 
    schemaname as schema,
    count(*) as tables
FROM pg_tables 
WHERE schemaname IN ('reference', 'raw', 'fundamental', 'alternative', 'agg', 'indicators', 'quality')
GROUP BY schemaname
ORDER BY schemaname;
"

echo ""
echo "连续聚合视图:"
PGPASSWORD=$PASSWORD psql -h $HOST -p $PORT -U $USER -d $DATABASE -c "
SELECT view_name FROM timescaledb_information.continuous_aggregates ORDER BY view_name;
"
