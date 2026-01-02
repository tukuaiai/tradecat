# TradeCat 项目修复方案

> 生成时间: 2025-01-03
> 版本: v1.0
> 状态: 待执行

---

## 📋 目录

- [P0 - 高优先级问题](#p0---高优先级问题)
- [P1 - 中优先级问题](#p1---中优先级问题)
- [P2 - 低优先级优化](#p2---低优先级优化)
- [架构重构建议](#架构重构建议)
- [执行计划](#执行计划)

---

## P0 - 高优先级问题

### 问题 1: 硬编码数据库路径

**问题 ID**: P0-001
**严重程度**: 🔴 高
**影响范围**: 部署/迁移
**修复难度**: 低

#### 问题描述

`services/trading-service/config/.env.example` 中硬编码了绝对路径，导致项目迁移或部署时必须手动修改。

```python
# 当前配置
INDICATOR_SQLITE_PATH=/home/lenovo/.projects/tradecat/libs/database/services/telegram-service/market_data.db
```

#### 修复方案

**步骤 1**: 修改 `services/trading-service/config/.env.example`

```diff
- INDICATOR_SQLITE_PATH=/home/lenovo/.projects/tradecat/libs/database/services/telegram-service/market_data.db
+ INDICATOR_SQLITE_PATH=${PROJECT_ROOT}/libs/database/services/telegram-service/market_data.db
```

**步骤 2**: 修改 `services/trading-service/src/simple_scheduler.py`

```python
# 第 29 行附近
PROJECT_ROOT = os.path.dirname(os.path.dirname(TRADING_SERVICE_DIR))
SQLITE_PATH = os.environ.get(
    "INDICATOR_SQLITE_PATH",
    os.path.join(PROJECT_ROOT, "libs/database/services/telegram-service/market_data.db")
).replace("${PROJECT_ROOT}", PROJECT_ROOT)
```

**步骤 3**: 验证

```bash
# 测试配置解析
cd services/trading-service
python3 -c "
import os
os.environ['PROJECT_ROOT'] = '/tmp/tradecat'
path = '\${PROJECT_ROOT}/libs/db/market_data.db'
print(path.replace('\${PROJECT_ROOT}', os.environ['PROJECT_ROOT']))
"
```

#### 预期效果

- 项目可迁移到任意路径
- 支持容器化部署（Docker/K8s）

---

### 问题 2: 依赖版本未锁定

**问题 ID**: P0-002
**严重程度**: 🔴 高
**影响范围**: 生产环境稳定性
**修复难度**: 中

#### 问题描述

所有 `requirements.txt` 使用 `>=` 版本号，可能导致依赖漂移。

#### 修复方案

**步骤 1**: 生成锁文件

```bash
# 为每个服务生成 requirements.lock.txt
cd services/data-service
pip freeze > requirements.lock.txt

cd ../trading-service
pip freeze > requirements.lock.txt

cd ../telegram-service
pip freeze > requirements.lock.txt

cd ../order-service
pip freeze > requirements.lock.txt
```

**步骤 2**: 手动锁定关键依赖

编辑各服务的 `requirements.txt`:

```txt
# data-service/requirements.txt
psycopg[binary,pool]==3.1.18
aiohttp==3.9.3
ccxt==4.2.0
requests==2.31.0
cryptofeed==2.4.0

# trading-service/requirements.txt
psycopg[binary,pool]==3.1.18
pandas==2.2.0
numpy==1.26.4
TA-Lib==0.4.28
m-patternpy==2.0.0

# telegram-service/requirements.txt
python-telegram-bot==20.7
aiohttp==3.9.3
httpx==0.25.2
requests==2.31.0
```

**步骤 3**: 更新 `scripts/init.sh`

```bash
#!/bin/bash
# 添加依赖锁定检查
init_service() {
    local service=$1
    if [ -f "services/$service/requirements.lock.txt" ]; then
        pip install -r services/$service/requirements.lock.txt
    else
        pip install -r services/$service/requirements.txt
    fi
}
```

#### 预期效果

- 确保生产环境依赖版本一致
- 避免因依赖更新导致的破坏性变更

---

### 问题 3: 环境变量命名不一致

**问题 ID**: P0-003
**严重程度**: 🟡 中
**影响范围**: 代码维护
**修复难度**: 低

#### 问题描述

`BOT_TOKEN` 和 `TELEGRAM_BOT_TOKEN` 混用，容易混淆。

#### 修复方案

**步骤 1**: 统一变量名为 `TELEGRAM_BOT_TOKEN`

修改 `services/telegram-service/config/.env.example`:

```diff
- BOT_TOKEN=your_bot_token_here
+ TELEGRAM_BOT_TOKEN=your_bot_token_here
```

**步骤 2**: 修改 `services/telegram-service/src/bot/app.py`

```python
# 第 259 行附近
- BOT_TOKEN = _require_env('BOT_TOKEN', required=True)
- TELEGRAM_BOT_TOKEN = BOT_TOKEN  # 为了兼容性添加别名
+ TELEGRAM_BOT_TOKEN = _require_env('TELEGRAM_BOT_TOKEN', required=True)

# 移除所有 BOT_TOKEN 引用
```

**步骤 3**: 更新文档

修改 `README.md` 中所有 `BOT_TOKEN` 为 `TELEGRAM_BOT_TOKEN`

#### 预期效果

- 变量命名统一
- 减少配置错误

---

### 问题 4: 数据库查询缺少索引优化

**问题 ID**: P0-004
**严重程度**: 🔴 高
**影响范围**: 性能
**修复难度**: 中

#### 问题描述

`simple_scheduler.py` 中的优先级查询在大数据量时性能差。

#### 修复方案

**步骤 1**: 创建索引文件

新建 `libs/database/db/schema/008_optimize_priority_queries.sql`:

```sql
-- 为 K 线优先级查询优化
CREATE INDEX IF NOT EXISTS idx_candles_5m_symbol_ts
ON market_data.candles_5m(symbol, bucket_ts DESC);

CREATE INDEX IF NOT EXISTS idx_candles_5m_ts
ON market_data.candles_5m(bucket_ts DESC);

-- 为期货优先级查询优化
CREATE INDEX IF NOT EXISTS idx_futures_metrics_5m_symbol_ts
ON market_data.binance_futures_metrics_5m(symbol, create_time DESC);

-- 创建持续聚合视图（每小时更新）
CREATE MATERIALIZED VIEW IF NOT EXISTS market_data.candles_5m_1h_agg
WITH (timescaledb.continuous) AS
SELECT
    time_bucket('1 hour', bucket_ts) AS hour,
    symbol,
    SUM(quote_volume) as total_qv,
    AVG((high-low)/NULLIF(close,0)) as volatility,
    FIRST(close, bucket_ts) as open,
    LAST(close, bucket_ts) as close
FROM market_data.candles_5m
GROUP BY hour, symbol;

-- 设置刷新策略
SELECT add_continuous_aggregate_policy('market_data.candles_5m_1h_agg',
    start_offset => INTERVAL '1 hour',
    end_offset => INTERVAL '5 minutes',
    schedule_interval => INTERVAL '1 hour');
```

**步骤 2**: 应用索引

```bash
PGPASSWORD=postgres psql -h localhost -p 5433 -U postgres -d market_data -f \
    libs/database/db/schema/008_optimize_priority_queries.sql
```

**步骤 3**: 优化查询逻辑

修改 `services/trading-service/src/simple_scheduler.py`:

```python
def _query_kline_priority(top_n: int = 30) -> set:
    """K线维度优先级 - 使用预聚合视图"""
    symbols = set()
    try:
        with psycopg.connect(DB_URL) as conn:
            # 使用 1 小时聚合视图替代原始查询
            sql = """
                WITH base AS (
                    SELECT symbol,
                           SUM(total_qv) as volume_24h,
                           AVG(volatility) as avg_volatility
                    FROM market_data.candles_5m_1h_agg
                    WHERE hour > NOW() - INTERVAL '24 hours'
                    GROUP BY symbol
                ),
                ranks AS (
                    SELECT symbol,
                           ROW_NUMBER() OVER (ORDER BY volume_24h DESC) as v_rank,
                           ROW_NUMBER() OVER (ORDER BY avg_volatility DESC) as vol_rank
                    FROM base
                )
                SELECT DISTINCT symbol FROM ranks
                WHERE v_rank <= %s OR vol_rank <= %s
            """
            cur = conn.execute(sql, (top_n, top_n))
            symbols.update(r[0] for r in cur.fetchall())
    except Exception as e:
        log(f"K线优先级查询失败: {e}")
    return symbols
```

#### 预期效果

- 查询速度提升 5-10 倍
- 降低数据库负载

---

### 问题 5: SQLite 并发写入风险

**问题 ID**: P0-005
**严重程度**: 🔴 高
**影响范围**: 数据完整性
**修复难度**: 中

#### 问题描述

多线程同时写入 SQLite 可能导致 "database is locked"。

#### 修复方案

**步骤 1**: 启用 WAL 模式

修改 `services/trading-service/src/simple_scheduler.py`:

```python
import sqlite3
import threading

# 全局连接锁
_sqlite_lock = threading.Lock()

def get_sqlite_connection() -> sqlite3.Connection:
    """获取 SQLite 连接，启用 WAL 模式"""
    conn = sqlite3.connect(SQLITE_PATH, check_same_thread=False)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=NORMAL")
    conn.execute("PRAGMA busy_timeout=5000")  # 5秒超时
    return conn

def get_indicator_latest(interval: str) -> datetime:
    """查询 SQLite 指标该周期最新数据时间"""
    try:
        with _sqlite_lock:  # 加锁
            conn = get_sqlite_connection()
            row = conn.execute("""
                SELECT MAX(数据时间) as latest FROM [MACD柱状扫描器.py] WHERE 周期 = ?
            """, (interval,)).fetchone()
            conn.close()
            if row and row[0]:
                ts_str = row[0].replace("+00:00", "").replace("T", " ")
                return datetime.fromisoformat(ts_str).replace(tzinfo=timezone.utc)
            return None
    except Exception as e:
        log(f"SQLite 查询失败: {e}")
        return None
```

**步骤 2**: 批量写入优化

创建新文件 `services/trading-service/src/utils/sqlite_pool.py`:

```python
"""SQLite 连接池"""
import sqlite3
import threading
from contextlib import contextmanager
from typing import Optional

class SQLitePool:
    """SQLite 连接池"""

    def __init__(self, db_path: str, pool_size: int = 3):
        self.db_path = db_path
        self.pool_size = pool_size
        self._pool = []
        self._lock = threading.Lock()
        self._initialize_pool()

    def _initialize_pool(self):
        """初始化连接池"""
        for _ in range(self.pool_size):
            conn = self._create_connection()
            if conn:
                self._pool.append(conn)

    def _create_connection(self) -> Optional[sqlite3.Connection]:
        """创建新连接"""
        try:
            conn = sqlite3.connect(
                self.db_path,
                check_same_thread=False
            )
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("PRAGMA synchronous=NORMAL")
            conn.execute("PRAGMA busy_timeout=5000")
            return conn
        except Exception as e:
            return None

    @contextmanager
    def get_connection(self):
        """获取连接"""
        conn = None
        try:
            with self._lock:
                if self._pool:
                    conn = self._pool.pop()
            if not conn:
                conn = self._create_connection()
            yield conn
        finally:
            if conn:
                with self._lock:
                    self._pool.append(conn)

    def close_all(self):
        """关闭所有连接"""
        with self._lock:
            for conn in self._pool:
                try:
                    conn.close()
                except:
                    pass
            self._pool.clear()


# 全局连接池实例
_sqlite_pool: Optional[SQLitePool] = None
_pool_lock = threading.Lock()

def get_sqlite_pool(db_path: str) -> SQLitePool:
    """获取全局连接池"""
    global _sqlite_pool
    with _pool_lock:
        if _sqlite_pool is None:
            _sqlite_pool = SQLitePool(db_path, pool_size=3)
        return _sqlite_pool
```

**步骤 3**: 更新指标写入逻辑

修改 `services/trading-service/src/indicators/base.py`:

```python
from utils.sqlite_pool import get_sqlite_pool

def batch_insert(table_name: str, data: list):
    """批量插入数据"""
    pool = get_sqlite_pool(SQLITE_PATH)
    with pool.get_connection() as conn:
        cursor = conn.cursor()
        cursor.executemany(
            f"INSERT OR REPLACE INTO [{table_name}] VALUES ({','.join(['?'] * len(data[0]))})",
            data
        )
        conn.commit()
```

#### 预期效果

- 消除数据库锁冲突
- 提升写入吞吐量 3-5 倍

---

## P1 - 中优先级问题

### 问题 6: 配置分散管理

**问题 ID**: P1-001
**严重程度**: 🟡 中
**影响范围**: 可维护性
**修复难度**: 高

#### 修复方案

**步骤 1**: 创建统一配置加载器

新建 `libs/common/config_loader.py`:

```python
"""统一配置加载器"""
import os
import json
from pathlib import Path
from typing import Any, Optional, Dict
from dotenv import load_dotenv

class ConfigLoader:
    """配置加载器"""

    def __init__(self, project_root: Path, service_name: str):
        self.project_root = project_root
        self.service_name = service_name
        self._cache: Dict[str, Any] = {}

        # 加载顺序: 公共配置 -> 服务配置 -> 环境变量
        self._load_configs()

    def _load_configs(self):
        """按优先级加载配置"""
        # 1. 加载公共配置
        common_env = self.project_root / "config" / ".env"
        if common_env.exists():
            load_dotenv(common_env, override=False)

        # 2. 加载服务私有配置
        service_env = (
            self.project_root /
            "services" /
            self.service_name /
            "config" /
            ".env"
        )
        if service_env.exists():
            load_dotenv(service_env, override=True)

    def get(self, key: str, default: Any = None, required: bool = False) -> Any:
        """获取配置项"""
        if key in self._cache:
            return self._cache[key]

        value = os.getenv(key, default)

        if required and value is None:
            raise ValueError(
                f"配置项 {key} 未设置，请检查配置文件"
            )

        self._cache[key] = value
        return value

    def get_bool(self, key: str, default: bool = False) -> bool:
        """获取布尔值"""
        value = self.get(key, str(default))
        return value.lower() in ('true', '1', 'yes', 'on')

    def get_int(self, key: str, default: int = 0) -> int:
        """获取整数值"""
        value = self.get(key, str(default))
        try:
            return int(value)
        except ValueError:
            raise ValueError(f"配置项 {key} 必须是整数: {value}")

    def get_float(self, key: str, default: float = 0.0) -> float:
        """获取浮点数"""
        value = self.get(key, str(default))
        try:
            return float(value)
        except ValueError:
            raise ValueError(f"配置项 {key} 必须是浮点数: {value}")

    def get_list(self, key: str, default: str = "", sep: str = ",") -> list:
        """获取列表"""
        value = self.get(key, default)
        return [item.strip() for item in value.split(sep) if item.strip()]


def get_config(project_root: Path, service_name: str) -> ConfigLoader:
    """获取配置实例"""
    return ConfigLoader(project_root, service_name)
```

**步骤 2**: 更新各服务使用统一配置

修改 `services/trading-service/src/config.py`:

```python
from pathlib import Path
from libs.common.config_loader import get_config

PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
config = get_config(PROJECT_ROOT, "trading-service")

# 使用配置
DATABASE_URL = config.get("DATABASE_URL", required=True)
MAX_WORKERS = config.get_int("MAX_WORKERS", default=4)
INTERVALS = config.get_list("INTERVALS", default="1m,5m,15m,1h")
```

#### 预期效果

- 配置统一管理
- 减少重复代码

---

### 问题 7: 虚拟环境重复依赖

**问题 ID**: P1-002
**严重程度**: 🟡 中
**影响范围**: 资源占用
**修复难度**: 高

#### 修复方案

**步骤 1**: 评估使用 Poetry

```bash
# 安装 Poetry
pip install poetry

# 转换项目结构
cd /home/lenovo/.projects/tradecat

# 创建根目录 pyproject.toml
cat > pyproject.toml << 'EOF'
[tool.poetry]
name = "tradecat"
version = "1.0.0"
description = "加密货币量化交易数据平台"
authors = ["tukuaiai"]

[tool.poetry.dependencies]
python = "^3.10"
psycopg = {extras = ["binary", "pool"], version = "^3.1.0"}
aiohttp = "^3.9.0"
ccxt = "^4.0.0"
requests = "^2.31.0"
pandas = "^2.0.0"
numpy = "^1.24.0"
python-telegram-bot = "^20.0"

[tool.poetry.group.dev.dependencies]
pytest = "^7.4.0"
ruff = "^0.1.0"

[build-system]
requires = ["poetry-core"]
build-backend = "poetry.core.masonry.api"
EOF
```

**步骤 2**: 为每个服务创建独立配置

```bash
# data-service
cd services/data-service
poetry init --name=tradecat-data-service

# trading-service
cd ../trading-service
poetry init --name=tradecat-trading-service

# telegram-service
cd ../telegram-service
poetry init --name=tradecat-telegram-service
```

**步骤 3**: 安装依赖

```bash
# 使用 uv 替代 Poetry（更快）
pip install uv

# 安装根依赖
uv pip install -r requirements.txt

# 各服务使用根虚拟环境
export VIRTUAL_ENV=/home/lenovo/.projects/tradecat/.venv
source $VIRTUAL_ENV/bin/activate
```

#### 预期效果

- 减少磁盘占用 50%+
- 加快依赖安装速度

---

### 问题 8: 日志配置分散

**问题 ID**: P1-003
**严重程度**: 🟡 中
**影响范围**: 可观测性
**修复难度**: 中

#### 修复方案

**步骤 1**: 创建统一日志配置

新建 `libs/common/logging_config.py`:

```python
"""统一日志配置"""
import logging
import sys
from pathlib import Path
from typing import Optional

def setup_logging(
    service_name: str,
    log_level: str = "INFO",
    log_dir: Optional[Path] = None,
):
    """配置日志"""

    # 创建格式化器
    formatter = logging.Formatter(
        fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # 根日志器
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level.upper()))

    # 清除现有处理器
    root_logger.handlers.clear()

    # 控制台处理器
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    # 文件处理器（可选）
    if log_dir:
        log_dir.mkdir(parents=True, exist_ok=True)
        log_file = log_dir / f"{service_name}.log"

        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)

    # 第三方库日志降级
    for logger_name in ['httpx', 'apscheduler', 'urllib3']:
        logging.getLogger(logger_name).setLevel(logging.WARNING)

    return root_logger


def get_logger(name: str) -> logging.Logger:
    """获取日志器"""
    return logging.getLogger(name)
```

**步骤 2**: 更新各服务

修改 `services/trading-service/src/simple_scheduler.py`:

```python
from libs.common.logging_config import setup_logging, get_logger

# 初始化日志
setup_logging(
    service_name="trading-service",
    log_level=os.getenv("LOG_LEVEL", "INFO"),
    log_dir=Path(__file__).parent.parent / "logs"
)

logger = get_logger(__name__)

# 替换所有 print
- log(msg: str):
-     print(f"[{datetime.now():%Y-%m-%d %H:%M:%S}] {msg}", flush=True)
+ logger.info(msg)
```

#### 预期效果

- 日志格式统一
- 支持结构化日志

---

### 问题 9: 错误处理过于宽泛

**问题 ID**: P1-004
**严重程度**: 🟡 中
**影响范围**: 可调试性
**修复难度**: 低

#### 修复方案

**步骤 1**: 创建错误处理工具

新建 `libs/common/error_handler.py`:

```python
"""错误处理工具"""
import logging
from functools import wraps
from typing import Callable, TypeVar, Optional
from psycopg import OperationalError, DatabaseError
from sqlite3 import OperationalError as SQLiteOperationalError

T = TypeVar('T')

logger = logging.getLogger(__name__)

def handle_database_errors(func: Callable[..., T]) -> Callable[..., T]:
    """数据库错误处理装饰器"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except OperationalError as e:
            logger.error(f"数据库操作错误: {e}", exc_info=True)
            raise
        except DatabaseError as e:
            logger.error(f"数据库错误: {e}", exc_info=True)
            raise
        except SQLiteOperationalError as e:
            logger.error(f"SQLite 错误: {e}", exc_info=True)
            raise
    return wrapper


def retry_on_failure(
    max_retries: int = 3,
    retryable_exceptions: tuple = (Exception,),
    backoff: float = 1.0,
):
    """失败重试装饰器"""
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args, **kwargs):
            import time

            last_exception = None
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except retryable_exceptions as e:
                    last_exception = e
                    if attempt < max_retries - 1:
                        wait_time = backoff * (2 ** attempt)
                        logger.warning(
                            f"{func.__name__} 失败 ({attempt+1}/{max_retries}), "
                            f"{wait_time:.1f}s后重试: {e}"
                        )
                        time.sleep(wait_time)
                    else:
                        logger.error(
                            f"{func.__name__} 失败已达最大重试次数: {e}",
                            exc_info=True
                        )
            raise last_exception
        return wrapper
    return decorator
```

**步骤 2**: 应用到关键函数

修改 `services/trading-service/src/simple_scheduler.py`:

```python
from libs.common.error_handler import handle_database_errors, retry_on_failure

@handle_database_errors
def _query_kline_priority(top_n: int = 30) -> set:
    """K线维度优先级"""
    # 原有逻辑...
```

#### 预期效果

- 错误信息更详细
- 自动重试机制

---

### 问题 10: 缺少健康检查端点

**问题 ID**: P1-005
**严重程度**: 🟡 中
**影响范围**: 部署
**修复难度**: 低

#### 修复方案

**步骤 1**: 为每个服务添加健康检查

创建 `services/trading-service/src/health.py`:

```python
"""健康检查端点"""
from fastapi import FastAPI
from fastapi.responses import JSONResponse
import psycopg
import sqlite3
from pathlib import Path

app = FastAPI()

@app.get("/health")
async def health_check():
    """健康检查"""
    checks = {
        "status": "healthy",
        "services": {}
    }

    # 检查 TimescaleDB 连接
    try:
        with psycopg.connect(DB_URL) as conn:
            conn.execute("SELECT 1")
        checks["services"]["timescaledb"] = "ok"
    except Exception as e:
        checks["services"]["timescaledb"] = f"error: {e}"
        checks["status"] = "degraded"

    # 检查 SQLite 连接
    try:
        conn = sqlite3.connect(SQLITE_PATH)
        conn.execute("SELECT 1")
        conn.close()
        checks["services"]["sqlite"] = "ok"
    except Exception as e:
        checks["services"]["sqlite"] = f"error: {e}"
        checks["status"] = "degraded"

    return JSONResponse(content=checks)


@app.get("/health/ready")
async def readiness_check():
    """就绪检查"""
    # 添加就绪逻辑（如：数据已加载、服务已启动）
    return {"status": "ready"}
```

**步骤 2**: 更新启动脚本

修改 `services/trading-service/scripts/start.sh`:

```bash
start() {
    # ... 原有启动逻辑 ...

    # 启动健康检查服务（可选）
    if [ "$ENABLE_HEALTH_CHECK" = "true" ]; then
        python3 -m uvicorn src.health:app --host 0.0.0.0 --port 8080 &
        echo $! > $PID_DIR/health.pid
    fi
}

stop() {
    # ... 停止逻辑 ...

    if [ -f "$PID_DIR/health.pid" ]; then
        kill $(cat "$PID_DIR/health.pid")
        rm "$PID_DIR/health.pid"
    fi
}
```

**步骤 3**: 添加 Docker 健康检查

创建 `docker-compose.yml`:

```yaml
version: '3.8'

services:
  trading-service:
    build: ./services/trading-service
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8080/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
```

#### 预期效果

- 支持 Docker healthcheck
- 支持 Kubernetes liveness/readiness probe

---

## P2 - 低优先级优化

### 问题 11: 硬编码币种过滤列表

**问题 ID**: P2-001
**严重程度**: 🟢 低
**影响范围**: 可维护性
**修复难度**: 低

#### 修复方案

**步骤 1**: 移至配置文件

修改 `services/telegram-service/config/.env.example`:

```diff
+ # ---------- 数据过滤 ----------
+ # 禁止显示的币种（逗号分隔）
+ BLOCKED_SYMBOLS=BNXUSDT,ALPACAUSDT
```

**步骤 2**: 更新代码

修改 `services/telegram-service/src/bot/app.py`:

```python
class UserRequestHandler:
    def __init__(self, card_registry: Optional[RankingRegistry] = None):
        # 从配置读取
        self.blocked_symbols = set(
            os.getenv("BLOCKED_SYMBOLS", "BNXUSDT,ALPACAUSDT")
            .split(",")
        )
```

---

### 问题 12: 添加单元测试

**问题 ID**: P2-002
**严重程度**: 🟢 低
**影响范围**: 代码质量
**修复难度**: 中

#### 修复方案

**步骤 1**: 创建测试框架

```bash
# 安装测试依赖
pip install pytest pytest-asyncio pytest-cov

# 创建测试目录
mkdir -p services/trading-service/tests
```

**步骤 2**: 编写示例测试

创建 `services/trading-service/tests/test_simple_scheduler.py`:

```python
"""测试 simple_scheduler"""
import pytest
from unittest.mock import Mock, patch
from datetime import datetime, timezone

@pytest.fixture
def mock_config():
    """模拟配置"""
    import os
    os.environ["DATABASE_URL"] = "postgresql://test:test@localhost/test"
    os.environ["INDICATOR_SQLITE_PATH"] = "/tmp/test.db"


def test_parse_list():
    """测试列表解析"""
    from simple_scheduler import _parse_list

    assert _parse_list("BTCUSDT,ETHUSDT") == ["BTCUSDT", "ETHUSDT"]
    assert _parse_list("BTCUSDT, ETHUSDT,") == ["BTCUSDT", "ETHUSDT"]
    assert _parse_list("") == []


@pytest.mark.asyncio
async def test_get_high_priority_symbols_fast():
    """测试高优先级币种获取"""
    from simple_scheduler import get_high_priority_symbols_fast

    with patch('simple_scheduler._query_kline_priority') as mock_kline:
        with patch('simple_scheduler._query_futures_priority') as mock_futures:
            mock_kline.return_value = {"BTCUSDT", "ETHUSDT"}
            mock_futures.return_value = {"ETHUSDT", "SOLUSDT"}

            result = get_high_priority_symbols_fast(top_n=10)

            assert "BTCUSDT" in result
            assert "ETHUSDT" in result
            assert "SOLUSDT" in result
```

**步骤 3**: 运行测试

```bash
cd services/trading-service
pytest tests/ -v --cov=src
```

---

### 问题 13: 定期清理 SQLite 数据库

**问题 ID**: P2-003
**严重程度**: 🟢 低
**影响范围**: 资源占用
**修复难度**: 中

#### 修复方案

**步骤 1**: 创建清理脚本

新建 `scripts/cleanup_sqlite.sh`:

```bash
#!/bin/bash
# SQLite 数据库清理脚本

DB_PATH="${1:-libs/database/services/telegram-service/market_data.db}"
KEEP_DAYS="${2:-30}"

echo "清理 SQLite 数据库: $DB_PATH"
echo "保留最近 $KEEP_DAYS 天数据"

sqlite3 "$DB_PATH" << SQL
-- 删除旧数据
DELETE FROM [MACD柱状扫描器.py]
WHERE datetime(数据时间) < datetime('now', '-$KEEP_DAYS days');

-- 优化数据库
VACUUM;
SQL

echo "清理完成"
```

**步骤 2**: 添加到 cron

```bash
# 编辑 crontab
crontab -e

# 每周日凌晨 2 点清理
0 2 * * 0 /home/lenovo/.projects/tradecat/scripts/cleanup_sqlite.sh
```

---

## 架构重构建议

### 建议 1: 引入消息队列

**目标**: 解耦服务间通信

**方案**:

1. 选择消息队列: Redis Stream / RabbitMQ / Kafka
2. 修改架构:
   - data-service → Redis Stream (K 线数据)
   - trading-service ← Redis Stream (消费数据)
   - trading-service → Redis Stream (指标数据)
   - telegram-service ← Redis Stream (消费指标)

**示例**:

```python
# data-service/publisher.py
import redis

r = redis.Redis(host='localhost', port=6379, db=0)

def publish_kline(symbol: str, interval: str, data: dict):
    """发布 K 线数据"""
    r.xadd(f"kline:{interval}", {
        "symbol": symbol,
        "open": data['open'],
        "high": data['high'],
        "low": data['low'],
        "close": data['close'],
        "volume": data['volume']
    })


# trading-service/consumer.py
import redis

r = redis.Redis(host='localhost', port=6379, db=0)

def consume_klines(interval: str):
    """消费 K 线数据"""
    last_id = '$'
    while True:
        events = r.xread({f"kline:{interval}": last_id}, block=5000)
        if not events:
            continue

        for stream, messages in events:
            for msg_id, data in messages:
                process_kline(data)
                last_id = msg_id
```

---

### 建议 2: 添加 API 网关

**目标**: 统一入口，处理认证、限流

**方案**: 使用 Kong / APISIX / Traefik

```yaml
# kong.yml
services:
  - name: telegram-service
    url: http://telegram-service:8080
    routes:
      - name: telegram-route
        paths:
          - /telegram
    plugins:
      - name: rate-limiting
        config:
          minute: 100
      - name: jwt
```

---

### 建议 3: 监控和告警

**目标**: 可观测性

**方案**:

1. **指标采集**:
   - 集成 Prometheus
   - 暴露 `/metrics` 端点

2. **日志聚合**:
   - 使用 Loki / ELK

3. **链路追踪**:
   - 集成 Jaeger / Zipkin

**示例**:

```python
# metrics.py
from prometheus_client import Counter, Histogram, start_http_server

# 定义指标
kline_counter = Counter('klines_processed_total', 'Total klines processed', ['symbol'])
calc_duration = Histogram('indicator_calc_duration_seconds', 'Indicator calculation duration')

@calc_duration.time()
def calculate_indicator(symbol: str):
    """计算指标"""
    kline_counter.labels(symbol=symbol).inc()
    # ... 计算逻辑
```

---

## 执行计划

### 阶段一: 高优先级修复 (1-2 周)

| 任务 | 负责人 | 工期 | 依赖 |
|:---|:---:|:---:|:---|
| P0-001: 硬编码路径修复 | Dev | 0.5 天 | - |
| P0-002: 依赖版本锁定 | Dev | 1 天 | - |
| P0-003: 环境变量统一 | Dev | 0.5 天 | - |
| P0-004: 数据库索引优化 | DBA | 2 天 | - |
| P0-005: SQLite 并发优化 | Dev | 2 天 | P0-001 |

### 阶段二: 中优先级优化 (2-3 周)

| 任务 | 负责人 | 工期 | 依赖 |
|:---|:---:|:---:|:---|
| P1-001: 配置中心实现 | Dev | 3 天 | 阶段一完成 |
| P1-002: 虚拟环境优化 | Dev | 2 天 | - |
| P1-003: 日志统一配置 | Dev | 1 天 | - |
| P1-004: 错误处理改进 | Dev | 2 天 | - |
| P1-005: 健康检查端点 | Dev | 1 天 | - |

### 阶段三: 低优先级优化 (1-2 周)

| 任务 | 负责人 | 工期 | 依赖 |
|:---|:---:|:---:|:---|
| P2-001: 配置化硬编码 | Dev | 0.5 天 | - |
| P2-002: 单元测试添加 | Dev | 3 天 | - |
| P2-003: 数据清理脚本 | Dev | 1 天 | - |

### 阶段四: 架构重构 (1-2 个月)

| 任务 | 负责人 | 工期 | 依赖 |
|:---|:---:|:---:|:---|
| 建议 1: 消息队列引入 | Arch | 2 周 | P1-001 |
| 建议 2: API 网关部署 | Ops | 1 周 | 建议 1 |
| 建议 3: 监控系统搭建 | Ops | 2 周 | - |

---

## 验收标准

### 功能验收

- [ ] 所有配置项支持环境变量覆盖
- [ ] 所有依赖版本已锁定
- [ ] 数据库查询响应时间 < 1s
- [ ] 无 SQLite 错误日志
- [ ] 健康检查端点可访问

### 性能验收

- [ ] 优先级查询耗时 < 500ms
- [ ] 指标计算吞吐量 > 100 symbols/min
- [ ] 虚拟环境磁盘占用 < 300MB

### 稳定性验收

- [ ] 7 天无崩溃
- [ ] 错误率 < 0.1%
- [ ] 单元测试覆盖率 > 60%

---

## 风险评估

| 风险 | 影响 | 概率 | 应对措施 |
|:---|:---:|:---:|:---|
| 依赖升级导致兼容性问题 | 高 | 中 | 充分测试，保留回滚方案 |
| 数据库迁移失败 | 高 | 低 | 先在测试环境验证 |
| 配置变更导致服务启动失败 | 中 | 中 | 添加配置校验逻辑 |
| 虚拟环境重构影响开发 | 中 | 高 | 提供迁移文档和工具 |

---

## 附录

### A. 相关文档

- [AGENTS.md](AGENTS.md) - AI Agent 操作手册
- [README.md](README.md) - 项目文档
- [TODO.md](TODO.md) - 待办事项

### B. 命令速查

```bash
# 数据库连接
PGPASSWORD=postgres psql -h localhost -p 5433 -U postgres -d market_data

# SQLite 连接
sqlite3 libs/database/services/telegram-service/market_data.db

# 服务启动
./scripts/start.sh daemon

# 服务停止
./scripts/start.sh daemon-stop

# 查看日志
tail -f services/*/logs/*.log
```

### C. 联系方式

- 问题反馈: GitHub Issues
- 技术讨论: Telegram 群 @glue_coding

---

**文档版本**: v1.0
**最后更新**: 2025-01-03
**审核状态**: 待审核
