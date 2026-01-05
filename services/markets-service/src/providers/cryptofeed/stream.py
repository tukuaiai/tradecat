"""Cryptofeed WebSocket 流处理器"""
from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, List

from cryptofeed import FeedHandler
from cryptofeed.defines import CANDLES
from cryptofeed.exchanges import Binance

# 将项目根目录加入 sys.path，以便复用 libs.common.symbols 的分组解析
PROJECT_ROOT = Path(__file__).resolve().parents[6]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from libs.common import symbols as symbol_config  # noqa: E402


@dataclass
class CandleEvent:
    """K线事件"""
    exchange: str
    symbol: str
    timestamp: float
    open: float
    high: float
    low: float
    close: float
    volume: float
    closed: bool


class CryptoFeedStream:
    """Cryptofeed WebSocket 流 - 用于实时数据采集"""

    def __init__(self, exchange: str = "binance"):
        self.exchange = exchange
        self._handler: FeedHandler | None = None
        self._callbacks: dict[str, Callable] = {}

    def on_candle(self, callback: Callable[[CandleEvent], None]):
        """注册 K 线回调"""
        self._callbacks["candle"] = callback

    async def _candle_callback(self, candle, receipt_timestamp):
        """内部 K 线回调"""
        if "candle" in self._callbacks:
            event = CandleEvent(
                exchange=candle.exchange,
                symbol=candle.symbol,
                timestamp=candle.timestamp,
                open=float(candle.open),
                high=float(candle.high),
                low=float(candle.low),
                close=float(candle.close),
                volume=float(candle.volume),
                closed=candle.closed,
            )
            self._callbacks["candle"](event)

    def subscribe(self, symbols: list[str], channels: list[str] = None):
        """订阅交易对"""
        channels = channels or [CANDLES]

        self._handler = FeedHandler()

        # 根据交易所选择
        exchange_cls = Binance  # 可扩展其他交易所

        callbacks = {}
        if CANDLES in channels:
            callbacks[CANDLES] = self._candle_callback

        self._handler.add_feed(
            exchange_cls(
                symbols=symbols,
                channels=channels,
                callbacks=callbacks
            )
        )

    def run(self):
        """运行 (阻塞)"""
        if self._handler:
            self._handler.run()

    def stop(self):
        """停止"""
        if self._handler:
            self._handler.stop()


# ==================== 分组解析辅助 ====================
def _to_binance_perp(symbol: str) -> str:
    """将 BTCUSDT -> BTC-USDT-PERP（Binance 合约标记）"""
    sym = symbol.strip().upper()
    if sym.endswith("USDT"):
        base = sym[:-4]
        return f"{base}-USDT-PERP"
    return sym


def _from_binance_perp(symbol: str) -> str:
    """将 Binance 永续标记还原为标准符号 BTCUSDT"""
    if "-USDT-PERP" in symbol:
        return symbol.replace("-USDT-PERP", "USDT")
    return symbol.replace("-", "")


def load_symbols_from_env() -> List[str]:
    """
    读取 env 中的分组配置，生成 Cryptofeed 可用的交易对列表。
    - 若 SYMBOLS_GROUPS=auto/all 返回空列表（调用方决定 fallback）
    - 支持 SYMBOLS_EXTRA/SYMBOLS_EXCLUDE 处理
    """
    cfg = symbol_config.get_configured_symbols()
    if cfg is None:
        return []
    return [_to_binance_perp(sym) for sym in cfg]
