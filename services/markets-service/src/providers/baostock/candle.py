"""BaoStock K线数据获取器 - 完全免费"""
from __future__ import annotations

import asyncio
from datetime import datetime
from decimal import Decimal
from typing import Any

from core.fetcher import BaseFetcher
from core.registry import register_fetcher
from models.candle import Candle, CandleQuery


@register_fetcher("baostock", "candle")
class BaoStockCandleFetcher(BaseFetcher[CandleQuery, Candle]):
    """BaoStock K线获取器 - A股完全免费历史数据"""

    def __init__(self):
        self._logged_in = False

    def _ensure_login(self):
        if not self._logged_in:
            import baostock as bs
            bs.login()
            self._logged_in = True

    def transform_query(self, params: dict[str, Any]) -> CandleQuery:
        return CandleQuery(**params)

    async def extract(self, query: CandleQuery) -> list[dict[str, Any]]:
        import baostock as bs

        await asyncio.to_thread(self._ensure_login)

        # 转换 symbol: 000001 -> sh.000001 或 sz.000001
        symbol = query.symbol
        if not symbol.startswith(("sh.", "sz.")):
            prefix = "sh" if symbol.startswith("6") else "sz"
            symbol = f"{prefix}.{symbol}"

        start = query.start.strftime("%Y-%m-%d") if query.start else "2015-01-01"
        end = query.end.strftime("%Y-%m-%d") if query.end else datetime.now().strftime("%Y-%m-%d")

        rs = await asyncio.to_thread(
            bs.query_history_k_data_plus,
            symbol, "date,open,high,low,close,volume,amount",
            start_date=start, end_date=end,
            frequency="d", adjustflag="2"  # 前复权
        )

        data = []
        while rs.error_code == "0" and rs.next():
            data.append(dict(zip(rs.fields, rs.get_row_data())))
        return data

    def transform_data(self, raw: list[dict[str, Any]]) -> list[Candle]:
        results = []
        for r in raw:
            if not r.get("open"):
                continue
            results.append(Candle(
                market="cn_stock",
                asset_type="spot",
                exchange="sse" if r.get("code", "").startswith("sh") else "szse",
                symbol=r.get("code", "").split(".")[-1],
                interval="1d",
                timestamp=datetime.strptime(r["date"], "%Y-%m-%d"),
                open=Decimal(r["open"]),
                high=Decimal(r["high"]),
                low=Decimal(r["low"]),
                close=Decimal(r["close"]),
                volume=Decimal(r["volume"]) if r["volume"] else Decimal(0),
                quote_volume=Decimal(r["amount"]) if r.get("amount") else None,
                source="baostock",
            ))
        return results
