"""支撑阻力排行榜卡片

数据源：market_data.db 表 全量支撑阻力扫描器.py
"""

from __future__ import annotations

import logging
from typing import Dict, List, Tuple

from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from cards.data_provider import get_ranking_provider, format_symbol
from cards.i18n import btn_auto as _btn_auto, gettext as _t, resolve_lang, translate_field, format_sort_field
from cards.base import RankingCard, format_number


class 支撑阻力排行卡片(RankingCard):
    FALLBACK = "card.sr.fallback"
    provider = get_ranking_provider()

    def __init__(self) -> None:
        super().__init__(
            card_id="sr_ranking",
            button_text="🧱 支撑阻力",
            button_key="card.support_resistance.btn",
            category="free",
            description="支撑阻力突破/反弹信号榜",
            default_state={
                "sr_period": "15m",
                "sr_sort": "desc",  # 默认降序
                "sr_limit": 10,
                "sr_sort_field": "distance_pct",
                "sr_market": "futures",
                "sr_fields": {},
            },
            callback_prefixes=[
                "sr_ranking",
                "sr_",  # 兼容通用前缀
                "sr_period_",
                "sr_sort_",
                "sr_limit_",
                "sr_sort_field_",
                "sr_market_",
                "field_sr_toggle_",
            ],
            priority=25,
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
            ("signal", "信号", False),
            ("distance_pct", "距关键位%", False),
            ("distance_support", "距支撑%", True),
            ("distance_resist", "距阻力%", True),
            ("break_price", "突破价", False),
            ("break_type", "类型", False),
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
        if data in (self.card_id, self.entry_callback, "sr_ranking_refresh"):
            await self._reply(query, h, ensure)
            return True
        if data == "sr_nop":
            return True
        if data.startswith("sr_market_"):
            h.user_states["sr_market"] = data.replace("sr_market_", "")
            await self._edit(query, h, ensure)
            return True
        if data.startswith("sr_sort_field_"):
            h.user_states["sr_sort_field"] = data.replace("sr_sort_field_", "")
            await self._edit(query, h, ensure)
            return True
        if data.startswith("sr_period_"):
            h.user_states["sr_period"] = data.replace("sr_period_", "")
            await self._edit(query, h, ensure)
            return True
        if data.startswith("sr_sort_"):
            h.user_states["sr_sort"] = data.replace("sr_sort_", "")
            await self._edit(query, h, ensure)
            return True
        if data.startswith("sr_limit_"):
            val = data.replace("sr_limit_", "")
            if val.isdigit():
                h.user_states["sr_limit"] = int(val)
                await self._edit(query, h, ensure)
                return True
            return False
        if data.startswith("field_sr_toggle_"):
            col = data.replace("field_sr_toggle_", "")
            fields_state = self._ensure_field_state(h)
            if col in fields_state:
                fields_state[col] = not fields_state[col]
                h.user_states["sr_fields"] = fields_state
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
        period = h.user_states.get("sr_period", "15m")
        sort_order = h.user_states.get("sr_sort", "desc")
        limit = h.user_states.get("sr_limit", 10)
        sort_field = h.user_states.get("sr_sort_field", "distance_support")
        fields_state = self._ensure_field_state(h)
        rows, header = self._load_rows(period, sort_order, limit, sort_field, fields_state, lang)
        aligned = h.dynamic_align_format(rows) if rows else _t("data.no_data", lang=lang)
        time_info = h.get_current_time_display()
        sort_symbol = "🔽" if sort_order == "desc" else "🔼"
        display_sort_field = format_sort_field(sort_field, lang=lang, field_lists=[getattr(self, "general_display_fields", []), getattr(self, "special_display_fields", [])])
        text = (
            f'{_t("card.support_resistance.title", lang=lang)}\n'
            f"{_t('card.common.update_time', lang=lang).format(time=time_info['full'])}\n"
            f"{_t('card.common.sort_info', lang=lang).format(period=period, field=display_sort_field, symbol=sort_symbol)}\n"
            f"{header}\n"
            f"```\n{aligned}\n```\n"
            f"{_t('card.sr.hint', lang=lang)}\n"
            f"{_t('card.common.last_update', lang=lang).format(time=time_info['full'])}"
        )
        if callable(ensure):
            text = ensure(text, _t(self.FALLBACK))
        kb = self._build_keyboard(h)
        return text, kb

    def _build_keyboard(self, h):
        fields_state = self._ensure_field_state(h)
        period = h.user_states.get("sr_period", "15m")
        sort_order = h.user_states.get("sr_sort", "desc")
        current_limit = h.user_states.get("sr_limit", 10)
        current_sort_field = h.user_states.get("sr_sort_field", "distance_pct")
        market = h.user_states.get("sr_market", "futures")

        def b(label: str, data: str, active: bool = False, disabled: bool = False):

            if disabled:

                return InlineKeyboardButton(label, callback_data=data or 'nop')

            return _btn_auto(None, label, data, active=active)


        kb: List[List[InlineKeyboardButton]] = []

        show_market_row = False
        if show_market_row:
            kb.append([
                b("现货", "sr_market_spot", active=market == "spot"),
                b("期货", "sr_market_futures", active=market == "futures"),
            ])

        gen_row: List[InlineKeyboardButton] = []
        for col_id, label, _ in self.general_display_fields:
            state_on = fields_state.get(col_id, True)
            show_label = label if state_on else f"❎{label}"
            gen_row.append(InlineKeyboardButton(show_label, callback_data=f"field_sr_toggle_{col_id}"))
        kb.append(gen_row)

        spec_row: List[InlineKeyboardButton] = []
        for col_id, label, _ in self.special_display_fields:
            state_on = fields_state.get(col_id, True)
            show_label = label if state_on else f"❎{label}"
            spec_row.append(InlineKeyboardButton(show_label, callback_data=f"field_sr_toggle_{col_id}"))
        kb.append(spec_row)

        general_sort = [("quote_volume", "成交额"), ("振幅", "振幅"), ("成交笔数", "成交笔数"), ("主动买卖比", "主动买卖比"), ("price", "价格")]
        kb.append([
            b(lbl, f"sr_sort_field_{fid}", active=(current_sort_field == fid))
            for fid, lbl in general_sort
        ])

        special_sort = [
            ("distance_support", "距支撑%"),
            ("distance_resist", "距阻力%"),
            ("distance_pct", "距关键位%"),
            ("break_price", "突破价"),
            ("signal", "信号"),
        ]
        kb.append([
            b(lbl, f"sr_sort_field_{fid}", active=(current_sort_field == fid))
            for fid, lbl in special_sort
        ])
        periods = ["1m", "5m", "15m", "1h", "4h", "1d", "1w"]
        kb.append([b(p, f"sr_period_{p}", active=p == period) for p in periods])

        kb.append([
            b("降序", "sr_sort_desc", active=sort_order == "desc"),
            b("升序", "sr_sort_asc", active=sort_order == "asc"),
            b("10条", "sr_limit_10", active=current_limit == 10),
            b("20条", "sr_limit_20", active=current_limit == 20),
            b("30条", "sr_limit_30", active=current_limit == 30),
        ])

        kb.append([
            _btn_auto(None, "🏠主菜单", "ranking_menu"),
            _btn_auto(None, "🔄刷新", "sr_ranking_refresh"),
        ])

        return InlineKeyboardMarkup(kb)

    def _load_rows(self, period: str, sort_order: str, limit: int, sort_field: str, field_state: Dict[str, bool], lang: str | None = None) -> Tuple[List[List[str]], str]:
        items: List[Dict] = []
        try:
            metrics = self.provider.merge_with_base("支撑阻力榜单", period, base_fields=["当前价格", "成交额"])
            for row in metrics:
                sym = format_symbol(row.get("symbol") or row.get("交易对") or row.get("币种") or "")
                if not sym:
                    continue
                support = float(row.get("支撑位") or 0)
                resist = float(row.get("阻力位") or 0)
                price = float(row.get("price") or row.get("当前价格") or 0)
                if price <= 0:
                    continue  # 无价格无法计算距离
                break_price = resist or support or 0
                break_type = "阻力" if resist else ("支撑" if support else "-")
                strength_raw = row.get("强度等级")
                strength_map = {"强": 3.0, "中": 2.0, "弱": 1.0, None: 0.0}
                try:
                    strength_val = float(strength_raw)
                except Exception:
                    strength_val = strength_map.get(strength_raw, 0.0)

                # 优先使用扫描器写入的百分比列，其次现场计算
                dist_support = row.get("distance_support") or row.get("距支撑百分比")
                dist_resist = row.get("distance_resist") or row.get("距阻力百分比")
                dist_pct = row.get("distance_pct") or row.get("距关键位百分比")
                if dist_support is None and support > 0:
                    dist_support = abs(price - support) / price * 100
                if dist_resist is None and resist > 0:
                    dist_resist = abs(resist - price) / price * 100
                if dist_pct is None:
                    distances = [d for d in (dist_support, dist_resist) if d is not None]
                    dist_pct = min(distances) if distances else None

                items.append({
                    "symbol": sym,
                    "signal": break_type,
                    "strength": strength_val,
                    "price": price,
                    "break_price": break_price,
                    "break_type": break_type,
                    "quote_volume": float(row.get("quote_volume") or row.get("成交额") or 0),
                    "成交笔数": float(row.get("成交笔数") or row.get("交易次数") or 0),
                    "振幅": float(row.get("振幅") or 0),
                    "主动买卖比": float(row.get("主动买卖比") or 0),
                    "distance_support": dist_support,
                    "distance_resist": dist_resist,
                    "distance_pct": dist_pct,
                })
        except Exception as exc:  # pragma: no cover
            self._logger.warning("读取支撑阻力榜单失败: %s", exc)
            return [], _t("card.header.rank_symbol", lang=lang)

        reverse = sort_order != "asc"

        def _sort_val(item):
            val = item.get(sort_field)
            if val is None:
                # None 放末尾：降序用 -inf，升序用 +inf
                return float("-inf") if reverse else float("inf")
            return val

        items.sort(key=_sort_val, reverse=reverse)
        active_special = [f for f in self.special_display_fields if field_state.get(f[0], True)]
        active_general = [f for f in self.general_display_fields if field_state.get(f[0], True)]

        header_parts = [_t("card.header.rank", lang=lang), _t("card.header.symbol", lang=lang)] + [translate_field(lab, lang=lang) for _, lab, _ in active_special] + [translate_field(lab, lang=lang) for _, lab, _ in active_general]

        rows: List[List[str]] = []
        for idx, item in enumerate(items[:limit], 1):
            row: List[str] = [f"{idx}", item["symbol"]]
            for col_id, _, _ in active_special:
                val = item.get(col_id)
                if isinstance(val, (int, float)):
                    if col_id in {"distance_pct", "distance_support", "distance_resist"}:
                        row.append(f"{format_number(val, 2)}%")
                    else:
                        row.append(format_number(val, 2))
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
                    row.append(format_number(val, 4) if val else "-")
                elif isinstance(val, (int, float)):
                    row.append(format_number(val, 2))
                else:
                    row.append(str(val) if val not in (None, "") else "-")
            rows.append(row)
        return rows, "/".join(header_parts)

    # ---------- 工具 ----------
    def _ensure_field_state(self, h) -> Dict[str, bool]:
        state = h.user_states.get("sr_fields")
        if not state:
            state = {col: False for col, _, _ in self.general_display_fields + self.special_display_fields}
            # 默认开启：距支撑%、距阻力%；其余关闭
            for _on in {"distance_support", "distance_resist"}:
                if _on in state:
                    state[_on] = True
            h.user_states["sr_fields"] = state

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


CARD = 支撑阻力排行卡片()
