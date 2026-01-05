"""API Key 负载均衡管理器"""
from __future__ import annotations

import logging
import os
import random
import time
from dataclasses import dataclass
from threading import Lock

logger = logging.getLogger(__name__)


@dataclass
class KeyState:
    """单个 Key 的状态"""
    key: str
    requests: int = 0
    errors: int = 0
    last_used: float = 0
    cooldown_until: float = 0  # 冷却到期时间

    @property
    def is_available(self) -> bool:
        return time.time() >= self.cooldown_until


class KeyManager:
    """多 Key 负载均衡

    支持策略:
    - round_robin: 轮询
    - least_used: 最少使用
    - random: 随机

    用法:
        # 环境变量配置多个 key，逗号分隔
        FRED_API_KEY=key1,key2,key3

        # 代码中使用
        km = KeyManager("FRED_API_KEY")
        key = km.get_key()
        km.report_success(key)  # 或 km.report_error(key)
    """

    def __init__(
        self,
        env_var: str,
        strategy: str = "round_robin",
        cooldown_seconds: float = 60,
    ):
        self.env_var = env_var
        self.strategy = strategy
        self.cooldown_seconds = cooldown_seconds
        self._lock = Lock()
        self._index = 0

        # 解析 keys
        raw = os.getenv(env_var, "")
        keys = [k.strip() for k in raw.split(",") if k.strip()]
        self._keys: dict[str, KeyState] = {k: KeyState(key=k) for k in keys}

        if keys:
            logger.info(f"[KeyManager] {env_var}: 加载 {len(keys)} 个 keys")

    @property
    def available_keys(self) -> list[KeyState]:
        """获取可用的 keys"""
        return [s for s in self._keys.values() if s.is_available]

    def get_key(self) -> str | None:
        """获取一个 key"""
        with self._lock:
            available = self.available_keys
            if not available:
                # 所有 key 都在冷却，返回冷却时间最短的
                if self._keys:
                    return min(self._keys.values(), key=lambda s: s.cooldown_until).key
                return None

            if self.strategy == "round_robin":
                state = available[self._index % len(available)]
                self._index += 1
            elif self.strategy == "least_used":
                state = min(available, key=lambda s: s.requests)
            else:  # random
                state = random.choice(available)

            state.requests += 1
            state.last_used = time.time()
            return state.key

    def report_success(self, key: str):
        """报告成功"""
        if key in self._keys:
            self._keys[key].errors = 0

    def report_error(self, key: str, cooldown: bool = True):
        """报告错误，可选进入冷却"""
        if key not in self._keys:
            return

        state = self._keys[key]
        state.errors += 1

        if cooldown and state.errors >= 3:
            state.cooldown_until = time.time() + self.cooldown_seconds
            logger.warning(f"[KeyManager] {key[:8]}... 进入冷却 {self.cooldown_seconds}s")

    def stats(self) -> dict:
        """获取统计"""
        return {
            "total": len(self._keys),
            "available": len(self.available_keys),
            "keys": [
                {
                    "key": f"{s.key[:8]}...",
                    "requests": s.requests,
                    "errors": s.errors,
                    "available": s.is_available,
                }
                for s in self._keys.values()
            ],
        }


# 预置常用服务的 Key Manager
_managers: dict[str, KeyManager] = {}

def get_key_manager(env_var: str, **kwargs) -> KeyManager:
    """获取或创建 KeyManager 单例"""
    if env_var not in _managers:
        _managers[env_var] = KeyManager(env_var, **kwargs)
    return _managers[env_var]
