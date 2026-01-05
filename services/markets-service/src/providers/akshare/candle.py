"""AKShare K线数据获取器"""
from __future__ import annotations

import asyncio
import os
from datetime import datetime
from decimal import Decimal
from typing import Any

from config import settings
from core.fetcher import BaseFetcher
from core.registry import register_fetcher
from models.candle import Candle, CandleQuery


@register_fetcher("akshare", "candle")
class AKShareCandleFetcher(BaseFetcher[CandleQuery, Candle]):
    """AKShare K线获取器 - A股/港股/期货/债券"""

    def __init__(self, market: str = "cn_stock"):
        self.market = market
        # akshare 通过 requests 使用代理
        if settings.http_proxy:
            os.environ.setdefault("HTTP_PROXY", settings.http_proxy)
            os.environ.setdefault("HTTPS_PROXY", settings.http_proxy)

    def transform_query(self, params: dict[str, Any]) -> CandleQuery:
        return CandleQuery(**params)

    async def extract(self, query: CandleQuery) -> list[dict[str, Any]]:
        import akshare as ak

        start_str = query.start.strftime("%Y%m%d") if query.start else "20200101"
        end_str = query.end.strftime("%Y%m%d") if query.end else datetime.now().strftime("%Y%m%d")

        # 根据市场类型调用不同接口
        if self.market == "cn_stock":
            df = await asyncio.to_thread(
                ak.stock_zh_a_hist,
                symbol=query.symbol,
                period="daily",
                start_date=start_str,
                end_date=end_str,
                adjust=""
            )
        elif self.market == "hk_stock":
            df = await asyncio.to_thread(
                ak.stock_hk_hist,
                symbol=query.symbol,
                period="daily",
                start_date=start_str,
                end_date=end_str,
                adjust=""
            )
        elif self.market == "futures":
            df = await asyncio.to_thread(
                ak.futures_zh_daily_sina,
                symbol=query.symbol
            )
        else:
            return []

        return df.to_dict("records") if df is not None and not df.empty else []

    def transform_data(self, raw: list[dict[str, Any]]) -> list[Candle]:
        results = []
        for r in raw:
            # A股字段映射
            ts = r.get("日期") or r.get("date")
            if isinstance(ts, str):
                ts = datetime.strptime(ts, "%Y-%m-%d")

            results.append(Candle(
                market=self.market,
                asset_type="spot",
                exchange="sse" if self.market == "cn_stock" else "hkex",
                symbol=str(r.get("股票代码", r.get("symbol", ""))),
                interval="1d",
                timestamp=ts,
                open=Decimal(str(r.get("开盘", r.get("open", 0)))),
                high=Decimal(str(r.get("最高", r.get("high", 0)))),
                low=Decimal(str(r.get("最低", r.get("low", 0)))),
                close=Decimal(str(r.get("收盘", r.get("close", 0)))),
                volume=Decimal(str(r.get("成交量", r.get("volume", 0)))),
                quote_volume=Decimal(str(r.get("成交额", 0))) if r.get("成交额") else None,
                source="akshare",
            ))
        return results
