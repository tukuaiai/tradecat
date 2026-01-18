"""排行榜卡片基类定义"""

from __future__ import annotations

from abc import ABC, abstractmethod
import math
from typing import Any, Dict, Iterable, List, Sequence


class RankingCard(ABC):
    """所有排行榜卡片需要实现的统一接口"""

    def __init__(
        self,
        card_id: str,
        button_text: str,
        category: str = "free",
        cost: int = 0,
        description: str | None = None,
        default_state: Dict[str, Any] | None = None,
        callback_prefixes: Sequence[str] | None = None,
        priority: int = 100,
        entry_callback: str | None = None,
        button_key: str | None = None,
    ) -> None:
        self.card_id = card_id
        self.button_text = button_text
        self.button_key = button_key  # i18n 键，如 "card.ema.btn"
        self.category = category
        self.cost = cost
        self.description = description or ""
        self.default_state = dict(default_state or {})
        self.callback_prefixes: List[str] = list(callback_prefixes or [])
        self.priority = priority
        self._entry_callback = entry_callback or card_id

    @property
    def entry_callback(self) -> str:
        """主菜单按钮使用的 callback_data"""
        return self._entry_callback

    def handles_callback(self, callback_data: str) -> bool:
        """判断某个回调是否由此卡片处理"""
        if callback_data == self.card_id or callback_data == self.entry_callback:
            return True
        return any(callback_data.startswith(prefix) for prefix in self.callback_prefixes)

    @abstractmethod
    async def handle_callback(self, update, context, services: Dict[str, Any]) -> bool:
        """处理按钮/命令，返回是否已消费"""

    def iter_default_state(self) -> Iterable[tuple[str, Any]]:
        """遍历卡片需要注入的用户状态默认值"""
        return self.default_state.items()

    async def ensure_access(self, query, user_handler, *, feature_name: str | None = None) -> bool:
        """如有必要检查并扣除积分"""
        # 全部卡片改为免费模式，直接放行，避免出现任何积分/扣费提示
        return True


# ==================== 通用格式化工具 ====================
def format_number(value: Any, digits: int = 4) -> str:
    """数值格式化，裁剪尾随 0，非数值安全回退。

    - 默认保留 4 位小数，然后去掉尾随 0 与小数点
    - 处理 nan/inf/None 返回 "-"
    """
    try:
        val = float(value)
    except (TypeError, ValueError):
        return str(value) if value not in (None, "") else "-"

    if math.isnan(val) or math.isinf(val):
        return "-"

    fmt = f"{val:.{digits}f}"
    fmt = fmt.rstrip("0").rstrip(".")
    if fmt == "-0":  # 避免 -0 展示
        fmt = "0"
    return fmt


__all__ = ["RankingCard", "format_number"]
