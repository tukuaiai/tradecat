"""TET Pipeline 基类 - Transform-Extract-Transform"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Generic, TypeVar

from pydantic import BaseModel

QueryT = TypeVar("QueryT", bound=BaseModel)
DataT = TypeVar("DataT", bound=BaseModel)


class BaseFetcher(ABC, Generic[QueryT, DataT]):
    """数据获取器基类 - TET Pipeline 模式

    1. Transform: 验证并转换查询参数
    2. Extract: 从数据源获取原始数据
    3. Transform: 将原始数据转换为标准模型
    """

    provider: str = ""  # 数据源名称

    @abstractmethod
    def transform_query(self, params: dict[str, Any]) -> QueryT:
        """Transform: 将原始参数转换为标准查询对象"""
        pass

    @abstractmethod
    async def extract(self, query: QueryT) -> list[dict[str, Any]]:
        """Extract: 从外部数据源获取原始数据"""
        pass

    @abstractmethod
    def transform_data(self, raw: list[dict[str, Any]]) -> list[DataT]:
        """Transform: 将原始数据转换为标准化模型"""
        pass

    async def fetch(self, **params) -> list[DataT]:
        """完整 TET 流程"""
        query = self.transform_query(params)
        raw = await self.extract(query)
        return self.transform_data(raw)

    def fetch_sync(self, **params) -> list[DataT]:
        """同步版本"""
        import asyncio
        return asyncio.run(self.fetch(**params))
