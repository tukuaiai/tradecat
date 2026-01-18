"""成交量比率排行榜卡片

数据源：market_data.db 表 成交量比率扫描器.py
字段：排名,币种,周期,方向,强度,量比,信号概述,当前价格,成交额（USDT）,数据时间
"""

from __future__ import annotations

import logging
from typing import Dict, List, Tuple

from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from cards.data_provider import get_ranking_provider, format_symbol
from cards.i18n import (
    btn_auto as _btn_auto,
    gettext as _t,
    resolve_lang,
    translate_field,
    translate_value,
    format_sort_field,
)
from cards.base import RankingCard, format_number


class 成交量比率排行卡片(RankingCard):
    FALLBACK = "card.volume_ratio.fallback"
    provider = get_ranking_provider()

    def __init__(self) -> None:
        super().__init__(
            card_id="volume_ratio_ranking",
            button_text="📦 成交量比率",
            button_key="card.volume_ratio.btn",
            category="free",
            description="成交量比率(当前/均量)排行榜",
            default_state={
                "vr_period": "15m",
                "vr_sort": "desc",
                "vr_limit": 10,
                "vr_sort_field": "ratio",
                "vr_market": "futures",
                "vr_fields": {},
            },
            callback_prefixes=[
                "volume_ratio_ranking",
                "volume_ratio_",            # 兼容旧版回调
                "volume_ratio_period_",     # 兼容旧版周期
                "volume_ratio_sort_",       # 兼容旧版排序
                "volume_ratio_limit_",      # 兼容旧版条数
                "volume_ratio_sort_field_", # 兼容旧版排序字段
                "vr_period_",
                "vr_sort_",
                "vr_limit_",
                "vr_sort_field_",
                "vr_market_",
                "field_vr_toggle_",
            ],
            priority=32,
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
            ("ratio", "量比", True),
            ("direction", "方向", True),
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
        if data in (self.card_id, self.entry_callback, "volume_ratio_ranking_refresh"):
            await self._reply(query, h, ensure)
            return True
        if data == "vr_nop":
            return True
        # 兼容旧版前缀（volume_ratio_*）
        if data.startswith("volume_ratio_period_"):
            h.user_states["vr_period"] = data.replace("volume_ratio_period_", "")
            await self._edit(query, h, ensure)
            return True
        if data.startswith("volume_ratio_sort_field_"):
            h.user_states["vr_sort_field"] = data.replace("volume_ratio_sort_field_", "")
            await self._edit(query, h, ensure)
            return True
        if data.startswith("volume_ratio_sort_"):
            h.user_states["vr_sort"] = data.replace("volume_ratio_sort_", "")
            await self._edit(query, h, ensure)
            return True
        if data.startswith("volume_ratio_limit_"):
            val = data.replace("volume_ratio_limit_", "")
            if val.isdigit():
                h.user_states["vr_limit"] = int(val)
                await self._edit(query, h, ensure)
                return True
            return False

        if data.startswith("vr_market_"):
            h.user_states["vr_market"] = data.replace("vr_market_", "")
            await self._edit(query, h, ensure)
            return True
        if data.startswith("vr_sort_field_"):
            h.user_states["vr_sort_field"] = data.replace("vr_sort_field_", "")
            await self._edit(query, h, ensure)
            return True
        if data.startswith("vr_period_"):
            h.user_states["vr_period"] = data.replace("vr_period_", "")
            await self._edit(query, h, ensure)
            return True
        if data.startswith("vr_sort_"):
            h.user_states["vr_sort"] = data.replace("vr_sort_", "")
            await self._edit(query, h, ensure)
            return True
        if data.startswith("vr_limit_"):
            val = data.replace("vr_limit_", "")
            if val.isdigit():
                h.user_states["vr_limit"] = int(val)
                await self._edit(query, h, ensure)
                return True
            return False
        if data.startswith("field_vr_toggle_"):
            col = data.replace("field_vr_toggle_", "")
            fields_state = self._ensure_field_state(h)
            if col in fields_state:
                fields_state[col] = not fields_state[col]
                h.user_states["vr_fields"] = fields_state
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

    async def _build_payload(self, h, ensure, lang: str = "zh_CN", update=None) -> Tuple[str, object]:
        period = h.user_states.get("vr_period", "15m")
        sort_order = h.user_states.get("vr_sort", "desc")
        limit = h.user_states.get("vr_limit", 10)
        sort_field = h.user_states.get("vr_sort_field", "ratio")
        allowed_fields = {f[0] for f in self.general_display_fields + self.special_display_fields}
        if sort_field not in allowed_fields:
            sort_field = "ratio"
            h.user_states["vr_sort_field"] = sort_field
        fields_state = self._ensure_field_state(h)
        rows, header = self._load_rows(period, sort_order, limit, sort_field, fields_state, lang)
        aligned = h.dynamic_align_format(rows) if rows else _t("data.no_data", lang=lang)
        time_info = h.get_current_time_display()
        sort_symbol = "🔽" if sort_order == "desc" else "🔼"
        display_sort_field = format_sort_field(sort_field, lang=lang, field_lists=[getattr(self, "general_display_fields", []), getattr(self, "special_display_fields", [])])
        text = (
            f'{_t("card.volume_ratio.title", lang=lang)}\n'
            f"{_t('card.common.update_time', lang=lang).format(time=time_info['full'])}\n"
            f"{_t('card.common.sort_info', lang=lang).format(period=period, field=display_sort_field, symbol=sort_symbol)}\n"
            f"{header}\n"
            f"```\n{aligned}\n```\n"
            f"{_t('card.volume.hint', lang=lang)}\n"
            f"{_t('card.common.last_update', lang=lang).format(time=time_info['full'])}"
        )
        if callable(ensure):
            text = ensure(text, _t(self.FALLBACK))
        kb = self._build_keyboard(h)
        return text, kb

    def _build_keyboard(self, h):
        fields_state = self._ensure_field_state(h)
        period = h.user_states.get("vr_period", "15m")
        sort_order = h.user_states.get("vr_sort", "desc")
        current_limit = h.user_states.get("vr_limit", 10)
        current_sort_field = h.user_states.get("vr_sort_field", "ratio")
        market = h.user_states.get("vr_market", "futures")

        def b(label: str, data: str, active: bool = False, disabled: bool = False):

            if disabled:

                return InlineKeyboardButton(label, callback_data=data or 'nop')

            return _btn_auto(None, label, data, active=active)


        kb: List[List[InlineKeyboardButton]] = []

        show_market_row = False
        if show_market_row:
            kb.append([
                b("现货", "vr_market_spot", active=market == "spot"),
                b("期货", "vr_market_futures", active=market == "futures"),
            ])

        gen_row: List[InlineKeyboardButton] = []
        for col_id, label, _ in self.general_display_fields:
            state_on = fields_state.get(col_id, True)
            show_label = label if state_on else f"❎{label}"
            gen_row.append(InlineKeyboardButton(show_label, callback_data=f"field_vr_toggle_{col_id}"))
        kb.append(gen_row)

        spec_row: List[InlineKeyboardButton] = []
        for col_id, label, _ in self.special_display_fields:
            state_on = fields_state.get(col_id, True)
            show_label = label if state_on else f"❎{label}"
            spec_row.append(InlineKeyboardButton(show_label, callback_data=f"field_vr_toggle_{col_id}"))
        kb.append(spec_row)

        general_sort = [("quote_volume", "成交额"), ("振幅", "振幅"), ("成交笔数", "成交笔数"), ("主动买卖比", "主动买卖比"), ("price", "价格")]
        kb.append([
            b(lbl, f"vr_sort_field_{fid}", active=(current_sort_field == fid))
            for fid, lbl in general_sort
        ])

        special_sort = [("ratio", "量比"), ("direction", "方向")]
        kb.append([
            b(lbl, f"vr_sort_field_{fid}", active=(current_sort_field == fid))
            for fid, lbl in special_sort
        ])
        periods = ["1m", "5m", "15m", "1h", "4h", "1d", "1w"]
        kb.append([b(p, f"vr_period_{p}", active=p == period) for p in periods])

        kb.append([
            b("降序", "vr_sort_desc", active=sort_order == "desc"),
            b("升序", "vr_sort_asc", active=sort_order == "asc"),
            b("10条", "vr_limit_10", active=current_limit == 10),
            b("20条", "vr_limit_20", active=current_limit == 20),
            b("30条", "vr_limit_30", active=current_limit == 30),
        ])

        kb.append([
            _btn_auto(None, "🏠主菜单", "ranking_menu"),
            _btn_auto(None, "🔄刷新", "volume_ratio_ranking_refresh"),
        ])

        return InlineKeyboardMarkup(kb)

    def _load_rows(self, period: str, sort_order: str, limit: int, sort_field: str, field_state: Dict[str, bool], lang: str | None = None) -> Tuple[List[List[str]], str]:
        items: List[Dict] = []
        try:
            metrics = self.provider.merge_with_base("成交量比率榜单", period, base_fields=["当前价格", "成交额"])
            for row in metrics:
                sym = format_symbol(row.get("symbol") or row.get("交易对") or row.get("币种") or "")
                if not sym:
                    continue
                items.append({
                    "symbol": sym,
                    "ratio": float(row.get("量比") or 0),
                    "price": float(row.get("price") or row.get("当前价格") or 0),
                    "direction": row.get("方向") or row.get("信号概述") or "-",
                    "quote_volume": float(row.get("quote_volume") or 0),
                    "振幅": float(row.get("振幅") or 0),
                    "成交笔数": float(row.get("成交笔数") or 0),
                    "主动买卖比": float(row.get("主动买卖比") or 0),
                })
        except Exception as exc:  # pragma: no cover
            self._logger.warning("读取成交量比率榜单失败: %s", exc)
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
                if isinstance(val, (int, float)):
                    row.append(format_number(val, 2))
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
                    row.append(format_number(val, 4) if val else "-")
                elif isinstance(val, (int, float)):
                    row.append(format_number(val, 2))
                else:
                    row.append(str(val) if val not in (None, "") else "-")
            rows.append(row)
        return rows, "/".join(header_parts)

    # ---------- 工具 ----------
    def _ensure_field_state(self, h) -> Dict[str, bool]:
        state = h.user_states.get("vr_fields")
        if not state:
            state = {}
            for col, _, _ in self.general_display_fields + self.special_display_fields:
                state[col] = False
            # 默认开启：量比、方向
            for _on in {"ratio", "direction"}:
                if _on in state:
                    state[_on] = True
            h.user_states["vr_fields"] = state

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


CARD = 成交量比率排行卡片()
