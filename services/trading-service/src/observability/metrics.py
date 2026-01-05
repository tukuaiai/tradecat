"""
指标收集模块

提供 Prometheus 风格的指标收集，支持：
- Counter: 计数器（只增不减）
- Gauge: 仪表盘（可增可减）
- Histogram: 直方图（分布统计）
- Summary: 摘要（百分位统计）

指标存储在内存中，可通过 /metrics 端点暴露或写入文件
"""
import time
import threading
import json
from pathlib import Path
from datetime import datetime, timezone
from dataclasses import dataclass, field
from typing import Dict, List, Any
from collections import defaultdict


@dataclass
class MetricValue:
    """单个指标值"""
    value: float
    labels: Dict[str, str]
    timestamp: float = field(default_factory=time.time)


class Counter:
    """计数器 - 只增不减"""

    def __init__(self, name: str, help_text: str = ""):
        self.name = name
        self.help = help_text
        self._values: Dict[tuple, float] = defaultdict(float)
        self._lock = threading.Lock()

    def inc(self, value: float = 1, **labels):
        key = tuple(sorted(labels.items()))
        with self._lock:
            self._values[key] += value

    def get(self, **labels) -> float:
        key = tuple(sorted(labels.items()))
        return self._values.get(key, 0)

    def collect(self) -> List[MetricValue]:
        with self._lock:
            return [
                MetricValue(v, dict(k))
                for k, v in self._values.items()
            ]


class Gauge:
    """仪表盘 - 可增可减"""

    def __init__(self, name: str, help_text: str = ""):
        self.name = name
        self.help = help_text
        self._values: Dict[tuple, float] = {}
        self._lock = threading.Lock()

    def set(self, value: float, **labels):
        key = tuple(sorted(labels.items()))
        with self._lock:
            self._values[key] = value

    def inc(self, value: float = 1, **labels):
        key = tuple(sorted(labels.items()))
        with self._lock:
            self._values[key] = self._values.get(key, 0) + value

    def dec(self, value: float = 1, **labels):
        self.inc(-value, **labels)

    def get(self, **labels) -> float:
        key = tuple(sorted(labels.items()))
        return self._values.get(key, 0)

    def collect(self) -> List[MetricValue]:
        with self._lock:
            return [
                MetricValue(v, dict(k))
                for k, v in self._values.items()
            ]


class Histogram:
    """直方图 - 分布统计"""

    DEFAULT_BUCKETS = (0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1, 2.5, 5, 10, float("inf"))

    def __init__(self, name: str, help_text: str = "", buckets: tuple = None):
        self.name = name
        self.help = help_text
        self.buckets = buckets or self.DEFAULT_BUCKETS
        self._counts: Dict[tuple, Dict[float, int]] = defaultdict(lambda: {b: 0 for b in self.buckets})
        self._sums: Dict[tuple, float] = defaultdict(float)
        self._totals: Dict[tuple, int] = defaultdict(int)
        self._lock = threading.Lock()

    def observe(self, value: float, **labels):
        key = tuple(sorted(labels.items()))
        with self._lock:
            self._sums[key] += value
            self._totals[key] += 1
            for bucket in self.buckets:
                if value <= bucket:
                    self._counts[key][bucket] += 1

    def collect(self) -> List[MetricValue]:
        results = []
        with self._lock:
            for key, buckets in self._counts.items():
                labels = dict(key)
                for bucket, count in buckets.items():
                    results.append(MetricValue(
                        count,
                        {**labels, "le": str(bucket)},
                    ))
                results.append(MetricValue(self._sums[key], {**labels, "type": "sum"}))
                results.append(MetricValue(self._totals[key], {**labels, "type": "count"}))
        return results


class MetricsCollector:
    """指标收集器"""

    def __init__(self):
        self._metrics: Dict[str, Any] = {}
        self._lock = threading.Lock()

    def counter(self, name: str, help_text: str = "") -> Counter:
        with self._lock:
            if name not in self._metrics:
                self._metrics[name] = Counter(name, help_text)
            return self._metrics[name]

    def gauge(self, name: str, help_text: str = "") -> Gauge:
        with self._lock:
            if name not in self._metrics:
                self._metrics[name] = Gauge(name, help_text)
            return self._metrics[name]

    def histogram(self, name: str, help_text: str = "", buckets: tuple = None) -> Histogram:
        with self._lock:
            if name not in self._metrics:
                self._metrics[name] = Histogram(name, help_text, buckets)
            return self._metrics[name]

    def collect_all(self) -> Dict[str, List[MetricValue]]:
        """收集所有指标"""
        result = {}
        with self._lock:
            for name, metric in self._metrics.items():
                result[name] = metric.collect()
        return result

    def to_prometheus(self) -> str:
        """导出为 Prometheus 格式"""
        lines = []
        for name, values in self.collect_all().items():
            metric = self._metrics[name]
            if metric.help:
                lines.append(f"# HELP {name} {metric.help}")
            lines.append(f"# TYPE {name} {type(metric).__name__.lower()}")
            for mv in values:
                label_str = ",".join(f'{k}="{v}"' for k, v in mv.labels.items())
                if label_str:
                    lines.append(f"{name}{{{label_str}}} {mv.value}")
                else:
                    lines.append(f"{name} {mv.value}")
        return "\n".join(lines)

    def to_json(self) -> str:
        """导出为 JSON 格式"""
        data = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "metrics": {}
        }
        for name, values in self.collect_all().items():
            data["metrics"][name] = [
                {"value": mv.value, "labels": mv.labels}
                for mv in values
            ]
        return json.dumps(data, ensure_ascii=False)

    def save(self, path: Path):
        """保存指标到文件"""
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(self.to_json(), encoding="utf-8")


# 全局指标收集器
metrics = MetricsCollector()

# 预定义指标
indicator_compute_total = metrics.counter(
    "indicator_compute_total",
    "指标计算总次数"
)
indicator_compute_errors = metrics.counter(
    "indicator_compute_errors",
    "指标计算错误次数"
)
indicator_compute_duration = metrics.histogram(
    "indicator_compute_duration_seconds",
    "指标计算耗时",
    buckets=(0.1, 0.5, 1, 2, 5, 10, 30, 60, 120)
)
db_read_duration = metrics.histogram(
    "db_read_duration_seconds",
    "数据库读取耗时",
    buckets=(0.1, 0.5, 1, 2, 5, 10, 30)
)
db_write_duration = metrics.histogram(
    "db_write_duration_seconds",
    "数据库写入耗时",
    buckets=(0.01, 0.05, 0.1, 0.5, 1, 2, 5)
)
active_symbols = metrics.gauge(
    "active_symbols",
    "活跃交易对数量"
)
last_compute_timestamp = metrics.gauge(
    "last_compute_timestamp",
    "最后计算时间戳"
)
