"""
事件驱动指标计算引擎

监听 PostgreSQL NOTIFY 通道，K线闭合后自动触发对应周期计算。

架构:
  启动 → 全量计算（用 Engine）
  candles_1m (NOTIFY) → 触发对应周期增量计算
"""
import json
import logging
import signal
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from queue import Queue
from typing import Dict, List, Optional

import psycopg
import select

from ..config import config

LOG = logging.getLogger("indicator_service.event")

# 周期配置: (周期名, 分钟数, CA刷新延迟秒)
INTERVALS = [
    ("1m", 1, 2),
    ("5m", 5, 5),
    ("15m", 15, 5),
    ("1h", 60, 10),
    ("4h", 240, 10),
    ("1d", 1440, 10),
    ("1w", 10080, 10),
]


@dataclass
class TriggerEvent:
    """触发事件"""
    interval: str
    trigger_time: datetime
    symbols: Optional[List[str]] = None


class EventEngine:
    """事件驱动引擎 - 简化版，直接调用 Engine 计算"""

    def __init__(self,
                 symbols: Optional[List[str]] = None,
                 intervals: Optional[List[str]] = None,
                 workers: int = 4):
        self.symbols = symbols
        self.intervals = intervals or ["1m", "5m", "15m", "1h", "4h", "1d", "1w"]
        self.workers = workers

        self._running = False
        self._trigger_queue: Queue = Queue()
        self._last_triggered: Dict[str, datetime] = {}
        self._initialized = False  # 计算线程已就绪
        self._ready_for_events = False  # 已识别高优先级币种，可以接受 NOTIFY
        self._high_symbols = []
        self._interval_locks: Dict[str, threading.Lock] = {}

        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

    def _signal_handler(self, signum, frame):
        LOG.info(f"收到信号 {signum}，停止...")
        self.stop()

    def stop(self):
        self._running = False

    def run(self):
        """主运行循环"""
        LOG.info("=" * 60)
        LOG.info("事件驱动引擎启动")
        LOG.info("=" * 60)

        self._running = True

        # 计算线程池先启动，保证可并行消费
        calc_thread = threading.Thread(target=self._calculation_loop, daemon=True)
        calc_thread.start()

        # 后台初始化（不会阻塞监听）
        threading.Thread(target=self._init_engine, daemon=True).start()

        # 主线程立即开始监听
        self._listen_loop()

        LOG.info("引擎已停止")

    def _init_engine(self):
        """后台初始化 - 识别高优先级币种并全量计算"""
        from .async_full_engine import get_high_priority_symbols_fast

        # 识别高优先级币种
        LOG.info("识别高优先级币种...")
        t0 = time.time()
        self._high_symbols = list(get_high_priority_symbols_fast(top_n=30))
        LOG.info(f"高优先级: {len(self._high_symbols)} 币种, {time.time()-t0:.1f}s")
        self._ready_for_events = True

        # 启动时全量计算一次（不阻塞通知消费）
        LOG.info("=" * 40)
        LOG.info("调度启动全量计算（后台）...")
        self._trigger_queue.put(TriggerEvent(interval="__full__", trigger_time=datetime.now(timezone.utc)))
        LOG.info("=" * 40)

        self._initialized = True
        LOG.info("计算线程就绪，开始监听事件驱动增量更新...")

    def _listen_loop(self):
        """监听 PostgreSQL NOTIFY"""
        conn = psycopg.connect(config.db_url, autocommit=True)
        conn.execute("LISTEN candle_1m_update")
        conn.execute("LISTEN metrics_5m_update")
        LOG.info("开始监听: candle_1m_update, metrics_5m_update")

        while self._running:
            if select.select([conn], [], [], 1.0)[0]:
                for notify in conn.notifies():
                    self._handle_notify(notify.channel, notify.payload)

        conn.close()

    def _handle_notify(self, channel: str, payload: str):
        """处理 NOTIFY 消息"""
        # 高优先级币种未准备时忽略
        if not self._ready_for_events:
            return

        try:
            data = json.loads(payload)
            is_closed = data.get("is_closed", False)

            if not is_closed:
                return

            if channel == "candle_1m_update":
                bucket_ts = data.get("bucket_ts")
                if bucket_ts:
                    self._schedule_candle_triggers(bucket_ts)

            elif channel == "metrics_5m_update":
                create_time = data.get("create_time")
                if create_time:
                    self._schedule_metrics_triggers(create_time)

        except Exception as e:
            LOG.error(f"处理通知失败: {e}")

    def _schedule_candle_triggers(self, bucket_ts_str: str):
        """根据 1m K线闭合时间，调度对应周期计算"""
        try:
            # 解析时间
            if isinstance(bucket_ts_str, str):
                bucket_ts = datetime.fromisoformat(bucket_ts_str.replace("Z", "+00:00"))
            else:
                bucket_ts = bucket_ts_str

            minute = bucket_ts.hour * 60 + bucket_ts.minute

            for interval, minutes, delay in INTERVALS:
                if interval not in self.intervals:
                    continue

                # 检查是否是该周期的闭合点
                if minute % minutes == 0:
                    # 避免重复触发
                    last = self._last_triggered.get(interval)
                    if last and (bucket_ts - last).total_seconds() < minutes * 60 - 10:
                        continue

                    self._last_triggered[interval] = bucket_ts

                    # 延迟触发（等待 CA 刷新）
                    trigger_time = datetime.now(timezone.utc) + timedelta(seconds=delay)
                    event = TriggerEvent(interval=interval, trigger_time=trigger_time)
                    self._trigger_queue.put(event)
                    LOG.info(f"[{interval}] 调度计算 @ {bucket_ts}, 延迟 {delay}s")

        except Exception as e:
            LOG.error(f"调度失败: {e}")

    def _schedule_metrics_triggers(self, create_time_str: str):
        """根据期货数据时间，调度期货指标计算"""
        # 期货指标单独处理，这里简化为同样的逻辑
        pass

    def _do_compute(self, interval: str):
        """执行单个周期的计算 - 直接用 Engine"""
        from .engine import Engine
        LOG.info(f"[{interval}] 计算 {len(self._high_symbols)} 币种...")
        t0 = time.time()

        if interval == "__full__":
            Engine(
                symbols=self._high_symbols,
                intervals=self.intervals,
                max_workers=self.workers,
            ).run(mode="all")
        else:
            Engine(
                symbols=self._high_symbols,
                intervals=[interval],
                max_workers=self.workers,
            ).run(mode="all")

        LOG.info(f"[{interval}] 完成: {time.time()-t0:.1f}s")

    def _calculation_loop(self):
        """计算循环 - 处理触发队列"""
        with ThreadPoolExecutor(max_workers=self.workers) as executor:
            while self._running:
                try:
                    event = self._trigger_queue.get(timeout=1.0)
                except Exception:
                    continue

                executor.submit(self._run_single_event, event)

    def _run_single_event(self, event: TriggerEvent):
        """带互斥的单事件执行，避免同周期重入"""
        lock = self._interval_locks.setdefault(event.interval, threading.Lock())
        if not lock.acquire(blocking=False):
            LOG.info(f"[{event.interval}] 正在计算，跳过重复触发")
            return
        try:
            now = datetime.now(timezone.utc)
            wait_seconds = (event.trigger_time - now).total_seconds()
            if wait_seconds > 0:
                time.sleep(wait_seconds)
            self._do_compute(event.interval)
        except Exception as e:
            LOG.error(f"计算错误: {e}")
        finally:
            lock.release()


def run_event_engine(symbols=None, intervals=None, workers=4):
    """启动事件驱动引擎"""
    engine = EventEngine(symbols=symbols, intervals=intervals, workers=workers)
    engine.run()
