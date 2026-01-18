"""ATR 波幅排行榜卡片

数据源：market_data.db 表 ATR波幅扫描器.py
字段：排名,币种,周期,强度,波动分类,ATR百分比,上轨,中轨,下轨,当前价格,成交额（USDT）,数据时间
"""

from __future__ import annotations

import logging
from typing import Dict, List, Tuple

from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from cards.base import RankingCard
from cards.data_provider import get_ranking_provider, format_symbol
from cards.i18n import (
    btn_auto as _btn_auto,
    gettext as _t,
    resolve_lang,
    translate_field,
    translate_value,
    format_sort_field,
)


class ATR排行卡片(RankingCard):
    FALLBACK = "card.atr.fallback"
    provider = get_ranking_provider()

    def __init__(self) -> None:
        super().__init__(
            card_id="atr_ranking",
            button_text="🧭 波动率",
            button_key="card.atr.btn",
            category="free",
            description="波幅强度榜（ATR%）",
            default_state={
                "atr_period": "15m",
                "atr_sort": "desc",
                "atr_limit": 10,
                "atr_sort_field": "atr_pct",
                "atr_market": "futures",
                "atr_fields": {},
            },
            callback_prefixes=[
                "atr_ranking",
                "atr_period_",
                "atr_sort_",
                "atr_limit_",
                "atr_sort_field_",
                "atr_market_",
                "field_atr_toggle_",
            ],
            priority=26,
        )
        self._logger = logging.getLogger(__name__)

        self.general_display_fields: List[Tuple[str, str, bool]] = [
            ("quote_volume", "成交额", False),
            ("振幅", "振幅", False),
            ("成交笔数", "成交笔数", False),
            ("主动买卖比", "主动买卖比", False),
            ("price", "价格", True),
        ]
        # 专有字段全部允许开关（仅使用表存在的列）
        self.special_display_fields: List[Tuple[str, str, bool]] = [
            ("atr_pct", "ATR%", True),
            ("category", "波动", True),
            ("upper", "上轨", False),
            ("middle", "中轨", False),
            ("lower", "下轨", False),
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
        if data in (self.card_id, self.entry_callback, "atr_ranking_refresh"):
            await self._reply(query, h, ensure)
            return True
        if data == "atr_nop":
            return True
        if data.startswith("atr_market_"):
            h.user_states["atr_market"] = data.replace("atr_market_", "")
            await self._edit(query, h, ensure)
            return True
        if data.startswith("atr_sort_field_"):
            h.user_states["atr_sort_field"] = data.replace("atr_sort_field_", "")
            await self._edit(query, h, ensure)
            return True
        if data.startswith("atr_period_"):
            h.user_states["atr_period"] = data.replace("atr_period_", "")
            await self._edit(query, h, ensure)
            return True
        if data.startswith("atr_sort_"):
            h.user_states["atr_sort"] = data.replace("atr_sort_", "")
            await self._edit(query, h, ensure)
            return True
        if data.startswith("atr_limit_"):
            val = data.replace("atr_limit_", "")
            if val.isdigit():
                h.user_states["atr_limit"] = int(val)
                await self._edit(query, h, ensure)
                return True
            return False
        if data.startswith("field_atr_toggle_"):
            col = data.replace("field_atr_toggle_", "")
            fields_state = self._ensure_field_state(h)
            if col in fields_state and not self._is_core(col):
                fields_state[col] = not fields_state[col]
                h.user_states["atr_fields"] = fields_state
            await self._edit(query, h, ensure)
            return True
        return False

    async def _reply(self, query, h, ensure):
        lang = resolve_lang(query)
        text, kb = await self._build_payload(h, ensure, lang, query)
        await query.message.reply_text(text, reply_markup=kb, parse_mode="Markdown")

    async def _edit(self, query, h, ensure):
        lang = resolve_lang(query)
        lang = resolve_lang(query)
        text, kb = await self._build_payload(h, ensure, lang, query)
        await query.edit_message_text(text, reply_markup=kb, parse_mode="Markdown")

    async def _build_payload(self, h, ensure, lang: str = "zh_CN", update=None) -> Tuple[str, object]:
        period = h.user_states.get("atr_period", "15m")
        sort_order = h.user_states.get("atr_sort", "desc")
        limit = h.user_states.get("atr_limit", 10)
        allowed_fields = {f[0] for f in self.general_display_fields + self.special_display_fields}
        sort_field = h.user_states.get("atr_sort_field", "atr_pct")
        if sort_field not in allowed_fields:
            sort_field = "atr_pct"
            h.user_states["atr_sort_field"] = sort_field
        fields_state = self._ensure_field_state(h)
        rows, header = self._load_rows(period, sort_order, limit, sort_field, fields_state, lang)
        aligned = h.dynamic_align_format(rows) if rows else _t("data.no_data", lang=lang)
        time_info = h.get_current_time_display()
        sort_symbol = "🔽" if sort_order == "desc" else "🔼"
        display_sort_field = format_sort_field(sort_field, lang=lang, field_lists=[getattr(self, "general_display_fields", []), getattr(self, "special_display_fields", [])])
        text = (
            f"{_t('card.atr.title', lang=lang)}\n"
            f"{_t('time.update', update, lang=lang, time=time_info['full'])}\n"
            f"{_t('card.common.sort_info', lang=lang).format(period=period, field=display_sort_field, symbol=sort_symbol)}\n"
            f"{header}\n"
            f"```\n{aligned}\n```\n"
            f"{_t('card.atr.hint', lang=lang)}"
        )
        if callable(ensure):
            text = ensure(text, _t(self.FALLBACK))
        kb = self._build_keyboard(h)
        return text, kb

    def _build_keyboard(self, h):
        fields_state = self._ensure_field_state(h)
        period = h.user_states.get("atr_period", "15m")
        sort_order = h.user_states.get("atr_sort", "desc")
        current_limit = h.user_states.get("atr_limit", 10)
        current_sort_field = h.user_states.get("atr_sort_field", "atr_pct")
        market = h.user_states.get("atr_market", "futures")

        def b(label: str, data: str, active: bool = False, disabled: bool = False):

            if disabled:

                return InlineKeyboardButton(label, callback_data=data or 'nop')

            return _btn_auto(None, label, data, active=active)


        kb: List[List[InlineKeyboardButton]] = []

        show_market_row = False
        if show_market_row:
            kb.append([
                b("现货", "atr_market_spot", active=market == "spot"),
                b("期货", "atr_market_futures", active=market == "futures"),
            ])

        gen_row: List[InlineKeyboardButton] = []
        for col_id, label, is_core in self.general_display_fields:
            state_on = fields_state.get(col_id, is_core or True)
            show_label = label if state_on or is_core else f"❎{label}"
            gen_row.append(InlineKeyboardButton(show_label, callback_data="atr_nop" if is_core else f"field_atr_toggle_{col_id}"))
        kb.append(gen_row)

        spec_row: List[InlineKeyboardButton] = []
        for col_id, label, is_core in self.special_display_fields:
            state_on = fields_state.get(col_id, is_core or True)
            show_label = label if state_on or is_core else f"❎{label}"
            spec_row.append(InlineKeyboardButton(show_label, callback_data="atr_nop" if is_core else f"field_atr_toggle_{col_id}"))
        kb.append(spec_row)

        general_sort = [("quote_volume", "成交额"), ("振幅", "振幅"), ("成交笔数", "成交笔数"), ("主动买卖比", "主动买卖比"), ("price", "价格")]
        kb.append([
            b(lbl, f"atr_sort_field_{fid}", active=(current_sort_field == fid))
            for fid, lbl in general_sort
        ])

        special_sort = [
            ("atr_pct", "ATR%"),
            ("category", "波动"),
            ("upper", "上轨"),
            ("middle", "中轨"),
            ("lower", "下轨"),
        ]
        kb.append([
            b(lbl, f"atr_sort_field_{fid}", active=(current_sort_field == fid))
            for fid, lbl in special_sort
        ])
        periods = ["1m", "5m", "15m", "1h", "4h", "1d", "1w"]
        kb.append([b(p, f"atr_period_{p}", active=p == period) for p in periods])

        kb.append([
            b("降序", "atr_sort_desc", active=sort_order == "desc"),
            b("升序", "atr_sort_asc", active=sort_order == "asc"),
            b("10条", "atr_limit_10", active=current_limit == 10),
            b("20条", "atr_limit_20", active=current_limit == 20),
            b("30条", "atr_limit_30", active=current_limit == 30),
        ])

        kb.append([
            _btn_auto(None, "🏠主菜单", "ranking_menu"),
            _btn_auto(None, "🔄刷新", "atr_ranking_refresh"),
        ])

        return InlineKeyboardMarkup(kb)

    def _load_rows(self, period: str, sort_order: str, limit: int, sort_field: str, field_state: Dict[str, bool], lang: str | None = None) -> Tuple[List[List[str]], str]:
        items: List[Dict] = []
        try:
            metrics = self.provider.merge_with_base("ATR波幅榜单", period, base_fields=["成交额", "当前价格"])
            for row in metrics:
                sym = format_symbol(row.get("symbol") or row.get("交易对") or row.get("币种") or "")
                if not sym:
                    continue
                atr_pct = float(row.get("ATR百分比") or 0)
                price = float(row.get("price") or row.get("当前价格") or 0)
                items.append({
                    "symbol": sym,
                    "atr_pct": atr_pct,
                    "category": row.get("波动分类") or row.get("分类") or "-",
                    "upper": float(row.get("上轨") or 0),
                    "middle": float(row.get("中轨") or 0),
                    "lower": float(row.get("下轨") or 0),
                    "price": price,
                    "quote_volume": float(row.get("quote_volume") or 0),
                    "振幅": float(row.get("振幅") or 0),
                    "成交笔数": float(row.get("成交笔数") or 0),
                    "主动买卖比": float(row.get("主动买卖比") or 0),
                })
        except Exception as exc:  # pragma: no cover
            self._logger.warning("读取 ATR 榜单失败: %s", exc)
            return [], _t("card.header.rank_symbol", lang=lang)

        reverse = sort_order != "asc"
        items.sort(key=lambda x: x.get(sort_field, 0), reverse=reverse)
        active_special = [f for f in self.special_display_fields if field_state.get(f[0], f[2] or True)]
        active_general = [f for f in self.general_display_fields if field_state.get(f[0], f[2] or True)]

        header_parts = [_t("card.header.rank", lang=lang), _t("card.header.symbol", lang=lang)] + [translate_field(lab, lang=lang) for _, lab, _ in active_special] + [translate_field(lab, lang=lang) for _, lab, _ in active_general]

        rows: List[List[str]] = []
        for idx, item in enumerate(items[:limit], 1):
            row: List[str] = [f"{idx}", item["symbol"]]
            for col_id, _, _ in active_special:
                val = item.get(col_id)
                if col_id == "atr_pct":
                    row.append(f"{val:.2f}%" if val else "-")
                elif isinstance(val, (int, float)):
                    row.append(f"{val:.2f}")
                else:
                    translated = translate_value(val, lang=lang)
                    row.append(str(translated) if translated not in (None, "") else "-")
            for col_id, _, _ in active_general:
                val = item.get(col_id)
                if col_id == "振幅":
                    pct = (val * 100) if isinstance(val, (int, float)) and val <= 5 else val
                    row.append(f"{pct:.2f}%" if isinstance(pct, (int, float)) else "-")
                elif col_id == "quote_volume":
                    row.append(self._format_volume(val))
                elif col_id == "price":
                    row.append(f"{val:.4f}" if val else "-")
                elif isinstance(val, (int, float)):
                    row.append(f"{val:.2f}")
                else:
                    translated = translate_value(val, lang=lang)
                    row.append(str(translated) if translated not in (None, "") else "-")
            rows.append(row)
        return rows, "/".join(header_parts)

    # ---------- 工具 ----------
    def _ensure_field_state(self, h) -> Dict[str, bool]:
        state = h.user_states.get("atr_fields")
        if not state:
            state = {}
            for col, _, _ in self.general_display_fields + self.special_display_fields:
                # 默认全部开启，用户可手动关闭
                state[col] = True
            # 全局默认关闭的通用字段（仅初始化时执行）
            for _off in {"quote_volume", "振幅", "成交笔数", "主动买卖比", "upper", "middle", "lower"}:
                if _off in state:
                    state[_off] = False
            h.user_states["atr_fields"] = state

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


CARD = ATR排行卡片()
