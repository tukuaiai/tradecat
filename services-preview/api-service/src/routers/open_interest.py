"""Open Interest 路由 (对齐 CoinGlass /api/futures/open-interest/history)"""

import psycopg

from fastapi import APIRouter, Query

from src.config import get_settings
from src.utils.errors import ErrorCode, api_response, error_response
from src.utils.symbol import normalize_symbol

router = APIRouter(tags=["futures"])

VALID_INTERVALS = ["1m", "5m", "15m", "30m", "1h", "4h", "12h", "1d"]


@router.get("/open-interest/history")
async def get_open_interest_history(
    symbol: str = Query(..., description="交易对 (BTC 或 BTCUSDT)"),
    exchange: str = Query(default="Binance", description="交易所"),
    interval: str = Query(default="1h", description="周期"),
    limit: int = Query(default=100, ge=1, le=1000, description="返回数量"),
    startTime: int | None = Query(default=None, description="开始时间 (毫秒)"),
    endTime: int | None = Query(default=None, description="结束时间 (毫秒)"),
) -> dict:
    """获取 Open Interest 历史数据"""
    settings = get_settings()
    symbol = normalize_symbol(symbol)

    if interval not in VALID_INTERVALS:
        return error_response(ErrorCode.INVALID_INTERVAL, f"无效的 interval: {interval}")

    try:
        conn = psycopg.connect(settings.DATABASE_URL)
        cursor = conn.cursor()

        query = """
            SELECT symbol, create_time, sum_open_interest_value
            FROM market_data.binance_futures_metrics_5m
            WHERE symbol = %s
        """
        params: list = [symbol]

        if startTime:
            query += " AND create_time >= to_timestamp(%s / 1000.0)"
            params.append(startTime)
        if endTime:
            query += " AND create_time <= to_timestamp(%s / 1000.0)"
            params.append(endTime)

        query += " ORDER BY create_time DESC LIMIT %s"
        params.append(limit)

        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()

        # CoinGlass OI 格式 (OHLC style)
        data = []
        for row in reversed(rows):
            oi_value = float(row[2]) if row[2] else 0
            data.append({
                "time": int(row[1].timestamp() * 1000),
                "open": str(oi_value),
                "high": str(oi_value),
                "low": str(oi_value),
                "close": str(oi_value)
            })

        return api_response(data)
    except psycopg.OperationalError as e:
        return error_response(ErrorCode.SERVICE_UNAVAILABLE, f"数据库连接失败: {e}")
    except Exception as e:
        return error_response(ErrorCode.INTERNAL_ERROR, f"查询失败: {e}")
