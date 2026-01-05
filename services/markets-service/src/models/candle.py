"""K线数据模型 - 跨市场统一"""
from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, Field


class CandleQuery(BaseModel):
    """K线查询参数"""
    market: str = Field(..., description="市场: crypto/us_stock/cn_stock/futures/forex")
    symbol: str = Field(..., description="标的代码")
    interval: str = Field(default="1d", description="周期: 1m/5m/15m/1h/4h/1d/1w")
    start: Optional[datetime] = None
    end: Optional[datetime] = None
    limit: int = Field(default=1000, ge=1, le=10000)


class Candle(BaseModel):
    """K线数据 - 标准化模型"""
    # 标识
    market: str = Field(..., description="市场类型")
    asset_type: str = Field(default="spot", description="资产类型: spot/perpetual/quarterly/option")
    exchange: str = Field(..., description="交易所")
    symbol: str = Field(..., description="标的代码")
    interval: str = Field(..., description="K线周期")

    # 时间
    timestamp: datetime = Field(..., description="K线时间 (UTC)")

    # OHLCV
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    volume: Decimal = Field(default=Decimal(0))

    # 可选字段
    quote_volume: Optional[Decimal] = Field(default=None, description="成交额")
    trade_count: Optional[int] = Field(default=None, description="成交笔数")
    open_interest: Optional[Decimal] = Field(default=None, description="持仓量 (衍生品)")

    # 元数据
    source: str = Field(default="", description="数据来源")

    class Config:
        json_encoders = {Decimal: str}
