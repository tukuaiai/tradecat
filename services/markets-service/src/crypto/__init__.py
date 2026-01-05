"""加密货币数据采集模块 - 移植自 data-service

支持双模式写入:
- CRYPTO_WRITE_MODE=raw    → 写入 raw.crypto_kline_1m (新架构)
- CRYPTO_WRITE_MODE=legacy → 写入 market_data.candles_1m (兼容旧架构)
"""
from .config import settings, INTERVAL_TO_MS, normalize_interval, GapTask
from .collectors.backfill import DataBackfiller, GapScanner
from .collectors.metrics import MetricsCollector
from .collectors.ws import WSCollector

__all__ = [
    "settings",
    "INTERVAL_TO_MS",
    "normalize_interval",
    "GapTask",
    "DataBackfiller",
    "GapScanner",
    "MetricsCollector",
    "WSCollector",
]
