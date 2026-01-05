"""Schema 适配器 - 旧表字段 ↔ 新表字段映射

字段映射:
- K线: bucket_ts → open_time, trade_count → trades
- 期货: create_time → timestamp, sum_open_interest → open_interest, ...
"""
from __future__ import annotations

from datetime import timedelta
from typing import List, Sequence

from .config import settings


class KlineAdapter:
    """K线字段适配: market_data.candles_1m ↔ raw.crypto_kline_1m"""
    
    # 旧字段 → 新字段
    FIELD_MAP = {
        "bucket_ts": "open_time",
        "trade_count": "trades",
    }
    # 新字段 → 旧字段
    REVERSE_MAP = {v: k for k, v in FIELD_MAP.items()}
    
    @classmethod
    def to_new_schema(cls, rows: Sequence[dict], batch_id: int) -> List[dict]:
        """旧格式 → 新格式 (写入 raw.crypto_kline_1m)"""
        result = []
        for r in rows:
            new_row = {}
            for k, v in r.items():
                new_key = cls.FIELD_MAP.get(k, k)
                new_row[new_key] = v
            # 添加新表必需字段
            new_row["ingest_batch_id"] = batch_id
            # 计算 close_time
            if "close_time" not in new_row and "open_time" in new_row:
                new_row["close_time"] = new_row["open_time"] + timedelta(minutes=1)
            result.append(new_row)
        return result
    
    @classmethod
    def to_legacy_schema(cls, rows: Sequence[dict]) -> List[dict]:
        """新格式 → 旧格式 (兼容下游)"""
        result = []
        skip_fields = {"ingest_batch_id", "close_time", "ingested_at", "updated_at", "source_event_time"}
        for r in rows:
            old_row = {}
            for k, v in r.items():
                if k in skip_fields:
                    continue
                old_key = cls.REVERSE_MAP.get(k, k)
                old_row[old_key] = v
            result.append(old_row)
        return result


class MetricsAdapter:
    """期货指标字段适配: binance_futures_metrics_5m ↔ raw.crypto_metrics_5m"""
    
    # 旧字段 → 新字段
    FIELD_MAP = {
        "create_time": "timestamp",
        "sum_open_interest": "open_interest",
        "sum_open_interest_value": "open_interest_value",
        "sum_toptrader_long_short_ratio": "top_long_short_ratio",
        "count_long_short_ratio": "long_short_ratio",
        "sum_taker_long_short_vol_ratio": "taker_buy_sell_ratio",
    }
    REVERSE_MAP = {v: k for k, v in FIELD_MAP.items()}
    
    # 新表不支持的字段 (丢弃)
    DROPPED_FIELDS = {"count_toptrader_long_short_ratio", "is_closed"}
    
    @classmethod
    def to_new_schema(cls, rows: Sequence[dict], batch_id: int) -> List[dict]:
        """旧格式 → 新格式 (写入 raw.crypto_metrics_5m)"""
        result = []
        for r in rows:
            new_row = {}
            for k, v in r.items():
                if k in cls.DROPPED_FIELDS:
                    continue
                new_key = cls.FIELD_MAP.get(k, k)
                new_row[new_key] = v
            new_row["ingest_batch_id"] = batch_id
            result.append(new_row)
        return result
    
    @classmethod
    def to_legacy_schema(cls, rows: Sequence[dict]) -> List[dict]:
        """新格式 → 旧格式"""
        result = []
        skip_fields = {"ingest_batch_id", "ingested_at", "updated_at"}
        for r in rows:
            old_row = {}
            for k, v in r.items():
                if k in skip_fields:
                    continue
                old_key = cls.REVERSE_MAP.get(k, k)
                old_row[old_key] = v
            result.append(old_row)
        return result


def get_kline_table(interval: str = "1m") -> str:
    """获取 K线表名"""
    if settings.is_raw_mode:
        return f"{settings.raw_schema}.crypto_kline_{interval}"
    return f"{settings.db_schema}.candles_{interval}"


def get_metrics_table() -> str:
    """获取期货指标表名"""
    if settings.is_raw_mode:
        return f"{settings.raw_schema}.crypto_metrics_5m"
    return f"{settings.db_schema}.binance_futures_metrics_5m"


def get_kline_conflict_keys() -> tuple:
    """获取 K线表冲突键"""
    if settings.is_raw_mode:
        return ("exchange", "symbol", "open_time")
    return ("exchange", "symbol", "bucket_ts")


def get_metrics_conflict_keys() -> tuple:
    """获取期货指标表冲突键"""
    if settings.is_raw_mode:
        return ("exchange", "symbol", "timestamp")
    return ("symbol", "create_time")


def get_kline_time_field() -> str:
    """获取 K线时间字段名"""
    return "open_time" if settings.is_raw_mode else "bucket_ts"


def get_metrics_time_field() -> str:
    """获取期货指标时间字段名"""
    return "timestamp" if settings.is_raw_mode else "create_time"
