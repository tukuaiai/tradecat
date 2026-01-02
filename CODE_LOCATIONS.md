# TradeCat 项目修复 - 代码位置清单

> 生成时间: 2025-01-03 05:45
> 版本: v1.0
> 用途: 指导修复工作的具体代码位置

---

## 📋 目录

- [🔴 P0 - 高优先级问题位置](#🔴-p0---高优先级问题位置)
- [🟡 P1 - 中优先级问题位置](#🟡-p1---中优先级问题位置)
- [🟢 P2 - 低优先级问题位置](#🟢-p2---低优先级问题位置)
- [📊 代码位置汇总](#📊-代码位置汇总)
- [🎯 快速定位命令](#🎯-快速定位命令)

---

## 🔴 P0 - 高优先级问题位置

### P0-001: 硬编码数据库路径 ⚠️

**状态**: 部分完成 (50%)
**影响**: 部署/迁移
**修复难度**: 低

#### 需要修改的代码

| 文件 | 行号 | 当前代码 | 问题 |
|:---|:---:|:---|:---|
| `services/trading-service/src/simple_scheduler.py` | 30 | `SQLITE_PATH = os.environ.get("INDICATOR_SQLITE_PATH", os.path.join(PROJECT_ROOT, "libs/database/services/telegram-service/market_data.db"))` | 缺少 `.replace("${PROJECT_ROOT}", PROJECT_ROOT)` |

#### 修复方案

**在 `simple_scheduler.py` 第 30 行后添加**:

```python
).replace("${PROJECT_ROOT}", PROJECT_ROOT)
```

**完整代码应该是**:

```python
SQLITE_PATH = os.environ.get(
    "INDICATOR_SQLITE_PATH",
    os.path.join(PROJECT_ROOT, "libs/database/services/telegram-service/market_data.db")
).replace("${PROJECT_ROOT}", PROJECT_ROOT)
```

---

### P0-003: 环境变量命名不一致 ❌

**状态**: 未完成 (0%)
**影响**: 代码维护
**修复难度**: 低

#### 需要修改的代码

| 文件 | 行号 | 当前代码 | 问题 |
|:---|:---:|:---|:---|
| `services/telegram-service/config/.env.example` | 9 | `BOT_TOKEN=your_bot_token_here` | 应改为 `TELEGRAM_BOT_TOKEN` |
| `services/telegram-service/src/bot/app.py` | 259 | `BOT_TOKEN = _require_env('BOT_TOKEN', required=True)` | 应使用 `TELEGRAM_BOT_TOKEN` |
| `services/telegram-service/src/bot/app.py` | 5487 | `print(f"🔑 使用 BOT_TOKEN: {BOT_TOKEN[:10]}...{BOT_TOKEN[-10:]}")` | 应使用 `TELEGRAM_BOT_TOKEN` |
| `services/telegram-service/src/bot/app.py` | 5522 | `application = Application.builder().token(BOT_TOKEN).request(request).build()` | 应使用 `TELEGRAM_BOT_TOKEN` |
| `services/telegram-service/src/bot/app.py` | 5676 | `BOT_TOKEN = _require_env('BOT_TOKEN', required=True)` | 应使用 `TELEGRAM_BOT_TOKEN` |
| `services/telegram-service/src/bot/app.py` | 5677 | `url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"` | 应使用 `TELEGRAM_BOT_TOKEN` |

#### 修复方案

**步骤 1**: 修改 `services/telegram-service/config/.env.example`

```diff
- BOT_TOKEN=your_bot_token_here
+ TELEGRAM_BOT_TOKEN=your_bot_token_here
```

**步骤 2**: 在 `services/telegram-service/src/bot/app.py` 中全局替换

```diff
- BOT_TOKEN = _require_env('BOT_TOKEN', required=True)
+ TELEGRAM_BOT_TOKEN = _require_env('TELEGRAM_BOT_TOKEN', required=True)

- print(f"🔑 使用 BOT_TOKEN: {BOT_TOKEN[:10]}...{BOT_TOKEN[-10:]}")
+ print(f"🔑 使用 TELEGRAM_BOT_TOKEN: {TELEGRAM_BOT_TOKEN[:10]}...{TELEGRAM_BOT_TOKEN[-10:]}")

- application = Application.builder().token(BOT_TOKEN).request(request).build()
+ application = Application.builder().token(TELEGRAM_BOT_TOKEN).request(request).build()

- url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
+ url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
```

---

### P0-004: 数据库查询索引优化 ❌

**状态**: 未完成 (0%)
**影响**: 性能
**修复难度**: 中

#### 需要创建的文件

| 文件 | 状态 | 操作 |
|:---|:---:|:---|
| `libs/database/db/schema/008_optimize_priority_queries.sql` | **文件不存在** | **需要创建** |

#### 修复方案

**创建新文件**: `libs/database/db/schema/008_optimize_priority_queries.sql`

```sql
-- ========================================
-- 优先级查询优化索引
-- ========================================
-- 创建时间: 2025-01-03
-- 用途: 优化高优先级币种查询性能

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

**应用索引**:

```bash
PGPASSWORD=postgres psql -h localhost -p 5433 -U postgres -d market_data -f \
    libs/database/db/schema/008_optimize_priority_queries.sql
```

---

### P0-005: SQLite 并发写入优化 ⚠️

**状态**: 部分完成 (70%)
**影响**: 数据完整性
**修复难度**: 中

#### 需要修改的代码

| 文件 | 行号 | 当前代码 | 问题 |
|:---|:---:|:---|:---|
| `services/trading-service/src/simple_scheduler.py` | 49-55 | `_get_sqlite_conn()` 函数 | 缺少线程锁保护 |

#### 修复方案

**步骤 1**: 在 `simple_scheduler.py` 第 13 行后添加导入

```python
import threading
```

**步骤 2**: 在第 46 行后（`_sqlite_conn = None` 之后）添加线程锁

```python
# SQLite 连接复用（避免频繁开关连接）
_sqlite_conn = None
_sqlite_lock = threading.Lock()  # 添加线程锁
```

**步骤 3**: 修改 `_get_sqlite_conn()` 函数（第 49-55 行）

```python
def _get_sqlite_conn():
    """获取 SQLite 连接（单例复用 + 线程安全）"""
    global _sqlite_conn
    with _sqlite_lock:  # 添加线程锁保护
        if _sqlite_conn is None:
            _sqlite_conn = sqlite3.connect(SQLITE_PATH, check_same_thread=False)
            _sqlite_conn.execute("PRAGMA journal_mode=WAL")
            _sqlite_conn.execute("PRAGMA busy_timeout=5000")  # 5秒超时
    return _sqlite_conn
```

---

## 🟡 P1 - 中优先级问题位置

### P1-001: 配置分散管理 ❌

**状态**: 未完成 (0%)
**影响**: 可维护性
**修复难度**: 高

#### 需要创建的文件

| 文件 | 状态 | 操作 |
|:---|:---:|:---|
| `libs/common/config_loader.py` | **文件不存在** | **需要创建** |

#### 修复方案

**创建新文件**: `libs/common/config_loader.py`

```python
"""统一配置加载器"""
import os
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

---

### P1-003: 日志配置分散 ❌

**状态**: 未完成 (0%)
**影响**: 可观测性
**修复难度**: 中

#### 需要修改的代码

| 文件 | 行号 | 当前代码 | 问题 |
|:---|:---:|:---|:---|
| `services/trading-service/src/simple_scheduler.py` | 67-68 | `def log(msg: str):` 和 `print()` | 应使用 `logging` |

#### 需要创建的文件

| 文件 | 状态 | 操作 |
|:---|:---:|:---|
| `libs/common/logging_config.py` | **文件不存在** | **需要创建** |

#### 修复方案

**步骤 1**: 创建新文件 `libs/common/logging_config.py`

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

**步骤 2**: 修改 `services/trading-service/src/simple_scheduler.py`

**2.1 添加导入（第 13-14 行后）**:

```python
import logging
from libs.common.logging_config import setup_logging, get_logger
```

**2.2 添加日志初始化（第 44 行后，`high_priority_symbols = []` 之后）**:

```python
# 初始化日志
setup_logging(
    service_name="trading-service",
    log_level=os.getenv("LOG_LEVEL", "INFO"),
    log_dir=os.path.join(TRADING_SERVICE_DIR, "logs")
)
logger = get_logger(__name__)
```

**2.3 移除 `log` 函数（第 67-68 行）**:

```python
- def log(msg: str):
-     print(f"[{datetime.now():%Y-%m-%d %H:%M:%S}] {msg}", flush=True)
+ # log 函数已移除，使用 logger.info(msg)
```

**2.4 全局替换所有 `log(` 调用为 `logger.info(`**

---

### P1-004: 错误处理过于宽泛 ❌

**状态**: 未完成 (0%)
**影响**: 可调试性
**修复难度**: 低

#### 需要修改的代码

| 文件 | 行号 | 当前代码 | 问题 |
|:---|:---:|:---|:---|
| `services/trading-service/src/simple_scheduler.py` | 157 | `except Exception as e:` | 捕获过于宽泛 |
| `services/trading-service/src/simple_scheduler.py` | 204 | `except Exception as e:` | 捕获过于宽泛 |
| `services/trading-service/src/simple_scheduler.py` | 221 | `except Exception as e:` | 捕获过于宽泛 |
| `services/trading-service/src/simple_scheduler.py` | 236 | `except Exception as e:` | 捕获过于宽泛 |
| `services/trading-service/src/simple_scheduler.py` | 252 | `except Exception as e:` | 捕获过于宽泛 |
| `services/trading-service/src/simple_scheduler.py` | 273 | `except Exception as e:` | 捕获过于宽泛 |
| `services/trading-service/src/simple_scheduler.py` | 372 | `except Exception as e:` | 捕获过于宽泛 |

#### 需要创建的文件

| 文件 | 状态 | 操作 |
|:---|:---:|:---|
| `libs/common/error_handler.py` | **文件不存在** | **需要创建** |

#### 修复方案

**步骤 1**: 创建新文件 `libs/common/error_handler.py`

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

**步骤 2**: 修改 `simple_scheduler.py` 中的异常处理

**示例 - 第 90-138 行 `_query_kline_priority` 函数**:

```python
@handle_database_errors  # 添加装饰器
def _query_kline_priority(top_n: int = 30) -> set:
    """K线维度优先级 - 交易量+波动率+涨跌幅"""
    symbols = set()
    try:
        # ... 原有代码 ...
        return symbols
    except psycopg.Error as e:  # 具体异常类型
        logger.error(f"查询失败: {e}", exc_info=True)
        return symbols
```

**对所有 7 处 `except Exception` 进行类似修改**:

```diff
- except Exception as e:
+ except (psycopg.Error, sqlite3.Error) as e:
```

---

### P1-005: 缺少健康检查端点 ❌

**状态**: 未完成 (0%)
**影响**: 部署
**修复难度**: 低

#### 需要创建的文件

| 文件 | 状态 | 操作 |
|:---|:---:|:---|
| `services/trading-service/src/health.py` | **文件不存在** | **需要创建** |
| `services/data-service/src/health.py` | **文件不存在** | **需要创建** |
| `services/telegram-service/src/health.py` | **文件不存在** | **需要创建** |

#### 修复方案

**步骤 1**: 创建 `services/trading-service/src/health.py`

```python
"""健康检查端点"""
from fastapi import FastAPI
from fastapi.responses import JSONResponse
import psycopg
import sqlite3
import os

app = FastAPI()

DB_URL = os.environ.get("DATABASE_URL", "postgresql://opentd:OpenTD_pass@localhost:5433/market_data")
SQLITE_PATH = os.environ.get("INDICATOR_SQLITE_PATH", "/tmp/market_data.db")

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
    return {"status": "ready"}
```

**步骤 2**: 为 `data-service` 和 `telegram-service` 创建类似的 `health.py` 文件

**步骤 3**: 更新 `requirements.txt` 添加依赖

```python
# 各服务的 requirements.txt 添加
fastapi==0.109.0
uvicorn[standard]==0.27.0
```

---

## 🟢 P2 - 低优先级问题位置

### P2-002: 添加单元测试 ❌

**状态**: 未完成 (0%)
**影响**: 代码质量
**修复难度**: 中

#### 需要创建的目录和文件

| 文件 | 状态 | 操作 |
|:---|:---:|:---|
| `services/trading-service/tests/` | **目录不存在** | **需要创建** |
| `services/data-service/tests/` | **目录不存在** | **需要创建** |
| `services/telegram-service/tests/` | **目录不存在** | **需要创建** |

#### 修复方案

**步骤 1**: 创建测试目录

```bash
mkdir -p services/trading-service/tests
mkdir -p services/data-service/tests
mkdir -p services/telegram-service/tests
```

**步骤 2**: 创建 `services/trading-service/tests/__init__.py`

```python
"""测试包"""
```

**步骤 3**: 创建 `services/trading-service/tests/test_simple_scheduler.py`

```python
"""测试 simple_scheduler"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timezone
import os

@pytest.fixture
def mock_config():
    """模拟配置"""
    os.environ["DATABASE_URL"] = "postgresql://test:test@localhost/test"
    os.environ["INDICATOR_SQLITE_PATH"] = "/tmp/test.db"


def test_parse_list():
    """测试列表解析"""
    import sys
    sys.path.insert(0, "services/trading-service/src")
    from simple_scheduler import _parse_list

    assert _parse_list("BTCUSDT,ETHUSDT") == ["BTCUSDT", "ETHUSDT"]
    assert _parse_list("BTCUSDT, ETHUSDT,") == ["BTCUSDT", "ETHUSDT"]
    assert _parse_list("") == []


@pytest.mark.asyncio
async def test_get_high_priority_symbols_fast(mock_config):
    """测试高优先级币种获取"""
    import sys
    sys.path.insert(0, "services/trading-service/src")
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

**步骤 4**: 运行测试

```bash
cd services/trading-service
pytest tests/ -v --cov=src
```

---

### P2-003: 定期清理 SQLite 数据库 ❌

**状态**: 未完成 (0%)
**影响**: 资源占用
**修复难度**: 中

#### 需要创建的文件

| 文件 | 状态 | 操作 |
|:---|:---:|:---|
| `scripts/cleanup_sqlite.sh` | **文件不存在** | **需要创建** |

#### 修复方案

**创建新文件**: `scripts/cleanup_sqlite.sh`

```bash
#!/bin/bash
# SQLite 数据库清理脚本

DB_PATH="${1:-/home/lenovo/.projects/tradecat/libs/database/services/telegram-service/market_data.db}"
KEEP_DAYS="${2:-30}"

echo "清理 SQLite 数据库: $DB_PATH"
echo "保留最近 $KEEP_DAYS 天数据"

# 检查数据库文件是否存在
if [ ! -f "$DB_PATH" ]; then
    echo "错误: 数据库文件不存在: $DB_PATH"
    exit 1
fi

# 备份数据库
BACKUP_DIR="/home/lenovo/.projects/tradecat/backups/sqlite"
mkdir -p "$BACKUP_DIR"
BACKUP_FILE="$BACKUP_DIR/market_data_$(date +%Y%m%d_%H%M%S).db"

echo "备份数据库到: $BACKUP_FILE"
cp "$DB_PATH" "$BACKUP_FILE"

# 清理旧数据
sqlite3 "$DB_PATH" << SQL
-- 删除旧数据（根据各表的 timestamp 字段）
DELETE FROM [MACD柱状扫描器.py]
WHERE datetime(数据时间) < datetime('now', '-$KEEP_DAYS days');

DELETE FROM [KDJ随机指标扫描器.py]
WHERE datetime(数据时间) < datetime('now', '-$KEEP_DAYS days');

-- 清理其他指标表...
-- (根据实际表结构添加)

-- 优化数据库
VACUUM;
ANALYZE;
SQL

echo "清理完成"
echo "清理后的数据库大小:"
du -h "$DB_PATH"

# 保留备份（删除 7 天前的备份）
find "$BACKUP_DIR" -name "market_data_*.db" -mtime +7 -delete
```

**步骤 2**: 添加执行权限

```bash
chmod +x scripts/cleanup_sqlite.sh
```

**步骤 3**: 添加到 crontab

```bash
# 编辑 crontab
crontab -e

# 每周日凌晨 2 点清理，保留 30 天数据
0 2 * * 0 /home/lenovo/.projects/tradecat/scripts/cleanup_sqlite.sh "" 30 >> /var/log/tradecat/cleanup.log 2>&1
```

---

## 📊 代码位置汇总

### 需要修改的文件 (6 个)

| 问题ID | 文件 | 修改类型 | 行号 |
|:---|:---|:---:|:---|
| P0-001 | `services/trading-service/src/simple_scheduler.py` | 添加代码 | 30 |
| P0-003 | `services/telegram-service/config/.env.example` | 修改变量名 | 9 |
| P0-003 | `services/telegram-service/src/bot/app.py` | 全局替换 | 259, 5487, 5522, 5676, 5677 |
| P0-005 | `services/trading-service/src/simple_scheduler.py` | 添加代码 | 13, 46, 49-55 |
| P1-003 | `services/trading-service/src/simple_scheduler.py` | 删除/添加代码 | 13-14, 44, 67-68 |
| P1-004 | `services/trading-service/src/simple_scheduler.py` | 修改异常处理 | 157, 204, 221, 236, 252, 273, 372 |

### 需要创建的文件 (9 个)

| 问题ID | 文件 | 说明 |
|:---|:---|:---|
| P0-004 | `libs/database/db/schema/008_optimize_priority_queries.sql` | 数据库索引优化 |
| P1-001 | `libs/common/config_loader.py` | 统一配置加载器 |
| P1-003 | `libs/common/logging_config.py` | 统一日志配置 |
| P1-004 | `libs/common/error_handler.py` | 错误处理工具 |
| P1-005 | `services/trading-service/src/health.py` | 健康检查端点 |
| P1-005 | `services/data-service/src/health.py` | 健康检查端点 |
| P1-005 | `services/telegram-service/src/health.py` | 健康检查端点 |
| P2-002 | `services/trading-service/tests/test_simple_scheduler.py` | 单元测试 |
| P2-003 | `scripts/cleanup_sqlite.sh` | 数据清理脚本 |

### 工作量评估

| 问题 | 需要修改 | 需要创建 | 总计 | 预计时间 |
|:---|:---:|:---:|:---:|:---:|
| P0-001 | 1 处 | 0 | 1 | 5 分钟 |
| P0-003 | 6 处 | 0 | 6 | 15 分钟 |
| P0-004 | 0 | 1 个文件 | 1 | 20 分钟 |
| P0-005 | 3 处 | 0 | 3 | 15 分钟 |
| P1-001 | 0 | 1 个文件 | 1 | 30 分钟 |
| P1-003 | 3 处 | 1 个文件 | 4 | 45 分钟 |
| P1-004 | 7 处 | 1 个文件 | 8 | 30 分钟 |
| P1-005 | 0 | 3 个文件 | 3 | 45 分钟 |
| P2-002 | 0 | 1 个文件 + 目录 | 1 | 60 分钟 |
| P2-003 | 0 | 1 个文件 | 1 | 20 分钟 |
| **总计** | **20 处** | **9 个文件** | **29** | **~5 小时** |

---

## 🎯 快速定位命令

### 查找所有需要修改的位置

```bash
# P0-001: 查找 SQLITE_PATH 定义
grep -n "SQLITE_PATH" services/trading-service/src/simple_scheduler.py

# P0-003: 查找 BOT_TOKEN 使用
grep -n "BOT_TOKEN" services/telegram-service/src/bot/app.py

# P1-003: 查找 print 语句
grep -n "print(" services/trading-service/src/simple_scheduler.py

# P1-004: 查找宽泛异常捕获
grep -n "except Exception" services/trading-service/src/simple_scheduler.py

# P1-004: 统计所有 except Exception
grep -r "except Exception" services/trading-service/src/simple_scheduler.py | wc -l
```

### 检查缺失文件

```bash
# 检查缺失的配置文件
ls -la libs/common/config_loader.py 2>/dev/null || echo "❌ 缺失 config_loader.py"
ls -la libs/common/logging_config.py 2>/dev/null || echo "❌ 缺失 logging_config.py"
ls -la libs/common/error_handler.py 2>/dev/null || echo "❌ 缺失 error_handler.py"

# 检查缺失的健康检查文件
ls -la services/trading-service/src/health.py 2>/dev/null || echo "❌ 缺失 trading-service/health.py"
ls -la services/data-service/src/health.py 2>/dev/null || echo "❌ 缺失 data-service/health.py"
ls -la services/telegram-service/src/health.py 2>/dev/null || echo "❌ 缺失 telegram-service/health.py"

# 检查缺失的测试目录
ls -la services/trading-service/tests/ 2>/dev/null || echo "❌ 缺失 trading-service/tests/"
ls -la services/data-service/tests/ 2>/dev/null || echo "❌ 缺失 data-service/tests/"
ls -la services/telegram-service/tests/ 2>/dev/null || echo "❌ 缺失 telegram-service/tests/"

# 检查缺失的优化 schema
ls -la libs/database/db/schema/008_*.sql 2>/dev/null || echo "❌ 缺失 008 优化 schema"

# 检查缺失的清理脚本
ls -la scripts/cleanup_sqlite.sh 2>/dev/null || echo "❌ 缺失 cleanup_sqlite.sh"
```

### 批量检查脚本

```bash
#!/bin/bash
# 检查所有缺失的文件

echo "=== 检查缺失文件 ==="

# 检查配置文件
for file in \
    "libs/common/config_loader.py" \
    "libs/common/logging_config.py" \
    "libs/common/error_handler.py"; do
    if [ ! -f "$file" ]; then
        echo "❌ 缺失: $file"
    fi
done

# 检查健康检查文件
for svc in trading-service data-service telegram-service; do
    if [ ! -f "services/$svc/src/health.py" ]; then
        echo "❌ 缺失: services/$svc/src/health.py"
    fi
done

# 检查测试目录
for svc in trading-service data-service telegram-service; do
    if [ ! -d "services/$svc/tests/" ]; then
        echo "❌ 缺失: services/$svc/tests/"
    fi
done

# 检查优化 schema
if [ ! -f "libs/database/db/schema/008_optimize_priority_queries.sql" ]; then
    echo "❌ 缺失: libs/database/db/schema/008_optimize_priority_queries.sql"
fi

# 检查清理脚本
if [ ! -f "scripts/cleanup_sqlite.sh" ]; then
    echo "❌ 缺失: scripts/cleanup_sqlite.sh"
fi

echo "=== 检查完成 ==="
```

---

## 📌 修改优先级排序

### 阶段一: 高优先级修复 (1-2 小时)

| 优先级 | 问题 | 文件数 | 难度 | 预计时间 |
|:---:|:---|:---:|:---:|:---:|
| 1 | P0-001 | 1 | 低 | 5 分钟 |
| 2 | P0-003 | 2 | 低 | 15 分钟 |
| 3 | P0-005 | 1 | 中 | 15 分钟 |
| 4 | P0-004 | 1 | 中 | 20 分钟 |

### 阶段二: 中优先级修复 (2-3 小时)

| 优先级 | 问题 | 文件数 | 难度 | 预计时间 |
|:---:|:---|:---:|:---:|:---:|
| 1 | P1-003 | 2 | 中 | 45 分钟 |
| 2 | P1-004 | 2 | 中 | 30 分钟 |
| 3 | P1-005 | 3 | 低 | 45 分钟 |
| 4 | P1-001 | 1 | 高 | 30 分钟 |

### 阶段三: 低优先级优化 (1-2 小时)

| 优先级 | 问题 | 文件数 | 难度 | 预计时间 |
|:---:|:---|:---:|:---:|:---:|
| 1 | P2-003 | 1 | 低 | 20 分钟 |
| 2 | P2-002 | 1 | 中 | 60 分钟 |

---

## ⚠️ 关键提示

### 1. 必须修改的文件

**P0-003** 需要同时修改 **2 个文件**，共 **6 处** `BOT_TOKEN` 引用:

```bash
# 快速查找所有需要修改的位置
grep -n "BOT_TOKEN" services/telegram-service/src/bot/app.py
grep -n "BOT_TOKEN" services/telegram-service/config/.env.example
```

### 2. 全局替换命令

**P0-003**: 在 `bot/app.py` 中全局替换 `BOT_TOKEN` 为 `TELEGRAM_BOT_TOKEN`

```bash
# 使用 sed 进行全局替换
sed -i 's/BOT_TOKEN/TELEGRAM_BOT_TOKEN/g' services/telegram-service/src/bot/app.py
sed -i 's/BOT_TOKEN/TELEGRAM_BOT_TOKEN/g' services/telegram-service/config/.env.example
```

### 3. 异常处理修改

**P1-004**: 需要修改 **7 处** `except Exception`

```python
# 建议的模式替换
- except Exception as e:
+ except (psycopg.Error, sqlite3.Error) as e:
```

### 4. 所有缺失的文件都可以在 `FIX_PLAN.md` 中找到完整实现代码

---

## ✅ 验收检查清单

### 功能完整性

- [ ] P0-001: 路径替换逻辑实现
- [ ] P0-003: 环境变量统一为 `TELEGRAM_BOT_TOKEN`
- [ ] P0-004: 数据库索引创建成功
- [ ] P0-005: SQLite 线程锁添加
- [ ] P1-003: 日志系统统一
- [ ] P1-004: 异常处理具体化
- [ ] P1-005: 健康检查端点可访问
- [ ] P2-002: 单元测试通过
- [ ] P2-003: 数据清理脚本可用

### 代码质量

- [ ] 无硬编码绝对路径
- [ ] 使用统一日志系统
- [ ] 错误处理具体化
- [ ] 有单元测试覆盖
- [ ] 有健康检查端点

### 文件完整性

- [ ] `libs/common/config_loader.py` 存在
- [ ] `libs/common/logging_config.py` 存在
- [ ] `libs/common/error_handler.py` 存在
- [ ] 所有服务的 `health.py` 存在
- [ ] 所有服务的 `tests/` 目录存在
- [ ] `008_optimize_priority_queries.sql` 存在
- [ ] `cleanup_sqlite.sh` 存在

---

## 📞 联系方式

- 问题反馈: GitHub Issues
- 技术讨论: Telegram 群 @glue_coding
- 完整修复方案: 参考 `FIX_PLAN.md`

---

**文档版本**: v1.0
**最后更新**: 2025-01-03 05:45
**相关文档**: [FIX_PLAN.md](FIX_PLAN.md)
