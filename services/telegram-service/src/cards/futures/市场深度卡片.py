"""市场深度卡片"""

from __future__ import annotations

import asyncio
import re
from typing import Dict, List, Tuple

from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from cards.base import RankingCard
from cards.data_provider import format_symbol
from cards.i18n import btn_auto as _btn_auto, gettext as _t, resolve_lang, format_sort_field, translate_field
from cards.排行榜服务 import DEFAULT_PERIODS, get_market_depth_service, normalize_period


class MarketDepthCard(RankingCard):
    """🔬 市场深度排行 - 市场深度排行榜"""

    FALLBACK = "card.depth.fallback"

    def __init__(self) -> None:
        super().__init__(
            card_id="market_depth",
            button_text="🧊 市场深度",
            button_key="card.depth.btn",
            category="free",
            description="市场深度与买卖盘分析",
            default_state={
                "market_depth_limit": 10,
                "market_depth_sort_type": "ratio",
                "market_depth_sort": "desc",
                "market_depth_period": "15m",
                "market_depth_fields": {},
                "market_depth_market": "futures",
            },
            callback_prefixes=[
                "market_depth",
                "market_depth_",
                "market_depth_sort_field_",
                "market_depth_sort_",
                "market_depth_limit_",
                "market_depth_period_",
                "market_depth_market_",
                "field_md_toggle_",
                "md_",  # 兼容缩写
            ],
            priority=6,
        )

        self.general_display_fields: list[tuple[str, str, bool]] = [
            ("quote_volume", "成交额", False),
            ("振幅", "振幅", False),
            ("成交笔数", "成交笔数", False),
            ("主动买卖比", "主动买卖比", False),
            ("price", "价格", False),
        ]
        self.special_display_fields: list[tuple[str, str, bool]] = [
            ("ratio", "深度比", False),
            ("bid_wall", "买墙", False),
            ("ask_wall", "卖墙", False),
            ("spread", "价差", False),
        ]

    def handles_callback(self, callback_data: str) -> bool:
        if super().handles_callback(callback_data):
            return True
        return bool(re.fullmatch(r"market_depth_(10|20|30)", callback_data))

    async def handle_callback(self, update, context, services: Dict[str, object]) -> bool:
        query = update.callback_query
        if not query:
            return False

        user_handler = services.get("user_handler")
        ensure_valid_text = services.get("ensure_valid_text")
        if user_handler is None:
            return False

        data = query.data or ""

        if data in {self.card_id, "market_depth_refresh"}:
            await self._reply(query, user_handler, ensure_valid_text)
            return True

        if data == "md_nop":
            return True
        if data.startswith("market_depth_market_"):
            user_handler.user_states['market_depth_market'] = data.replace("market_depth_market_", "")
            await self._edit(query, user_handler, ensure_valid_text)
            return True
        if data.startswith("market_depth_sort_field_"):
            sort_type = data.replace("market_depth_sort_field_", "")
            user_handler.user_states['market_depth_sort_type'] = sort_type
            await self._edit(query, user_handler, ensure_valid_text)
            return True

        if data.startswith("market_depth_sort_"):
            sort_order = data.replace("market_depth_sort_", "")
            user_handler.user_states['market_depth_sort'] = sort_order
            await self._edit(query, user_handler, ensure_valid_text)
            return True

        if data.startswith("market_depth_period_"):
            period = data.replace("market_depth_period_", "")
            user_handler.user_states['market_depth_period'] = normalize_period(period, DEFAULT_PERIODS, default="15m")
            await self._edit(query, user_handler, ensure_valid_text)
            return True

        if data.startswith("market_depth_limit_"):
            limit_val = data.replace("market_depth_limit_", "")
            if limit_val.isdigit():
                user_handler.user_states['market_depth_limit'] = int(limit_val)
                await self._edit(query, user_handler, ensure_valid_text)
                return True

        if data.startswith("field_md_toggle_"):
            col = data.replace("field_md_toggle_", "")
            fields_state = self._ensure_field_state(user_handler)
            if col in fields_state:
                fields_state[col] = not fields_state[col]
                user_handler.user_states["market_depth_fields"] = fields_state
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
        limit = user_handler.user_states.get('market_depth_limit', 10)
        sort_type = user_handler.user_states.get('market_depth_sort_type', 'ratio')
        sort_order = user_handler.user_states.get('market_depth_sort', 'desc')
        period = user_handler.user_states.get('market_depth_period', '1h')
        period = normalize_period(period, DEFAULT_PERIODS, default="15m")
        user_handler.user_states['market_depth_period'] = period
        fields_state = self._ensure_field_state(user_handler)

        service = get_market_depth_service(user_handler)
        rows, header = await loop.run_in_executor(
            None,
            self._load_rows,
            service,
            limit,
            sort_type,
            sort_order,
            period,
            fields_state,
        )

        aligned = user_handler.dynamic_align_format(rows) if rows else _t("data.no_data", lang=lang)
        time_info = user_handler.get_current_time_display()
        sort_symbol = "🔽" if sort_order == "desc" else "🔼"
        text = (
            f"{_t('card.depth.title', lang=lang)}\n"
            f"{_t('card.common.update_time', lang=lang).format(time=time_info['full'])}\n"
            f"{_t('card.common.sort_info', lang=lang).format(period=period, field=format_sort_field(sort_type, lang=lang, field_lists=[self.general_display_fields, self.special_display_fields]), symbol=sort_symbol)}\n"
            f"{header}\n"
            f"```\n{aligned}\n```\n"
            f"{_t('card.depth.hint', lang=lang)}\n"
            f"{_t('card.common.last_update', lang=lang).format(time=time_info['full'])}"
        )

        if callable(ensure_valid_text):
            text = ensure_valid_text(text, self.FALLBACK)

        keyboard = self._build_keyboard(user_handler, fields_state)

        return text, keyboard

    def _build_keyboard(self, h, fields_state: Dict[str, bool]):
        sort_order = h.user_states.get('market_depth_sort', 'desc')
        sort_type = h.user_states.get('market_depth_sort_type', 'ratio')
        current_limit = h.user_states.get('market_depth_limit', 10)
        period = h.user_states.get('market_depth_period', '15m')

        def b(label: str, data: str, active: bool = False, disabled: bool = False):

            if disabled:

                return InlineKeyboardButton(label, callback_data=data or 'nop')

            return _btn_auto(None, label, data, active=active)


        kb: list[list[InlineKeyboardButton]] = []
        # 行1 市场省略（仅期货）

        # 行2 通用字段开关
        gen_row = []
        for col_id, label, is_core in self.general_display_fields:
            state_on = fields_state.get(col_id, is_core or False)
            show_label = label if state_on or is_core else f"❎{label}"
            gen_row.append(InlineKeyboardButton(show_label, callback_data=f"field_md_toggle_{col_id}"))
        kb.append(gen_row)

        # 行3 专用字段开关
        spec_row = []
        for col_id, label, is_core in self.special_display_fields:
            state_on = fields_state.get(col_id, is_core or False)
            show_label = label if state_on or is_core else f"❎{label}"
            spec_row.append(InlineKeyboardButton(show_label, callback_data=f"field_md_toggle_{col_id}"))
        kb.append(spec_row)

        # 行4 通用排序
        general_sort = [(cid, lab) for cid, lab, _ in self.general_display_fields]
        kb.append([b(lbl, f"market_depth_sort_field_{cid}", active=(sort_type == cid)) for cid, lbl in general_sort])

        # 行5 专用排序
        special_sort = [(cid, lab) for cid, lab, _ in self.special_display_fields]
        kb.append([b(lbl, f"market_depth_sort_field_{cid}", active=(sort_type == cid)) for cid, lbl in special_sort])

        # 行6 周期
        kb.append([b(p, f"market_depth_period_{p}", active=p == period) for p in DEFAULT_PERIODS])

        # 行7 排序方向 + 条数
        kb.append([
            b("降序", "market_depth_sort_desc", active=sort_order == "desc"),
            b("升序", "market_depth_sort_asc", active=sort_order == "asc"),
            b("10条", "market_depth_limit_10", active=current_limit == 10),
            b("20条", "market_depth_limit_20", active=current_limit == 20),
            b("30条", "market_depth_limit_30", active=current_limit == 30),
        ])

        # 行8 主控
        kb.append([
            _btn_auto(None, "🏠主菜单", "ranking_menu"),
            _btn_auto(None, "🔄刷新", "market_depth_refresh"),
        ])

        return InlineKeyboardMarkup(kb)

    def _load_rows(
        self,
        service,
        limit: int,
        sort_type: str,
        sort_order: str,
        period: str,
        fields_state: Dict[str, bool],
        lang: str | None = None,
    ) -> Tuple[List[List[str]], str]:
        raw_rows = service.render_rows(limit, sort_type, sort_order, period)
        if not raw_rows:
            return [], _t("card.header.rank_symbol", lang=lang)

        items = []
        for r in raw_rows:
            if len(r) < 6:
                continue
            items.append({
                "symbol": r[1],
                "ratio": float(r[2]) if r[2] not in (None, "") else 0,
                "bid_wall": float(r[3]) if r[3] not in (None, "") else 0,
                "ask_wall": float(r[4]) if r[4] not in (None, "") else 0,
                "spread": float(r[5]) if r[5] not in (None, "") else 0,
                "quote_volume": 0,
                "振幅": 0,
                "成交笔数": 0,
                "主动买卖比": 0,
                "price": 0,
            })

        reverse = sort_order != "asc"
        items.sort(key=lambda x: x.get(sort_type, 0), reverse=reverse)
        active_special = [f for f in self.special_display_fields if fields_state.get(f[0], f[2] or False)]
        active_general = [f for f in self.general_display_fields if fields_state.get(f[0], f[2] or False)]
        header_parts = [_t("card.header.rank", lang=lang), _t("card.header.symbol", lang=lang)] + [translate_field(lab, lang=lang) for _, lab, _ in active_special] + [translate_field(lab, lang=lang) for _, lab, _ in active_general]

        out_rows: list[list[str]] = []
        for idx, item in enumerate(items[:limit], 1):
            display_symbol = format_symbol(item["symbol"])
            row = [f"{idx}", display_symbol]
            for col_id, _, _ in active_special:
                val = item.get(col_id)
                row.append(f"{val:.2f}" if isinstance(val, (int, float)) else "-")
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
            out_rows.append(row)

        return out_rows, "/".join(header_parts)

    # ---------- 工具 ----------
    def _get_all_fields(self) -> List[Tuple[str, str, bool]]:
        return [
            ("ratio", "深度比", False),
            ("bid_wall", "买墙", False),
            ("ask_wall", "卖墙", False),
            ("spread", "价差", False),
        ]

    def _filter_columns(self, rows: List[List[str]], active_cols: List[str]) -> List[List[str]]:
        # rows 格式：[[rank, symbol, ratio, bid, ask, spread], ...]
        # 需按 active_cols 筛列，并保留前两列
        col_order = ["ratio", "bid_wall", "ask_wall", "spread"]
        keep_indices = [0, 1] + [2 + col_order.index(c) for c in col_order if c in active_cols]
        return [[row[i] for i in keep_indices if i < len(row)] for row in rows]

    def _build_header(self, header: str, active_cols: List[str]) -> str:
        base = ["排名", "币种"]
        mapping = {cid: label for cid, label, _ in self._get_all_fields()}
        base += [mapping[c] for c in ["ratio", "bid_wall", "ask_wall", "spread"] if c in active_cols]
        return "/".join(base)

    def _ensure_field_state(self, h) -> Dict[str, bool]:
        state = h.user_states.get("market_depth_fields") or {}
        if not state:
            for col, _, is_core in self.general_display_fields + self.special_display_fields:
                if col in {"price", "ratio"}:
                    state[col] = True
                else:
                    state[col] = True if is_core else False
            h.user_states["market_depth_fields"] = state

        for _off in {"quote_volume", "振幅", "成交笔数", "主动买卖比"}:
            if _off in state:
                state[_off] = False

        return state


CARD = MarketDepthCard()
