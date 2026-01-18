"""EMA 收敛/发散排行榜卡片

数据源：market_data.db 表 `G，C点扫描器.py`（含 EMA7/25/99、带宽评分、趋势方向）
排序：默认按带宽评分降序；周期可切换；TOP10/20/30。
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


class EMA排行卡片(RankingCard):
    FALLBACK = "card.ema.fallback"

    def __init__(self) -> None:
        super().__init__(
            card_id="ema_ranking",
            button_text="🧮 EMA",
            button_key="card.ema.btn",
            category="free",
            description="EMA 区间收敛/发散强度榜",
            default_state={
                "ema_period": "15m",
                "ema_sort": "desc",
                "ema_limit": 10,
                # 默认按带宽评分排序，展示收敛/发散强度
                "ema_sort_field": "bandwidth",
                "ema_market": "futures",
                "ema_fields": {},
            },
            callback_prefixes=[
                "ema_ranking",
                "ema_",  # 通用前缀
                "ema_period_",
                "ema_sort_",
                "ema_limit_",
                "ema_sort_field_",
                "ema_market_",
                "field_ema_toggle_",
            ],
            priority=21,
        )
        self._logger = logging.getLogger(__name__)
        # 统一数据访问入口
        self.provider = get_ranking_provider()

        # 与 KDJ 卡片保持一致的字段配置：默认仅价格/方向开启，其他可切换
        self.general_display_fields: List[Tuple[str, str, bool]] = [
            ("quote_volume", "成交额", False),
            ("振幅", "振幅", False),
            ("成交笔数", "成交笔数", False),
            ("主动买卖比", "主动买卖比", False),
            ("price", "价格", False),
        ]
        self.special_display_fields: List[Tuple[str, str, bool]] = [
            ("ema7", "EMA7", False),
            ("ema25", "EMA25", False),
            ("ema99", "EMA99", False),
            ("bandwidth", "带宽评分", False),
            ("trend", "趋势", False),
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
        if data in (self.card_id, self.entry_callback, "ema_ranking_refresh"):
            await self._reply(query, h, ensure)
            return True
        if data == "ema_nop":
            return True
        if data.startswith("ema_market_"):
            h.user_states["ema_market"] = data.replace("ema_market_", "")
            await self._edit(query, h, ensure)
            return True
        if data.startswith("ema_sort_field_"):
            h.user_states["ema_sort_field"] = data.replace("ema_sort_field_", "")
            await self._edit(query, h, ensure)
            return True
        if data.startswith("ema_period_"):
            h.user_states["ema_period"] = data.replace("ema_period_", "")
            await self._edit(query, h, ensure)
            return True
        if data.startswith("ema_sort_"):
            h.user_states["ema_sort"] = data.replace("ema_sort_", "")
            await self._edit(query, h, ensure)
            return True
        if data.startswith("ema_limit_"):
            val = data.replace("ema_limit_", "")
            if val.isdigit():
                h.user_states["ema_limit"] = int(val)
                await self._edit(query, h, ensure)
                return True
            return False
        if data.startswith("field_ema_toggle_"):
            col = data.replace("field_ema_toggle_", "")
            fields_state = self._ensure_field_state(h)
            if col in fields_state:
                fields_state[col] = not fields_state[col]
                h.user_states["ema_fields"] = fields_state
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
        period = h.user_states.get("ema_period", "15m")
        sort_order = h.user_states.get("ema_sort", "desc")
        limit = h.user_states.get("ema_limit", 10)
        allowed_fields = {f[0] for f in self.general_display_fields + self.special_display_fields}
        sort_field = h.user_states.get("ema_sort_field", "bandwidth")
        if sort_field not in allowed_fields:
            sort_field = "bandwidth"
            h.user_states["ema_sort_field"] = sort_field
        fields_state = self._ensure_field_state(h)
        # 只使用指定周期的数据；如果没有数据则显示“暂无数据”
        rows, header = self._load_rows(period, sort_order, limit, sort_field, fields_state, lang)
        aligned = h.dynamic_align_format(rows) if rows else _t("data.no_data", lang=lang)
        time_info = h.get_current_time_display()
        sort_symbol = "🔽" if sort_order == "desc" else "🔼"
        display_sort_field = format_sort_field(sort_field, lang=lang, field_lists=[getattr(self, "general_display_fields", []), getattr(self, "special_display_fields", [])])
        text = (
            f"{_t('card.ema.title', lang=lang)}\n"
            f"{_t('card.common.update_time', lang=lang).format(time=time_info['full'])}\n"
            f"{_t('card.common.sort_info', lang=lang).format(period=period, field=display_sort_field, symbol=sort_symbol)}\n"
            f"{header}\n"
            f"```\n{aligned}\n```\n"
            f"{_t('card.ema.hint', lang=lang)}\n"
            f"{_t('card.common.last_update', lang=lang).format(time=time_info['full'])}"
        )
        if callable(ensure):
            text = ensure(text, _t(self.FALLBACK))
        kb = self._build_keyboard(h)
        return text, kb

    def _build_keyboard(self, h):
        fields_state = self._ensure_field_state(h)
        period = h.user_states.get("ema_period", "15m")
        sort_order = h.user_states.get("ema_sort", "desc")
        current_limit = h.user_states.get("ema_limit", 10)
        current_sort_field = h.user_states.get("ema_sort_field", "bandwidth")
        market = h.user_states.get("ema_market", "futures")

        def b(label: str, data: str, active: bool = False, disabled: bool = False):

            if disabled:

                return InlineKeyboardButton(label, callback_data=data or 'nop')

            return _btn_auto(None, label, data, active=active)


        kb: List[List[InlineKeyboardButton]] = []

        show_market_row = False
        if show_market_row:
            kb.append([
                b("现货", "ema_market_spot", active=market == "spot"),
                b("期货", "ema_market_futures", active=market == "futures"),
            ])

        # 通用字段开关行（关闭时显示 ❎ 前缀）
        gen_row: List[InlineKeyboardButton] = []
        for col_id, label, is_core in self.general_display_fields:
            state_on = fields_state.get(col_id, True if is_core else False)
            show_label = label if state_on or is_core else f"❎{label}"
            gen_row.append(
                InlineKeyboardButton(
                    show_label,
                    callback_data="ema_nop" if is_core else f"field_ema_toggle_{col_id}",
                )
            )
        kb.append(gen_row)

        # 专用字段开关行
        spec_row: List[InlineKeyboardButton] = []
        for col_id, label, is_core in self.special_display_fields:
            state_on = fields_state.get(col_id, True if is_core else False)
            show_label = label if state_on or is_core else f"❎{label}"
            spec_row.append(
                InlineKeyboardButton(
                    show_label,
                    callback_data="ema_nop" if is_core else f"field_ema_toggle_{col_id}",
                )
            )
        kb.append(spec_row)

        general_sort = [("quote_volume", "成交额"), ("振幅", "振幅"), ("成交笔数", "成交笔数"), ("主动买卖比", "主动买卖比"), ("price", "价格")]
        kb.append([
            b(lbl, f"ema_sort_field_{fid}", active=(current_sort_field == fid))
            for fid, lbl in general_sort
        ])

        special_sort = [("ema7", "EMA7"), ("ema25", "EMA25"), ("ema99", "EMA99"), ("bandwidth", "带宽评分"), ("trend", "趋势")]
        kb.append([
            b(lbl, f"ema_sort_field_{fid}", active=(current_sort_field == fid))
            for fid, lbl in special_sort
        ])
        periods = ["1m", "5m", "15m", "1h", "4h", "1d", "1w"]
        kb.append([b(p, f"ema_period_{p}", active=p == period) for p in periods])

        kb.append([
            b("降序", "ema_sort_desc", active=sort_order == "desc"),
            b("升序", "ema_sort_asc", active=sort_order == "asc"),
            b("10条", "ema_limit_10", active=current_limit == 10),
            b("20条", "ema_limit_20", active=current_limit == 20),
            b("30条", "ema_limit_30", active=current_limit == 30),
        ])

        kb.append([
            _btn_auto(None, "🏠主菜单", "ranking_menu"),
            _btn_auto(None, "🔄刷新", "ema_ranking_refresh"),
        ])

        return InlineKeyboardMarkup(kb)

    def _load_rows(self, period: str, sort_order: str, limit: int, sort_field: str, field_state: Dict[str, bool], lang: str | None = None) -> Tuple[List[List[str]], str]:
        items: List[Dict] = []
        try:
            metrics = self.provider.merge_with_base("G，C点扫描器.py", period, base_fields=["价格", "成交额"])
            for row in metrics:
                row_period = (row.get("周期") or row.get("period") or "").strip()
                if row_period.lower() != period.lower():
                    continue
                sym = (row.get("币种") or row.get("symbol") or row.get("交易对") or "").strip().upper()
                if not sym:
                    continue
                items.append({
                    "symbol": sym,
                    "price": self._to_float(row, ["price", "价格", "当前价格", "最新价格"]),
                    "ema7": self._to_float(row, ["EMA7", "ema7"]),
                    "ema25": self._to_float(row, ["EMA25", "ema25"]),
                    "ema99": self._to_float(row, ["EMA99", "ema99"]),
                    "bandwidth": self._to_float(row, ["带宽评分", "bandwidth"]),
                    "trend": row.get("趋势方向") or row.get("trend") or "-",
                    "quote_volume": self._to_float(row, ["quote_volume", "成交额"]),
                    "振幅": self._to_float(row, ["振幅"]),
                    "成交笔数": self._to_float(row, ["成交笔数", "交易次数"]),
                    "主动买卖比": self._to_float(row, ["主动买卖比"]),
                })
        except Exception as exc:  # pragma: no cover
            self._logger.warning("读取收敛发散榜单失败: %s", exc)
            return [], _t("card.header.rank_symbol", lang=lang)

        reverse = sort_order != "asc"
        items.sort(key=lambda x: x.get(sort_field, 0), reverse=reverse)
        active_special = [f for f in self.special_display_fields if field_state.get(f[0], f[2] or False)]
        active_general = [f for f in self.general_display_fields if field_state.get(f[0], f[2] or False)]

        header_parts = [_t("card.header.rank", lang=lang), _t("card.header.symbol", lang=lang)] + [translate_field(lab, lang=lang) for _, lab, _ in active_special] + [translate_field(lab, lang=lang) for _, lab, _ in active_general]

        rows: List[List[str]] = []
        for idx, item in enumerate(items[:limit], 1):
            # 展示层去掉 USDT 后缀，保持与其他卡片一致
            display_symbol = format_symbol(item["symbol"])
            row: List[str] = [f"{idx}", display_symbol]
            for col_id, _, _ in active_special:
                val = item.get(col_id)
                if isinstance(val, (int, float)):
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

    @staticmethod
    def _to_float(row: Dict, keys: List[str]) -> float:
        for k in keys:
            v = row.get(k)
            if v in (None, ""):
                continue
            try:
                return float(v)
            except Exception:
                continue
        return 0.0

    # ---------- 工具 ----------
    def _ensure_field_state(self, h) -> Dict[str, bool]:
        state = h.user_states.get("ema_fields")
        if not state:
            state = {}
            # 仅保留“带宽评分”“趋势”默认开启，其余字段默认关闭
            preferred_on = {"bandwidth", "trend"}
            for col, _, _ in self.general_display_fields:
                state[col] = col in preferred_on
            for col, _, _ in self.special_display_fields:
                state[col] = col in preferred_on
            # 全局默认关闭的通用字段（仅初始化时执行）
            for _off in {"quote_volume", "振幅", "成交笔数", "主动买卖比"}:
                if _off in state:
                    state[_off] = False
            h.user_states["ema_fields"] = state

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


CARD = EMA排行卡片()
