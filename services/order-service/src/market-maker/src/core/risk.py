"""风控模块"""
import time
import logging
from dataclasses import dataclass
from typing import Dict
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class RiskState:
    paused_until: float = 0
    global_paused_until: float = 0


class RiskManager:
    """风控管理器"""

    def __init__(self, per_symbol_limit: float = 200, global_limit: float = 2000,
                 flat_threshold: float = 400, cooldown: float = 10, risk_log_details: bool = False):
        self.per_symbol_limit = per_symbol_limit
        self.global_limit = global_limit
        self.flat_threshold = flat_threshold
        self.cooldown = cooldown
        self.state: Dict[str, RiskState] = {}
        self.global_state = RiskState()
        self._alerts_path = Path("logs/alerts.log")
        self.risk_log_details = risk_log_details

    def check(self, symbol: str, notional: float, total_notional: float, details: dict | None = None) -> str:
        """检查风控
        
        返回: "ok" | "pause" | "flat" | "global_pause"
        """
        now = time.time()
        state = self.state.setdefault(symbol, RiskState())

        # 全局熔断
        if now < self.global_state.paused_until:
            return "global_pause"

        if total_notional > self.global_limit:
            self.global_state.paused_until = now + self.cooldown
            self._alert("GLOBAL_PAUSE", f"total={total_notional:.2f}", details)
            return "global_pause"

        # 单品种检查
        if now < state.paused_until:
            return "pause"

        if notional > self.flat_threshold:
            state.paused_until = now + self.cooldown * 3
            self._alert("FORCE_FLAT", f"{symbol} notional={notional:.2f}", details)
            return "flat"

        if notional > self.per_symbol_limit:
            state.paused_until = now + self.cooldown
            self._alert("RISK_PAUSE", f"{symbol} notional={notional:.2f}", details)
            return "pause"

        return "ok"

    def _alert(self, level: str, msg: str, details: dict | None = None):
        ts = time.strftime("%Y-%m-%d %H:%M:%S")
        detail_str = ""
        if self.risk_log_details and details:
            safe_pairs = [f"{k}={details.get(k)}" for k in sorted(details.keys())]
            detail_str = " | " + " ".join(safe_pairs)
        line = f"[{ts}] [{level}] {msg}{detail_str}"
        logger.warning(f"ALERT: {msg}")
        try:
            self._alerts_path.parent.mkdir(parents=True, exist_ok=True)
            try:
                self._alerts_path.parent.chmod(0o700)
            except Exception:
                pass
            with open(self._alerts_path, "a") as f:
                f.write(line + "\n")
            try:
                self._alerts_path.chmod(0o600)
            except Exception:
                pass
        except Exception:
            pass
