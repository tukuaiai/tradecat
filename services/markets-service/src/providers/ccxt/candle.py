"""CCXT K线数据获取器"""
from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any

import ccxt

from config import settings
from core.fetcher import BaseFetcher
from core.registry import register_fetcher
from models.candle import Candle, CandleQuery


@register_fetcher("ccxt", "candle")
class CCXTCandleFetcher(BaseFetcher[CandleQuery, Candle]):
    """CCXT K线获取器 - 支持 100+ 加密货币交易所"""

    def __init__(self, exchange: str = "binance", market_type: str = "swap"):
        self.exchange_id = exchange
        self.market_type = market_type
        self._client = None

    @property
    def client(self) -> ccxt.Exchange:
        if self._client is None:
            cls = getattr(ccxt, self.exchange_id)
            self._client = cls({
                "enableRateLimit": True,
                "timeout": 30000,
                "proxies": {"http": settings.http_proxy, "https": settings.http_proxy} if settings.http_proxy else None,
                "options": {"defaultType": self.market_type},
            })
        return self._client

    def transform_query(self, params: dict[str, Any]) -> CandleQuery:
        return CandleQuery(**params)

    async def extract(self, query: CandleQuery) -> list[dict[str, Any]]:
        # 转换 symbol 格式: BTCUSDT -> BTC/USDT:USDT
        symbol = query.symbol.upper()
        if self.market_type == "swap":
            base = symbol.replace("USDT", "")
            ccxt_symbol = f"{base}/USDT:USDT"
        else:
            ccxt_symbol = f"{symbol[:-4]}/USDT" if symbol.endswith("USDT") else symbol

        since_ms = int(query.start.timestamp() * 1000) if query.start else None

        # 异步执行同步方法
        ohlcv = await asyncio.to_thread(
            self.client.fetch_ohlcv,
            ccxt_symbol, query.interval, since=since_ms, limit=query.limit
        )

        return [{"ts": c[0], "o": c[1], "h": c[2], "l": c[3], "c": c[4], "v": c[5]} for c in ohlcv]

    def transform_data(self, raw: list[dict[str, Any]]) -> list[Candle]:
        return [Candle(
            market="crypto",
            asset_type="perpetual" if self.market_type == "swap" else "spot",
            exchange=self.exchange_id,
            symbol=raw[0].get("symbol", ""),  # 需要从外部传入
            interval="1d",  # 需要从外部传入
            timestamp=datetime.fromtimestamp(r["ts"] / 1000, tz=timezone.utc),
            open=Decimal(str(r["o"])),
            high=Decimal(str(r["h"])),
            low=Decimal(str(r["l"])),
            close=Decimal(str(r["c"])),
            volume=Decimal(str(r["v"])),
            source="ccxt",
        ) for r in raw]
