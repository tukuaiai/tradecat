"""资金流向排行榜卡片"""

from __future__ import annotations

import asyncio
import re
from typing import Dict, List, Tuple

from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from cards.base import RankingCard
from cards.data_provider import get_ranking_provider, format_symbol
from cards.排行榜服务 import (
    DEFAULT_PERIODS,
    MONEY_FLOW_FUTURES_PERIODS,
    MONEY_FLOW_SPOT_PERIODS,
    normalize_period,
)


class MoneyFlowCard(RankingCard):
    """🌊 资金流向排行 - 资金流向排行榜"""

    FALLBACK = "💰 资金流向数据加载中，请稍后重试..."
    SHOW_MARKET_SWITCH = False  # 当前仅期货，隐藏市场切换行

    def __init__(self) -> None:
        super().__init__(
            card_id="money_flow",
            button_text="🚰 资金流向",
            category="free",
            description="资金净流量榜（Smart Money Flow）",
            default_state={
                "money_flow_limit": 10,
                "money_flow_period": "15m",
                "money_flow_sort": "desc",
                "money_flow_type": "volume",   # 默认按成交额排序
                "money_flow_market": "futures",
                "money_flow_fields": {},
            },
            callback_prefixes=[
                "money_flow",
                "money_flow_",
                "market_",
                "money_flow_market_",
                "money_flow_sort_field_",
                "money_flow_period_",
                "money_flow_period",
                "money_flow_sort_",
                "money_flow_sort",
                "money_flow_limit_",
                "money_flow_limit",
                "field_money_flow_toggle_",
            ],
            priority=5,
        )

        self.provider = get_ranking_provider()

        # 对齐 KDJ：通用四列默认关，价格开；专用列“净流”开，其余关
        self.general_display_fields: List[Tuple[str, str, bool]] = [
            ("quote_volume", "成交额", False),
            ("振幅", "振幅", False),
            ("成交笔数", "成交笔数", False),
            ("主动买卖比", "主动买卖比", False),
            ("price", "价格", True),
        ]
        self.special_display_fields: List[Tuple[str, str, bool]] = [
            ("absolute", "净流", True),
            ("volume", "成交额", False),
            ("inflow", "流入", False),
            ("outflow", "流出", False),
        ]

    def handles_callback(self, callback_data: str) -> bool:
        if super().handles_callback(callback_data):
            return True
        return bool(
            re.fullmatch(r"(market|sort_field|period|sort|limit)_[\\w]+", callback_data)
        )

    async def handle_callback(self, update, context, services: Dict[str, object]) -> bool:
        query = update.callback_query
        if not query:
            return False

        user_handler = services.get("user_handler")
        ensure_valid_text = services.get("ensure_valid_text")
        if user_handler is None:
            return False

        data = query.data or ""

        if data in {self.card_id, "money_flow_refresh"}:
            await self._reply(query, user_handler, ensure_valid_text)
            return True

        if data.startswith("money_flow_market_") or data.startswith("market_"):
            market = data.replace("money_flow_market_", "").replace("market_", "")
            user_handler.user_states['money_flow_market'] = market
            await self._edit(query, user_handler, ensure_valid_text)
            return True

        if data.startswith("money_flow_sort_field_"):
            flow_type = data.replace("money_flow_sort_field_", "")
            user_handler.user_states['money_flow_type'] = flow_type
            await self._edit(query, user_handler, ensure_valid_text)
            return True

        if data.startswith("money_flow_period_") or data.startswith("money_flow_period"):
            period = data.replace("money_flow_period_", "").replace("money_flow_period", "")
            allowed = MONEY_FLOW_SPOT_PERIODS if user_handler.user_states.get("money_flow_market", "futures") == "spot" else MONEY_FLOW_FUTURES_PERIODS
            user_handler.user_states['money_flow_period'] = normalize_period(period, allowed, default="15m")
            await self._edit(query, user_handler, ensure_valid_text)
            return True

        if data.startswith("money_flow_sort_") or data.startswith("money_flow_sort"):
            sort_order = data.replace("money_flow_sort_", "").replace("money_flow_sort", "")
            user_handler.user_states['money_flow_sort'] = sort_order
            await self._edit(query, user_handler, ensure_valid_text)
            return True

        if data.startswith("money_flow_limit_") or data.startswith("money_flow_limit"):
            limit_val = data.replace("money_flow_limit_", "").replace("money_flow_limit", "")
            if limit_val.isdigit():
                user_handler.user_states['money_flow_limit'] = int(limit_val)
                await self._edit(query, user_handler, ensure_valid_text)
                return True
        if data.startswith("field_money_flow_toggle_"):
            col = data.replace("field_money_flow_toggle_", "")
            fields_state = self._ensure_field_state(user_handler)
            if col in fields_state and not self._is_core(col):
                fields_state[col] = not fields_state[col]
                user_handler.user_states["money_flow_fields"] = fields_state
            await self._edit(query, user_handler, ensure_valid_text)
            return True

        return False

    async def _reply(self, query, user_handler, ensure_valid_text) -> None:
        text, keyboard = await self._build_payload(user_handler, ensure_valid_text)
        await query.message.reply_text(text, reply_markup=keyboard, parse_mode='Markdown')

    async def _edit(self, query, user_handler, ensure_valid_text) -> None:
        text, keyboard = await self._build_payload(user_handler, ensure_valid_text)
        await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')

    async def _build_payload(self, user_handler, ensure_valid_text) -> Tuple[str, object]:
        loop = asyncio.get_event_loop()
        limit = user_handler.user_states.get('money_flow_limit', 10)
        period = user_handler.user_states.get('money_flow_period', '15m')
        sort_order = user_handler.user_states.get('money_flow_sort', 'desc')
        flow_type = user_handler.user_states.get('money_flow_type', 'absolute')
        market = user_handler.user_states.get('money_flow_market', 'futures')
        fields_state = self._ensure_field_state(user_handler)

        # 调试：检查字段状态
        print(f"[DEBUG] money_flow_fields state: {fields_state}")
        print(f"[DEBUG] user_handler.user_states: {user_handler.user_states}")

        allowed = MONEY_FLOW_SPOT_PERIODS if market == "spot" else MONEY_FLOW_FUTURES_PERIODS
        period = normalize_period(period, allowed, default="15m")
        user_handler.user_states['money_flow_period'] = period

        rows, header = await loop.run_in_executor(
            None,
            self._load_rows,
            user_handler,
            limit,
            period,
            sort_order,
            flow_type,
            market,
            fields_state,
        )

        aligned = user_handler.dynamic_align_format(rows) if rows else "暂无数据"
        time_info = user_handler.get_current_time_display()
        sort_symbol = "🔽" if sort_order == "desc" else "🔼"
        display_sort_field = flow_type.replace("_", "\\_")
        text = (
            f"💧 资金流向数据\n"
            f"⏰ 更新 {time_info['full']}\n"
            f"📊 排序 {period} {display_sort_field}({sort_symbol})\n"
            f"{header}\n"
            f"```\n{aligned}\n```\n"
            f"💡 净流=流入-流出；可切换净流/成交额/流入/流出/价格等维度\n"
            f"⏰ 最后更新 {time_info['full']}"
        )

        if callable(ensure_valid_text):
            text = ensure_valid_text(text, self.FALLBACK)

        keyboard = self._build_keyboard(user_handler)

        return text, keyboard

    def _build_keyboard(self, handler):
        fields_state = self._ensure_field_state(handler)
        period = handler.user_states.get("money_flow_period", "15m")
        sort_order = handler.user_states.get("money_flow_sort", "desc")
        current_limit = handler.user_states.get("money_flow_limit", 10)
        flow_type = handler.user_states.get("money_flow_type", "absolute")
        market = handler.user_states.get("money_flow_market", "futures")

        def b(label: str, data: str, active: bool = False, disabled: bool = False):
            if disabled:
                return InlineKeyboardButton(label, callback_data="money_flow_nop")
            return InlineKeyboardButton(f"✅{label}" if active else label, callback_data=data)

        kb: List[List[InlineKeyboardButton]] = []

        if self.SHOW_MARKET_SWITCH:
            kb.append([
                b("现货", "money_flow_market_spot", active=market == "spot"),
                b("期货", "money_flow_market_futures", active=market == "futures"),
            ])

        gen_row: List[InlineKeyboardButton] = []
        for col_id, label, is_core in self.general_display_fields:
            state_on = fields_state.get(col_id, True if is_core else False)
            show_label = label if state_on or is_core else f"❎{label}"
            gen_row.append(
                InlineKeyboardButton(
                    show_label,
                    callback_data=f"field_money_flow_toggle_{col_id}",
                )
            )
        kb.append(gen_row)

        spec_row: List[InlineKeyboardButton] = []
        for col_id, label, is_core in self.special_display_fields:
            state_on = fields_state.get(col_id, True if is_core else False)
            show_label = label if state_on or is_core else f"❎{label}"
            spec_row.append(
                InlineKeyboardButton(
                    show_label,
                    callback_data=f"field_money_flow_toggle_{col_id}",
                )
            )
        kb.append(spec_row)

        # 通用排序行需与通用字段开关保持一致
        general_sort = [(cid, lab) for cid, lab, _ in self.general_display_fields]
        kb.append([
            b(lbl, f"money_flow_sort_field_{fid}", active=(flow_type == fid))
            for fid, lbl in general_sort
        ])

        special_sort = [("absolute", "净流"), ("volume", "成交额"), ("inflow", "流入"), ("outflow", "流出")]
        kb.append([
            b(lbl, f"money_flow_sort_field_{fid}", active=(flow_type == fid))
            for fid, lbl in special_sort
        ])

        kb.append([b(p, f"money_flow_period_{p}", active=p == period) for p in DEFAULT_PERIODS])

        kb.append([
            b("降序", "money_flow_sort_desc", active=sort_order == "desc"),
            b("升序", "money_flow_sort_asc", active=sort_order == "asc"),
            b("10条", "money_flow_limit_10", active=current_limit == 10),
            b("20条", "money_flow_limit_20", active=current_limit == 20),
            b("30条", "money_flow_limit_30", active=current_limit == 30),
        ])

        kb.append([
            InlineKeyboardButton("🏠主菜单", callback_data="ranking_menu"),
            InlineKeyboardButton("🔄刷新", callback_data="money_flow_refresh"),
        ])

        return InlineKeyboardMarkup(kb)

    # ---------- 数据与字段状态 ----------
    def _load_rows(
        self,
        handler,
        limit: int,
        period: str,
        sort_order: str,
        flow_type: str,
        market: str,
        field_state: Dict[str, bool],
    ) -> Tuple[List[List[str]], str]:
        allowed = MONEY_FLOW_SPOT_PERIODS if market == "spot" else MONEY_FLOW_FUTURES_PERIODS
        period = normalize_period(period, allowed, default="15m")
        handler.user_states["money_flow_period"] = period

        items: List[Dict] = []

        # 从基础数据表读取
        try:
            base_map = self.provider.fetch_base(period)
            for sym, r in base_map.items():
                items.append({
                    "symbol": format_symbol(sym),
                    "absolute": float(r.get("资金流向") or 0),
                    "volume": float(r.get("成交额") or 0),
                    "inflow": float(r.get("主动买额") or 0),
                    "outflow": float(r.get("主动卖出额") or 0),
                    "成交笔数": float(r.get("成交笔数") or r.get("交易次数") or 0),
                    "price": float(r.get("当前价格") or 0),
                    "quote_volume": float(r.get("成交额") or 0),
                })
        except Exception:
            pass

        reverse = sort_order != "asc"
        items.sort(key=lambda x: x.get(flow_type, 0), reverse=reverse)

        active_special = [f for f in self.special_display_fields if field_state.get(f[0], True)]
        active_general = [f for f in self.general_display_fields if field_state.get(f[0], True)]

        header_parts = ["排名", "币种"] + [lab for _, lab, _ in active_special] + [lab for _, lab, _ in active_general]

        rows: List[List[str]] = []
        for idx, item in enumerate(items[:limit], 1):
            row: List[str] = [f"{idx}", item["symbol"]]
            for col_id, _, _ in active_special:
                val = item.get(col_id)
                if col_id in {"absolute", "volume", "inflow", "outflow"}:
                    row.append(self._format_volume(val))
                else:
                    row.append(str(val) if val not in (None, "") else "-")
            for col_id, _, _ in active_general:
                val = item.get(col_id)
                if col_id == "quote_volume":
                    row.append(self._format_volume(val))
                elif col_id == "price":
                    row.append(f"{val:.4f}" if val else "-")
                else:
                    row.append(str(val) if val not in (None, "") else "-")
            rows.append(row)
        return rows, "/".join(header_parts)

    def _ensure_field_state(self, handler) -> Dict[str, bool]:
        state = handler.user_states.get("money_flow_fields")
        desired_keys = {c for c, _, _ in self.general_display_fields + self.special_display_fields}
        need_reset = state is None or set(state.keys()) != desired_keys
        if need_reset:
            state = {c: False for c in desired_keys}
            # 默认开启：仅净流 + 价格
            for k in ("absolute", "price"):
                if k in state:
                    state[k] = True
            handler.user_states["money_flow_fields"] = state

        return state

    def _is_core(self, col_id: str) -> bool:
        for cid, _, is_core in self.general_display_fields + self.special_display_fields:
            if cid == col_id:
                return is_core
        return False

    @staticmethod
    def _format_volume(value: float) -> str:
        if value is None:
            return "-"
        sign = "+" if value > 0 else "-" if value < 0 else ""
        v = abs(value)
        if v >= 1e9:
            return f"{sign}{v/1e9:.2f}B"
        if v >= 1e6:
            return f"{sign}{v/1e6:.2f}M"
        if v >= 1e3:
            return f"{sign}{v/1e3:.2f}K"
        return f"{sign}{v:.2f}"


CARD = MoneyFlowCard()
