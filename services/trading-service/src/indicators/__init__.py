"""
指标模块

- incremental/: 真正增量计算（EMA/累加/单行读取）
- batch/: 需要历史窗口（rolling/全量计算）

计算结果统一写入 SQLite。
"""
from .base import (
    Indicator,
    IndicatorMeta,
    register,
    get_indicator,
    get_all_indicators,
    get_batch_indicators,
    get_incremental_indicators,
)

# === 增量指标（可递推/单行）===
from .incremental import macd
from .incremental import kdj
from .incremental import atr
from .incremental import ema_gc
from .incremental import obv
from .incremental import cvd
from .incremental import base_data
from .incremental import buy_sell_ratio
from .incremental import futures_sentiment

# === 批量指标（需要窗口）===
from .batch import k_pattern
from .batch import trend_line
from .batch import support_resistance
from .batch import vpvr
from .batch import super_trend
from .batch import bollinger
from .batch import vwap
from .batch import volume_ratio
from .batch import mfi
from .batch import liquidity
from .batch import tv_rsi
from .batch import tv_trend_cloud
from .batch import tv_big_money
from .batch import tv_fib_sniper
from .batch import tv_zero_lag
from .batch import tv_volume_signal
from .batch import tv_long_short
from .batch import scalping
from .batch import harmonic
from .batch import futures_aggregate
from .batch import lean_indicators
from .batch import data_monitor
from .batch import futures_gap_monitor

__all__ = [
    "Indicator",
    "IndicatorMeta",
    "register",
    "get_indicator",
    "get_all_indicators",
    "get_batch_indicators",
    "get_incremental_indicators",
]
