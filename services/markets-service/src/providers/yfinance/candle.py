"""yfinance K线数据获取器"""
from __future__ import annotations

import asyncio
import os
from datetime import timezone
from decimal import Decimal
from typing import Any

from config import settings
from core.fetcher import BaseFetcher
from core.registry import register_fetcher
from models.candle import Candle, CandleQuery


@register_fetcher("yfinance", "candle")
class YFinanceCandleFetcher(BaseFetcher[CandleQuery, Candle]):
    """yfinance K线获取器 - 美股/港股/外汇/加密"""

    INTERVAL_MAP = {
        "1m": "1m", "5m": "5m", "15m": "15m", "30m": "30m",
        "1h": "1h", "4h": "4h", "1d": "1d", "1w": "1wk", "1M": "1mo"
    }

    def __init__(self):
        # 设置代理环境变量 (yfinance 通过 requests 使用)
        if settings.http_proxy:
            os.environ.setdefault("HTTP_PROXY", settings.http_proxy)
            os.environ.setdefault("HTTPS_PROXY", settings.http_proxy)

    def transform_query(self, params: dict[str, Any]) -> CandleQuery:
        return CandleQuery(**params)

    async def extract(self, query: CandleQuery) -> list[dict[str, Any]]:
        import yfinance as yf

        ticker = yf.Ticker(query.symbol)
        interval = self.INTERVAL_MAP.get(query.interval, "1d")

        df = await asyncio.to_thread(
            ticker.history,
            start=query.start,
            end=query.end,
            interval=interval
        )

        if df is None or df.empty:
            return []

        df = df.reset_index()
        return df.to_dict("records")

    def transform_data(self, raw: list[dict[str, Any]]) -> list[Candle]:
        results = []
        for r in raw:
            ts = r.get("Date") or r.get("Datetime")
            if hasattr(ts, "to_pydatetime"):
                ts = ts.to_pydatetime()
            if ts.tzinfo is None:
                ts = ts.replace(tzinfo=timezone.utc)

            results.append(Candle(
                market="us_stock",
                asset_type="spot",
                exchange="nasdaq",
                symbol="",  # 需要从外部传入
                interval="1d",
                timestamp=ts,
                open=Decimal(str(r.get("Open", 0))),
                high=Decimal(str(r.get("High", 0))),
                low=Decimal(str(r.get("Low", 0))),
                close=Decimal(str(r.get("Close", 0))),
                volume=Decimal(str(r.get("Volume", 0))),
                source="yfinance",
            ))
        return results
