"""期货情绪聚合：合约持仓量/变动排行榜卡片

数据源：SQLite `期货情绪聚合表.py`（最新一根），字段：持仓金额/持仓变动/持仓变动%/市场占比 等。
展示：默认 15m，降序按持仓金额；支持开关与排序切换。
"""

from __future__ import annotations

import logging
from typing import Dict, List, Tuple

from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from cards.base import RankingCard
from cards.data_provider import get_ranking_provider, format_symbol
from cards.i18n import btn_auto as _btn_auto, gettext as _t, resolve_lang, translate_field, format_sort_field


class FuturesOIRankingCard(RankingCard):
    """🐋 合约持仓榜：关注持仓规模与变动速度"""

    FALLBACK = "card.futures_sentiment.fallback"
    provider = get_ranking_provider()

    SHOW_MARKET_SWITCH = False
    DEFAULT_MARKET = "futures"

    def __init__(self) -> None:
        super().__init__(
            card_id="futures_oi_ranking",
            button_text="🐋 持仓聚合",
            button_key="card.oi_aggregate.btn",
            category="free",
            description="期货合约持仓量/变动排行榜，基于期货情绪聚合表",
            default_state={
                "oi_period": "15m",
                "oi_sort": "desc",
                "oi_limit": 10,
                "oi_sort_field": "oi_value",
                "oi_market": self.DEFAULT_MARKET,
                "oi_fields": {},
            },
            callback_prefixes=[
                "futures_oi_ranking",
                "oi_period_",
                "oi_sort_",
                "oi_limit_",
                "oi_sort_field_",
                "oi_market_",
                "field_oi_toggle_",
            ],
            priority=22,
        )
        self._logger = logging.getLogger(__name__)

        # 通用字段（基础行情透传）
        self.general_display_fields: List[Tuple[str, str, bool]] = [
            ("quote_volume", "成交额", False),
            ("振幅", "振幅", False),
            ("成交笔数", "成交笔数", False),
            ("主动买卖比", "主动买卖比", False),
            ("price", "价格", False),
        ]

        # 专用字段（持仓聚合专属）
        self.special_display_fields: List[Tuple[str, str, bool]] = [
            ("oi_value", "持仓金额", False),
            ("oi_change", "持仓变动", False),
            ("oi_change_pct", "持仓变动%", False),
            ("market_share", "市场占比", False),
        ]

    # ========= 回调处理 =========
    async def handle_callback(self, update, context, services: Dict[str, object]) -> bool:
        query = update.callback_query
        if not query:
            return False
        h = services.get("user_handler")
        ensure = services.get("ensure_valid_text")
        if h is None:
            return False

        data = query.data or ""

        if data in (self.card_id, self.entry_callback, "futures_oi_ranking_refresh"):
            await self._reply(query, h, ensure)
            return True
        if data == "oi_nop":
            return True

        # 排序字段优先匹配，避免与 sort_ 前缀冲突
        if data.startswith("oi_sort_field_"):
            h.user_states["oi_sort_field"] = data.replace("oi_sort_field_", "")
            await self._edit(query, h, ensure)
            return True

        if data.startswith("oi_market_"):
            h.user_states["oi_market"] = data.replace("oi_market_", "")
            await self._edit(query, h, ensure)
            return True

        if data.startswith("oi_period_"):
            h.user_states["oi_period"] = data.replace("oi_period_", "")
            await self._edit(query, h, ensure)
            return True

        if data.startswith("oi_sort_"):
            h.user_states["oi_sort"] = data.replace("oi_sort_", "")
            await self._edit(query, h, ensure)
            return True

        if data.startswith("oi_limit_"):
            val = data.replace("oi_limit_", "")
            if val.isdigit():
                h.user_states["oi_limit"] = int(val)
                await self._edit(query, h, ensure)
                return True
            return False

        if data.startswith("field_oi_toggle_"):
            col = data.replace("field_oi_toggle_", "")
            fields_state = self._ensure_field_state(h)
            if col in fields_state:
                fields_state[col] = not fields_state[col]
                h.user_states["oi_fields"] = fields_state
            await self._edit(query, h, ensure)
            return True

        return False

    # ========= 渲染 =========
    async def _reply(self, query, h, ensure):
        lang = resolve_lang(query)
        text, kb = await self._build_payload(h, ensure, lang, query)
        await query.message.reply_text(text, reply_markup=kb, parse_mode="Markdown")

    async def _edit(self, query, h, ensure):
        lang = resolve_lang(query)
        text, kb = await self._build_payload(h, ensure, lang, query)
        await query.edit_message_text(text, reply_markup=kb, parse_mode="Markdown")

    async def _build_payload(self, h, ensure, lang: str = "zh_CN", update=None) -> Tuple[str, object]:
        period = h.user_states.get("oi_period", "15m")
        sort_order = h.user_states.get("oi_sort", "desc")
        limit = h.user_states.get("oi_limit", 10)
        sort_field = h.user_states.get("oi_sort_field", "oi_value")
        fields_state = self._ensure_field_state(h)

        rows, header = self._load_rows(period, sort_order, limit, sort_field, fields_state, lang)
        aligned = h.dynamic_align_format(rows) if rows else _t("data.no_data", lang=lang)

        sort_symbol = "🔽" if sort_order == "desc" else "🔼"
        display_sort_field = format_sort_field(sort_field, lang=lang, field_lists=[getattr(self, "general_display_fields", []), getattr(self, "special_display_fields", [])])
        time_info = h.get_current_time_display()

        text = (
            f'{_t("card.oi_aggregate.title", lang=lang)}\n'
            f"{_t('card.common.update_time', lang=lang).format(time=time_info['full'])}\n"
            f"{_t('card.common.sort_info', lang=lang).format(period=period, field=display_sort_field, symbol=sort_symbol)}\n"
            f"{header}\n"
            "```\n"
            f"{aligned}\n"
            "```\n"
            f'{_t("card.oi_aggregate.hint", lang=lang)}\n'
            f"{_t('card.common.last_update', lang=lang).format(time=time_info['full'])}"
        )
        if callable(ensure):
            text = ensure(text, _t(self.FALLBACK))
        kb = self._build_keyboard(h)
        return text, kb

    def _build_keyboard(self, h):
        fields_state = self._ensure_field_state(h)
        period = h.user_states.get("oi_period", "15m")
        sort_order = h.user_states.get("oi_sort", "desc")
        current_limit = h.user_states.get("oi_limit", 10)
        current_sort_field = h.user_states.get("oi_sort_field", "oi_value")
        market = h.user_states.get("oi_market", self.DEFAULT_MARKET)

        def b(label: str, data: str, active: bool = False, disabled: bool = False):

            if disabled:

                return InlineKeyboardButton(label, callback_data=data or 'nop')

            return _btn_auto(None, label, data, active=active)


        kb: List[List[InlineKeyboardButton]] = []

        # 行1 市场（仅当需要切换时展示）
        if self.SHOW_MARKET_SWITCH:
            kb.append([
                b("现货", "oi_market_spot", active=market == "spot"),
                b("期货", "oi_market_futures", active=market == "futures"),
            ])

        # 行2 通用字段开关
        gen_row: List[InlineKeyboardButton] = []
        for col_id, label, _ in self.general_display_fields:
            state_on = fields_state.get(col_id, True)
            show_label = label if state_on else f"❎{label}"
            gen_row.append(InlineKeyboardButton(show_label, callback_data=f"field_oi_toggle_{col_id}"))
        kb.append(gen_row)

        # 行3 专用字段开关
        spec_row: List[InlineKeyboardButton] = []
        for col_id, label, _ in self.special_display_fields:
            state_on = fields_state.get(col_id, True)
            show_label = label if state_on else f"❎{label}"
            spec_row.append(InlineKeyboardButton(show_label, callback_data=f"field_oi_toggle_{col_id}"))
        kb.append(spec_row)

        # 行4 通用排序
        kb.append([
            b(lbl, f"oi_sort_field_{fid}", active=(current_sort_field == fid))
            for fid, lbl, _ in self.general_display_fields
        ])

        # 行5 专用排序
        kb.append([
            b(lbl, f"oi_sort_field_{fid}", active=(current_sort_field == fid))
            for fid, lbl, _ in self.special_display_fields
        ])

        # 行6 周期
        periods = ["1m", "5m", "15m", "1h", "4h", "1d", "1w"]
        kb.append([b(p, f"oi_period_{p}", active=p == period) for p in periods])

        # 行7 排序方向 + 条数
        kb.append([
            b("降序", "oi_sort_desc", active=sort_order == "desc"),
            b("升序", "oi_sort_asc", active=sort_order == "asc"),
            b("10条", "oi_limit_10", active=current_limit == 10),
            b("20条", "oi_limit_20", active=current_limit == 20),
            b("30条", "oi_limit_30", active=current_limit == 30),
        ])

        # 行8 主控
        kb.append([
            _btn_auto(None, "🏠主菜单", "ranking_menu"),
            _btn_auto(None, "🔄刷新", "futures_oi_ranking_refresh"),
        ])

        return InlineKeyboardMarkup(kb)

    # ========= 数据加载 =========
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
            metrics = self.provider.merge_with_base(
                "期货情绪聚合表.py",
                period,
                base_fields=["数据时间"],
            )
            for row in metrics:
                sym = format_symbol(row.get("symbol") or row.get("交易对") or "")
                if not sym:
                    continue

                oi_value = float(row.get("持仓金额") or 0)
                oi_change = float(row.get("持仓变动") or 0)
                oi_change_pct = float(row.get("持仓变动%") or 0)
                market_share = float(row.get("市场占比") or 0)

                items.append({
                    "symbol": sym,
                    "oi_value": oi_value,
                    "oi_change": oi_change,
                    "oi_change_pct": oi_change_pct,
                    "market_share": market_share,
                    # 通用字段
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
            # 专用列
            for col_id, _, _ in active_special:
                val = item.get(col_id)
                if col_id in {"oi_value", "oi_change"}:
                    row.append(self._format_volume(val))
                elif col_id in {"oi_change_pct", "market_share"}:
                    # 原始值为小数比例，展示时转换为百分比
                    pct = val * 100 if isinstance(val, (int, float)) else val
                    row.append(self._format_percent(pct))
                else:
                    row.append(f"{val:.2f}" if isinstance(val, (int, float)) else str(val))
            # 通用列
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

    # ========= 工具 =========
    def _ensure_field_state(self, h) -> Dict[str, bool]:
        state = h.user_states.get("oi_fields")
        if not state:
            state = {}
            for col, _, _ in self.general_display_fields + self.special_display_fields:
                state[col] = True
            # 默认关闭：通用行情列 + 市场占比（只保留持仓金额/变动/变动%）
            for _off in {"quote_volume", "振幅", "成交笔数", "主动买卖比", "market_share", "price"}:
                if _off in state:
                    state[_off] = False
            h.user_states["oi_fields"] = state
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


# 注册入口
CARD = FuturesOIRankingCard()
