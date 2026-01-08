"""WebSocket 订单簿采集器 - L2_BOOK → 百分比聚合 → TimescaleDB

复用 K 线采集器模式：批量写入 + 缺口巡检 + 自动重连
"""
from __future__ import annotations

import asyncio
import logging
import sys
import threading
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path
from typing import Dict, List, Optional

from ..adapters.ccxt import load_symbols, normalize_symbol
from ..adapters.cryptofeed import preload_symbols
from ..adapters.metrics import metrics
from ..adapters.timescale import TimescaleAdapter
from ..config import settings

# 添加 libs/common 到路径
_libs_path = Path(__file__).parent.parent.parent.parent.parent.parent / "libs" / "common"
if str(_libs_path) not in sys.path:
    sys.path.insert(0, str(_libs_path))

logger = logging.getLogger("ws.book_depth")

# 聚合百分比档位: ±1%, ±2%, ±3%, ±4%, ±5%
PERCENTAGE_LEVELS = [-5, -4, -3, -2, -1, 1, 2, 3, 4, 5]


@dataclass
class BookDepthRow:
    """订单簿深度行"""
    timestamp: datetime
    exchange: str
    symbol: str
    percentage: int
    depth: Decimal
    notional: Decimal


class BookDepthCollector:
    """WebSocket 订单簿采集器 - 时间窗口批量写入

    数据流: L2_BOOK snapshot → 按百分比聚合 → 批量写入 raw.crypto_book_depth
    """

    FLUSH_WINDOW = 10.0  # 订单簿更新频繁，10 秒窗口
    MAX_BUFFER = 5000    # 10 个档位 * 300 币种 = 3000，留余量

    def __init__(self):
        self._ts = TimescaleAdapter()
        self._symbols = self._load_symbols()
        self._buffer: List[dict] = []
        self._buffer_lock = asyncio.Lock()
        self._last_data_time: float = 0
        self._flush_task: Optional[asyncio.Task] = None
        self._stop_event = threading.Event()

    def _load_symbols(self) -> Dict[str, str]:
        """加载交易对映射: cryptofeed 格式 -> 标准格式
        
        优先使用 config/.env 的 SYMBOLS_GROUPS 配置，
        若为 auto/all 则从交易所加载全部。
        """
        from symbols import get_configured_symbols
        
        configured = get_configured_symbols()
        if configured:
            # 使用配置的币种
            raw = [s if s.endswith("USDT") else f"{s}USDT" for s in configured]
            logger.info("使用配置的 %d 个币种 (SYMBOLS_GROUPS)", len(raw))
        else:
            # auto/all 模式，从交易所加载
            raw = load_symbols(settings.ccxt_exchange)
            if not raw:
                raise RuntimeError("未加载到交易对")
            logger.info("使用交易所全部 %d 个币种 (auto/all 模式)", len(raw))
        
        mapping = {}
        for s in raw:
            n = normalize_symbol(s)
            if n:
                mapping[f"{n[:-4]}-USDT-PERP"] = n
        preload_symbols(list(mapping.values()))
        logger.info("加载 %d 个交易对", len(mapping))
        return mapping

    def _aggregate_book(self, mid_price: float, bids: list, asks: list) -> List[tuple]:
        """将订单簿聚合到百分比档位

        Args:
            mid_price: 中间价 (best_bid + best_ask) / 2
            bids: [(price, size), ...] 买单
            asks: [(price, size), ...] 卖单

        Returns:
            [(percentage, depth, notional), ...] 10 个档位
        """
        if mid_price <= 0:
            return []

        results = []
        for pct in PERCENTAGE_LEVELS:
            if pct < 0:
                # 负百分比: 买单侧 (价格低于中间价)
                threshold = mid_price * (1 + pct / 100)  # e.g. -5% → 0.95 * mid
                depth = Decimal(0)
                notional = Decimal(0)
                for price, size in bids:
                    if price >= threshold:
                        depth += Decimal(str(size))
                        notional += Decimal(str(price)) * Decimal(str(size))
            else:
                # 正百分比: 卖单侧 (价格高于中间价)
                threshold = mid_price * (1 + pct / 100)  # e.g. +5% → 1.05 * mid
                depth = Decimal(0)
                notional = Decimal(0)
                for price, size in asks:
                    if price <= threshold:
                        depth += Decimal(str(size))
                        notional += Decimal(str(price)) * Decimal(str(size))

            results.append((pct, depth, notional))

        return results

    async def _on_book(self, book, receipt_ts: float) -> None:
        """订单簿回调 - 聚合后缓冲"""
        sym = self._symbols.get(book.symbol)
        if not sym:
            return

        # 获取最优买卖价计算中间价
        # cryptofeed 的 book 对象: book.book.bids/asks 是 SortedDict
        # .index(0) 返回 (price, size) 元组
        if not book.book or not book.book.bids or not book.book.asks:
            return

        try:
            best_bid_price, _ = book.book.bids.index(0)
            best_ask_price, _ = book.book.asks.index(0)
            mid_price = (float(best_bid_price) + float(best_ask_price)) / 2
        except (IndexError, TypeError):
            return

        # 转换订单簿格式: items() 返回 [(price, size), ...]
        bids = [(float(p), float(s)) for p, s in book.book.bids.items()]
        asks = [(float(p), float(s)) for p, s in book.book.asks.items()]

        # 聚合到百分比档位
        aggregated = self._aggregate_book(mid_price, bids, asks)
        if not aggregated:
            return

        ts = datetime.fromtimestamp(book.timestamp, tz=timezone.utc)
        rows = [
            {
                "timestamp": ts,
                "exchange": settings.db_exchange,
                "symbol": sym,
                "percentage": pct,
                "depth": depth,
                "notional": notional,
            }
            for pct, depth, notional in aggregated
        ]

        async with self._buffer_lock:
            self._buffer.extend(rows)
            self._last_data_time = time.monotonic()

            if len(self._buffer) >= self.MAX_BUFFER:
                await self._flush()
            elif self._flush_task is None or self._flush_task.done():
                self._flush_task = asyncio.create_task(self._delayed_flush())

    async def _delayed_flush(self) -> None:
        """延迟刷新"""
        await asyncio.sleep(self.FLUSH_WINDOW)
        async with self._buffer_lock:
            if time.monotonic() - self._last_data_time >= self.FLUSH_WINDOW:
                await self._flush()

    async def _flush(self) -> None:
        """刷新缓冲区到数据库"""
        if not self._buffer:
            return

        rows = self._buffer.copy()
        self._buffer.clear()

        try:
            n = await asyncio.to_thread(self._upsert_book_depth, rows)
            metrics.inc("book_depth_written", n)
            logger.debug("批量写入 %d 条订单簿数据", n)
        except Exception as e:
            logger.error("批量写入失败: %s", e)

    def _upsert_book_depth(self, rows: List[dict]) -> int:
        """写入订单簿数据到 raw.crypto_book_depth"""
        if not rows:
            return 0

        from psycopg import sql

        cols = ["timestamp", "exchange", "symbol", "percentage", "depth", "notional"]
        conflict_keys = ["exchange", "symbol", "timestamp", "percentage"]
        update_cols = ["depth", "notional"]

        temp_table = f"temp_book_depth_{int(time.time() * 1000)}"

        with self._ts.connection() as conn:
            with conn.cursor() as cur:
                # 创建临时表
                cur.execute(sql.SQL("""
                    CREATE TEMP TABLE {temp} (LIKE raw.crypto_book_depth INCLUDING DEFAULTS)
                    ON COMMIT DROP
                """).format(temp=sql.Identifier(temp_table)))

                # COPY 写入临时表
                with cur.copy(sql.SQL("COPY {temp} ({cols}) FROM STDIN").format(
                    temp=sql.Identifier(temp_table),
                    cols=sql.SQL(", ").join(map(sql.Identifier, cols))
                )) as copy:
                    for row in rows:
                        copy.write_row(tuple(row[c] for c in cols))

                # Upsert 到目标表
                cur.execute(sql.SQL("""
                    INSERT INTO raw.crypto_book_depth ({cols})
                    SELECT {cols} FROM {temp}
                    ON CONFLICT ({conflict}) DO UPDATE SET
                        {updates}
                """).format(
                    cols=sql.SQL(", ").join(map(sql.Identifier, cols)),
                    temp=sql.Identifier(temp_table),
                    conflict=sql.SQL(", ").join(map(sql.Identifier, conflict_keys)),
                    updates=sql.SQL(", ").join(
                        sql.SQL("{c} = EXCLUDED.{c}").format(c=sql.Identifier(c))
                        for c in update_cols
                    )
                ))
                n = cur.rowcount

            conn.commit()
        return n if n > 0 else len(rows)

    def _on_book_sync(self, book, receipt_ts: float) -> None:
        """同步回调包装器"""
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                asyncio.create_task(self._on_book(book, receipt_ts))
            else:
                asyncio.run(self._on_book(book, receipt_ts))
        except RuntimeError:
            asyncio.run(self._on_book(book, receipt_ts))

    def run(self) -> None:
        """运行采集器"""
        from cryptofeed import FeedHandler
        from cryptofeed.defines import L2_BOOK
        from cryptofeed.exchanges import BinanceFutures

        log_file = settings.log_dir / "cryptofeed_book.log"
        handler = FeedHandler(config={
            "uvloop": False,
            "log": {"filename": str(log_file), "level": "INFO"}
        })

        kw = {
            "symbols": list(self._symbols.keys()),
            "channels": [L2_BOOK],
            "callbacks": {L2_BOOK: self._on_book_sync},
            "timeout": 60,
        }
        if settings.http_proxy:
            kw["http_proxy"] = settings.http_proxy

        handler.add_feed(BinanceFutures(**kw))
        logger.info("启动 BookDepth WSS: 符号=%d", len(self._symbols))

        try:
            handler.run()
        finally:
            asyncio.run(self._final_flush())
            self._ts.close()

    async def _final_flush(self) -> None:
        """最终刷新"""
        async with self._buffer_lock:
            await self._flush()


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(name)s - %(message)s"
    )
    BookDepthCollector().run()


if __name__ == "__main__":
    main()
