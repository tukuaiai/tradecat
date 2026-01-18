"""资金费率排行榜卡片"""

from __future__ import annotations

import asyncio
import re
from typing import Dict, Tuple

from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from cards.base import RankingCard
from cards.i18n import btn_auto as _btn_auto, gettext as _t, format_sort_field, resolve_lang, translate_field
from cards.排行榜服务 import DEFAULT_PERIODS, get_funding_service, normalize_period


class FundingRateCard(RankingCard):
    """🎯 资金费率排行 - 资金费率排行榜"""

    FALLBACK = "card.funding.fallback"

    def __init__(self) -> None:
        super().__init__(
            card_id="funding_rate",
            button_text="💱 资金费率",
            button_key="card.funding_rate.btn",
            category="free",
            description="资金费率/权重排行榜",
            default_state={
                "funding_limit": 10,
                "funding_sort": "desc",
                "funding_sort_type": "funding_rate",
                "funding_period": "15m",
                "funding_market": "futures",
                "funding_fields": {},
            },
            callback_prefixes=[
                "funding_rate",
                "funding_",
                "funding_sort_field_",
                "funding_sort_",
                "funding_limit_",
                "funding_period_",
                "funding_market_",
                "field_funding_toggle_",
            ],
            priority=3,
        )

        # 通用/专用字段定义
        self.general_display_fields = [
            ("quote_volume", "成交额", False),
            ("振幅", "振幅", False),
            ("成交笔数", "成交笔数", False),
            ("主动买卖比", "主动买卖比", False),
            ("price", "价格", False),
        ]
        self.special_display_fields = [
            ("funding_rate", "资金费率", False),
            ("weighted_rate", "加权费率", False),
        ]

    def handles_callback(self, callback_data: str) -> bool:
        if super().handles_callback(callback_data):
            return True
        return bool(re.fullmatch(r"funding_(10|20|30)", callback_data))

    async def handle_callback(self, update, context, services: Dict[str, object]) -> bool:
        query = update.callback_query
        if not query:
            return False

        user_handler = services.get("user_handler")
        ensure_valid_text = services.get("ensure_valid_text")
        if user_handler is None:
            return False

        data = query.data or ""

        if data in {self.card_id, "funding_rate_refresh"}:
            await self._reply(query, user_handler, ensure_valid_text)
            return True

        if data == "funding_nop":
            return True
        if data.startswith("funding_market_"):
            user_handler.user_states["funding_market"] = data.replace("funding_market_", "")
            await self._edit(query, user_handler, ensure_valid_text)
            return True
        if data.startswith("funding_sort_"):
            sort_order = data.replace("funding_sort_", "")
            user_handler.user_states['funding_sort'] = sort_order
            await self._edit(query, user_handler, ensure_valid_text)
            return True

        if data.startswith("funding_sort_field_"):
            sort_type = data.replace("funding_sort_field_", "")
            user_handler.user_states['funding_sort_type'] = sort_type
            await self._edit(query, user_handler, ensure_valid_text)
            return True

        if data.startswith("funding_period_"):
            period = data.replace("funding_period_", "")
            user_handler.user_states['funding_period'] = normalize_period(period, DEFAULT_PERIODS, default="15m")
            await self._edit(query, user_handler, ensure_valid_text)
            return True

        if data.startswith("funding_limit_"):
            limit_val = data.replace("funding_limit_", "")
            if limit_val.isdigit():
                user_handler.user_states['funding_limit'] = int(limit_val)
                await self._edit(query, user_handler, ensure_valid_text)
                return True

        if data.startswith("field_funding_toggle_"):
            col = data.replace("field_funding_toggle_", "")
            fields_state = self._ensure_field_state(user_handler)
            if col in fields_state:
                fields_state[col] = not fields_state[col]
                user_handler.user_states["funding_fields"] = fields_state
            await self._edit(query, user_handler, ensure_valid_text)
            return True

        return False

    async def _reply(self, query, user_handler, ensure_valid_text) -> None:
        text, keyboard = await self._build_payload(user_handler, ensure_valid_text)
        await query.message.reply_text(text, reply_markup=keyboard, parse_mode='Markdown')

    async def _edit(self, query, user_handler, ensure_valid_text) -> None:
        text, keyboard = await self._build_payload(user_handler, ensure_valid_text)
        await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')

    async def _build_payload(self, user_handler, ensure_valid_text, lang=None, query=None) -> Tuple[str, object]:
        if lang is None and query is not None:
            lang = resolve_lang(query)
        loop = asyncio.get_event_loop()
        limit = user_handler.user_states.get('funding_limit', 10)
        sort_order = user_handler.user_states.get('funding_sort', 'desc')
        sort_type = user_handler.user_states.get('funding_sort_type', 'funding_rate')
        period = user_handler.user_states.get('funding_period', '1h')
        period = normalize_period(period, DEFAULT_PERIODS, default="15m")
        user_handler.user_states['funding_period'] = period
        fields_state = self._ensure_field_state(user_handler)

        service = get_funding_service(user_handler)
        rows, header = await loop.run_in_executor(
            None, self._load_rows, service, limit, sort_order, sort_type, period, fields_state
        )
        aligned = user_handler.dynamic_align_format(rows) if rows else _t("data.no_data", lang=lang)
        time_info = user_handler.get_current_time_display()
        sort_symbol = "🔽" if sort_order == "desc" else "🔼"
        text = (
            f"{_t('card.funding.title', lang=lang)}\n"
            f"{_t('card.common.update_time', lang=lang).format(time=time_info['full'])}\n"
            f"{_t('card.common.sort_info', lang=lang).format(period=period, field=format_sort_field(sort_type, lang=lang, field_lists=[self.general_display_fields, self.special_display_fields]), symbol=sort_symbol)}\n"
            f"{header}\n"
            f"```\n{aligned}\n```\n"
            f"{_t('card.funding.hint', lang=lang)}\n"
            f"{_t('card.common.last_update', lang=lang).format(time=time_info['full'])}"
        )
        if callable(ensure_valid_text):
            text = ensure_valid_text(text, _t(self.FALLBACK))
        keyboard = self._build_keyboard(user_handler, fields_state)
        return text, keyboard

    def _build_keyboard(self, h, fields_state: Dict[str, bool]):
        sort_order = h.user_states.get('funding_sort', 'desc')
        current_limit = h.user_states.get('funding_limit', 10)
        sort_type = h.user_states.get('funding_sort_type', 'funding_rate')
        h.user_states.get('funding_period', '1d')

        def b(label: str, data: str, active: bool = False, disabled: bool = False):

            if disabled:

                return InlineKeyboardButton(label, callback_data=data or 'nop')

            return _btn_auto(None, label, data, active=active)


        kb: list[list[InlineKeyboardButton]] = []
        # 行1 市场省略
        # 行2 通用字段开关
        gen_row = []
        for col_id, label, is_core in self.general_display_fields:
            state_on = fields_state.get(col_id, is_core or False)
            show_label = label if state_on or is_core else f"❎{label}"
            gen_row.append(InlineKeyboardButton(show_label, callback_data=f"field_funding_toggle_{col_id}"))
        kb.append(gen_row)
        # 行3 专用字段开关
        spec_row = []
        for col_id, label, is_core in self.special_display_fields:
            state_on = fields_state.get(col_id, is_core or False)
            show_label = label if state_on or is_core else f"❎{label}"
            spec_row.append(InlineKeyboardButton(show_label, callback_data=f"field_funding_toggle_{col_id}"))
        kb.append(spec_row)
        # 行4 通用排序
        general_sort = [(cid, lab) for cid, lab, _ in self.general_display_fields]
        kb.append([b(lbl, f"funding_sort_field_{cid}", active=(sort_type == cid)) for cid, lbl in general_sort])
        # 行5 专用排序
        special_sort = [(cid, lab) for cid, lab, _ in self.special_display_fields]
        kb.append([b(lbl, f"funding_sort_field_{cid}", active=(sort_type == cid)) for cid, lbl in special_sort])
        # 行6 周期（固定1d）
        period_label = _t("period.1d")
        kb.append([InlineKeyboardButton(f"✅{period_label}", callback_data="funding_nop")])
        # 行7 排序方向 + 条数
        kb.append([
            b("降序", "funding_sort_desc", active=sort_order == "desc"),
            b("升序", "funding_sort_asc", active=sort_order == "asc"),
            b("10条", "funding_limit_10", active=current_limit == 10),
            b("20条", "funding_limit_20", active=current_limit == 20),
            b("30条", "funding_limit_30", active=current_limit == 30),
        ])
        # 行8 主控
        kb.append([
            _btn_auto(None, "🏠主菜单", "ranking_menu"),
            _btn_auto(None, "🔄刷新", "funding_rate_refresh"),
        ])
        return InlineKeyboardMarkup(kb)

    # ---------- 工具 ----------
    def _ensure_field_state(self, h) -> Dict[str, bool]:
        state = h.user_states.get("funding_fields") or {}
        if not state:
            for col, _, is_core in self.general_display_fields + self.special_display_fields:
                if col in {"price", "funding_rate"}:
                    state[col] = True
                else:
                    state[col] = True if is_core else False
            h.user_states["funding_fields"] = state
        for _off in {"quote_volume", "振幅", "成交笔数", "主动买卖比"}:
            if _off in state:
                state[_off] = False
        return state

    def _load_rows(self, service, limit: int, sort_order: str, sort_type: str, period: str, field_state: Dict[str, bool], lang: str | None = None):
        data = service.handler.get_funding_rate_ranking(limit=limit, sort_order=sort_order, sort_type=sort_type)
        if isinstance(data, str):
            return [], _t("card.header.rank_symbol", lang=lang)
        items = []
        for r in data or []:
            sym = (r.get("symbol") or "").replace("USDT", "").upper()
            items.append({
                "symbol": sym,
                "funding_rate": float(r.get("funding_rate") or r.get("lastFundingRate") or 0) * 100,
                "weighted_rate": float(r.get("avg_funding_rate_by_vol") or r.get("avg_funding_rate_by_oi") or 0),
                "quote_volume": float(r.get("quote_volume") or 0),
                "price": float(r.get("price") or r.get("last_price") or 0),
                "振幅": float(r.get("振幅") or 0),
                "成交笔数": float(r.get("成交笔数") or r.get("交易次数") or 0),
                "主动买卖比": float(r.get("主动买卖比") or 0),
            })
        reverse = sort_order != "asc"
        items.sort(key=lambda x: x.get(sort_type, 0), reverse=reverse)
        active_special = [f for f in self.special_display_fields if field_state.get(f[0], f[2] or False)]
        active_general = [f for f in self.general_display_fields if field_state.get(f[0], f[2] or False)]
        header_parts = [_t("card.header.rank", lang=lang), _t("card.header.symbol", lang=lang)] + [translate_field(lab, lang=lang) for _, lab, _ in active_special] + [translate_field(lab, lang=lang) for _, lab, _ in active_general]
        rows: list[list[str]] = []
        for idx, item in enumerate(items[:limit], 1):
            row = [f"{idx}", item["symbol"]]
            for col_id, _, _ in active_special:
                val = item.get(col_id)
                row.append(f"{val:.4f}%" if isinstance(val, (int, float)) else "-")
            for col_id, _, _ in active_general:
                val = item.get(col_id)
                if col_id == "quote_volume":
                    row.append(self._format_volume(val))
                elif col_id == "振幅":
                    pct = (val * 100) if isinstance(val, (int, float)) and val <= 5 else val
                    row.append(f"{pct:.2f}%" if isinstance(pct, (int, float)) else "-")
                elif col_id == "成交笔数":
                    row.append(f"{val:.2f}" if isinstance(val, (int, float)) else (str(val) if val not in (None, "") else "-"))
                elif col_id == "主动买卖比":
                    row.append(f"{val*100:.2f}%" if isinstance(val, (int, float)) else "-")
                elif col_id == "price":
                    row.append(f"{val:.4f}" if val else "-")
                else:
                    row.append(str(val) if val not in (None, "") else "-")
            rows.append(row)
        return rows, "/".join(header_parts)


CARD = FundingRateCard()
