"""
信号发布器 - 支持回调订阅
"""

import logging
from collections.abc import Callable

from .types import SignalEvent

logger = logging.getLogger(__name__)

# 可选持久化回调列表（用于写历史、审计）
_persist_callbacks: list[Callable[[SignalEvent], None]] = []


class SignalPublisher:
    """
    信号发布器

    使用回调机制实现解耦：
    - signal-service 负责检测并发布事件
    - telegram-service 订阅事件并推送消息

    后续可扩展为 Redis Pub/Sub 等分布式方案
    """

    _callbacks: list[Callable[[SignalEvent], None]] = []
    _async_callbacks: list[Callable[[SignalEvent], None]] = []

    @classmethod
    def register_persist(cls, callback: Callable[[SignalEvent], None]):
        """注册持久化回调（同步执行，失败记录警告）"""
        if callback not in _persist_callbacks:
            _persist_callbacks.append(callback)
            logger.info(f"注册持久化回调: {callback.__name__}")

    @classmethod
    def subscribe(cls, callback: Callable[[SignalEvent], None], is_async: bool = False):
        """
        订阅信号事件

        Args:
            callback: 回调函数，接收 SignalEvent 参数
            is_async: 是否为异步回调
        """
        if is_async:
            if callback not in cls._async_callbacks:
                cls._async_callbacks.append(callback)
                logger.info(f"注册异步信号回调: {callback.__name__}")
        else:
            if callback not in cls._callbacks:
                cls._callbacks.append(callback)
                logger.info(f"注册同步信号回调: {callback.__name__}")

    @classmethod
    def unsubscribe(cls, callback: Callable[[SignalEvent], None]):
        """取消订阅"""
        if callback in cls._callbacks:
            cls._callbacks.remove(callback)
        if callback in cls._async_callbacks:
            cls._async_callbacks.remove(callback)

    @classmethod
    def publish(cls, event: SignalEvent):
        """
        发布信号事件（同步）

        Args:
            event: 信号事件
        """
        logger.debug(f"发布信号: {event.symbol} {event.direction} - {event.signal_type}")

        for callback in _persist_callbacks:
            try:
                callback(event)
            except Exception as e:
                logger.warning(f"持久化回调失败 [{callback.__name__}]: {e}")

        for callback in cls._callbacks:
            try:
                callback(event)
            except Exception as e:
                logger.warning(f"信号回调执行失败 [{callback.__name__}]: {e}")

    @classmethod
    async def publish_async(cls, event: SignalEvent):
        """
        发布信号事件（异步）

        Args:
            event: 信号事件
        """
        import asyncio

        logger.debug(f"异步发布信号: {event.symbol} {event.direction} - {event.signal_type}")

        for callback in _persist_callbacks:
            try:
                callback(event)
            except Exception as e:
                logger.warning(f"持久化回调失败 [{callback.__name__}]: {e}")

        # 先执行同步回调
        for callback in cls._callbacks:
            try:
                callback(event)
            except Exception as e:
                logger.warning(f"信号回调执行失败 [{callback.__name__}]: {e}")

        # 再执行异步回调
        for callback in cls._async_callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(event)
                else:
                    callback(event)
            except Exception as e:
                logger.warning(f"异步信号回调执行失败 [{callback.__name__}]: {e}")

    @classmethod
    def clear(cls):
        """清除所有订阅（用于测试）"""
        cls._callbacks.clear()
        cls._async_callbacks.clear()

    @classmethod
    def subscriber_count(cls) -> int:
        """返回订阅者数量"""
        return len(cls._callbacks) + len(cls._async_callbacks)
