"""成交数据模型"""
from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel


class Trade(BaseModel):
    """逐笔成交 - 标准化模型"""
    market: str
    exchange: str
    symbol: str
    timestamp: datetime

    trade_id: Optional[str] = None
    price: Decimal
    amount: Decimal
    side: str  # buy/sell

    source: str = ""
