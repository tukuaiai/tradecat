"""成交量排行榜卡片（对齐 KDJ 模板开关与排序逻辑）

数据源：基础数据同步器.py
字段：成交量、振幅、成交笔数、主动买卖比、价格
"""

from __future__ import annotations

import logging
from typing import Dict, List, Tuple

from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from cards.base import RankingCard, format_number
from cards.data_provider import get_ranking_provider, format_symbol
from cards.i18n import btn_auto as _btn_auto, gettext as _t, resolve_lang
from cards.排行榜服务 import DEFAULT_PERIODS, normalize_period


class VolumeRankingCard(RankingCard):
    FALLBACK = "card.volume.fallback"
    provider = get_ranking_provider()

    def __init__(self) -> None:
        super().__init__(
            card_id="volume_ranking",
            button_text="📊 成交量",
            button_key="card.volume.btn",
            category="free",
            description="按成交量排序的榜单",
            default_state={
                "volume_period": "15m",
                "volume_sort": "desc",
                "volume_limit": 10,
                # 成交量作为专用字段默认排序
                "volume_sort_field": "base_volume",
                "volume_fields": {},
            },
            callback_prefixes=[
                "volume_ranking",
                "volume_period_",
                "volume_sort_",
                "volume_limit_",
                "volume_sort_field_",
                "field_volume_toggle_",
            ],
            priority=1,
            entry_callback="volume_ranking",
        )
        self._logger = logging.getLogger(__name__)

        # 对齐 KDJ 模板的字段开关（col_id, label, is_core）
        # 通用字段：与文档保持一致，默认都可关，价格默认开启
        self.general_display_fields: List[Tuple[str, str, bool]] = [
            ("quote_volume", "成交额", False),
            ("振幅", "振幅", False),
            ("成交笔数", "成交笔数", False),
            ("主动买卖比", "主动买卖比", False),
            ("price", "价格", False),  # 可开关，默认开启在 _ensure_field_state
        ]

        # 专用字段：成交量（币本位），与通用分行展示/排序
        self.special_display_fields: List[Tuple[str, str, bool]] = [
            ("base_volume", "成交量", False),  # 默认开启在 _ensure_field_state
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
        if data in (self.card_id, self.entry_callback, "volume_ranking_refresh"):
            await self._reply(query, h, ensure)
            return True
        # 排序字段前缀与排序方向前缀存在包含关系，需先匹配字段再匹配方向
        if data.startswith("volume_sort_field_"):
            h.user_states["volume_sort_field"] = data.replace("volume_sort_field_", "")
            await self._edit(query, h, ensure)
            return True
        if data.startswith("volume_period_"):
            h.user_states["volume_period"] = data.replace("volume_period_", "")
            await self._edit(query, h, ensure)
            return True
        if data.startswith("volume_sort_"):
            sort_val = data.replace("volume_sort_", "")
            if sort_val in {"asc", "desc"}:
                h.user_states["volume_sort"] = sort_val
            await self._edit(query, h, ensure)
            return True
        if data.startswith("volume_limit_"):
            val = data.replace("volume_limit_", "")
            if val.isdigit():
                h.user_states["volume_limit"] = int(val)
                await self._edit(query, h, ensure)
                return True
            return False
        if data.startswith("field_volume_toggle_"):
            col = data.replace("field_volume_toggle_", "")
            fields_state = self._ensure_field_state(h)
            if col in fields_state:
                fields_state[col] = not fields_state[col]
                h.user_states["volume_fields"] = fields_state
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
        period = h.user_states.get("volume_period", "15m")
        sort_order = h.user_states.get("volume_sort", "desc")
        limit = h.user_states.get("volume_limit", 10)
        sort_field = h.user_states.get("volume_sort_field", "base_volume")
        fields_state = self._ensure_field_state(h)

        allowed_fields = {f[0] for f in self.general_display_fields + self.special_display_fields}
        if sort_field not in allowed_fields:
            sort_field = "base_volume"
            h.user_states["volume_sort_field"] = sort_field

        # 调试输出
        print(f"[DEBUG] 交易量卡片 - sort_field: {sort_field}, fields_state: {fields_state}")

        period = normalize_period(period, DEFAULT_PERIODS, default="15m")
        h.user_states["volume_period"] = period

        items = self._load_rows(period, lang)
        reverse = sort_order != "asc"
        items.sort(key=lambda x: x.get(sort_field, 0), reverse=reverse)

        # 修复：使用与 _build_keyboard 相同的默认值计算方式
        active_general = [f for f in self.general_display_fields if fields_state.get(f[0], f[2] or False)]
        active_special = [f for f in self.special_display_fields if fields_state.get(f[0], True)]  # 特殊字段默认True
        lang = resolve_lang(update, lang)
        from cards.i18n import translate_field
        header_parts = [_t("card.header.rank", lang=lang), _t("card.header.symbol", lang=lang)]
        header_parts += [translate_field(lab, lang=lang) for _, lab, _ in active_special]
        header_parts += [translate_field(lab, lang=lang) for _, lab, _ in active_general]

        rows: List[List[str]] = []
        for idx, item in enumerate(items[:limit], 1):
            row: List[str] = [f"{idx}", item["symbol"]]
            # 专用列（成交量）
            for col_id, _, _ in active_special:
                val = item.get(col_id)
                if col_id == "base_volume":
                    row.append(self._format_volume(val))
                elif isinstance(val, (int, float)):
                    row.append(format_number(val, 2))
                else:
                    row.append(str(val) if val not in (None, "") else "-")
            # 通用列
            for col_id, _, _ in active_general:
                val = item.get(col_id)
                if col_id == "quote_volume":
                    row.append(self._format_volume(val))
                elif col_id == "price":
                    row.append(format_number(val, 4))
                elif col_id == "振幅":
                    pct = (val * 100) if isinstance(val, (int, float)) and val <= 5 else val
                    row.append(f"{pct:.2f}%" if isinstance(pct, (int, float)) else "-")
                elif isinstance(val, (int, float)):
                    row.append(format_number(val, 2))
                else:
                    row.append(str(val) if val not in (None, "") else "-")
            rows.append(row)

        aligned = h.dynamic_align_format(rows) if rows else _t("data.no_data", lang=lang)
        time_info = h.get_current_time_display()
        sort_symbol = "🔽" if sort_order == "desc" else "🔼"
        # Markdown 模式下需转义下划线，避免出现“Can't parse entities”错误
        safe_sort_field = str(sort_field).replace("_", "\\_")

        text = (
            f"{_t('card.volume.title', lang=lang)}\n"
            f"{_t('card.common.update_time', lang=lang).format(time=time_info['full'])}\n"
            f"{_t('card.common.sort_info', lang=lang).format(period=period, field=safe_sort_field, symbol=sort_symbol)}\n"
            f"{'/'.join(header_parts)}\n"
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
        period = h.user_states.get("volume_period", "15m")
        sort_order = h.user_states.get("volume_sort", "desc")
        current_limit = h.user_states.get("volume_limit", 10)
        sort_field = h.user_states.get("volume_sort_field", "base_volume")

        def b(label: str, data: str, active: bool = False, disabled: bool = False):

            if disabled:

                return InlineKeyboardButton(label, callback_data=data or 'nop')

            return _btn_auto(None, label, data, active=active)


        kb: List[List[InlineKeyboardButton]] = []

        # 行1 通用字段开关
        gen_row: List[InlineKeyboardButton] = []
        for col_id, label, is_core in self.general_display_fields:
            state_on = fields_state.get(col_id, is_core or False)
            show_label = label if state_on or is_core else f"❎{label}"
            gen_row.append(
                InlineKeyboardButton(
                    show_label,
                    callback_data="volume_nop" if is_core else f"field_volume_toggle_{col_id}",
                )
            )
        kb.append(gen_row)

        # 行2 专用字段开关
        spec_row: List[InlineKeyboardButton] = []
        for col_id, label, _ in self.special_display_fields:
            state_on = fields_state.get(col_id, True)
            show_label = label if state_on else f"❎{label}"
            spec_row.append(InlineKeyboardButton(show_label, callback_data=f"field_volume_toggle_{col_id}"))
        kb.append(spec_row)

        # 行3 通用排序字段
        sort_options = [(cid, lab) for cid, lab, _ in self.general_display_fields]
        sort_buttons = [b(lbl, f"volume_sort_field_{cid}", active=(sort_field == cid)) for cid, lbl in sort_options]
        if sort_buttons:
            kb.append(sort_buttons)

        # 行4 专用排序字段
        spec_sort = [(cid, lab) for cid, lab, _ in self.special_display_fields]
        spec_buttons = [b(lbl, f"volume_sort_field_{cid}", active=(sort_field == cid)) for cid, lbl in spec_sort]
        if spec_buttons:
            kb.append(spec_buttons)

        # 行5 周期
        kb.append([b(p, f"volume_period_{p}", active=p == period) for p in DEFAULT_PERIODS])

        # 行6 排序方向 + 条数
        kb.append([
            b("降序", "volume_sort_desc", active=sort_order == "desc"),
            b("升序", "volume_sort_asc", active=sort_order == "asc"),
            b("10条", "volume_limit_10", active=current_limit == 10),
            b("20条", "volume_limit_20", active=current_limit == 20),
            b("30条", "volume_limit_30", active=current_limit == 30),
        ])

        # 行7 主菜单 + 刷新
        kb.append([
            _btn_auto(None, "🏠主菜单", "ranking_menu"),
            _btn_auto(None, "🔄刷新", "volume_ranking_refresh"),
        ])

        return InlineKeyboardMarkup(kb)

    # ---------- 数据读取 ----------
    def _load_rows(self, period: str, lang: str | None = None) -> List[Dict]:
        items: List[Dict] = []
        try:
            base_map = self.provider.fetch_base(period)
            for sym, r in base_map.items():
                base_vol = float(r.get("成交量") or r.get("base_volume") or 0)
                price = float(r.get("当前价格") or r.get("price") or 0)
                quote_vol = float(r.get("成交额") or (base_vol * price) or 0)
                items.append({
                    "symbol": format_symbol(sym),
                    "base_volume": base_vol,
                    "quote_volume": quote_vol,
                    "振幅": float(r.get("振幅") or 0),
                    "成交笔数": float(r.get("成交笔数") or r.get("交易次数") or 0),
                    "主动买卖比": float(r.get("主动买卖比") or 0),
                    "price": price,
                })
        except Exception as exc:
            self._logger.warning("读取成交量数据失败: %s", exc)
        return items

    # ---------- 字段状态 ----------
    def _ensure_field_state(self, h) -> Dict[str, bool]:
        state = h.user_states.get("volume_fields") or {}
        if not state:
            for col, _, is_core in self.general_display_fields + self.special_display_fields:
                # price、base_volume 默认开启，其余按模板默认关闭
                if col in ("price", "base_volume"):
                    state[col] = True
                else:
                    state[col] = True if is_core else False
            h.user_states["volume_fields"] = state
        return state

    # ---------- 工具 ----------
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
    def _format_price(price: float) -> str:
        if not price:
            return "-"
        if price >= 1000:
            return f"${price:,.0f}"
        if price >= 1:
            return f"${price:.4f}"
        return f"${price:.6f}"


CARD = VolumeRankingCard()
