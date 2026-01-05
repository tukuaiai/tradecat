"""OpenBB 综合数据聚合器 - 作为降级备份"""
from __future__ import annotations

import asyncio
import os
from decimal import Decimal
from typing import Any

from config import settings
from core.fetcher import BaseFetcher
from core.registry import register_fetcher
from models.candle import Candle, CandleQuery


@register_fetcher("openbb", "candle")
class OpenBBFetcher(BaseFetcher[CandleQuery, Candle]):
    """OpenBB 聚合器 - 100+ 数据源，作为降级备份"""

    def __init__(self, provider: str = "yfinance"):
        """
        Args:
            provider: OpenBB 内置 provider (yfinance/polygon/fmp/intrinio 等)
        """
        self.provider = provider
        self._obb = None
        # OpenBB 通过 requests 使用代理
        if settings.http_proxy:
            os.environ.setdefault("HTTP_PROXY", settings.http_proxy)
            os.environ.setdefault("HTTPS_PROXY", settings.http_proxy)

    @property
    def obb(self):
        if self._obb is None:
            from openbb import obb
            self._obb = obb
        return self._obb

    def transform_query(self, params: dict[str, Any]) -> CandleQuery:
        return CandleQuery(**params)

    async def extract(self, query: CandleQuery) -> list[dict[str, Any]]:
        start = query.start.strftime("%Y-%m-%d") if query.start else None
        end = query.end.strftime("%Y-%m-%d") if query.end else None

        result = await asyncio.to_thread(
            self.obb.equity.price.historical,
            symbol=query.symbol,
            start_date=start,
            end_date=end,
            provider=self.provider
        )

        if result and hasattr(result, "to_df"):
            df = result.to_df()
            return df.reset_index().to_dict("records")
        return []

    def transform_data(self, raw: list[dict[str, Any]]) -> list[Candle]:
        results = []
        for r in raw:
            ts = r.get("date") or r.get("index")
            if hasattr(ts, "to_pydatetime"):
                ts = ts.to_pydatetime()

            results.append(Candle(
                market="us_stock",
                asset_type="spot",
                exchange="",
                symbol="",
                interval="1d",
                timestamp=ts,
                open=Decimal(str(r.get("open", 0))),
                high=Decimal(str(r.get("high", 0))),
                low=Decimal(str(r.get("low", 0))),
                close=Decimal(str(r.get("close", 0))),
                volume=Decimal(str(r.get("volume", 0))),
                source=f"openbb:{self.provider}",
            ))
        return results
