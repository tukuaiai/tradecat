"""爆仓排行榜卡片"""

from __future__ import annotations

import re
from typing import Dict


from cards.base import RankingCard


class LiquidationRankingCard(RankingCard):
    """🕷️ 爆仓排行 - 爆仓排行榜"""

    FALLBACK = "card.liquidation.fallback"

    def __init__(self) -> None:
        # 暂时关闭该卡片：移除菜单入口/回调，防止展示
        super().__init__(
            # 设为隐藏状态：不注册按钮，不响应回调
            card_id="__disabled_liquidation__",
            button_text="",
            category="hidden",
            description="",
            default_state={},
            callback_prefixes=[],
            priority=999,
        )

    def handles_callback(self, callback_data: str) -> bool:
        if super().handles_callback(callback_data):
            return True
        return bool(re.fullmatch(r"liquidation_(10|20|30)", callback_data))

    async def handle_callback(self, update, context, services: Dict[str, object]) -> bool:
        # 已禁用，直接返回 False
        return False

    # 其余逻辑已停用


CARD = LiquidationRankingCard()
