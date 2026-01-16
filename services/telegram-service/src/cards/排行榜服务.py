"""排行榜共享服务模块

本文件集中封装所有排行榜卡片可复用的渲染与键盘逻辑，确保不同卡片的
文本、对齐、按钮样式保持一致，符合《排行榜卡片拓展指南》与《数据对齐》
两份规范：
- 标题/时间/排序提示统一格式；
- 数据列使用 `handler.dynamic_align_format` 做等宽对齐，前两列左对齐，其余右对齐；
- 键盘遵循“周期行 → 排序行 → 数量行”的二维布局。
"""

from __future__ import annotations

import logging
from typing import Dict, List, Sequence

from cards.data_provider import get_ranking_provider, format_symbol
from cards.i18n import btn_auto as _btn_auto, gettext as _t, resolve_lang, translate_field, format_sort_field

from telegram import InlineKeyboardButton, InlineKeyboardMarkup


LOGGER = logging.getLogger(__name__)

# 文档约定的固定周期顺序
DEFAULT_PERIODS = ["1m", "5m", "15m", "1h", "4h", "1d", "1w"]
# 各服务可用周期：统一使用 1d 表示日线，禁止再用 legacy 写法
# 注意：所有周期列表都应包含 1w，因为数据库中有 1w 数据
VOLUME_FUTURES_PERIODS = ["5m", "15m", "30m", "1h", "4h", "12h", "1d", "1w"]
VOLUME_SPOT_PERIODS = ["5m", "15m", "30m", "1h", "4h", "12h", "1d", "1w"]
POSITION_PERIODS = ["5m", "15m", "30m", "1h", "4h", "1d", "1w"]
LIQUIDATION_PERIODS = ["1h", "4h", "12h", "1d", "1w"]
MONEY_FLOW_FUTURES_PERIODS = ["5m", "15m", "30m", "1h", "4h", "12h", "1d", "1w"]
MONEY_FLOW_SPOT_PERIODS = ["5m", "15m", "30m", "1h", "4h", "12h", "1d", "1w"]
MONEY_FLOW_PERIODS = MONEY_FLOW_SPOT_PERIODS


def normalize_period(requested: str, allowed: Sequence[str], default: str = "4h") -> str:
    """将文档要求的标准周期映射到实际支持的周期；日线统一为 1d"""
    alias = {
        "1m": "5m",   # 聚合粒度下限
        f"{24}h": "1d",  # 兼容旧写法，统一映射到 1d
        "1w": "1w",
    }
    target = alias.get(requested, requested)
    if target in allowed:
        return target
    if default in allowed:
        return default
    return allowed[0] if allowed else default


class BaseService:
    """简单包装 handler 的基类"""

    def __init__(self, handler) -> None:
        self.handler = handler


class VolumeRankingService(BaseService):
    def __init__(self, handler) -> None:
        super().__init__(handler)
        # 统一使用 SQLite 数据访问层
        self.provider = get_ranking_provider()

    def render_text(
        self,
        limit: int,
        period: str,
        sort_order: str,
        market_type: str,
        sort_field: str = "volume",
        fields_state: Dict[str, bool] | None = None,
        update=None,
        lang: str | None = None,
    ) -> str:
        allowed = VOLUME_SPOT_PERIODS if market_type == "spot" else VOLUME_FUTURES_PERIODS
        period = normalize_period(period, allowed, default="4h")

        # 使用 SQLite 数据
        try:
            rows = self._load_from_provider(period)
            if rows:
                return self._render_from_rows(
                    rows,
                    period,
                    sort_order,
                    market_type,
                    sort_field,
                    limit,
                    fields_state,
                    update=update,
                    lang=lang,
                )
        except Exception as exc:  # pragma: no cover
            LOGGER.warning("Volume provider 读取失败，回退旧逻辑: %s", exc)

        # 兜底：旧 handler 计算（若仍可用）
        try:
            return self.handler.get_volume_ranking(limit, period, sort_order, market_type, sort_field=sort_field)  # type: ignore[arg-type]
        except TypeError:
            return self.handler.get_volume_ranking(limit, period, sort_order, market_type)

    def _load_from_provider(self, period: str) -> List[Dict[str, float]]:
        """从新系统获取成交额数据。

        优先从基础数据表按周期取最近一条，使用 `成交额`、`当前价格`、`变化率`。
        若未来补充 Volume 专用表，可在此扩展。
        """
        base_map = self.provider.fetch_base(period)
        rows: List[Dict[str, float]] = []
        for sym, r in base_map.items():
            # 用户要求成交量榜直接使用“成交量”列，不再用成交额
            volume = float(r.get("成交量") or 0)
            quote_volume = volume  # 以“成交量”作为主要排序值
            price = float(r.get("当前价格") or r.get("price") or 0)
            change = float(r.get("变化率") or 0)
            # 数据里变化率可能是小数 (0.03) 也可能已是百分比 (3)。做一次统一
            if abs(change) < 1:
                change *= 100
            rows.append({
                "symbol": sym.upper(),
                "quote_volume": quote_volume,
                "base_volume": volume,
                "last_close": price,
                "first_close": float(r.get("开盘价") or price or 1),
                "change_percent": change,
                "振幅": float(r.get("振幅") or 0),
                "成交笔数": float(r.get("成交笔数") or r.get("交易次数") or 0),
                "主动买卖比": float(r.get("主动买卖比") or 0),
            })
        return rows

    def _render_from_rows(
        self,
        rows: List[Dict[str, float]],
        period: str,
        sort_order: str,
        market_type: str,
        sort_field: str,
        limit: int,
        fields_state: Dict[str, bool] | None = None,
        *,
        update=None,
        lang: str | None = None,
    ) -> str:
        sort_symbol = "🔽" if sort_order == 'desc' else "🔼"
        sort_text = "降序" if sort_order == 'desc' else "升序"
        period_display = {
            '5m': '5分钟', '15m': '15分钟', '30m': '30分钟',
            '1h': '1小时', '4h': '4小时', '12h': '12小时',
            '1d': '1天', '1w': '1周'
        }
        market_text = '合约' if market_type == 'futures' else '现货'
        period_text = period_display.get(period, period)

        reverse = sort_order == 'desc'
        def _key(row: Dict[str, float]) -> float:
            # 默认用成交额排序；若请求 price 则按价格排序
            if sort_field in {"price", "last_close"}:
                return float(row.get('last_close') or 0.0)
            if sort_field in {"strength", "volume", "quote_volume"}:
                vol = float(row.get('quote_volume') or 0.0)
                if vol:
                    return vol
                return float(row.get('base_volume') or 0.0)
            return float(row.get('quote_volume') or 0.0)

        ordered_rows = sorted(rows, key=_key, reverse=reverse)[:limit]
        show_quote_volume = fields_state.get("quote_volume", True) if fields_state is not None else True
        show_price = fields_state.get("price", True) if fields_state is not None else True
        data_rows: List[List[str]] = []
        for idx, row in enumerate(ordered_rows, 1):
            quote_volume = float(row.get('quote_volume') or 0)
            base_volume = float(row.get('base_volume') or 0)
            last_close = float(row.get('last_close') or 0)
            first_close = float(row.get('first_close') or (last_close or 1))
            volume_str = self._format_volume(quote_volume or base_volume * last_close)
            price_str = self._format_price(last_close)
            change_percent = 0.0
            if first_close:
                change_percent = ((last_close - first_close) / first_close) * 100
            change_str = self._format_pct(change_percent)
            row_cells = [f"{idx}.", row.get('symbol', '').upper()]
            if show_quote_volume:
                row_cells.append(volume_str)
            if show_price:
                row_cells.append(price_str)
            row_cells.append(change_str)
            data_rows.append(row_cells)

        lang = resolve_lang(update, lang)
        aligned = self.handler.dynamic_align_format(data_rows) if data_rows else _t("data.no_data", lang=lang)
        time_info = self.handler.get_current_time_display()
        title = _t("card.volume.title", lang=lang)
        header_parts = [_t("card.header.rank", lang=lang), _t("card.header.symbol", lang=lang)]
        if show_quote_volume:
            header_parts.append(f"{period_text}{_t('field.volume', lang=lang)}(±)")
        if show_price:
            header_parts.append(_t("field.price", lang=lang))
        header_parts.append(f"{period_text}{_t('field.change', lang=lang)}(±)")
        header = "/".join(header_parts)

        return f"""{title}
{_t('card.common.update_time', lang=lang).format(time=time_info['full'])}
{_t('card.common.sort_info', lang=lang).format(period=period_text, field=format_sort_field('volume', lang=lang), symbol=sort_symbol)}
{header}
```
{aligned}
```
{_t('card.volume.hint', lang=lang)}
{_t('card.common.last_update', lang=lang).format(time=time_info['full'])}"""

    @staticmethod
    def _format_volume(value: float) -> str:
        """压缩表示：带符号，单位 K/M/B，固定两位小数。"""
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
    def _format_pct(value: float) -> str:
        if value is None:
            return "-"
        sign = "+" if value > 0 else "-" if value < 0 else ""
        return f"{sign}{abs(value):.0f}%"

    @staticmethod
    def _format_price(price: float) -> str:
        if price >= 1000:
            return f"${price:,.0f}"
        if price >= 1:
            return f"${price:.3f}"
        return f"${price:.6f}"

    def build_keyboard(self, period: str, sort_order: str, limit: int, market_type: str, sort_field: str = "volume", *, callback_prefix: str = ""):
        sort_fields = [("volume", "成交额"), ("price", "价格"), ("change", "涨跌")]
        return build_standard_keyboard(
            current_market=market_type,
            general_fields=GENERAL_FIELDS,
            special_fields=sort_fields,
            current_sort_field=sort_field or "quote_volume",
            current_period=period,
            current_sort_order=sort_order,
            current_limit=limit,
            main_callback="ranking_menu",
            refresh_callback="volume_ranking_refresh",
            callback_prefix=callback_prefix,
        )


class PositionRankingService(BaseService):
    def render_text(self, limit: int, sort_order: str, period: str, sort_field: str = "position") -> str:
        period = normalize_period(period, POSITION_PERIODS, default="4h")
        try:
            return self.handler.get_position_ranking(limit, sort_order, period, sort_field=sort_field)  # type: ignore[arg-type]
        except TypeError:
            return self.handler.get_position_ranking(limit, sort_order, period)

    def build_keyboard(self, sort_order: str, limit: int, period: str, sort_field: str = "position", *, callback_prefix: str = ""):
        sort_fields = [("position", "持仓占比"), ("price", "价格")]
        return build_standard_keyboard(
            current_market=None,
            general_fields=GENERAL_FIELDS,
            special_fields=sort_fields,
            current_sort_field=sort_field or "quote_volume",
            current_period=period,
            current_sort_order=sort_order,
            current_limit=limit,
            main_callback="ranking_menu",
            refresh_callback="position_ranking_refresh",
            callback_prefix=callback_prefix,
        )


class FundingRateService(BaseService):
    def render_text(self, limit: int, sort_order: str, sort_type: str, period: str) -> str:
        return self.handler.get_funding_rate_ranking(limit, sort_order, sort_type)

    def build_keyboard(self, sort_order: str, limit: int, sort_type: str, period: str, *, callback_prefix: str = ""):
        sort_fields = [("funding_rate", "资金费率"), ("funding_weight", "加权费率"), ("price", "价格")]
        return build_standard_keyboard(
            current_market=None,
            general_fields=GENERAL_FIELDS,
            special_fields=sort_fields,
            current_sort_field=sort_type,
            current_period=period,
            current_sort_order=sort_order,
            current_limit=limit,
            main_callback="ranking_menu",
            refresh_callback="funding_rate_refresh",
            callback_prefix=callback_prefix,
        )


class LiquidationRankingService(BaseService):
    def render_text(self, limit: int, sort_order: str, period: str, data_type: str) -> str:
        period = normalize_period(period, LIQUIDATION_PERIODS, default="4h")
        return self.handler.get_liquidation_ranking(limit, sort_order, period, data_type)

    def build_keyboard(self, limit: int, sort_order: str, period: str, data_type: str, *, callback_prefix: str = ""):
        sort_fields = [("total", "总爆仓"), ("long", "多单"), ("short", "空单"), ("price", "价格")]
        return build_standard_keyboard(
            current_market=None,
            general_fields=GENERAL_FIELDS,
            special_fields=sort_fields,
            current_sort_field=data_type,
            current_period=period,
            current_sort_order=sort_order,
            current_limit=limit,
            main_callback="ranking_menu",
            refresh_callback="liquidation_ranking_refresh",
            callback_prefix=callback_prefix,
        )


class MoneyFlowService(BaseService):
    def render_text(
        self,
        limit: int,
        period: str,
        sort_order: str,
        flow_type: str,
        market: str,
    ) -> str:
        allowed = MONEY_FLOW_SPOT_PERIODS if market == "spot" else MONEY_FLOW_FUTURES_PERIODS
        period = normalize_period(period, allowed, default="4h")
        return self.handler.get_money_flow(limit, period, sort_order, flow_type, market)

    def build_keyboard(
        self,
        period: str,
        sort_order: str,
        limit: int,
        flow_type: str,
        market: str,
        *,
        callback_prefix: str = "",
    ):
        sort_fields = [("absolute", "净流"), ("volume", "成交额"), ("price", "价格")]
        return build_standard_keyboard(
            current_market=market,
            general_fields=GENERAL_FIELDS,
            special_fields=sort_fields,
            current_sort_field=flow_type,
            current_period=period,
            current_sort_order=sort_order,
            current_limit=limit,
            main_callback="ranking_menu",
            refresh_callback="money_flow_refresh",
            callback_prefix=callback_prefix,
        )


class MarketDepthService(BaseService):
    def render_rows(self, limit: int, sort_type: str, sort_order: str, period: str) -> List[List[str]]:
        """返回行数据供卡片裁剪列，格式：[[rank, symbol, ratio, bid_wall, ask_wall, spread], ...]"""
        _ = normalize_period(period, DEFAULT_PERIODS, default="1h")
        rows: List[List[str]] = []
        try:
            raw = self.handler.get_market_depth(limit, sort_type, sort_order)
            # 若已是字符串则放弃裁剪，返回空由上层兜底
            if isinstance(raw, str):
                return []
            for idx, item in enumerate(raw or [], 1):
                rows.append([
                    f"{idx}",
                    (item.get("symbol") or "").upper(),
                    self._fmt(item.get("ratio")),
                    self._fmt(item.get("bid_wall")),
                    self._fmt(item.get("ask_wall")),
                    self._fmt(item.get("spread")),
                ])
        except Exception:
            return []
        return rows[:limit]

    @staticmethod
    def _fmt(val) -> str:
        if val is None:
            return "-"
        try:
            v = float(val)
            return f"{v:.4f}"
        except Exception:
            return str(val)

    def build_keyboard(self, limit: int, sort_type: str, sort_order: str, period: str, *, callback_prefix: str = ""):
        sort_fields = [("ratio", "深度比"), ("spread", "价差"), ("bid_depth", "买墙"), ("ask_depth", "卖墙")]
        return build_standard_keyboard(
            current_market=None,
            general_fields=GENERAL_FIELDS,
            special_fields=sort_fields,
            current_sort_field=sort_type,
            current_period=period,
            current_sort_order=sort_order,
            current_limit=limit,
            main_callback="ranking_menu",
            refresh_callback="market_depth_refresh",
            callback_prefix=callback_prefix,
        )


class RatioRankingService(BaseService):
    def render_text(self, limit: int, sort_order: str, ratio_type: str, period: str) -> str:
        _ = normalize_period(period, DEFAULT_PERIODS, default="1h")
        return self.handler.get_unified_ratio_data(limit, sort_order, ratio_type)

    def build_keyboard(self, sort_order: str, limit: int, ratio_type: str, period: str, *, callback_prefix: str = ""):
        sort_fields = [("position_market", "持仓市占"), ("volume_market", "量能市占"), ("volume_oi", "量能OI比"), ("price", "价格")]
        return build_standard_keyboard(
            current_market=None,
            general_fields=GENERAL_FIELDS,
            special_fields=sort_fields,
            current_sort_field=ratio_type,
            current_period=period,
            current_sort_order=sort_order,
            current_limit=limit,
            main_callback="ranking_menu",
            refresh_callback="position_market_ratio_refresh",
            callback_prefix=callback_prefix,
        )


def get_volume_service(handler) -> VolumeRankingService:
    return VolumeRankingService(handler)


def get_position_service(handler) -> PositionRankingService:
    return PositionRankingService(handler)


def get_funding_service(handler) -> FundingRateService:
    return FundingRateService(handler)


def get_liquidation_service(handler) -> LiquidationRankingService:
    return LiquidationRankingService(handler)


def get_money_flow_service(handler) -> MoneyFlowService:
    return MoneyFlowService(handler)


def get_market_depth_service(handler) -> MarketDepthService:
    return MarketDepthService(handler)


def get_ratio_service(handler) -> RatioRankingService:
    return RatioRankingService(handler)


# ---------------------- 通用键盘构建 ----------------------
GENERAL_FIELDS: List[tuple[str, str]] = [
    ("quote_volume", "成交额"),
    ("振幅", "振幅"),
    ("成交笔数", "成交笔数"),
    ("主动买卖比", "主动买卖比"),
    ("price", "价格"),
]


def build_standard_keyboard(
    *,
    current_market: str | None = None,
    general_fields: List[tuple[str, str]] | None = None,
    special_fields: List[tuple[str, str]] | None = None,
    sort_fields: List[tuple[str, str]] | None = None,  # 兼容旧参数，若传 general/special 则忽略
    current_sort_field: str | None = None,
    current_period: str = "1h",
    periods: Sequence[str] | None = None,
    current_sort_order: str = "desc",
    limits: Sequence[int] | None = None,
    current_limit: int = 20,
    main_callback: str = "ranking_menu",
    refresh_callback: str = "refresh",
    callback_prefix: str = "",
    show_market_row: bool = True,  # 控制是否显示市场类型行
    show_sort_fields: bool = True,  # 控制是否显示排序字段行
    show_periods: bool = True,  # 控制是否显示周期行
    show_sort_limit: bool = True,  # 控制是否显示排序方向+条数行
    show_main_refresh: bool = True,  # 控制是否显示主菜单+刷新行
) -> InlineKeyboardMarkup:
    """统一的 6 行内联键盘布局，符合最新《排行榜卡片拓展指南》

    行1：市场类型（可隐藏）
    行2：通用排序字段（最多 5 个）
    行3：专用排序字段（最多 4 个，缺少可省略整行）
    行4：周期
    行5：排序方向 + 条数
    行6：主菜单 + 刷新
    """

    def btn(label: str, data: str, active: bool = False) -> InlineKeyboardButton:
        return _btn_auto(None, label, data, active=active)

    prefix = callback_prefix or ""
    if prefix and not prefix.endswith("_"):
        prefix = f"{prefix}_"

    general_fields = list(general_fields or GENERAL_FIELDS)
    if special_fields is None and sort_fields:
        special_fields = list(sort_fields)
    else:
        special_fields = list(special_fields or [])

    keyboard: List[List[InlineKeyboardButton]] = []

    # 第一行：市场类型（可选）
    if current_market is not None and show_market_row:
        keyboard.append([
            btn("现货", "market_spot", active=current_market == "spot"),
            btn("期货", "market_futures", active=current_market == "futures"),
        ])

    # 第二行：通用字段
    gf = general_fields
    if gf:
        row = [
            btn(label, f"{prefix}sort_field_{value}", active=(value == current_sort_field))
            for value, label in gf[:5]
        ]
        if show_sort_fields:
            keyboard.append(row)

    # 第三行：专用字段（可选）
    sf = special_fields
    if sf:
        row = [
            btn(label, f"{prefix}sort_field_{value}", active=(value == current_sort_field))
            for value, label in sf[:4]
        ]
        if row and show_sort_fields:
            keyboard.append(row)

    # 第四行：周期
    period_row = [btn(p, f"{prefix}period_{p}", active=p == current_period) for p in DEFAULT_PERIODS]
    if show_periods:
        keyboard.append(period_row)

    # 第五行：排序方向 + 条数
    limits = list(limits or [10, 20, 30])
    sort_limit_row: List[InlineKeyboardButton] = [
        btn("降序", f"{prefix}sort_desc", active=current_sort_order == "desc"),
        btn("升序", f"{prefix}sort_asc", active=current_sort_order == "asc"),
    ]
    for lim in limits:
        # 使用固定的中文标签，通过 BUTTON_KEY_MAP 自动翻译
        limit_label = {10: "10条", 20: "20条", 30: "30条"}.get(lim, f"{lim}")
        sort_limit_row.append(btn(limit_label, f"{prefix}limit_{lim}", active=lim == current_limit))
    if show_sort_limit:
        keyboard.append(sort_limit_row)

    # 第六行：返回排行榜 + 刷新
    if show_main_refresh:
        keyboard.append([
            _btn_auto(None, "btn.back_home", main_callback),
            _btn_auto(None, "btn.refresh", refresh_callback),
        ])

    return InlineKeyboardMarkup(keyboard)


# ---------------------- 主动买卖比（主动买卖额占比） ----------------------
class BuySellRatioService(BaseService):
    """主动买卖比排行榜服务，统一渲染格式与按钮布局"""


    def __init__(self, handler) -> None:
        super().__init__(handler)
        self.logger = logging.getLogger(__name__)
        self.provider = get_ranking_provider()

    def render_text(
        self,
        limit: int,
        period: str,
        sort_order: str,
        sort_field: str = "buy_ratio",
        update=None,
        lang: str | None = None,
    ) -> str:
        period = normalize_period(period, DEFAULT_PERIODS, default="1h")
        rows = self._load_from_db(period, sort_order, limit, sort_field)

        data_rows: List[List[str]] = []
        for idx, row in enumerate(rows, 1):
            symbol = (row.get("symbol") or "").upper()
            ratio = float(row.get("buy_ratio", 0))
            buy_quote = float(row.get("buy_quote", 0))
            sell_quote = float(row.get("sell_quote", 0))
            total_quote = float(row.get("quote_volume", buy_quote + sell_quote))
            price = float(row.get("last_close", 0))

            ratio_txt = f"{ratio*100:.2f}%"
            buy_txt = f"{buy_quote:,.0f}"
            sell_txt = f"{sell_quote:,.0f}"
            total_txt = f"{total_quote:,.0f}" if total_quote else "-"
            price_txt = f"${price:.4f}" if price else "-"

            data_rows.append([
                f"{idx}.",
                symbol,
                ratio_txt,
                buy_txt,
                sell_txt,
                total_txt,
                price_txt,
                period,
            ])

        lang = resolve_lang(update, lang)
        aligned = self.handler.dynamic_align_format(data_rows) if data_rows else _t("data.no_data", lang=lang)
        time_info = self.handler.get_current_time_display()
        sort_symbol = "🔽" if sort_order == "desc" else "🔼"
        return (
            f"{_t('card.taker_ratio.title', lang=lang)}\n"
            f"{_t('card.common.update_time', lang=lang).format(time=time_info['full'])}\n"
            f"{_t('card.common.sort_info', lang=lang).format(period=period, field=format_sort_field('taker_ratio', lang=lang), symbol=sort_symbol)}\n"
            f"{_t('card.header.rank', lang=lang)}/{_t('card.header.symbol', lang=lang)}/"
            f"{_t('field.taker_ratio', lang=lang)}/{_t('snapshot.field.taker_buy', lang=lang)}/"
            f"{_t('snapshot.field.taker_sell', lang=lang)}/{_t('field.volume', lang=lang)}/{_t('field.price', lang=lang)}\n"
            f"```\n{aligned}\n```\n"
            f"{_t('card.taker_ratio.hint', lang=lang)}\n"
            f"{_t('card.common.last_update', lang=lang).format(time=time_info['full'])}"
        )

    # ---------- 数据加载 ----------
    def _load_from_db(self, period: str, sort_order: str, limit: int, sort_field: str) -> List[Dict]:
        service = getattr(self.handler, "metric_service", None)
        if service and hasattr(service, "获取主动买卖比排行"):
            try:
                rows = service.获取主动买卖比排行("futures", period, limit, sort_order)
                return self._sort_rows(rows, sort_field, sort_order)[:limit]
            except Exception as exc:  # pragma: no cover
                self.logger.warning("metric_service 主动买卖比失败: %s", exc)
        try:
            metrics = self.provider.merge_with_base("主动买卖比榜单", period, base_fields=["成交额", "当前价格"])
            rows: List[Dict] = []
            for row in metrics:
                sym = format_symbol(row.get("symbol") or row.get("交易对") or row.get("币种") or "")
                if not sym:
                    continue
                rows.append({
                    "symbol": sym,
                    "buy_ratio": float(row.get("主动买卖比") or row.get("强度") or 0),
                    "buy_quote": float(row.get("主动买额") or row.get("主动买量") or 0),
                    "sell_quote": float(row.get("主动卖额") or row.get("主动卖量") or 0),
                    "quote_volume": float(row.get("成交额") or row.get("quote_volume") or 0),
                    "last_close": float(row.get("价格") or row.get("price") or row.get("当前价格") or 0),
                })
            return self._sort_rows(rows, sort_field, sort_order)[:limit]
        except Exception as exc:  # pragma: no cover
            self.logger.warning("SQLite 主动买卖比兜底失败: %s", exc)
            return []

    @staticmethod
    def _sort_rows(rows: List[Dict], sort_field: str, sort_order: str) -> List[Dict]:
        reverse = sort_order != "asc"
        def _key(r: Dict) -> float:
            if sort_field in {"quote_volume", "volume"}:
                return r.get("quote_volume", 0) or (r.get("buy_quote", 0) + r.get("sell_quote", 0))
            if sort_field in {"price"}:
                return r.get("last_close", 0)
            return r.get("buy_ratio", 0)
        return sorted(rows, key=_key, reverse=reverse)

    @staticmethod
    def _to_float(row: Dict, keys: List[str]) -> float:
        for key in keys:
            val = row.get(key)
            if val in (None, ""):
                continue
            try:
                return float(val)
            except Exception:
                continue
        return 0.0

    # ---------- 按钮 ----------
    def build_keyboard(self, period: str, sort_order: str, limit: int, sort_field: str, *, callback_prefix: str = ""):
        sort_fields = [("buy_ratio", "买卖比"), ("quote_volume", "成交额"), ("price", "价格")]
        return build_standard_keyboard(
            current_market=None,
            general_fields=GENERAL_FIELDS,
            special_fields=sort_fields,
            current_sort_field=sort_field or "quote_volume",
            current_period=period,
            current_sort_order=sort_order,
            current_limit=limit,
            main_callback="ranking_menu",
            refresh_callback="buy_sell_ratio_ranking_refresh",
            callback_prefix=callback_prefix,
        )


def get_buy_sell_ratio_service(handler) -> BuySellRatioService:
    return BuySellRatioService(handler)
