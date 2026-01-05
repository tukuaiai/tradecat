"""
服务配置加载模块。

对外提供 get_settings()，统一读取环境变量并做最小校验。
"""

from functools import lru_cache
from typing import Optional

from pydantic import BaseSettings, Field


class Settings(BaseSettings):
    """通过环境变量配置 vis-service。"""

    service_name: str = Field("vis-service", description="服务名，用于健康检查显示")
    host: str = Field("0.0.0.0", description="服务监听地址")
    port: int = Field(8087, description="服务监听端口")
    token: Optional[str] = Field(None, description="访问令牌，用于简易鉴权")

    database_url: Optional[str] = Field(
        default=None, description="TimescaleDB 连接串，复用上游 DATABASE_URL"
    )
    indicator_sqlite_path: Optional[str] = Field(
        default=None, description="SQLite 指标库路径，默认复用 telegram-service 库"
    )

    cache_ttl_seconds: int = Field(300, description="渲染结果缓存时间，秒")
    cache_max_items: int = Field(128, description="缓存条目上限")

    class Config:
        env_prefix = "VIS_SERVICE_"
        case_sensitive = False
        env_file = None  # 由启动脚本加载根 config/.env 后生效


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """缓存后的配置获取函数，避免重复解析环境变量。"""

    return Settings()
