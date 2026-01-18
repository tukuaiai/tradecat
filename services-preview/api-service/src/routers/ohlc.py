"""K线数据路由 (对齐 CoinGlass /api/futures/ohlc/history)"""

import psycopg

from fastapi import APIRouter, Query

from src.config import get_settings
from src.utils.errors import ErrorCode, api_response, error_response
from src.utils.symbol import normalize_symbol

router = APIRouter(tags=["futures"])

VALID_INTERVALS = ["1m", "5m", "15m", "30m", "1h", "4h", "12h", "1d"]


@router.get("/ohlc/history")
async def get_ohlc_history(
    symbol: str = Query(..., description="交易对 (BTC 或 BTCUSDT)"),
    exchange: str = Query(default="Binance", description="交易所"),
    interval: str = Query(default="1h", description="K线周期"),
    limit: int = Query(default=100, ge=1, le=1000, description="返回数量"),
    startTime: int | None = Query(default=None, description="开始时间 (毫秒)"),
    endTime: int | None = Query(default=None, description="结束时间 (毫秒)"),
) -> dict:
    """获取K线历史数据"""
    settings = get_settings()
    symbol = normalize_symbol(symbol)

    if interval not in VALID_INTERVALS:
        return error_response(ErrorCode.INVALID_INTERVAL, f"无效的 interval: {interval}")

    try:
        conn = psycopg.connect(settings.DATABASE_URL)
        cursor = conn.cursor()

        # 构建查询
        query = """
            SELECT symbol, bucket_ts, open, high, low, close, volume, quote_volume
            FROM market_data.candles_1m
            WHERE symbol = %s
        """
        params: list = [symbol]

        if startTime:
            query += " AND bucket_ts >= to_timestamp(%s / 1000.0)"
            params.append(startTime)
        if endTime:
            query += " AND bucket_ts <= to_timestamp(%s / 1000.0)"
            params.append(endTime)

        query += " ORDER BY bucket_ts DESC LIMIT %s"
        params.append(limit)

        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()

        # 转换为 CoinGlass 格式
        data = [
            {
                "time": int(row[1].timestamp() * 1000),
                "open": str(row[2]),
                "high": str(row[3]),
                "low": str(row[4]),
                "close": str(row[5]),
                "volume": str(row[6]),
                "volume_usd": str(row[7]) if row[7] else "0"
            }
            for row in reversed(rows)
        ]

        return api_response(data)
    except psycopg.OperationalError as e:
        return error_response(ErrorCode.SERVICE_UNAVAILABLE, f"数据库连接失败: {e}")
    except Exception as e:
        return error_response(ErrorCode.INTERNAL_ERROR, f"查询失败: {e}")
