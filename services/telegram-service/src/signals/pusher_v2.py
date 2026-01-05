"""
信号推送服务 v2
支持多用户订阅过滤、跳转键盘
"""
import asyncio
import logging
import threading
from typing import Optional, List, Callable

from .engine_v2 import Signal, get_engine
from .ui import is_table_enabled, get_signal_push_kb, SUBS_DB_PATH

logger = logging.getLogger(__name__)


class SignalPusher:
    """信号推送器 - 支持多用户订阅"""

    def __init__(self, send_func: Callable):
        """
        Args:
            send_func: 异步发送函数 async def send(user_id, text, reply_markup)
        """
        self.send_func = send_func
        self._subscribers: List[int] = []  # 订阅用户列表

    def _get_subscribers(self) -> List[int]:
        """获取所有订阅用户"""
        import sqlite3
        try:
            conn = sqlite3.connect(SUBS_DB_PATH)
            rows = conn.execute("SELECT user_id FROM signal_subs WHERE enabled = 1").fetchall()
            conn.close()
            return [r[0] for r in rows]
        except Exception:
            return []

    def _format_signal(self, signal: Signal) -> str:
        """格式化信号消息"""
        if signal.full_message:
            return signal.full_message

        icon = {"BUY": "🟢", "SELL": "🔴", "ALERT": "⚠️"}.get(signal.direction, "📊")
        strength_bar = "█" * (signal.strength // 10) + "░" * (10 - signal.strength // 10)

        return f"""{icon} {signal.direction} | {signal.symbol}

📌 {signal.rule_name}
⏱ 周期: {signal.timeframe}
💰 价格: {signal.price}
📊 强度: [{strength_bar}] {signal.strength}%

💬 {signal.message}"""

    async def push_async(self, signal: Signal):
        """异步推送信号到所有订阅用户"""
        subscribers = self._get_subscribers()
        if not subscribers:
            logger.debug("无订阅用户，跳过推送")
            return

        text = self._format_signal(signal)
        if len(text) > 4096:
            text = text[:4090] + "\n..."

        kb = get_signal_push_kb(signal.symbol)

        # 获取信号对应的表名
        from .engine_v2 import get_engine
        get_engine()
        # 从规则名找表名
        table = None
        from .rules import ALL_RULES
        for rule in ALL_RULES:
            if rule.name == signal.rule_name:
                table = rule.table
                break

        pushed = 0
        for uid in subscribers:
            # 检查用户是否订阅了该表
            if table and not is_table_enabled(uid, table):
                continue
            try:
                await self.send_func(uid, text, kb)
                pushed += 1
            except Exception as e:
                logger.warning(f"推送给用户 {uid} 失败: {e}")

        if pushed > 0:
            logger.info(f"信号已推送: {signal.symbol} {signal.direction} - {signal.rule_name} ({pushed}人)")


# 全局推送器
_pusher: Optional[SignalPusher] = None


def init_pusher(send_func: Callable):
    """初始化推送器"""
    global _pusher
    _pusher = SignalPusher(send_func)

    # 注册到引擎
    engine = get_engine()

    def on_signal(signal: Signal):
        if _pusher:
            # 在新线程中运行异步推送
            loop = asyncio.new_event_loop()
            loop.run_until_complete(_pusher.push_async(signal))
            loop.close()

    engine.register_callback(on_signal)
    logger.info("信号推送器已初始化")


def start_signal_loop(interval: int = 60):
    """在后台线程启动信号检测循环"""
    def run():
        engine = get_engine()
        logger.info(f"信号引擎启动，检查间隔: {interval}秒")
        engine.run_loop(interval=interval)

    thread = threading.Thread(target=run, daemon=True, name="SignalEngine")
    thread.start()
    return thread
