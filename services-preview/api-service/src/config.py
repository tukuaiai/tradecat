"""配置管理"""

import os
from pathlib import Path
from functools import lru_cache

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
ENV_FILE = PROJECT_ROOT / "config" / ".env"

load_dotenv(ENV_FILE)


class Settings:
    """服务配置"""

    # API 服务
    HOST: str = os.getenv("API_SERVICE_HOST", "0.0.0.0")
    PORT: int = int(os.getenv("API_SERVICE_PORT", "8088"))
    DEBUG: bool = os.getenv("API_SERVICE_DEBUG", "false").lower() == "true"

    # TimescaleDB
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "postgresql://postgres:postgres@localhost:5434/market_data"
    )

    # SQLite 路径
    SQLITE_INDICATORS_PATH: Path = (
        PROJECT_ROOT / "libs" / "database" / "services" / "telegram-service" / "market_data.db"
    )
    SQLITE_COOLDOWN_PATH: Path = (
        PROJECT_ROOT / "libs" / "database" / "services" / "signal-service" / "cooldown.db"
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
