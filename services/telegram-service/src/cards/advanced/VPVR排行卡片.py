"""VPVR 成交量分布排行榜卡片（仅保留宽度百分比）"""

from __future__ import annotations

import logging
from typing import Dict, List, Tuple

from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from cards.data_provider import get_ranking_provider, format_symbol
from cards.i18n import btn_auto as _btn_auto, gettext as _t, resolve_lang, translate_field, format_sort_field
from cards.base import RankingCard


class VPVR排行卡片(RankingCard):
    FALLBACK = "card.vpvr.fallback"
    provider = get_ranking_provider()

    def __init__(self) -> None:
        super().__init__(
            card_id="vpvr_ranking",
            button_text="🏛️ VPVR",
            button_key="card.vpvr.btn",
            category="free",
            description="成交量分布偏离价值区榜单（宽度用百分比）",
            default_state={
                "vpvr_period": "15m",
                "vpvr_sort": "desc",
                "vpvr_limit": 10,
                "vpvr_sort_field": "value_area_width_pct",
                "vpvr_market": "futures",
                "vpvr_fields": {},
            },
            callback_prefixes=[
                "vpvr_ranking",
                "vpvr_",
                "vpvr_period_",
                "vpvr_sort_",
                "vpvr_limit_",
                "vpvr_sort_field_",
                "vpvr_market_",
                "field_vpvr_toggle_",
            ],
            priority=22,
        )
        self._logger = logging.getLogger(__name__)

        self.general_display_fields: List[Tuple[str, str, bool]] = [
            ("quote_volume", "成交额", False),
            ("振幅", "振幅", False),
            ("成交笔数", "成交笔数", False),
            ("主动买卖比", "主动买卖比", False),
            ("price", "价格", True),
        ]
        self.special_display_fields: List[Tuple[str, str, bool]] = [
            ("vpvr_price", "VPVR价", True),
            ("value_area_low", "下沿", False),
            ("value_area_high", "上沿", False),
            ("coverage", "覆盖率", True),
            ("value_area_width_pct", "宽度%", True),
            ("value_area_pos", "位置", True),
        ]

    # ===== 回调 =====
    async def handle_callback(self, update, context, services: Dict[str, object]) -> bool:
        query = update.callback_query
        if not query:
            return False
        h = services.get("user_handler")
        ensure = services.get("ensure_valid_text")
        if h is None:
            return False
        data = query.data or ""

        if data in (self.card_id, self.entry_callback, "vpvr_ranking_refresh"):
            await self._reply(query, h, ensure)
            return True
        if data == "vpvr_nop":
            return True
        if data.startswith("vpvr_market_"):
            h.user_states["vpvr_market"] = data.replace("vpvr_market_", "")
            await self._edit(query, h, ensure)
            return True
        if data.startswith("vpvr_sort_field_"):
            h.user_states["vpvr_sort_field"] = data.replace("vpvr_sort_field_", "")
            await self._edit(query, h, ensure)
            return True
        if data.startswith("vpvr_period_"):
            h.user_states["vpvr_period"] = data.replace("vpvr_period_", "")
            await self._edit(query, h, ensure)
            return True
        if data.startswith("vpvr_sort_"):
            h.user_states["vpvr_sort"] = data.replace("vpvr_sort_", "")
            await self._edit(query, h, ensure)
            return True
        if data.startswith("vpvr_limit_"):
            val = data.replace("vpvr_limit_", "")
            if val.isdigit():
                h.user_states["vpvr_limit"] = int(val)
                await self._edit(query, h, ensure)
                return True
            return False
        if data.startswith("field_vpvr_toggle_"):
            col = data.replace("field_vpvr_toggle_", "")
            fields_state = self._ensure_field_state(h)
            if col in fields_state:
                fields_state[col] = not fields_state[col]
                h.user_states["vpvr_fields"] = fields_state
            await self._edit(query, h, ensure)
            return True
        return False

    # ===== 渲染 =====
    async def _reply(self, query, h, ensure):
        lang = resolve_lang(query)
        text, kb = await self._build_payload(h, ensure, lang, query)
        await query.message.reply_text(text, reply_markup=kb, parse_mode="Markdown")

    async def _edit(self, query, h, ensure):
        lang = resolve_lang(query)
        text, kb = await self._build_payload(h, ensure, lang, query)
        await query.edit_message_text(text, reply_markup=kb, parse_mode="Markdown")

    async def _build_payload(self, h, ensure, lang: str = "zh_CN", update=None) -> Tuple[str, object]:
        period = h.user_states.get("vpvr_period", "15m")
        sort_order = h.user_states.get("vpvr_sort", "desc")
        limit = h.user_states.get("vpvr_limit", 10)
        allowed_fields = {f[0] for f in self.general_display_fields + self.special_display_fields}
        sort_field = h.user_states.get("vpvr_sort_field", "coverage")
        if sort_field not in allowed_fields:
            sort_field = "coverage"
            h.user_states["vpvr_sort_field"] = sort_field
        fields_state = self._ensure_field_state(h)

        rows, header = self._load_rows(period, sort_order, limit, sort_field, fields_state, lang)
        aligned = h.dynamic_align_format(rows) if rows else _t("data.no_data", lang=lang)
        time_info = h.get_current_time_display()
        sort_symbol = "🔽" if sort_order == "desc" else "🔼"
        display_sort_field = format_sort_field(sort_field, lang=lang, field_lists=[getattr(self, "general_display_fields", []), getattr(self, "special_display_fields", [])])
        text = (
            f'{_t("card.vpvr.title", lang=lang)}\n'
            f"{_t('card.common.update_time', lang=lang).format(time=time_info['full'])}\n"
            f"{_t('card.common.sort_info', lang=lang).format(period=period, field=display_sort_field, symbol=sort_symbol)}\n"
            f"{header}\n"
            f"```\n{aligned}\n```\n"
            f"{_t('card.vpvr.hint', lang=lang)}\n"
            f"{_t('card.common.last_update', lang=lang).format(time=time_info['full'])}"
        )
        if callable(ensure):
            text = ensure(text, _t(self.FALLBACK))
        kb = self._build_keyboard(h)
        return text, kb

    def _build_keyboard(self, h):
        fields_state = self._ensure_field_state(h)
        period = h.user_states.get("vpvr_period", "15m")
        sort_order = h.user_states.get("vpvr_sort", "desc")
        current_limit = h.user_states.get("vpvr_limit", 10)
        if current_limit not in (10, 20, 30):
            current_limit = 10
            h.user_states["vpvr_limit"] = 10
        current_sort_field = h.user_states.get("vpvr_sort_field", "coverage")
        market = h.user_states.get("vpvr_market", "futures")

        def b(label: str, data: str, active: bool = False, disabled: bool = False):

            if disabled:

                return InlineKeyboardButton(label, callback_data=data or 'nop')

            return _btn_auto(None, label, data, active=active)


        kb: List[List[InlineKeyboardButton]] = []

        show_market_row = False
        if show_market_row:
            kb.append([
                b("现货", "vpvr_market_spot", active=market == "spot"),
                b("期货", "vpvr_market_futures", active=market == "futures"),
            ])

        kb.append([
            InlineKeyboardButton(label if fields_state.get(col_id, True) else f"❎{label}", callback_data=f"field_vpvr_toggle_{col_id}")
            for col_id, label, _ in self.general_display_fields
        ])

        kb.append([
            InlineKeyboardButton(label if fields_state.get(col_id, col_id == "coverage") else f"❎{label}", callback_data=f"field_vpvr_toggle_{col_id}")
            for col_id, label, _ in self.special_display_fields
        ])

        general_sort = [("quote_volume", "成交额"), ("振幅", "振幅"), ("成交笔数", "成交笔数"), ("主动买卖比", "主动买卖比"), ("price", "价格")]
        kb.append([b(lbl, f"vpvr_sort_field_{fid}", active=(current_sort_field == fid)) for fid, lbl in general_sort])

        special_sort = [
            ("coverage", "覆盖率"),
            ("value_area_low", "下沿"),
            ("value_area_high", "上沿"),
            ("value_area_width_pct", "宽度%"),
            ("vpvr_price", "VPVR价"),
            ("value_area_pos", "位置"),
        ]
        kb.append([b(lbl, f"vpvr_sort_field_{fid}", active=(current_sort_field == fid)) for fid, lbl in special_sort])

        periods = ["1m", "5m", "15m", "1h", "4h", "1d", "1w"]
        kb.append([b(p, f"vpvr_period_{p}", active=p == period) for p in periods])

        kb.append([
            b("降序", "vpvr_sort_desc", active=sort_order == "desc"),
            b("升序", "vpvr_sort_asc", active=sort_order == "asc"),
            b("10条", "vpvr_limit_10", active=current_limit == 10),
            b("20条", "vpvr_limit_20", active=current_limit == 20),
            b("30条", "vpvr_limit_30", active=current_limit == 30),
        ])

        kb.append([
            _btn_auto(None, "🏠主菜单", "ranking_menu"),
            _btn_auto(None, "🔄刷新", "vpvr_ranking_refresh"),
        ])

        return InlineKeyboardMarkup(kb)

    # ===== 数据 =====
    def _load_rows(self, period: str, sort_order: str, limit: int, sort_field: str, field_state: Dict[str, bool], lang: str | None = None) -> Tuple[List[List[str]], str]:
        items: List[Dict] = []
        try:
            metrics = self.provider.merge_with_base("VPVR榜单", period, base_fields=["当前价格", "成交额"])
            for row in metrics:
                sym = format_symbol(row.get("symbol") or row.get("交易对") or row.get("币种") or "")
                if not sym:
                    continue
                coverage = float(row.get("价值区覆盖率") or 0)
                price = float(row.get("price") or row.get("当前价格") or 0)

                def _to_float(v):
                    try:
                        if v in (None, ""):
                            return None
                        return float(v)
                    except Exception:
                        return None

                va_low = _to_float(row.get("价值区下沿") or row.get("value_area_low"))
                va_high = _to_float(row.get("价值区上沿") or row.get("value_area_high"))
                va_width_pct = _to_float(row.get("价值区宽度百分比") or row.get("value_area_width_pct"))
                vpvr_price = float(row.get("VPVR价格") or 0)
                if (va_width_pct is None or va_width_pct == 0) and va_low is not None and va_high is not None and vpvr_price:
                    va_width_pct = (va_high - va_low) / vpvr_price * 100

                pos_txt = row.get("价值区位置") or row.get("value_area_pos") or row.get("位置") or "-"
                if (not pos_txt or pos_txt == "-") and va_low is not None and va_high is not None and price:
                    if price > va_high:
                        pos_txt = "价值区上"
                    elif price < va_low:
                        pos_txt = "价值区下"
                    else:
                        pos_txt = "价值区内"

                items.append({
                    "symbol": sym,
                    "vpvr_price": vpvr_price,
                    "value_area_low": va_low if va_low is not None else 0.0,
                    "value_area_high": va_high if va_high is not None else 0.0,
                    "value_area_width_pct": va_width_pct if va_width_pct is not None else 0.0,
                    "coverage": coverage,
                    "price": price,
                    "value_area_pos": pos_txt,
                    "quote_volume": float(row.get("quote_volume") or 0),
                    "振幅": float(row.get("振幅") or 0),
                    "成交笔数": float(row.get("成交笔数") or 0),
                    "主动买卖比": float(row.get("主动买卖比") or 0),
                })
        except Exception as exc:  # pragma: no cover
            self._logger.warning("读取 VPVR 榜单失败: %s", exc)
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
                if col_id == "value_area_pos":
                    row.append(str(val) if val not in (None, "") else "-")
                elif isinstance(val, (int, float)):
                    if col_id == "coverage":
                        row.append(f"{val:.3f}")
                    elif col_id == "value_area_width_pct":
                        row.append(f"{val:.2f}%")
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

    # ===== 工具 =====
    def _ensure_field_state(self, h) -> Dict[str, bool]:
        state = h.user_states.get("vpvr_fields")
        if not state:
            state = {}
            for col, _, _ in self.general_display_fields + self.special_display_fields:
                state[col] = False
            # 默认仅开启：宽度%、位置，其余均关闭（用户可自行打开）
            for _on in {"value_area_width_pct", "value_area_pos"}:
                if _on in state:
                    state[_on] = True
            h.user_states["vpvr_fields"] = state
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


CARD = VPVR排行卡片()
