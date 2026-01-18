"""
服务配置加载模块。

对外提供 get_settings()，统一读取环境变量并做最小校验。
"""

import os
from functools import lru_cache
from typing import Optional
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings


PROJECT_ROOT = Path(__file__).resolve().parents[4]
DEFAULT_SQLITE = PROJECT_ROOT / "libs" / "database" / "services" / "telegram-service" / "market_data.db"


class Settings(BaseSettings):
    """通过环境变量配置 vis-service。"""

    service_name: str = Field("vis-service", description="服务名，用于健康检查显示")
    host: str = Field("0.0.0.0", description="服务监听地址")
    port: int = Field(8087, description="服务监听端口")
    token: Optional[str] = Field(None, description="访问令牌，用于简易鉴权")

    # env 优先级：VIS_SERVICE_DATABASE_URL > DATABASE_URL
    database_url: Optional[str] = Field(
        default_factory=lambda: os.getenv("DATABASE_URL"),
        description="TimescaleDB 连接串，默认继承全局 DATABASE_URL",
        env=["VIS_SERVICE_DATABASE_URL", "DATABASE_URL"],
    )
    # env 优先级：VIS_SERVICE_INDICATOR_SQLITE_PATH > INDICATOR_SQLITE_PATH > 默认路径
    indicator_sqlite_path: str = Field(
        default_factory=lambda: os.getenv("INDICATOR_SQLITE_PATH", DEFAULT_SQLITE),
        description="SQLite 指标库路径，默认复用 telegram-service 库",
        env=["VIS_SERVICE_INDICATOR_SQLITE_PATH", "INDICATOR_SQLITE_PATH"],
    )

    cache_ttl_seconds: int = Field(300, description="渲染结果缓存时间，秒")
    cache_max_items: int = Field(128, description="缓存条目上限")

    class Config:
        env_prefix = "VIS_SERVICE_"
        case_sensitive = False
        env_file = None  # 由启动脚本加载根 config/.env 后生效


def _resolve_sqlite(path_str: str) -> str:
    """支持相对路径，统一基于项目根目录解析为绝对路径。"""
    p = Path(path_str)
    if not p.is_absolute():
        p = (PROJECT_ROOT / p).resolve()
    return str(p)


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """缓存后的配置获取函数，避免重复解析环境变量。"""

    settings = Settings()
    settings.indicator_sqlite_path = _resolve_sqlite(settings.indicator_sqlite_path)
    return settings
