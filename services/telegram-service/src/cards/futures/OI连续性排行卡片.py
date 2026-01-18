"""期货情绪聚合：OI 连续性榜

核心字段：OI连续根数（正=连涨，负=连跌）。
"""

from __future__ import annotations

import logging
from typing import Dict, List, Tuple

from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from cards.base import RankingCard
from cards.data_provider import get_ranking_provider, format_symbol
from cards.i18n import btn_auto as _btn_auto, gettext as _t, resolve_lang, translate_field, format_sort_field


class FuturesOIStreakCard(RankingCard):
    """📈 OI连续性榜"""

    FALLBACK = "card.oi_streak.fallback"
    provider = get_ranking_provider()
    SHOW_MARKET_SWITCH = False
    DEFAULT_MARKET = "futures"

    def __init__(self) -> None:
        super().__init__(
            card_id="futures_oi_streak",
            button_text="📈 OI连续",
            button_key="card.oi_continuous.btn",
            category="free",
            description="OI 连涨/连跌根数排行榜，基于期货情绪聚合表",
            default_state={
                "streak_period": "15m",
                "streak_sort": "desc",
                "streak_limit": 10,
                "streak_sort_field": "oi_streak",
                "streak_market": self.DEFAULT_MARKET,
                "streak_fields": {},
            },
            callback_prefixes=[
                "futures_oi_streak",
                "streak_period_",
                "streak_sort_",
                "streak_limit_",
                "streak_sort_field_",
                "streak_market_",
                "field_streak_toggle_",
            ],
            priority=29,
        )
        self._logger = logging.getLogger(__name__)

        self.general_display_fields: List[Tuple[str, str, bool]] = [
            ("quote_volume", "成交额", False),
            ("振幅", "振幅", False),
            ("成交笔数", "成交笔数", False),
            ("主动买卖比", "主动买卖比", False),
            ("price", "价格", False),
        ]

        self.special_display_fields: List[Tuple[str, str, bool]] = [
            ("oi_streak", "OI连续根数", False),
        ]

    async def handle_callback(self, update, context, services: Dict[str, object]) -> bool:
        query = update.callback_query
        if not query:
            return False
        h = services.get("user_handler")
        ensure = services.get("ensure_valid_text")
        if h is None:
            return False

        data = query.data or ""
        if data in (self.card_id, self.entry_callback, "futures_oi_streak_refresh"):
            await self._reply(query, h, ensure)
            return True
        if data == "streak_nop":
            return True

        if data.startswith("streak_sort_field_"):
            h.user_states["streak_sort_field"] = data.replace("streak_sort_field_", "")
            await self._edit(query, h, ensure)
            return True
        if data.startswith("streak_market_"):
            h.user_states["streak_market"] = data.replace("streak_market_", "")
            await self._edit(query, h, ensure)
            return True
        if data.startswith("streak_period_"):
            h.user_states["streak_period"] = data.replace("streak_period_", "")
            await self._edit(query, h, ensure)
            return True
        if data.startswith("streak_sort_"):
            h.user_states["streak_sort"] = data.replace("streak_sort_", "")
            await self._edit(query, h, ensure)
            return True
        if data.startswith("streak_limit_"):
            val = data.replace("streak_limit_", "")
            if val.isdigit():
                h.user_states["streak_limit"] = int(val)
                await self._edit(query, h, ensure)
                return True
            return False
        if data.startswith("field_streak_toggle_"):
            col = data.replace("field_streak_toggle_", "")
            fields_state = self._ensure_field_state(h)
            if col in fields_state:
                fields_state[col] = not fields_state[col]
                h.user_states["streak_fields"] = fields_state
            await self._edit(query, h, ensure)
            return True
        return False

    async def _reply(self, query, h, ensure):
        lang = resolve_lang(query)
        text, kb = await self._build_payload(h, ensure, lang, query)
        await query.message.reply_text(text, reply_markup=kb, parse_mode="Markdown")

    async def _edit(self, query, h, ensure):
        lang = resolve_lang(query)
        text, kb = await self._build_payload(h, ensure, lang, query)
        await query.edit_message_text(text, reply_markup=kb, parse_mode="Markdown")

    async def _build_payload(self, h, ensure, lang=None, query=None):
        if lang is None and query is not None:
            lang = resolve_lang(query)
        period = h.user_states.get("streak_period", "15m")
        sort_order = h.user_states.get("streak_sort", "desc")
        limit = h.user_states.get("streak_limit", 10)
        sort_field = h.user_states.get("streak_sort_field", "oi_streak")
        fields_state = self._ensure_field_state(h)

        rows, header = self._load_rows(period, sort_order, limit, sort_field, fields_state, lang)
        aligned = h.dynamic_align_format(rows) if rows else _t("data.no_data", lang=lang)

        sort_symbol = "🔽" if sort_order == "desc" else "🔼"
        display_sort_field = format_sort_field(sort_field, lang=lang, field_lists=[getattr(self, "general_display_fields", []), getattr(self, "special_display_fields", [])])
        time_info = h.get_current_time_display()

        text = (
            f'{_t("card.oi_continuous.title", lang=lang)}\n'
            f"{_t('card.common.update_time', lang=lang).format(time=time_info['full'])}\n"
            f"{_t('card.common.sort_info', lang=lang).format(period=period, field=display_sort_field, symbol=sort_symbol)}\n"
            f"{header}\n"
            "```\n"
            f"{aligned}\n"
            "```\n"
            f'{_t("card.oi_continuous.hint", lang=lang)}\n'
            f"{_t('card.common.last_update', lang=lang).format(time=time_info['full'])}"
        )
        if callable(ensure):
            text = ensure(text, _t(self.FALLBACK))
        kb = self._build_keyboard(h)
        return text, kb

    def _build_keyboard(self, h):
        fields_state = self._ensure_field_state(h)
        period = h.user_states.get("streak_period", "15m")
        sort_order = h.user_states.get("streak_sort", "desc")
        current_limit = h.user_states.get("streak_limit", 10)
        current_sort_field = h.user_states.get("streak_sort_field", "oi_streak")
        market = h.user_states.get("streak_market", self.DEFAULT_MARKET)

        def b(label: str, data: str, active: bool = False, disabled: bool = False):

            if disabled:

                return InlineKeyboardButton(label, callback_data=data or 'nop')

            return _btn_auto(None, label, data, active=active)


        kb: List[List[InlineKeyboardButton]] = []
        if self.SHOW_MARKET_SWITCH:
            kb.append([
                b("现货", "streak_market_spot", active=market == "spot"),
                b("期货", "streak_market_futures", active=market == "futures"),
            ])

        gen_row: List[InlineKeyboardButton] = []
        for col_id, label, _ in self.general_display_fields:
            state_on = fields_state.get(col_id, True)
            show_label = label if state_on else f"❎{label}"
            gen_row.append(InlineKeyboardButton(show_label, callback_data=f"field_streak_toggle_{col_id}"))
        kb.append(gen_row)

        spec_row: List[InlineKeyboardButton] = []
        for col_id, label, _ in self.special_display_fields:
            state_on = fields_state.get(col_id, True)
            show_label = label if state_on else f"❎{label}"
            spec_row.append(InlineKeyboardButton(show_label, callback_data=f"field_streak_toggle_{col_id}"))
        kb.append(spec_row)

        kb.append([
            b(lbl, f"streak_sort_field_{fid}", active=current_sort_field == fid)
            for fid, lbl, _ in self.general_display_fields
        ])

        kb.append([
            b(lbl, f"streak_sort_field_{fid}", active=current_sort_field == fid)
            for fid, lbl, _ in self.special_display_fields
        ])

        periods = ["1m", "5m", "15m", "1h", "4h", "1d", "1w"]
        kb.append([b(p, f"streak_period_{p}", active=p == period) for p in periods])

        kb.append([
            b("降序", "streak_sort_desc", active=sort_order == "desc"),
            b("升序", "streak_sort_asc", active=sort_order == "asc"),
            b("10条", "streak_limit_10", active=current_limit == 10),
            b("20条", "streak_limit_20", active=current_limit == 20),
            b("30条", "streak_limit_30", active=current_limit == 30),
        ])

        kb.append([
            _btn_auto(None, "🏠主菜单", "ranking_menu"),
            _btn_auto(None, "🔄刷新", "futures_oi_streak_refresh"),
        ])
        return InlineKeyboardMarkup(kb)

    def _load_rows(
        self,
        period: str,
        sort_order: str,
        limit: int,
        sort_field: str,
        field_state: Dict[str, bool],
        lang: str | None = None,
    ):
        items: List[Dict] = []
        try:
            metrics = self.provider.merge_with_base("期货情绪聚合表.py", period, base_fields=["数据时间"])
            for row in metrics:
                sym = format_symbol(row.get("symbol") or row.get("交易对") or "")
                if not sym:
                    continue
                items.append({
                    "symbol": sym,
                    "oi_streak": float(row.get("OI连续根数") or 0),
                    "quote_volume": float(row.get("quote_volume") or 0),
                    "振幅": float(row.get("振幅") or 0),
                    "成交笔数": float(row.get("成交笔数") or 0),
                    "主动买卖比": float(row.get("主动买卖比") or 0),
                    "price": float(row.get("price") or 0),
                })
        except Exception as exc:  # pragma: no cover
            self._logger.warning("读取期货情绪聚合表失败: %s", exc)
            return [], _t("card.header.rank_symbol", lang=lang)

        reverse = sort_order != "asc"
        items.sort(key=lambda x: x.get(sort_field, 0), reverse=reverse)

        active_special = [f for f in self.special_display_fields if field_state.get(f[0], True)]
        active_general = [f for f in self.general_display_fields if field_state.get(f[0], True)]
        header_parts = [_t("card.header.rank", lang=lang), _t("card.header.symbol", lang=lang)] + [translate_field(lab, lang=lang) for _, lab, _ in active_special] + [translate_field(lab, lang=lang) for _, lab, _ in active_general]

        rows: List[List[str]] = []
        for idx, item in enumerate(items[:limit], 1):
            row: List[str] = [f"{idx}", item["symbol"]]
            for col_id, _, _ in active_special:
                val = item.get(col_id)
                row.append(f"{val:.0f}" if isinstance(val, (int, float)) else (str(val) if val not in (None, "") else "-"))
            for col_id, _, _ in active_general:
                val = item.get(col_id)
                if col_id == "振幅":
                    pct = (val * 100) if isinstance(val, (int, float)) and abs(val) < 10 else val
                    row.append(self._format_percent(pct)) if isinstance(pct, (int, float)) else row.append("-")
                elif col_id == "quote_volume":
                    row.append(self._format_volume(val))
                elif col_id == "price":
                    row.append(f"{val:.4f}" if val else "-")
                elif isinstance(val, (int, float)):
                    row.append(f"{val:.2f}")
                else:
                    row.append(str(val) if val not in (None, "") else "-")
            rows.append(row)
        return rows, "/".join(header_parts)

    def _ensure_field_state(self, h) -> Dict[str, bool]:
        state = h.user_states.get("streak_fields")
        if not state:
            state = {}
            for col, _, _ in self.general_display_fields + self.special_display_fields:
                state[col] = True
            for _off in {"quote_volume", "振幅", "成交笔数", "主动买卖比", "price"}:
                if _off in state:
                    state[_off] = False
            h.user_states["streak_fields"] = state
        return state

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

    @staticmethod
    def _format_percent(value: float) -> str:
        if value is None:
            return "-"
        try:
            sign = "+" if value > 0 else "-" if value < 0 else ""
            return f"{sign}{abs(value):.2f}%"
        except Exception:
            return "-"


CARD = FuturesOIStreakCard()
