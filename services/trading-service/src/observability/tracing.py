"""
简易 Tracing 模块

提供轻量级的分布式追踪能力：
- Span: 追踪单元
- trace: 装饰器/上下文管理器
- 支持嵌套调用链
"""
import time
import uuid
import threading
import json
import logging
from pathlib import Path
from datetime import datetime, timezone
from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List
from contextlib import contextmanager
from functools import wraps

LOG = logging.getLogger("tracing")

# 线程本地存储当前 Span
_current_span = threading.local()


@dataclass
class Span:
    """追踪单元"""
    name: str
    trace_id: str = field(default_factory=lambda: uuid.uuid4().hex[:16])
    span_id: str = field(default_factory=lambda: uuid.uuid4().hex[:8])
    parent_id: Optional[str] = None
    start_time: float = field(default_factory=time.time)
    end_time: Optional[float] = None
    status: str = "ok"
    tags: Dict[str, Any] = field(default_factory=dict)
    events: List[Dict[str, Any]] = field(default_factory=list)

    def set_tag(self, key: str, value: Any) -> "Span":
        self.tags[key] = value
        return self

    def add_event(self, name: str, **attrs):
        self.events.append({
            "name": name,
            "timestamp": time.time(),
            **attrs
        })

    def finish(self, status: str = "ok"):
        self.end_time = time.time()
        self.status = status
        _report_span(self)

    @property
    def duration_ms(self) -> float:
        end = self.end_time or time.time()
        return (end - self.start_time) * 1000

    def to_dict(self) -> Dict[str, Any]:
        return {
            "trace_id": self.trace_id,
            "span_id": self.span_id,
            "parent_id": self.parent_id,
            "name": self.name,
            "start_time": datetime.fromtimestamp(self.start_time, timezone.utc).isoformat(),
            "duration_ms": round(self.duration_ms, 2),
            "status": self.status,
            "tags": self.tags,
            "events": self.events,
        }


def get_current_span() -> Optional[Span]:
    """获取当前 Span"""
    return getattr(_current_span, "span", None)


def _set_current_span(span: Optional[Span]):
    _current_span.span = span


# Span 存储（内存，可替换为外部存储）
_spans: List[Span] = []
_spans_lock = threading.Lock()
_max_spans = 1000


def _report_span(span: Span):
    """记录 Span"""
    with _spans_lock:
        _spans.append(span)
        # 保留最近的 span
        if len(_spans) > _max_spans:
            _spans.pop(0)

    # 日志输出
    if span.status == "error":
        LOG.warning(f"Span {span.name} 失败", extra={"ctx": span.to_dict()})
    elif span.duration_ms > 5000:  # 慢操作告警
        LOG.warning(f"Span {span.name} 慢操作 {span.duration_ms:.0f}ms", extra={"ctx": span.to_dict()})


@contextmanager
def trace(name: str, **tags):
    """
    追踪上下文管理器
    
    用法:
        with trace("计算MACD", symbol="BTCUSDT", interval="5m"):
            compute_macd()
    """
    parent = get_current_span()
    span = Span(
        name=name,
        trace_id=parent.trace_id if parent else uuid.uuid4().hex[:16],
        parent_id=parent.span_id if parent else None,
        tags=tags,
    )
    _set_current_span(span)

    try:
        yield span
        span.finish("ok")
    except Exception as e:
        span.set_tag("error", str(e))
        span.finish("error")
        raise
    finally:
        _set_current_span(parent)


def traced(name: str = None):
    """追踪装饰器"""
    def decorator(func):
        span_name = name or func.__name__

        @wraps(func)
        def wrapper(*args, **kwargs):
            with trace(span_name) as span:
                # 尝试提取常用参数作为 tag
                if args and hasattr(args[0], "__class__"):
                    span.set_tag("class", args[0].__class__.__name__)
                return func(*args, **kwargs)
        return wrapper
    return decorator


def get_recent_spans(limit: int = 100) -> List[Dict]:
    """获取最近的 Span"""
    with _spans_lock:
        return [s.to_dict() for s in _spans[-limit:]]


def get_trace(trace_id: str) -> List[Dict]:
    """获取指定 trace 的所有 span"""
    with _spans_lock:
        return [s.to_dict() for s in _spans if s.trace_id == trace_id]


def save_traces(path: Path):
    """保存追踪数据到文件"""
    path.parent.mkdir(parents=True, exist_ok=True)
    data = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "spans": get_recent_spans(limit=_max_spans),
    }
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
