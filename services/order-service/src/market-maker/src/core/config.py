"""配置管理"""
import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import List

# 加载全局 config/.env
_SERVICE_ROOT = Path(__file__).parents[4]  # src/core/config.py -> core -> src -> market-maker -> src -> order-service
_PROJECT_ROOT = _SERVICE_ROOT.parents[1]   # order-service -> services -> tradecat
_env_file = _PROJECT_ROOT / "config" / ".env"
if _env_file.exists():
    for line in _env_file.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip())


@dataclass
class ExchangeConfig:
    name: str = "binanceusdm"
    api_key: str = ""
    api_secret: str = ""
    testnet: bool = True
    proxy: str = ""  # 从环境变量 HTTP_PROXY 读取
    hedge_mode: bool = False  # 是否启用双向持仓模式（不再通过 REST 探测）
    strict_no_rest_markets: bool = False  # 是否预置 markets 以避免 load_markets 隐式 REST
    markets_path: str = "config/markets.json"  # 预置合约元数据路径
    markets_sha256_path: str = "config/markets.sha256"  # markets.json 校验文件
    use_rest_snapshot: bool = False  # 是否启动时拉取一次账户快照（默认关闭）
    account_stale_seconds: int = 60  # 超过该时间未收到 ACCOUNT_UPDATE 视为失效


@dataclass
class StrategyConfig:
    symbols: List[str] = None
    gamma: float = 0.1
    T: float = 0.05
    max_inventory: float = 0.01
    order_size: float = 0.001
    min_spread_bps: float = 2
    order_interval: float = 1.0
    mid_none_limit: int = 3  # 连续缺失 mid 的容忍次数，超过后暂停报价
    order_ttl_seconds: float = 0.0  # 挂单生存时间，0 表示关闭刷新
    order_price_deviation_bps: float = 0.0  # 挂单价格偏离触发撤单的 bps，0 关闭
    cancel_cooldown_seconds: float = 0.0  # 撤单最短间隔，避免过度撤单

    def __post_init__(self):
        if self.symbols is None:
            self.symbols = ["BTC/USDT:USDT", "ETH/USDT:USDT"]


@dataclass
class RiskConfig:
    per_symbol_limit: float = 200
    global_limit: float = 2000
    flat_threshold: float = 400
    cooldown: float = 10
    risk_log_details: bool = False  # 是否打印持仓+挂单明细
    flat_retries: int = 2  # 平仓失败重试次数
    flat_retry_backoff: float = 0.5  # 平仓重试退避秒数


@dataclass
class Config:
    exchange: ExchangeConfig = None
    strategy: StrategyConfig = None
    risk: RiskConfig = None

    def __post_init__(self):
        self.exchange = self.exchange or ExchangeConfig()
        self.strategy = self.strategy or StrategyConfig()
        self.risk = self.risk or RiskConfig()

    @classmethod
    def from_file(cls, path: str) -> "Config":
        with open(path) as f:
            data = json.load(f)
        return cls(
            exchange=ExchangeConfig(**data.get("exchange", {})),
            strategy=StrategyConfig(**data.get("strategy", {})),
            risk=RiskConfig(**data.get("risk", {})),
        )

    @classmethod
    def from_env(cls) -> "Config":
        return cls(
            exchange=ExchangeConfig(
                api_key=os.getenv("API_KEY", ""),
                api_secret=os.getenv("API_SECRET", ""),
                testnet=os.getenv("TESTNET", "true").lower() == "true",
                proxy=os.getenv("HTTP_PROXY") or os.getenv("HTTPS_PROXY") or "",
            )
        )
