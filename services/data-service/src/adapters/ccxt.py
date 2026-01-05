"""CCXT 适配器 - 使用全局限流器"""
from __future__ import annotations

import asyncio
import logging
import os
import time
from datetime import datetime, timezone
from typing import Dict, List, Optional

import ccxt

from adapters.rate_limiter import acquire, parse_ban, release, set_ban

logger = logging.getLogger(__name__)

_clients: Dict[str, ccxt.Exchange] = {}
_symbols: Dict[str, List[str]] = {}
DEFAULT_PROXY = os.getenv("HTTP_PROXY") or os.getenv("HTTPS_PROXY")


def _parse_list(raw: str) -> List[str]:
    """将逗号分隔的币种字符串解析为大写列表，过滤空项。"""
    return [item.strip().upper() for item in raw.split(",") if item.strip()]


def get_client(exchange: str = "binance") -> ccxt.Exchange:
    if exchange not in _clients:
        cls = getattr(ccxt, exchange, None)
        if not cls:
            raise ValueError(f"不支持: {exchange}")
        _clients[exchange] = cls({
            "enableRateLimit": True,  # 保留内置限流作为双重保护
            "timeout": 30000,
            "proxies": {"http": DEFAULT_PROXY, "https": DEFAULT_PROXY} if DEFAULT_PROXY else None,
            "options": {"defaultType": "swap"},
        })
    return _clients[exchange]


# ========== 币种管理配置 ==========
# 使用共享模块
import sys
from pathlib import Path

_libs_path = str(Path(__file__).parents[4] / "libs")
if _libs_path not in sys.path:
    sys.path.insert(0, _libs_path)
from common.symbols import get_configured_symbols


def load_symbols(exchange: str = "binance") -> List[str]:
    key = f"{exchange}_usdt"
    if key not in _symbols:
        # 先检查是否有配置的币种
        configured = get_configured_symbols()
        if configured:
            _symbols[key] = configured
            logger.info("使用配置币种 %d 个", len(_symbols[key]))
        else:
            # 从交易所获取全部
            acquire(5)
            try:
                client = get_client(exchange)
                client.load_markets()
                all_symbols = sorted({
                    f"{m['base']}USDT" for m in client.markets.values()
                    if m.get("swap") and m.get("settle") == "USDT" and m.get("linear")
                })
                # 应用排除
                exclude = set(_parse_list(os.getenv("SYMBOLS_EXCLUDE", "")))
                extra = _parse_list(os.getenv("SYMBOLS_EXTRA", ""))
                _symbols[key] = [s for s in all_symbols if s not in exclude]
                _symbols[key] = sorted(set(_symbols[key]) | set(extra))
                logger.info("加载 %s USDT永续 %d 个", exchange, len(_symbols[key]))
            finally:
                release()
    return _symbols[key]


def fetch_ohlcv(exchange: str, symbol: str, interval: str = "1m",
               since_ms: Optional[int] = None, limit: int = 1000) -> List[List]:
    symbol = symbol.upper()
    if not symbol.endswith("USDT"):
        return []

    ccxt_sym = f"{symbol[:-4]}/USDT:USDT"

    for attempt in range(3):
        acquire(2)
        try:
            return get_client(exchange).fetch_ohlcv(ccxt_sym, interval, since=since_ms, limit=limit)
        except ccxt.RateLimitExceeded as e:
            # ccxt 会抛出 429/418，解析错误信息
            err_str = str(e)
            if "418" in err_str:
                # 已被 ban，等待更长时间
                ban_time = parse_ban(err_str)
                set_ban(ban_time if ban_time > time.time() else time.time() + 120)
            else:
                # 429 警告，立即停止
                set_ban(time.time() + 60)
            if attempt == 2:
                logger.warning("fetch_ohlcv 限流: %s", e)
                return []
        except (ccxt.NetworkError, ccxt.ExchangeNotAvailable, ccxt.RequestTimeout) as e:
            if attempt == 2:
                logger.warning("fetch_ohlcv 网络错误: %s", e)
                return []
            time.sleep(1 * (2 ** attempt))
        finally:
            release()


def to_rows(exchange: str, symbol: str, candles: List[List], source: str = "ccxt") -> List[dict]:
    return [{
        "exchange": exchange, "symbol": symbol.upper(),
        "bucket_ts": datetime.fromtimestamp(c[0] / 1000, tz=timezone.utc),
        "open": float(c[1]), "high": float(c[2]), "low": float(c[3]),
        "close": float(c[4]), "volume": float(c[5]),
        "quote_volume": None, "trade_count": None, "is_closed": True, "source": source,
        "taker_buy_volume": None, "taker_buy_quote_volume": None,
    } for c in candles if len(c) >= 6]


def normalize_symbol(symbol: str) -> Optional[str]:
    s = symbol.upper().replace("/", "").replace(":", "").replace("-", "")
    return s if s.endswith("USDT") else None


# 兼容旧代码
class _CompatLimiter:
    def acquire(self, w=1): acquire(w)
_limiter = _CompatLimiter()
def _check_and_wait_ban():
    return None
_parse_ban_time = parse_ban
_ban_until = 0
_ban_lock = None

async def async_acquire(weight: int = 1):
    await asyncio.to_thread(acquire, weight)

async def async_check_and_wait_ban():
    pass
