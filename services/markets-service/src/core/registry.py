"""Provider 注册表"""
from __future__ import annotations

from typing import Dict, Type

from .fetcher import BaseFetcher


class ProviderRegistry:
    """数据源注册表 - 管理所有 Provider"""

    _fetchers: Dict[str, Dict[str, Type[BaseFetcher]]] = {}

    @classmethod
    def register(cls, provider: str, data_type: str, fetcher_cls: Type[BaseFetcher]):
        """注册 Fetcher

        Args:
            provider: 数据源名称 (ccxt, akshare, yfinance)
            data_type: 数据类型 (candle, ticker, trade, orderbook)
            fetcher_cls: Fetcher 类
        """
        if provider not in cls._fetchers:
            cls._fetchers[provider] = {}
        cls._fetchers[provider][data_type] = fetcher_cls

    @classmethod
    def get(cls, provider: str, data_type: str) -> Type[BaseFetcher] | None:
        """获取 Fetcher 类"""
        return cls._fetchers.get(provider, {}).get(data_type)

    @classmethod
    def list_providers(cls) -> list[str]:
        """列出所有已注册的 Provider"""
        return list(cls._fetchers.keys())

    @classmethod
    def list_data_types(cls, provider: str) -> list[str]:
        """列出 Provider 支持的数据类型"""
        return list(cls._fetchers.get(provider, {}).keys())


def register_fetcher(provider: str, data_type: str):
    """装饰器: 注册 Fetcher"""
    def decorator(cls: Type[BaseFetcher]) -> Type[BaseFetcher]:
        cls.provider = provider
        ProviderRegistry.register(provider, data_type, cls)
        return cls
    return decorator
