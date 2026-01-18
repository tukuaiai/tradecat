"""VWAP 排行榜卡片

数据源：market_data.db 表 VWAP离线信号扫描.py
按钮：周期(1m/5m/15m/1h/4h/1d/1w) + 排序(升/降) + TOP10/20/30
逻辑：按指定周期过滤，按强度排序，字段缺失自动跳过，保持等宽对齐。
"""

from __future__ import annotations

import logging
from typing import Dict, List, Tuple

from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from cards.data_provider import get_ranking_provider, format_symbol
from cards.i18n import btn_auto as _btn_auto, gettext as _t, format_sort_field, resolve_lang, translate_field

from cards.base import RankingCard


class VWAP排行卡片(RankingCard):
    FALLBACK = "card.vwap.fallback"
    provider = get_ranking_provider()

    def __init__(self) -> None:
        super().__init__(
            card_id="vwap_ranking",
            button_text="📏 VWAP",
            button_key="card.vwap.btn",
            category="free",
            description="按VWAP偏离强度排序的榜单",
            default_state={
                "vwap_period": "15m",
                "vwap_sort": "desc",
                "vwap_limit": 10,
                "vwap_sort_field": "bandwidth_pct",
                "vwap_market": "futures",
                "vwap_fields": {},
            },
            callback_prefixes=[
                "vwap_ranking",
                "vwap_",  # 通用前缀
                "vwap_period_",
                "vwap_sort_",
                "vwap_limit_",
                "vwap_sort_field_",
                "vwap_market_",
                "field_vwap_toggle_",
            ],
            priority=20,
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
            ("deviation", "偏离", False),
            ("weighted_volume", "成交量加权", False),
            ("bandwidth_pct", "带宽%", True),
        ]

    # 入口与按钮
    async def handle_callback(self, update, context, services: Dict[str, object]) -> bool:
        query = update.callback_query
        if not query:
            return False
        handler = services.get("user_handler")
        ensure_valid_text = services.get("ensure_valid_text")
        if handler is None:
            return False
        data = query.data or ""
        if data in (self.card_id, self.entry_callback, "vwap_ranking_refresh"):
            await self._reply(query, handler, ensure_valid_text)
            return True
        if data == "vwap_nop":
            return True
        if data.startswith("vwap_market_"):
            handler.user_states["vwap_market"] = data.replace("vwap_market_", "")
            await self._edit(query, handler, ensure_valid_text)
            return True
        if data.startswith("vwap_sort_field_"):
            handler.user_states["vwap_sort_field"] = data.replace("vwap_sort_field_", "")
            await self._edit(query, handler, ensure_valid_text)
            return True
        if data.startswith("vwap_period_"):
            handler.user_states["vwap_period"] = data.replace("vwap_period_", "")
            await self._edit(query, handler, ensure_valid_text)
            return True
        if data.startswith("vwap_sort_"):
            handler.user_states["vwap_sort"] = data.replace("vwap_sort_", "")
            await self._edit(query, handler, ensure_valid_text)
            return True
        if data.startswith("vwap_limit_"):
            val = data.replace("vwap_limit_", "")
            if val.isdigit():
                handler.user_states["vwap_limit"] = int(val)
                await self._edit(query, handler, ensure_valid_text)
                return True
            return False
        if data.startswith("field_vwap_toggle_"):
            col = data.replace("field_vwap_toggle_", "")
            fields_state = self._ensure_field_state(handler)
            if col in fields_state:
                fields_state[col] = not fields_state[col]
                handler.user_states["vwap_fields"] = fields_state
            await self._edit(query, handler, ensure_valid_text)
            return True
        return False

    async def _reply(self, query, handler, ensure_valid_text):
        text, kb = await self._build_payload(handler, ensure_valid_text)
        await query.message.reply_text(text, reply_markup=kb, parse_mode="Markdown")

    async def _edit(self, query, handler, ensure_valid_text):
        text, kb = await self._build_payload(handler, ensure_valid_text)
        await query.edit_message_text(text, reply_markup=kb, parse_mode="Markdown")

    async def _build_payload(self, handler, ensure_valid_text, lang=None, query=None) -> Tuple[str, object]:
        if lang is None and query is not None:
            lang = resolve_lang(query)
        fields_state = self._ensure_field_state(handler)
        rows, header = self._load_rows(
            handler.user_states.get("vwap_period", "15m"),
            handler.user_states.get("vwap_sort", "desc"),
            handler.user_states.get("vwap_limit", 10),
            handler.user_states.get("vwap_sort_field", "deviation"),
            fields_state,
        )
        aligned = handler.dynamic_align_format(rows) if rows else _t("data.no_data", lang=lang)
        time_info = handler.get_current_time_display()
        sort_order = handler.user_states.get("vwap_sort", "desc")
        sort_symbol = "🔽" if sort_order == "desc" else "🔼"
        period = handler.user_states.get("vwap_period", "15m")
        sort_field = handler.user_states.get("vwap_sort_field", "deviation")
        display_sort_field = format_sort_field(sort_field, lang=lang, field_lists=[getattr(self, "general_display_fields", []), getattr(self, "special_display_fields", [])])
        text = (
            f"{_t('card.vwap.title', lang=lang)}\n"
            f"{_t('card.common.update_time', lang=lang).format(time=time_info['full'])}\n"
            f"{_t('card.common.sort_info', lang=lang).format(period=period, field=display_sort_field, symbol=sort_symbol)}\n"
            f"{header}\n"
            f"```\n{aligned}\n```\n"
            f"{_t('card.vwap.hint', lang=lang)}\n"
            f"{_t('card.common.last_update', lang=lang).format(time=time_info['full'])}"
        )
        if callable(ensure_valid_text):
            text = ensure_valid_text(text, self.FALLBACK)
        kb = self._build_keyboard(handler)
        return text, kb

    def _build_keyboard(self, handler):
        fields_state = self._ensure_field_state(handler)
        period = handler.user_states.get("vwap_period", "15m")
        sort_order = handler.user_states.get("vwap_sort", "desc")
        current_limit = handler.user_states.get("vwap_limit", 10)
        current_sort_field = handler.user_states.get("vwap_sort_field", "deviation")
        market = handler.user_states.get("vwap_market", "futures")

        def b(label: str, data: str, active: bool = False, disabled: bool = False):

            if disabled:

                return InlineKeyboardButton(label, callback_data=data or 'nop')

            return _btn_auto(None, label, data, active=active)


        kb: List[List[InlineKeyboardButton]] = []

        show_market_row = False
        if show_market_row:
            kb.append([
                b("现货", "vwap_market_spot", active=market == "spot"),
                b("期货", "vwap_market_futures", active=market == "futures"),
            ])

        gen_row: List[InlineKeyboardButton] = []
        for col_id, label, _ in self.general_display_fields:
            state_on = fields_state.get(col_id, True)
            show_label = label if state_on else f"❎{label}"
            gen_row.append(InlineKeyboardButton(show_label, callback_data=f"field_vwap_toggle_{col_id}"))
        kb.append(gen_row)

        spec_row: List[InlineKeyboardButton] = []
        for col_id, label, _ in self.special_display_fields:
            state_on = fields_state.get(col_id, True)
            show_label = label if state_on else f"❎{label}"
            spec_row.append(InlineKeyboardButton(show_label, callback_data=f"field_vwap_toggle_{col_id}"))
        kb.append(spec_row)

        general_sort = [("quote_volume", "成交额"), ("振幅", "振幅"), ("成交笔数", "成交笔数"), ("主动买卖比", "主动买卖比"), ("price", "价格")]
        kb.append([
            b(lbl, f"vwap_sort_field_{fid}", active=(current_sort_field == fid))
            for fid, lbl in general_sort
        ])

        special_sort = [
            ("deviation", "偏离"),
            ("weighted_volume", "成交量加权"),
            ("bandwidth_pct", "带宽%"),
        ]
        kb.append([
            b(lbl, f"vwap_sort_field_{fid}", active=(current_sort_field == fid))
            for fid, lbl in special_sort
        ])
        periods = ["1m", "5m", "15m", "1h", "4h", "1d", "1w"]
        kb.append([b(p, f"vwap_period_{p}", active=p == period) for p in periods])

        kb.append([
            b("降序", "vwap_sort_desc", active=sort_order == "desc"),
            b("升序", "vwap_sort_asc", active=sort_order == "asc"),
            b("10条", "vwap_limit_10", active=current_limit == 10),
            b("20条", "vwap_limit_20", active=current_limit == 20),
            b("30条", "vwap_limit_30", active=current_limit == 30),
        ])

        kb.append([
            _btn_auto(None, "🏠主菜单", "ranking_menu"),
            _btn_auto(None, "🔄刷新", "vwap_ranking_refresh"),
        ])

        return InlineKeyboardMarkup(kb)

    # 数据读取
    def _load_rows(self, period: str, sort_order: str, limit: int, sort_field: str, field_state: Dict[str, bool], lang: str | None = None) -> Tuple[List[List[str]], str]:
        items: List[Dict] = []
        try:
            metrics = self.provider.merge_with_base("VWAP榜单", period, base_fields=["当前价格", "成交额"])
            for row in metrics:
                sym = format_symbol(row.get("symbol") or row.get("交易对") or row.get("币种") or "")
                if not sym:
                    continue
                items.append({
                    "symbol": sym,
                    "deviation": float(row.get("偏离百分比") or row.get("偏离度") or 0),
                    "weighted_volume": float(row.get("成交量加权") or 0),
                    "bandwidth_pct": float(row.get("VWAP带宽百分比") or row.get("bandwidth_pct") or 0),
                    "price": float(row.get("price") or row.get("当前价格") or 0),
                    "quote_volume": float(row.get("quote_volume") or row.get("成交额（USDT）") or 0),
                    "成交笔数": float(row.get("成交笔数") or row.get("交易次数") or 0),
                    "振幅": float(row.get("振幅") or 0),
                    "主动买卖比": float(row.get("主动买卖比") or 0),
                })
        except Exception as exc:  # pragma: no cover
            self._logger.warning("读取VWAP榜单失败: %s", exc)
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
                    if col_id == "deviation":
                        row.append(f"{val:.3f}")
                    elif col_id == "bandwidth_pct":
                        row.append(f"{val:.2f}%")
                    elif col_id == "weighted_volume":
                        row.append(self._format_volume(val))
                    else:
                        row.append(f"{val:.2f}")
                else:
                    row.append(str(val) if val not in (None, "") else "-")
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
                    row.append(str(val) if val not in (None, "") else "-")
            rows.append(row)
        return rows, "/".join(header_parts)

    # ---------- 工具 ----------
    def _ensure_field_state(self, h) -> Dict[str, bool]:
        state = h.user_states.get("vwap_fields")
        if not state:
            state = {}
            for col, _, _ in self.general_display_fields + self.special_display_fields:
                state[col] = False
            # 默认开启：带宽%、价格；其余关闭
            for _on in {"bandwidth_pct", "price"}:
                if _on in state:
                    state[_on] = True
            h.user_states["vwap_fields"] = state

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


CARD = VWAP排行卡片()
