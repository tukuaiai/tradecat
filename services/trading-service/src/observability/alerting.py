"""
告警模块

支持多种告警通道：
- 日志告警（默认）
- 文件告警
- Webhook（可扩展 Telegram/钉钉/飞书）
"""
import json
import logging
import threading
import time
from enum import Enum
from pathlib import Path
from datetime import datetime, timezone
from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List
from urllib.request import urlopen, Request
from urllib.error import URLError

LOG = logging.getLogger("alerting")


class AlertLevel(Enum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class Alert:
    """告警事件"""
    level: AlertLevel
    title: str
    message: str
    source: str = "indicator_service"
    timestamp: float = field(default_factory=time.time)
    tags: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "level": self.level.value,
            "title": self.title,
            "message": self.message,
            "source": self.source,
            "timestamp": datetime.fromtimestamp(self.timestamp, timezone.utc).isoformat(),
            "tags": self.tags,
        }


class AlertChannel:
    """告警通道基类"""

    def send(self, alert: Alert) -> bool:
        raise NotImplementedError


class LogChannel(AlertChannel):
    """日志告警通道"""

    def send(self, alert: Alert) -> bool:
        level_map = {
            AlertLevel.INFO: logging.INFO,
            AlertLevel.WARNING: logging.WARNING,
            AlertLevel.ERROR: logging.ERROR,
            AlertLevel.CRITICAL: logging.CRITICAL,
        }
        LOG.log(
            level_map.get(alert.level, logging.WARNING),
            f"[ALERT] {alert.title}: {alert.message}",
            extra={"ctx": alert.tags}
        )
        return True


class FileChannel(AlertChannel):
    """文件告警通道"""

    def __init__(self, path: Path):
        self.path = path
        self._lock = threading.Lock()

    def send(self, alert: Alert) -> bool:
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            with self._lock:
                with open(self.path, "a", encoding="utf-8") as f:
                    f.write(json.dumps(alert.to_dict(), ensure_ascii=False) + "\n")
            return True
        except Exception as e:
            LOG.error(f"文件告警失败: {e}")
            return False


class WebhookChannel(AlertChannel):
    """Webhook 告警通道"""

    def __init__(self, url: str, headers: Dict[str, str] = None):
        self.url = url
        self.headers = headers or {"Content-Type": "application/json"}

    def send(self, alert: Alert) -> bool:
        try:
            data = json.dumps(alert.to_dict(), ensure_ascii=False).encode("utf-8")
            req = Request(self.url, data=data, headers=self.headers, method="POST")
            with urlopen(req, timeout=10) as resp:
                return resp.status == 200
        except URLError as e:
            LOG.error(f"Webhook 告警失败: {e}")
            return False


class AlertManager:
    """告警管理器"""

    def __init__(self):
        self._channels: List[AlertChannel] = [LogChannel()]
        self._history: List[Alert] = []
        self._lock = threading.Lock()
        self._max_history = 100
        # 告警抑制：相同告警在 N 秒内不重复发送
        self._suppress_seconds = 60
        self._last_alerts: Dict[str, float] = {}

    def add_channel(self, channel: AlertChannel):
        self._channels.append(channel)

    def _should_suppress(self, alert: Alert) -> bool:
        """检查是否应该抑制告警"""
        key = f"{alert.level.value}:{alert.title}"
        now = time.time()
        last_time = self._last_alerts.get(key, 0)
        if now - last_time < self._suppress_seconds:
            return True
        self._last_alerts[key] = now
        return False

    def send(self, alert: Alert) -> bool:
        if self._should_suppress(alert):
            return False

        with self._lock:
            self._history.append(alert)
            if len(self._history) > self._max_history:
                self._history.pop(0)

        success = True
        for channel in self._channels:
            try:
                if not channel.send(alert):
                    success = False
            except Exception as e:
                LOG.error(f"告警通道异常: {e}")
                success = False
        return success

    def get_history(self, limit: int = 50) -> List[Dict]:
        with self._lock:
            return [a.to_dict() for a in self._history[-limit:]]


# 全局告警管理器
_manager = AlertManager()


def alert(
    level: AlertLevel,
    title: str,
    message: str,
    source: str = "indicator_service",
    **tags
) -> bool:
    """发送告警"""
    return _manager.send(Alert(
        level=level,
        title=title,
        message=message,
        source=source,
        tags=tags,
    ))


def add_channel(channel: AlertChannel):
    """添加告警通道"""
    _manager.add_channel(channel)


def setup_alerting(
    file_path: Optional[Path] = None,
    webhook_url: Optional[str] = None,
):
    """配置告警通道"""
    if file_path:
        _manager.add_channel(FileChannel(file_path))
    if webhook_url:
        _manager.add_channel(WebhookChannel(webhook_url))


# 便捷函数
def alert_info(title: str, message: str, **tags):
    return alert(AlertLevel.INFO, title, message, **tags)


def alert_warning(title: str, message: str, **tags):
    return alert(AlertLevel.WARNING, title, message, **tags)


def alert_error(title: str, message: str, **tags):
    return alert(AlertLevel.ERROR, title, message, **tags)


def alert_critical(title: str, message: str, **tags):
    return alert(AlertLevel.CRITICAL, title, message, **tags)
