"""配置与数据模型"""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional

# 服务根目录
SERVICE_ROOT = Path(__file__).parent.parent  # src/config.py -> data-service
PROJECT_ROOT = SERVICE_ROOT.parent.parent    # tradecat/

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
    database_url: str = field(default_factory=lambda: os.getenv(
        "DATABASE_URL", "postgresql://postgres:postgres@localhost:5433/market_data"
    ))
    http_proxy: Optional[str] = field(default_factory=lambda: os.getenv("HTTP_PROXY") or os.getenv("HTTPS_PROXY"))

    # 日志和数据目录改为项目内
    log_dir: Path = field(default_factory=lambda: Path(os.getenv(
        "DATA_SERVICE_LOG_DIR", str(PROJECT_ROOT / "services" / "data-service" / "logs")
    )))
    data_dir: Path = field(default_factory=lambda: Path(os.getenv(
        "DATA_SERVICE_DATA_DIR", str(PROJECT_ROOT / "libs" / "database" / "csv")
    )))

    ws_gap_interval: int = field(default_factory=lambda: _int_env("BINANCE_WS_GAP_INTERVAL", 600))
    ws_gap_lookback: int = field(default_factory=lambda: _int_env("BINANCE_WS_GAP_LOOKBACK", 10080))
    ws_source: str = field(default_factory=lambda: os.getenv("BINANCE_WS_SOURCE", "binance_ws"))

    db_schema: str = field(default_factory=lambda: os.getenv("KLINE_DB_SCHEMA", "market_data"))
    db_exchange: str = field(default_factory=lambda: os.getenv("BINANCE_WS_DB_EXCHANGE", "binance_futures_um"))
    ccxt_exchange: str = field(default_factory=lambda: os.getenv("BINANCE_WS_CCXT_EXCHANGE", "binance"))

    def __post_init__(self):
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.data_dir.mkdir(parents=True, exist_ok=True)


settings = Settings()


INTERVAL_TO_MS = {
    "1m": 60_000, "3m": 180_000, "5m": 300_000, "15m": 900_000, "30m": 1_800_000,
    "1h": 3_600_000, "2h": 7_200_000, "4h": 14_400_000, "6h": 21_600_000, "12h": 43_200_000,
    "1d": 86_400_000, "1w": 604_800_000, "1M": 2_592_000_000,
}


@dataclass(slots=True)
class GapTask:
    """缺口任务"""
    symbol: str
    gap_start: datetime
    gap_end: datetime


def normalize_interval(interval: str) -> str:
    interval = interval.strip()
    if interval == "1M":
        return "1M"
    normalized = interval.lower()
    if normalized not in INTERVAL_TO_MS:
        raise ValueError(f"不支持的周期: {interval}")
    return normalized
