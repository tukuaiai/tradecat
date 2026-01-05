"""WebSocket 数据源 - 使用 cryptofeed 订阅行情与成交"""
import threading
from decimal import Decimal
from typing import Callable, Dict, List, Optional

from cryptofeed import FeedHandler
from cryptofeed.exchanges import BinanceFutures
from cryptofeed.defines import L2_BOOK, TRADES


def ccxt_to_cf_symbol(symbol: str) -> str:
    """将 ccxt 符号转换为 cryptofeed 符号格式，例如 BTC/USDT:USDT -> BTC-USDT-PERP"""
    base, rest = symbol.split("/")
    quote = rest.split(":")[0]
    return f"{base}-{quote}-PERP"


def cf_to_ccxt_symbol(symbol: str) -> str:
    """将 cryptofeed 符号转换为 ccxt 符号格式，反向映射"""
    parts = symbol.split("-")
    if len(parts) >= 2:
        return f"{parts[0]}/{parts[1]}:USDT"
    return symbol


class WSFeed:
    """基于 cryptofeed 的行情/成交订阅"""

    def __init__(self, exchange: str, symbols: List[str], proxy: Optional[str] = None):
        self.exchange = exchange
        self.symbols_ccxt = symbols
        self.symbols_cf = [ccxt_to_cf_symbol(s) for s in symbols]
        self.proxy = proxy
        self._handler: Optional[FeedHandler] = None
        self._thread: Optional[threading.Thread] = None
        self._mid_prices: Dict[str, float] = {}
        self._trade_listeners: List[Callable[[str, float, float, Optional[float]], None]] = []
        self._lock = threading.Lock()

    # -------------- 公共接口 --------------
    def start(self):
        """启动订阅（后台线程）"""
        if self._thread:
            return
        self._handler = FeedHandler()
        callbacks = {
            L2_BOOK: self._on_book,
            TRADES: self._on_trade,
        }
        # cryptofeed 代理参数
        feed_kwargs = {}
        if self.proxy:
            feed_kwargs["ws_proxy"] = self.proxy
        self._handler.add_feed(
            BinanceFutures,
            channels=[L2_BOOK, TRADES],
            symbols=self.symbols_cf,
            callbacks=callbacks,
            **feed_kwargs,
        )
        self._thread = threading.Thread(
            target=self._handler.run, kwargs={"install_signal_handlers": False}, daemon=True
        )
        self._thread.start()

    def stop(self):
        if self._handler:
            self._handler.stop()
        if self._thread:
            self._thread.join(timeout=5)
            self._thread = None

    def get_mid_price(self, symbol_ccxt: str) -> Optional[float]:
        with self._lock:
            return self._mid_prices.get(symbol_ccxt)

    def register_trade_listener(self, listener: Callable[[str, float, float, Optional[float]], None]):
        """listener(symbol_ccxt, price, amount, mid)"""
        self._trade_listeners.append(listener)

    # -------------- 回调 --------------
    async def _on_book(self, feed, symbol, book, timestamp, receipt_timestamp):
        bids = book.book.bids
        asks = book.book.asks
        if not bids or not asks:
            return
        best_bid = max(bids)
        best_ask = min(asks)
        mid = float((Decimal(best_bid) + Decimal(best_ask)) / Decimal(2))
        symbol_ccxt = cf_to_ccxt_symbol(symbol)
        with self._lock:
            self._mid_prices[symbol_ccxt] = mid

    async def _on_trade(self, feed, symbol, order_id, timestamp, side, amount, price, receipt_timestamp):
        symbol_ccxt = cf_to_ccxt_symbol(symbol)
        mid = self.get_mid_price(symbol_ccxt)
        for listener in self._trade_listeners:
            try:
                listener(symbol_ccxt, float(price), float(amount), mid)
            except Exception:
                # 保持订阅不中断
                continue
