"""期货综合指标路由"""

import psycopg

from fastapi import APIRouter, Query

from src.config import get_settings
from src.utils.errors import ErrorCode, api_response, error_response
from src.utils.symbol import normalize_symbol

router = APIRouter(tags=["futures"])

VALID_INTERVALS = ["1m", "5m", "15m", "30m", "1h", "4h", "12h", "1d"]


@router.get("/metrics")
async def get_futures_metrics(
    symbol: str = Query(..., description="交易对 (BTC 或 BTCUSDT)"),
    exchange: str = Query(default="Binance", description="交易所"),
    interval: str = Query(default="5m", description="周期"),
    limit: int = Query(default=100, ge=1, le=1000, description="返回数量"),
) -> dict:
    """获取期货综合指标数据"""
    settings = get_settings()
    symbol = normalize_symbol(symbol)

    if interval not in VALID_INTERVALS:
        return error_response(ErrorCode.INVALID_INTERVAL, f"无效的 interval: {interval}")

    try:
        conn = psycopg.connect(settings.DATABASE_URL)
        cursor = conn.cursor()

        query = """
            SELECT symbol, create_time, sum_open_interest_value, 
                   sum_toptrader_long_short_ratio, sum_taker_long_short_vol_ratio
            FROM market_data.binance_futures_metrics_5m
            WHERE symbol = %s
            ORDER BY create_time DESC
            LIMIT %s
        """
        cursor.execute(query, (symbol, limit))
        rows = cursor.fetchall()
        conn.close()

        data = [
            {
                "time": int(row[1].timestamp() * 1000),
                "symbol": row[0],
                "openInterest": str(row[2]) if row[2] else "0",
                "longShortRatio": str(row[3]) if row[3] else "0",
                "takerLongShortRatio": str(row[4]) if row[4] else "0"
            }
            for row in reversed(rows)
        ]

        return api_response(data)
    except psycopg.OperationalError as e:
        return error_response(ErrorCode.SERVICE_UNAVAILABLE, f"数据库连接失败: {e}")
    except Exception as e:
        return error_response(ErrorCode.INTERNAL_ERROR, f"查询失败: {e}")
