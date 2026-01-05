"""FRED 宏观数据获取器"""
from __future__ import annotations

import asyncio
import os
from datetime import datetime
from decimal import Decimal
from typing import Any

from pydantic import BaseModel, Field

from config import settings
from core.fetcher import BaseFetcher
from core.key_manager import get_key_manager
from core.registry import register_fetcher


class MacroQuery(BaseModel):
    """宏观数据查询"""
    series_id: str = Field(..., description="FRED 序列 ID, 如 GDP, UNRATE, DFF")
    start: datetime | None = None
    end: datetime | None = None


class MacroData(BaseModel):
    """宏观数据"""
    series_id: str
    timestamp: datetime
    value: Decimal
    source: str = "fred"


@register_fetcher("fredapi", "macro")
class FREDMacroFetcher(BaseFetcher[MacroQuery, MacroData]):
    """FRED 宏观数据获取器 - 美联储官方数据

    支持多 Key 负载均衡，在 config/.env 中配置:
        FRED_API_KEY=key1,key2,key3
    """

    # 常用序列
    SERIES = {
        "GDP": "国内生产总值",
        "UNRATE": "失业率",
        "CPIAUCSL": "CPI 消费者价格指数",
        "DFF": "联邦基金利率",
        "DGS10": "10年期国债收益率",
        "DGS2": "2年期国债收益率",
        "M2SL": "M2 货币供应",
        "FEDFUNDS": "联邦基金有效利率",
    }

    def __init__(self, api_key: str | None = None):
        self._single_key = api_key
        self._key_manager = get_key_manager("FRED_API_KEY") if not api_key else None
        # fredapi 通过 requests 使用代理
        if settings.http_proxy:
            os.environ.setdefault("HTTP_PROXY", settings.http_proxy)
            os.environ.setdefault("HTTPS_PROXY", settings.http_proxy)

    def _get_api_key(self) -> str:
        """获取 API Key (支持多 Key 轮询)"""
        if self._single_key:
            return self._single_key
        if self._key_manager:
            key = self._key_manager.get_key()
            if key:
                return key
        raise ValueError("需要 FRED_API_KEY 环境变量")

    def transform_query(self, params: dict[str, Any]) -> MacroQuery:
        return MacroQuery(**params)

    async def extract(self, query: MacroQuery) -> list[dict[str, Any]]:
        from fredapi import Fred

        api_key = self._get_api_key()
        fred = Fred(api_key=api_key)

        try:
            series = await asyncio.to_thread(
                fred.get_series,
                query.series_id,
                observation_start=query.start,
                observation_end=query.end
            )

            if self._key_manager:
                self._key_manager.report_success(api_key)

            return [{"date": idx, "value": val, "series_id": query.series_id}
                    for idx, val in series.items() if val == val]  # 过滤 NaN

        except Exception:
            if self._key_manager:
                self._key_manager.report_error(api_key)
            raise

    def transform_data(self, raw: list[dict[str, Any]]) -> list[MacroData]:
        return [MacroData(
            series_id=r["series_id"],
            timestamp=r["date"].to_pydatetime() if hasattr(r["date"], "to_pydatetime") else r["date"],
            value=Decimal(str(r["value"])),
            source="fred",
        ) for r in raw]
