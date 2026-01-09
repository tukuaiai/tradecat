"""WebSocket 订单簿采集器 - 双层采样存储

行业最成熟方案: 双层采样
- L1 快速层 (1s): top-of-book + 核心指标 → raw.crypto_order_book_tick
- L2 全量层 (5s): 完整盘口 + 深度统计 → raw.crypto_order_book

配置项 (config/.env):
    ORDER_BOOK_TICK_INTERVAL: 快速采样间隔，默认 1 秒
    ORDER_BOOK_FULL_INTERVAL: 全量采样间隔，默认 5 秒
    ORDER_BOOK_DEPTH: 每侧档位数，默认 1000
    ORDER_BOOK_RETENTION_DAYS: 保留天数，默认 30
    ORDER_BOOK_SYMBOLS: 可选，逗号分隔
"""
from __future__ import annotations

import asyncio
import json
import logging
import os
import sys
import time
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any, Dict, List, Optional

from ..adapters.ccxt import load_symbols, normalize_symbol
from ..adapters.cryptofeed import preload_symbols
from ..adapters.metrics import metrics
from ..adapters.timescale import TimescaleAdapter
from ..config import settings

_libs_path = Path(__file__).parent.parent.parent.parent.parent.parent / "libs" / "common"
if str(_libs_path) not in sys.path:
    sys.path.insert(0, str(_libs_path))

logger = logging.getLogger("ws.order_book")


def _get_config() -> dict:
    """读取配置"""
    return {
        "tick_interval": float(os.getenv("ORDER_BOOK_TICK_INTERVAL", "1")),
        "full_interval": float(os.getenv("ORDER_BOOK_FULL_INTERVAL", "5")),
        "depth": int(os.getenv("ORDER_BOOK_DEPTH", "1000")),
        "retention_days": int(os.getenv("ORDER_BOOK_RETENTION_DAYS", "30")),
        "symbols": os.getenv("ORDER_BOOK_SYMBOLS", ""),
    }


class OrderBookCollector:
    """订单簿采集器 - 双层采样存储
    
    行业最成熟方案:
    - L1 Tick 层 (1s): bid1/ask1 + spread + imbalance → 轻量表
    - L2 Full 层 (5s): 完整盘口 + 深度统计 → 完整表
    
    优势:
    - 高频信号 (价差/失衡) 1 秒级捕获
    - 完整盘口 5 秒级采样，平衡存储
    - 分离热/温数据，查询更高效
    """

    MAX_TICK_BUFFER = 5000   # tick 行小，可缓冲更多
    MAX_FULL_BUFFER = 1000

    def __init__(self):
        self._cfg = _get_config()
        self._ts = TimescaleAdapter()
        self._symbols = self._load_symbols()
        
        # 双缓冲区
        self._tick_buffer: List[dict] = []
        self._full_buffer: List[dict] = []
        self._buffer_lock = asyncio.Lock()
        
        # 时间戳与序号追踪
        self._last_tick: Dict[str, float] = {}
        self._last_full: Dict[str, float] = {}
        self._last_seq: Dict[str, int] = {}  # lastUpdateId 乱序检测
        
        self._flush_task: Optional[asyncio.Task] = None
        
        # 统计指标
        self._stats = {
            "received": 0,
            "written_tick": 0,
            "written_full": 0,
            "errors": 0,
            "out_of_order": 0,
        }

    def _load_symbols(self) -> Dict[str, str]:
        """加载交易对映射"""
        from symbols import get_configured_symbols

        if self._cfg["symbols"]:
            raw = [s.strip().upper() for s in self._cfg["symbols"].split(",") if s.strip()]
            raw = [s if s.endswith("USDT") else f"{s}USDT" for s in raw]
            logger.info("使用 ORDER_BOOK_SYMBOLS: %d 个币种", len(raw))
        else:
            configured = get_configured_symbols()
            if configured:
                raw = [s if s.endswith("USDT") else f"{s}USDT" for s in configured]
                logger.info("使用 SYMBOLS_GROUPS: %d 个币种", len(raw))
            else:
                raw = load_symbols(settings.ccxt_exchange)
                if not raw:
                    raise RuntimeError("未加载到交易对")
                logger.info("使用交易所全部: %d 个币种", len(raw))

        mapping = {}
        for s in raw:
            n = normalize_symbol(s)
            if n:
                mapping[f"{n[:-4]}-USDT-PERP"] = n
        preload_symbols(list(mapping.values()))
        return mapping

    def _compute_depth_stats(
        self, mid_price: float, bids: List[tuple], asks: List[tuple]
    ) -> Dict[str, Any]:
        """计算深度统计"""
        stats = {
            "bid_depth_1pct": Decimal(0),
            "ask_depth_1pct": Decimal(0),
            "bid_depth_5pct": Decimal(0),
            "ask_depth_5pct": Decimal(0),
            "bid_notional_1pct": Decimal(0),
            "ask_notional_1pct": Decimal(0),
            "bid_notional_5pct": Decimal(0),
            "ask_notional_5pct": Decimal(0),
        }
        
        if mid_price <= 0:
            return stats
        
        thresh_1pct = mid_price * 0.01
        thresh_5pct = mid_price * 0.05
        
        for price, size in bids:
            diff = mid_price - price
            p_dec, s_dec = Decimal(str(price)), Decimal(str(size))
            notional = p_dec * s_dec
            if diff <= thresh_1pct:
                stats["bid_depth_1pct"] += s_dec
                stats["bid_notional_1pct"] += notional
            if diff <= thresh_5pct:
                stats["bid_depth_5pct"] += s_dec
                stats["bid_notional_5pct"] += notional
            else:
                break
        
        for price, size in asks:
            diff = price - mid_price
            p_dec, s_dec = Decimal(str(price)), Decimal(str(size))
            notional = p_dec * s_dec
            if diff <= thresh_1pct:
                stats["ask_depth_1pct"] += s_dec
                stats["ask_notional_1pct"] += notional
            if diff <= thresh_5pct:
                stats["ask_depth_5pct"] += s_dec
                stats["ask_notional_5pct"] += notional
            else:
                break
        
        return stats

    def _build_tick_row(
        self, sym: str, ts: datetime, bids_dict: dict, asks_dict: dict
    ) -> Optional[dict]:
        """构建 L1 tick 行 (轻量)"""
        if not bids_dict or not asks_dict:
            return None
        
        bid_prices = sorted(bids_dict.keys(), reverse=True)
        ask_prices = sorted(asks_dict.keys())
        if not bid_prices or not ask_prices:
            return None
        
        bid1_p, bid1_s = float(bid_prices[0]), float(bids_dict[bid_prices[0]])
        ask1_p, ask1_s = float(ask_prices[0]), float(asks_dict[ask_prices[0]])
        mid = (bid1_p + ask1_p) / 2
        spread = ask1_p - bid1_p
        spread_bps = (spread / mid * 10000) if mid > 0 else 0
        
        # 快速计算 1% 深度 (只取前 50 档近似)
        bid_depth = sum(float(bids_dict[p]) for p in bid_prices[:50] if mid - float(p) <= mid * 0.01)
        ask_depth = sum(float(asks_dict[p]) for p in ask_prices[:50] if float(p) - mid <= mid * 0.01)
        total = bid_depth + ask_depth
        imbalance = (bid_depth - ask_depth) / total if total > 0 else 0
        
        return {
            "timestamp": ts,
            "exchange": settings.db_exchange,
            "symbol": sym,
            "mid_price": Decimal(str(mid)),
            "spread_bps": Decimal(str(round(spread_bps, 4))),
            "bid1_price": Decimal(str(bid1_p)),
            "bid1_size": Decimal(str(bid1_s)),
            "ask1_price": Decimal(str(ask1_p)),
            "ask1_size": Decimal(str(ask1_s)),
            "bid_depth_1pct": Decimal(str(bid_depth)),
            "ask_depth_1pct": Decimal(str(ask_depth)),
            "imbalance": Decimal(str(round(imbalance, 6))),
        }

    def _build_full_row(
        self, sym: str, ts: datetime, bids_dict: dict, asks_dict: dict,
        last_update_id: Optional[int] = None, transaction_time: Optional[datetime] = None
    ) -> Optional[dict]:
        """构建 L2 full 行 - 保留原始格式
        
        原始 Binance 格式:
            lastUpdateId, E (event_time), T (transaction_time)
            bids: [["price", "qty"], ...], asks: [["price", "qty"], ...]
        """
        if not bids_dict or not asks_dict:
            return None
        
        depth = self._cfg["depth"]
        bid_prices = sorted(bids_dict.keys(), reverse=True)[:depth]
        ask_prices = sorted(asks_dict.keys())[:depth]
        if not bid_prices or not ask_prices:
            return None
        
        bid1_p, bid1_s = float(bid_prices[0]), float(bids_dict[bid_prices[0]])
        ask1_p, ask1_s = float(ask_prices[0]), float(asks_dict[ask_prices[0]])
        mid = (bid1_p + ask1_p) / 2
        spread = ask1_p - bid1_p
        spread_bps = (spread / mid * 10000) if mid > 0 else 0
        
        # 深度统计
        bids_list = [(float(p), float(bids_dict[p])) for p in bid_prices]
        asks_list = [(float(p), float(asks_dict[p])) for p in ask_prices]
        stats = self._compute_depth_stats(mid, bids_list, asks_list)
        
        total_1pct = stats["bid_depth_1pct"] + stats["ask_depth_1pct"]
        imbalance = float((stats["bid_depth_1pct"] - stats["ask_depth_1pct"]) / total_1pct) if total_1pct > 0 else 0
        
        # 原始格式: [["price", "qty"], ...] 字符串保留精度
        bids_raw = [[str(p), str(bids_dict[p])] for p in bid_prices]
        asks_raw = [[str(p), str(asks_dict[p])] for p in ask_prices]
        
        return {
            "timestamp": ts,
            "exchange": settings.db_exchange,
            "symbol": sym,
            "last_update_id": last_update_id,
            "transaction_time": transaction_time,
            "depth": len(bids_list),
            "mid_price": Decimal(str(mid)),
            "spread": Decimal(str(spread)),
            "spread_bps": Decimal(str(round(spread_bps, 4))),
            "bid1_price": Decimal(str(bid1_p)),
            "bid1_size": Decimal(str(bid1_s)),
            "ask1_price": Decimal(str(ask1_p)),
            "ask1_size": Decimal(str(ask1_s)),
            **stats,
            "imbalance": Decimal(str(round(imbalance, 6))),
            "bids": json.dumps(bids_raw),
            "asks": json.dumps(asks_raw),
        }

    async def _on_book(self, book, receipt_ts: float) -> None:
        """订单簿回调 - 双层采样"""
        sym = self._symbols.get(book.symbol)
        if not sym:
            return
        if not book.book or not book.book.bids or not book.book.asks:
            return

        now = time.time()
        self._last_msg_time = now  # 心跳更新
        
        ts = datetime.fromtimestamp(book.timestamp, tz=timezone.utc)
        bids_dict = book.book.bids.to_dict()
        asks_dict = book.book.asks.to_dict()
        
        # 提取原始元数据 (cryptofeed: sequence_number = lastUpdateId)
        last_update_id = getattr(book, 'sequence_number', None)
        
        # 延迟监控: receipt_ts - event_ts
        delay_ms = int((receipt_ts - book.timestamp) * 1000)
        if delay_ms > 0:
            self._stats["total_delay_ms"] += delay_ms
            if delay_ms > self._stats["max_delay_ms"]:
                self._stats["max_delay_ms"] = delay_ms
            if delay_ms > 5000:  # 延迟超过 5 秒告警
                logger.warning("高延迟: %s delay=%dms", sym, delay_ms)
        
        self._stats["received"] += 1
        
        # 乱序检测: 如果 lastUpdateId 倒退则跳过
        if last_update_id is not None:
            prev_id = self._last_seq.get(sym, 0)
            if last_update_id < prev_id:
                self._stats["out_of_order"] += 1
                metrics.inc("order_book_out_of_order")
                logger.warning("乱序跳过: %s seq %d < %d", sym, last_update_id, prev_id)
                return
            self._last_seq[sym] = last_update_id

        async with self._buffer_lock:
            # L1 Tick 层 (高频)
            if now - self._last_tick.get(sym, 0) >= self._cfg["tick_interval"]:
                self._last_tick[sym] = now
                tick_row = self._build_tick_row(sym, ts, bids_dict, asks_dict)
                if tick_row:
                    self._tick_buffer.append(tick_row)
            
            # L2 Full 层 (低频)
            if now - self._last_full.get(sym, 0) >= self._cfg["full_interval"]:
                self._last_full[sym] = now
                full_row = self._build_full_row(
                    sym, ts, bids_dict, asks_dict,
                    last_update_id=last_update_id
                )
                if full_row:
                    self._full_buffer.append(full_row)
            
            # 触发刷新
            if len(self._tick_buffer) >= self.MAX_TICK_BUFFER or len(self._full_buffer) >= self.MAX_FULL_BUFFER:
                await self._flush()
            elif self._flush_task is None or self._flush_task.done():
                self._flush_task = asyncio.create_task(self._delayed_flush())

    async def _delayed_flush(self) -> None:
        await asyncio.sleep(self._cfg["tick_interval"])
        async with self._buffer_lock:
            await self._flush()

    async def _flush(self) -> None:
        tick_rows = self._tick_buffer.copy()
        full_rows = self._full_buffer.copy()
        self._tick_buffer.clear()
        self._full_buffer.clear()

        if tick_rows:
            try:
                n = await asyncio.to_thread(self._write_tick_rows, tick_rows)
                self._stats["written_tick"] += n
                metrics.inc("order_book_tick_written", n)
                logger.debug("写入 %d 条 tick 快照", n)
            except Exception as e:
                self._stats["errors"] += 1
                metrics.inc("order_book_write_errors")
                logger.error("tick 写入失败 (%d 条丢失): %s", len(tick_rows), e, exc_info=True)

        if full_rows:
            try:
                n = await asyncio.to_thread(self._write_full_rows, full_rows)
                self._stats["written_full"] += n
                metrics.inc("order_book_full_written", n)
                logger.info("写入 %d 条 full 快照", n)
            except Exception as e:
                self._stats["errors"] += 1
                metrics.inc("order_book_write_errors")
                logger.error("full 写入失败 (%d 条丢失): %s", len(full_rows), e, exc_info=True)

    def _write_tick_rows(self, rows: List[dict]) -> int:
        """写入 tick 表"""
        if not rows:
            return 0
        from psycopg import sql

        cols = [
            "exchange", "symbol", "timestamp",
            "mid_price", "spread_bps",
            "bid1_price", "bid1_size", "ask1_price", "ask1_size",
            "bid_depth_1pct", "ask_depth_1pct", "imbalance",
        ]
        temp = f"temp_tick_{int(time.time() * 1000)}"

        with self._ts.connection() as conn:
            with conn.cursor() as cur:
                cur.execute(sql.SQL(
                    "CREATE TEMP TABLE {t} (LIKE raw.crypto_order_book_tick INCLUDING DEFAULTS) ON COMMIT DROP"
                ).format(t=sql.Identifier(temp)))

                with cur.copy(sql.SQL("COPY {t} ({c}) FROM STDIN").format(
                    t=sql.Identifier(temp),
                    c=sql.SQL(", ").join(map(sql.Identifier, cols))
                )) as copy:
                    for r in rows:
                        copy.write_row(tuple(r[c] for c in cols))

                cur.execute(sql.SQL("""
                    INSERT INTO raw.crypto_order_book_tick ({c})
                    SELECT {c} FROM {t}
                    ON CONFLICT (exchange, symbol, timestamp) DO UPDATE SET
                        mid_price = EXCLUDED.mid_price,
                        spread_bps = EXCLUDED.spread_bps,
                        bid1_price = EXCLUDED.bid1_price,
                        bid1_size = EXCLUDED.bid1_size,
                        ask1_price = EXCLUDED.ask1_price,
                        ask1_size = EXCLUDED.ask1_size,
                        bid_depth_1pct = EXCLUDED.bid_depth_1pct,
                        ask_depth_1pct = EXCLUDED.ask_depth_1pct,
                        imbalance = EXCLUDED.imbalance
                """).format(
                    c=sql.SQL(", ").join(map(sql.Identifier, cols)),
                    t=sql.Identifier(temp),
                ))
                n = cur.rowcount
            conn.commit()
        return n if n > 0 else len(rows)

    def _write_full_rows(self, rows: List[dict]) -> int:
        """写入 full 表"""
        if not rows:
            return 0
        from psycopg import sql

        cols = [
            "exchange", "symbol", "timestamp",
            "last_update_id", "transaction_time", "depth",
            "mid_price", "spread", "spread_bps",
            "bid1_price", "bid1_size", "ask1_price", "ask1_size",
            "bid_depth_1pct", "ask_depth_1pct", "bid_depth_5pct", "ask_depth_5pct",
            "bid_notional_1pct", "ask_notional_1pct", "bid_notional_5pct", "ask_notional_5pct",
            "imbalance", "bids", "asks",
        ]
        update_cols = [c for c in cols if c not in ("timestamp", "exchange", "symbol")]
        temp = f"temp_full_{int(time.time() * 1000)}"

        with self._ts.connection() as conn:
            with conn.cursor() as cur:
                cur.execute(sql.SQL(
                    "CREATE TEMP TABLE {t} (LIKE raw.crypto_order_book INCLUDING DEFAULTS) ON COMMIT DROP"
                ).format(t=sql.Identifier(temp)))

                with cur.copy(sql.SQL("COPY {t} ({c}) FROM STDIN").format(
                    t=sql.Identifier(temp),
                    c=sql.SQL(", ").join(map(sql.Identifier, cols))
                )) as copy:
                    for r in rows:
                        copy.write_row(tuple(r[c] for c in cols))

                cur.execute(sql.SQL("""
                    INSERT INTO raw.crypto_order_book ({c})
                    SELECT {c} FROM {t}
                    ON CONFLICT (exchange, symbol, timestamp) DO UPDATE SET
                        {updates}
                """).format(
                    c=sql.SQL(", ").join(map(sql.Identifier, cols)),
                    t=sql.Identifier(temp),
                    updates=sql.SQL(", ").join(
                        sql.SQL("{col} = EXCLUDED.{col}").format(col=sql.Identifier(c))
                        for c in update_cols
                    ),
                ))
                n = cur.rowcount
            conn.commit()
        return n if n > 0 else len(rows)

    def run(self) -> None:
        """运行采集器"""
        from cryptofeed import FeedHandler
        from cryptofeed.defines import L2_BOOK
        from cryptofeed.exchanges import BinanceFutures

        cfg = self._cfg
        logger.info("双层采样配置: tick=%gs, full=%gs, depth=%d, symbols=%d",
                    cfg["tick_interval"], cfg["full_interval"], cfg["depth"], len(self._symbols))

        log_file = settings.log_dir / "cryptofeed_orderbook.log"
        handler = FeedHandler(config={"uvloop": False, "log": {"filename": str(log_file), "level": "INFO"}})

        kw = {
            "symbols": list(self._symbols.keys()),
            "channels": [L2_BOOK],
            "callbacks": {L2_BOOK: self._on_book},
            "timeout": 60,
        }
        if settings.http_proxy:
            kw["http_proxy"] = settings.http_proxy

        handler.add_feed(BinanceFutures(**kw))
        logger.info("启动 OrderBook WSS (双层采样模式)")

        # 定时统计任务
        async def _stats_reporter():
            while True:
                await asyncio.sleep(60)
                s = self._stats
                avg_delay = s["total_delay_ms"] // max(s["received"], 1)
                # 心跳检测
                idle_sec = int(time.time() - self._last_msg_time) if self._last_msg_time > 0 else 0
                if idle_sec > 30:
                    logger.warning("心跳超时: %ds 无数据", idle_sec)
                logger.info(
                    "统计: received=%d, tick=%d, full=%d, errors=%d, oos=%d, delay_avg=%dms, delay_max=%dms",
                    s["received"], s["written_tick"], s["written_full"],
                    s["errors"], s["out_of_order"], avg_delay, s["max_delay_ms"]
                )

        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.create_task(_stats_reporter())
            handler.run()
        finally:
            self._log_final_stats()
            asyncio.run(self._final_flush())
            self._ts.close()
    
    def _log_final_stats(self) -> None:
        """输出最终统计"""
        s = self._stats
        avg_delay = s["total_delay_ms"] // max(s["received"], 1)
        logger.info(
            "采集结束: received=%d, tick=%d, full=%d, errors=%d, oos=%d, delay_avg=%dms, delay_max=%dms",
            s["received"], s["written_tick"], s["written_full"],
            s["errors"], s["out_of_order"], avg_delay, s["max_delay_ms"]
        )

    async def _final_flush(self) -> None:
        async with self._buffer_lock:
            await self._flush()


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(name)s - %(message)s")
    OrderBookCollector().run()


if __name__ == "__main__":
    main()
