"""
结构化日志模块

特性：
- JSON格式输出（便于ELK/Loki采集）
- 上下文注入（交易对、周期、指标名）
- 性能计时装饰器
"""
import logging
import json
import sys
import time
from pathlib import Path
from datetime import datetime, timezone
from typing import Optional
from contextlib import contextmanager
from functools import wraps

_LOG_LEVEL = logging.INFO
_JSON_FORMAT = True


class JsonFormatter(logging.Formatter):
    """JSON格式日志"""

    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            "ts": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "msg": record.getMessage(),
        }

        # 添加额外上下文
        if hasattr(record, "ctx") and record.ctx:
            log_data["ctx"] = record.ctx

        # 添加异常信息
        if record.exc_info:
            log_data["exc"] = self.formatException(record.exc_info)

        # 添加位置信息（仅DEBUG）
        if record.levelno <= logging.DEBUG:
            log_data["loc"] = f"{record.filename}:{record.lineno}"

        return json.dumps(log_data, ensure_ascii=False, default=str)


class PlainFormatter(logging.Formatter):
    """简洁文本格式"""

    def format(self, record: logging.LogRecord) -> str:
        ts = datetime.now().strftime("%H:%M:%S")
        ctx_str = ""
        if hasattr(record, "ctx") and record.ctx:
            ctx_str = " " + " ".join(f"{k}={v}" for k, v in record.ctx.items())
        return f"{ts} [{record.levelname[0]}] {record.name}: {record.getMessage()}{ctx_str}"


class ContextLogger(logging.LoggerAdapter):
    """带上下文的Logger"""

    def process(self, msg, kwargs):
        extra = kwargs.get("extra", {})
        ctx = {**self.extra, **extra.get("ctx", {})}
        kwargs["extra"] = {"ctx": ctx}
        return msg, kwargs


def setup_logging(
    level: str = "INFO",
    log_file: Optional[str] = None,
    json_format: bool = True,
) -> None:
    """初始化日志系统"""
    global _LOG_LEVEL, _JSON_FORMAT
    _LOG_LEVEL = getattr(logging, level.upper(), logging.INFO)
    _JSON_FORMAT = json_format

    root = logging.getLogger()
    root.setLevel(_LOG_LEVEL)

    # 清除已有handler
    root.handlers.clear()

    # 选择格式
    formatter = JsonFormatter() if json_format else PlainFormatter()

    # 控制台输出
    console = logging.StreamHandler(sys.stdout)
    console.setFormatter(formatter)
    root.addHandler(console)

    # 文件输出
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_path, encoding="utf-8")
        file_handler.setFormatter(formatter)
        root.addHandler(file_handler)


def get_logger(name: str, **default_ctx) -> ContextLogger:
    """获取带上下文的Logger"""
    return ContextLogger(logging.getLogger(name), default_ctx)


@contextmanager
def log_context(logger: logging.Logger, operation: str, **ctx):
    """
    日志上下文管理器，自动记录开始/结束/耗时
    
    用法:
        with log_context(LOG, "计算指标", symbol="BTCUSDT", interval="5m"):
            do_something()
    """
    start = time.perf_counter()
    ctx["op"] = operation

    try:
        yield
        elapsed_ms = (time.perf_counter() - start) * 1000
        logger.info(f"{operation} 完成", extra={"ctx": {**ctx, "elapsed_ms": round(elapsed_ms, 1)}})
    except Exception as e:
        elapsed_ms = (time.perf_counter() - start) * 1000
        logger.error(f"{operation} 失败: {e}", extra={"ctx": {**ctx, "elapsed_ms": round(elapsed_ms, 1)}})
        raise


def timed(logger_name: str = "indicator_service"):
    """计时装饰器"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            logger = logging.getLogger(logger_name)
            start = time.perf_counter()
            try:
                result = func(*args, **kwargs)
                elapsed = (time.perf_counter() - start) * 1000
                logger.debug(f"{func.__name__} 耗时 {elapsed:.1f}ms")
                return result
            except Exception as e:
                elapsed = (time.perf_counter() - start) * 1000
                logger.error(f"{func.__name__} 失败 ({elapsed:.1f}ms): {e}")
                raise
        return wrapper
    return decorator
