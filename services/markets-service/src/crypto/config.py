"""加密货币采集配置

支持双模式:
- CRYPTO_WRITE_MODE=raw    → 写入 raw.* (新架构，含血缘追踪)
- CRYPTO_WRITE_MODE=legacy → 写入 market_data.* (兼容 trading-service)
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional

SERVICE_ROOT = Path(__file__).parent.parent.parent  # markets-service/
PROJECT_ROOT = SERVICE_ROOT.parent.parent           # tradecat/

# 加载 config/.env
_env_file = PROJECT_ROOT / "config" / ".env"
if _env_file.exists():
    for line in _env_file.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip())


def _int_env(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, default))
    except ValueError:
        return default


@dataclass
class Settings:
    """服务配置"""
    # 数据库 - 优先使用 MARKETS_SERVICE_DATABASE_URL
    database_url: str = field(default_factory=lambda: os.getenv(
        "MARKETS_SERVICE_DATABASE_URL",
        os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5433/market_data")
    ))
    
    # 写入模式: "raw" = raw.*, "legacy" = market_data.*
    write_mode: str = field(default_factory=lambda: os.getenv("CRYPTO_WRITE_MODE", "raw"))
    
    # Schema 配置
    db_schema: str = field(default_factory=lambda: os.getenv("KLINE_DB_SCHEMA", "market_data"))
    raw_schema: str = field(default_factory=lambda: os.getenv("RAW_DB_SCHEMA", "raw"))
    quality_schema: str = field(default_factory=lambda: os.getenv("QUALITY_DB_SCHEMA", "quality"))
    
    # 交易所配置
    db_exchange: str = field(default_factory=lambda: os.getenv("BINANCE_WS_DB_EXCHANGE", "binance_futures_um"))
    ccxt_exchange: str = field(default_factory=lambda: os.getenv("BINANCE_WS_CCXT_EXCHANGE", "binance"))
    
    # 代理
    http_proxy: Optional[str] = field(default_factory=lambda: os.getenv("HTTP_PROXY") or os.getenv("HTTPS_PROXY"))
    
    # 目录
    log_dir: Path = field(default_factory=lambda: SERVICE_ROOT / "logs")
    data_dir: Path = field(default_factory=lambda: PROJECT_ROOT / "libs" / "database" / "csv")
    
    # WebSocket 配置
    ws_gap_interval: int = field(default_factory=lambda: _int_env("BINANCE_WS_GAP_INTERVAL", 600))
    ws_gap_lookback: int = field(default_factory=lambda: _int_env("BINANCE_WS_GAP_LOOKBACK", 10080))
    ws_source: str = field(default_factory=lambda: os.getenv("BINANCE_WS_SOURCE", "binance_ws"))
    
    def __post_init__(self):
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.data_dir.mkdir(parents=True, exist_ok=True)
    
    @property
    def active_schema(self) -> str:
        """当前写入的 schema"""
        return self.raw_schema if self.write_mode == "raw" else self.db_schema
    
    @property
    def is_raw_mode(self) -> bool:
        """是否为 raw 模式"""
        return self.write_mode == "raw"


settings = Settings()


# 兼容 data-service 的常量
INTERVAL_TO_MS = {
    "1m": 60_000, "3m": 180_000, "5m": 300_000, "15m": 900_000, "30m": 1_800_000,
    "1h": 3_600_000, "2h": 7_200_000, "4h": 14_400_000, "6h": 21_600_000, "12h": 43_200_000,
    "1d": 86_400_000, "1w": 604_800_000, "1M": 2_592_000_000,
}


def normalize_interval(interval: str) -> str:
    """标准化周期字符串"""
    interval = interval.strip()
    if interval == "1M":
        return "1M"
    normalized = interval.lower()
    if normalized not in INTERVAL_TO_MS:
        raise ValueError(f"不支持的周期: {interval}")
    return normalized


@dataclass(slots=True)
class GapTask:
    """缺口任务"""
    symbol: str
    gap_start: datetime
    gap_end: datetime
