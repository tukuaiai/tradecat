"""
信号推送服务
将信号推送到 Telegram
"""

import asyncio
import logging
from typing import Optional
from telegram import Bot
from telegram.constants import ParseMode

from .engine import Signal, get_engine

logger = logging.getLogger(__name__)


class SignalPusher:
    """信号推送器"""
    
    def __init__(self, bot_token: str, chat_id: str):
        self.bot = Bot(token=bot_token)
        self.chat_id = chat_id
        self.loop = asyncio.new_event_loop()
    
    def _format_signal(self, signal: Signal) -> str:
        """格式化信号消息"""
        # 方向图标
        icon = {
            'BUY': '🟢',
            'SELL': '🔴',
            'ALERT': '⚠️'
        }.get(signal.direction, '📊')
        
        # 强度条
        strength_bar = '█' * (signal.strength // 10) + '░' * (10 - signal.strength // 10)
        
        return f"""
{icon} <b>{signal.direction}</b> | {signal.symbol}

📌 <b>{signal.rule_name}</b>
⏱ 周期: {signal.timeframe}
💰 价格: {signal.price}
📊 强度: [{strength_bar}] {signal.strength}%

💬 {signal.message}
"""
    
    async def _send_async(self, text: str):
        """异步发送消息"""
        try:
            await self.bot.send_message(
                chat_id=self.chat_id,
                text=text,
                parse_mode=ParseMode.HTML
            )
        except Exception as e:
            logger.error(f"发送消息失败: {e}")
    
    def push(self, signal: Signal):
        """推送信号"""
        text = self._format_signal(signal)
        self.loop.run_until_complete(self._send_async(text))
        logger.info(f"信号已推送: {signal.symbol} {signal.direction}")


def start_signal_service(bot_token: str, chat_id: str, interval: int = 60):
    """启动信号服务"""
    pusher = SignalPusher(bot_token, chat_id)
    engine = get_engine()
    engine.register_callback(pusher.push)
    
    logger.info(f"信号服务启动，推送到 chat_id: {chat_id}")
    engine.run_loop(interval=interval)
