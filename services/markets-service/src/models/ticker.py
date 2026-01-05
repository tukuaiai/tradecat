"""行情数据模型"""
from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel


class Ticker(BaseModel):
    """实时行情 - 标准化模型"""
    market: str
    exchange: str
    symbol: str
    timestamp: datetime

    bid: Optional[Decimal] = None
    ask: Optional[Decimal] = None
    last: Decimal

    volume_24h: Optional[Decimal] = None
    quote_volume_24h: Optional[Decimal] = None
    change_24h: Optional[Decimal] = None
    change_pct_24h: Optional[Decimal] = None

    high_24h: Optional[Decimal] = None
    low_24h: Optional[Decimal] = None

    source: str = ""
