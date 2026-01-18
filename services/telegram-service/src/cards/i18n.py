"""排行榜卡片与信号模块的轻量 i18n 辅助。

复用全局 gettext 配置，并按用户/Telegram 语言选择翻译。
仅做只读操作，不写入用户偏好文件。
"""
from __future__ import annotations

import contextvars
import json
import logging
from contextlib import contextmanager
from pathlib import Path
from typing import Optional

from telegram import InlineKeyboardButton

from libs.common.i18n import build_i18n_from_env

PROJECT_ROOT = Path(__file__).resolve().parents[2]
LOCALE_STORE = PROJECT_ROOT / "data" / "user_locale.json"
I18N = build_i18n_from_env()
logger = logging.getLogger(__name__)

_CURRENT_LANG: contextvars.ContextVar[Optional[str]] = contextvars.ContextVar("i18n_current_lang", default=None)

_user_locale_map: dict[str, str] = {}

def _load_user_locale_map(force_reload: bool = False) -> dict[str, str]:
    global _user_locale_map
    if _user_locale_map and not force_reload:
        return _user_locale_map
    if LOCALE_STORE.exists():
        try:
            _user_locale_map = json.loads(LOCALE_STORE.read_text(encoding="utf-8"))
        except Exception:
            _user_locale_map = {}
    else:
        _user_locale_map = {}
    return _user_locale_map


def reload_user_locale():
    """强制重新加载用户语言偏好（供外部调用）"""
    _load_user_locale_map(force_reload=True)


@contextmanager
def lang_context(lang: Optional[str]):
    """为当前异步上下文设置语言（供按钮/文本自动回退）。"""
    token = _CURRENT_LANG.set(I18N.resolve(lang) if lang else None)
    try:
        yield
    finally:
        _CURRENT_LANG.reset(token)


def _extract_user(obj):
    """从 Update/CallbackQuery/Message 等对象中提取 user。"""
    if obj is None:
        return None
    user = getattr(obj, "effective_user", None)
    if user:
        return user
    user = getattr(obj, "from_user", None)
    if user:
        return user
    msg = getattr(obj, "message", None)
    if msg:
        user = getattr(msg, "from_user", None)
        if user:
            return user
    cq = getattr(obj, "callback_query", None)
    if cq:
        user = getattr(cq, "from_user", None)
        if user:
            return user
    return None


def resolve_lang(update=None, lang: Optional[str] = None) -> str:
    """解析语言：显式 lang > 用户偏好文件 > Telegram 语言 > 默认。"""
    if lang:
        return I18N.resolve(lang)
    _load_user_locale_map()
    user = _extract_user(update)
    if user is not None:
        user_id = getattr(user, "id", None)
        if user_id is not None:
            pref = _user_locale_map.get(str(user_id))
            if pref:
                return I18N.resolve(pref)
        tg_lang = getattr(user, "language_code", None)
        if tg_lang:
            return I18N.resolve(tg_lang)
    ctx_lang = _CURRENT_LANG.get()
    if ctx_lang:
        return I18N.resolve(ctx_lang)
    return I18N.resolve(None)


def resolve_lang_by_user_id(user_id: Optional[int]) -> str:
    """根据用户ID解析语言（仅基于持久化偏好，缺省回退默认语言）。"""
    if user_id is None:
        return resolve_lang()
    _load_user_locale_map()
    pref = _user_locale_map.get(str(user_id))
    if pref:
        return I18N.resolve(pref)
    return I18N.resolve(None)


def gettext(message_id: str, update=None, lang: Optional[str] = None, **kwargs) -> str:
    # 防护：如果 message_id 不是字符串，说明调用方参数顺序错误
    if not isinstance(message_id, str):
        import traceback
        logger.error("❌ i18n.gettext 参数错误: message_id=%r (type=%s)\n调用栈:\n%s", 
                     str(message_id)[:100], type(message_id).__name__, 
                     ''.join(traceback.format_stack()[-6:-1]))
        return str(message_id)
    resolved = resolve_lang(update, lang)
    try:
        return I18N.gettext(message_id, lang=resolved, **kwargs)
    except Exception:
        return message_id


def btn(
    update,
    key: str,
    callback: str,
    *,
    active: bool = False,
    prefix: str = "✅",
    lang: Optional[str] = None,
) -> InlineKeyboardButton:
    text = gettext(key, update=update, lang=lang)
    if active and prefix:
        text = f"{prefix}{text}"
    return InlineKeyboardButton(text, callback_data=callback)

BUTTON_KEY_MAP = {
    "排序": "card.common.sort",
    "降序": "btn.sort.desc",
    "升序": "btn.sort.asc",
    "10条": "btn.limit.10",
    "20条": "btn.limit.20",
    "30条": "btn.limit.30",
    "现货": "market.spot",
    "期货": "market.futures",
    "🏠主菜单": "menu.home",
    "🏠 返回": "btn.back_home",
    "⬅️ 返回": "btn.back",
    "⬅️ 返回KDJ": "btn.back_kdj",
    "返回": "btn.back",
    "🔄刷新": "btn.refresh",
    "刷新": "btn.refresh",
    "⚙️设置": "btn.settings",
    "设置": "btn.settings",
    "开启推送": "signal.push.on",
    "关闭推送": "signal.push.off",
    "开启": "signal.push.on",
    "关闭": "signal.push.off",
    # 期货字段按钮 - 主动成交方向
    "主动多空比": "btn.field.taker_ratio",
    "主动偏离": "btn.field.taker_bias",
    "主动动量": "btn.field.taker_momentum",
    # 期货字段按钮 - 大户情绪
    "大户多空比": "btn.field.top_ratio",
    "大户偏离": "btn.field.top_bias",
    "大户动量": "btn.field.top_momentum",
    "大户波动": "btn.field.top_volatility",
    # 期货字段按钮 - 全市场情绪
    "全体多空比": "btn.field.crowd_ratio",
    "全体偏离": "btn.field.crowd_bias",
    "全体波动": "btn.field.crowd_volatility",
    # 期货字段按钮 - 持仓增减速
    "持仓变动%": "btn.field.oi_change_pct",
    "持仓变动": "btn.field.oi_change",
    "持仓金额": "btn.field.oi_value",
    # 信号按钮
    "分析": "btn.analyze",
    "AI分析": "btn.ai_analyze",
    # 排序字段标签
    "成交额": "field.volume",
    "成交量": "field.base_volume",
    "振幅": "field.amplitude",
    "成交笔数": "field.trades",
    "主动买卖比": "field.taker_ratio",
    "买卖比": "field.buy_sell_ratio",
    "价格": "field.price",
    "带宽评分": "field.bandwidth",
    "趋势": "field.trend",
    "形态": "field.pattern",
    "方向": "field.direction",
    "斜率": "field.slope",
    "量比": "field.volume_ratio",
    "净流": "field.net_flow",
    "流入": "field.inflow",
    "流出": "field.outflow",
    "谐波值": "field.harmonic",
    "柱值": "field.histogram",
    "信号线": "field.signal_line",
    # 扩展排序字段标签（补齐缺失翻译）
    "涨跌": "field.change",
    "持仓占比": "field.position_share",
    "持仓市占": "field.position_market",
    "量能市占": "field.volume_market",
    "量能OI比": "field.volume_oi",
    "总爆仓": "field.liquidation_total",
    "多单": "field.liquidation_long",
    "空单": "field.liquidation_short",
    "深度比": "field.depth_ratio",
    "价差": "field.spread",
    "买墙": "field.bid_wall",
    "卖墙": "field.ask_wall",
    "资金费率": "field.funding_rate",
    "加权费率": "field.funding_weight",
    "突破价": "field.break_price",
    "类型": "field.break_type",
    "稳定度分位": "field.stability_pct",
    "情绪差值绝对值": "field.sentiment_diff_abs",
    # 别名/短标签映射（复用已有词条）
    "|Z分数|": "snapshot.field.z_score",
    "上沿": "snapshot.field.value_area_high",
    "下沿": "snapshot.field.value_area_low",
    "中轨价": "snapshot.field.mid_price",
    "上轨价": "snapshot.field.upper_price",
    "下轨价": "snapshot.field.lower_price",
    "主动买额": "snapshot.field.taker_buy",
    "主动卖额": "snapshot.field.taker_sell",
    "主动连续根数": "snapshot.field.taker_streak",
    "位置": "snapshot.field.value_area_pos",
    "偏离": "snapshot.field.deviation",
    "宽度%": "snapshot.field.value_area_width",
    "强度": "snapshot.field.trend_strength",
    "得分": "snapshot.field.liquidity_score",
    "等级": "snapshot.field.liquidity_level",
    "成交量加权": "snapshot.field.weighted_volume",
    "持仓Z分数": "snapshot.field.z_score",
    "覆盖率": "snapshot.field.value_area_coverage",
    "距离趋势线%": "snapshot.field.distance_pct",
    "跳变幅度": "snapshot.field.taker_jump",
}

# 字段 ID -> 显示名（中文）映射（用于 sort_field/id 回退显示）
FIELD_ID_LABEL_MAP = {
    "absolute": "净流",
    "amihud_raw": "Amihud原值",
    "amihud_score": "Amihud得分",
    "ask_wall": "卖墙",
    "atr_pct": "ATR%",
    "bandwidth": "带宽",
    "bandwidth_pct": "带宽%",
    "base_volume": "成交量",
    "bid_wall": "买墙",
    "break_price": "突破价",
    "break_type": "类型",
    "buy_quote": "主动买额",
    "buy_ratio": "买卖比",
    "category": "波动",
    "change": "涨跌",
    "coverage": "覆盖率",
    "crowd_bias": "全体偏离",
    "crowd_ratio": "全体多空比",
    "crowd_vol": "全体波动",
    "crowd_volatility": "全体波动",
    "d": "D",
    "dea": "DEA",
    "delta_volume": "量能偏向",
    "deviation": "偏离",
    "dif": "DIF",
    "direction": "方向",
    "distance_pct": "距离趋势线%",
    "distance_resist": "距阻力%",
    "distance_support": "距支撑%",
    "div": "情绪差值",
    "div_abs": "情绪差值绝对值",
    "sentiment_diff_abs": "情绪差值绝对值",
    "depth_ratio": "深度比",
    "ema25": "EMA25",
    "ema7": "EMA7",
    "ema99": "EMA99",
    "flip_signal": "翻转信号",
    "funding_rate": "资金费率",
    "funding_weight": "加权费率",
    "index": "得分",
    "inflow": "流入",
    "j": "J",
    "k": "K",
    "kyle_raw": "Kyle原值",
    "kyle_score": "Kyle得分",
    "level": "等级",
    "liquidation_long": "多单",
    "liquidation_short": "空单",
    "liquidation_total": "总爆仓",
    "long": "多头",
    "lower": "下轨价",
    "macd": "柱值",
    "market_share": "市场占比",
    "mfi": "MFI",
    "mid_price": "中轨价",
    "mid_slope": "中轨斜率",
    "middle": "中轨",
    "net": "净流",
    "oi_change": "持仓变动",
    "oi_change_pct": "持仓变动%",
    "oi_slope": "持仓斜率",
    "oi_streak": "OI连续根数",
    "oi_value": "持仓金额",
    "oi_z": "持仓Z分数",
    "oi_z_abs": "|Z分数|",
    "outflow": "流出",
    "long": "多头",
    "short": "空头",
    "pattern": "形态",
    "percent_b": "百分比",
    "position": "持仓占比",
    "position_market": "持仓市占",
    "position_share": "持仓占比",
    "price": "价格",
    "quote_volume": "成交额",
    "ratio": "深度比",
    "risk_score": "风险分",
    "sell_quote": "主动卖额",
    "short": "空头",
    "signal": "信号",
    "slope": "斜率",
    "spread": "价差",
    "stability_pct": "稳定度分位",
    "strength": "强度",
    "taker_bias": "主动偏离",
    "taker_jump": "跳变幅度",
    "taker_momentum": "主动动量",
    "taker_ratio": "主动多空比",
    "taker_streak": "主动连续根数",
    "top_bias": "大户偏离",
    "top_momentum": "大户动量",
    "top_ratio": "大户多空比",
    "top_vol": "大户波动",
    "top_volatility": "大户波动",
    "trend": "趋势",
    "trend_dir": "方向",
    "trend_direction": "趋势方向",
    "trend_duration": "持续根数",
    "trend_strength": "强度",
    "upper": "上轨价",
    "value_area_high": "上沿",
    "value_area_low": "下沿",
    "value_area_pos": "位置",
    "value_area_width_pct": "宽度%",
    "vol_score": "波动率得分",
    "volatility": "波动率",
    "volume_market": "量能市占",
    "volume_oi": "量能OI比",
    "volume": "成交额",
    "volumn_score": "成交量得分",
    "vpvr_price": "VPVR价",
    "weighted_rate": "加权费率",
    "weighted_volume": "成交量加权",
    "主动买卖比": "主动买卖比",
    "成交笔数": "成交笔数",
    "振幅": "振幅",
}


def btn_auto(
    update,
    label: str,
    callback: str,
    *,
    active: bool = False,
    prefix: str = "✅",
    lang: Optional[str] = None,
) -> InlineKeyboardButton:
    """根据常见中文标签自动映射到词条；未命中则回退原文。
    
    支持 ❎ 前缀：如 "❎主动多空比" 会先去掉前缀查找映射，翻译后再加回前缀。
    """
    # 处理 ❎ 前缀
    off_prefix = ""
    clean_label = label
    if label.startswith("❎"):
        off_prefix = "❎"
        clean_label = label[1:]
    
    key = BUTTON_KEY_MAP.get(clean_label)
    if key:
        text = gettext(key, update=update, lang=lang)
    else:
        # 若传入的 label 本身是 key（带 .），尝试翻译；否则原文回退
        text = gettext(clean_label, update=update, lang=lang) if "." in clean_label else clean_label
    
    # 恢复 ❎ 前缀
    if off_prefix:
        text = f"{off_prefix}{text}"
    
    if active and prefix:
        text = f"{prefix}{text}"
    return InlineKeyboardButton(text, callback_data=callback)


# 快照字段名映射（中文 -> i18n 键）
SNAPSHOT_FIELD_MAP = {
    # 基础指标
    "带宽": "snapshot.field.bandwidth",
    "百分比": "snapshot.field.percent_b",
    "中轨斜率": "snapshot.field.mid_slope",
    "中轨价格": "snapshot.field.mid_price",
    "上轨价格": "snapshot.field.upper_price",
    "下轨价格": "snapshot.field.lower_price",
    "量比": "snapshot.field.vol_ratio",
    "信号概述": "snapshot.field.signal",
    "支撑位": "snapshot.field.support",
    "阻力位": "snapshot.field.resistance",
    "距支撑%": "snapshot.field.dist_support",
    "距阻力%": "snapshot.field.dist_resistance",
    "距关键位%": "snapshot.field.dist_key",
    "主动买量": "snapshot.field.taker_buy",
    "主动卖量": "snapshot.field.taker_sell",
    "主动买卖比": "snapshot.field.taker_ratio",
    "J": "snapshot.field.j",
    "K": "snapshot.field.k",
    "D": "snapshot.field.d",
    "方向": "snapshot.field.direction",
    "MACD": "snapshot.field.macd",
    "DIF": "snapshot.field.dif",
    "DEA": "snapshot.field.dea",
    "柱状图": "snapshot.field.histogram",
    "信号": "snapshot.field.signal",
    "OBV值": "snapshot.field.obv",
    "OBV变化率": "snapshot.field.obv_change",
    "谐波值": "snapshot.field.harmonic",
    # 期货指标
    "持仓金额": "snapshot.field.oi_value",
    "持仓张数": "snapshot.field.oi_contracts",
    "持仓变动%": "snapshot.field.oi_change_pct",
    "持仓变动": "snapshot.field.oi_change",
    "持仓斜率": "snapshot.field.oi_slope",
    "Z分数": "snapshot.field.z_score",
    "OI连续根数": "snapshot.field.oi_streak",
    "大户多空比": "snapshot.field.top_ratio",
    "大户偏离": "snapshot.field.top_bias",
    "大户动量": "snapshot.field.top_momentum",
    "大户波动": "snapshot.field.top_volatility",
    "全体多空比": "snapshot.field.crowd_ratio",
    "全体偏离": "snapshot.field.crowd_bias",
    "全体波动": "snapshot.field.crowd_volatility",
    "主动多空比": "snapshot.field.taker_ls_ratio",
    "主动偏离": "snapshot.field.taker_bias",
    "主动动量": "snapshot.field.taker_momentum",
    "主动跳变": "snapshot.field.taker_jump",
    "主动连续": "snapshot.field.taker_streak",
    "情绪差值": "snapshot.field.sentiment_diff",
    "翻转信号": "snapshot.field.reversal",
    "波动率": "snapshot.field.volatility",
    "风险分": "snapshot.field.risk_score",
    "市场占比": "snapshot.field.market_share",
    # 高级指标
    "EMA7": "snapshot.field.ema7",
    "EMA25": "snapshot.field.ema25",
    "EMA99": "snapshot.field.ema99",
    "带宽评分": "snapshot.field.bandwidth_score",
    "趋势方向": "snapshot.field.trend_dir",
    "价格": "snapshot.field.price",
    "ATR%": "snapshot.field.atr_pct",
    "波动": "snapshot.field.volatility_type",
    "上轨": "snapshot.field.upper",
    "中轨": "snapshot.field.mid",
    "下轨": "snapshot.field.lower",
    "CVD值": "snapshot.field.cvd",
    "变化率": "snapshot.field.change_rate",
    "偏离度": "snapshot.field.deviation",
    "偏离%": "snapshot.field.deviation_pct",
    "距离%": "snapshot.field.distance_pct",
    # 补充缺失的字段
    "ATR": "snapshot.field.atr",
    "MFI": "snapshot.field.mfi",
    "VPVR价": "snapshot.field.vpvr_price",
    "VWAP价格": "snapshot.field.vwap_price",
    "当前价格": "snapshot.field.current_price",
    "价值区上沿": "snapshot.field.value_area_high",
    "价值区下沿": "snapshot.field.value_area_low",
    "价值区位置": "snapshot.field.value_area_pos",
    "价值区宽度%": "snapshot.field.value_area_width",
    "价值区覆盖率": "snapshot.field.value_area_coverage",
    "加权成交额": "snapshot.field.weighted_volume",
    "带宽%": "snapshot.field.bandwidth_pct",
    "趋势强度": "snapshot.field.trend_strength",
    "趋势带": "snapshot.field.trend_band",
    "持续根数": "snapshot.field.duration_bars",
    "最近翻转时间": "snapshot.field.last_reversal",
    "流动性得分": "snapshot.field.liquidity_score",
    "流动性等级": "snapshot.field.liquidity_level",
    "成交量得分": "snapshot.field.volume_score",
    "波动率得分": "snapshot.field.volatility_score",
    "量能偏向": "snapshot.field.volume_bias",
    "Amihud原值": "snapshot.field.amihud_raw",
    "Amihud得分": "snapshot.field.amihud_score",
    "Kyle原值": "snapshot.field.kyle_raw",
    "Kyle得分": "snapshot.field.kyle_score",
}

# 数据值翻译映射（数据库返回的中文值 -> i18n 键）
DATA_VALUE_MAP = {
    # 成交量信号
    "缩量": "data.value.shrink",
    "放量": "data.value.expand",
    "正常": "data.value.normal",
    # KDJ/MACD 方向
    "延续": "data.value.continue",
    "金叉": "data.value.golden_cross",
    "死叉": "data.value.death_cross",
    "超买": "data.value.overbought",
    "超卖": "data.value.oversold",
    # 趋势方向
    "上涨": "data.value.up",
    "下跌": "data.value.down",
    "震荡": "data.value.sideways",
    "多头": "data.value.bullish",
    "空头": "data.value.bearish",
    # 强度
    "强": "data.value.strong",
    "中": "data.value.medium",
    "弱": "data.value.weak",
}


def translate_field(label: str, lang: str = None) -> str:
    """翻译字段名，优先查映射词条，未映射则返回原文。"""
    if not isinstance(label, str):
        return label
    # 兼容传入字段 ID
    label = FIELD_ID_LABEL_MAP.get(label, label)
    key = BUTTON_KEY_MAP.get(label) or SNAPSHOT_FIELD_MAP.get(label)
    if key:
        return gettext(key, lang=lang)
    return label


def format_sort_field(field: str, lang: str = None, field_lists: list[list[tuple]] | None = None) -> str:
    """排序字段展示：优先从字段列表取中文名，再走 i18n，并处理 Markdown 下划线转义。"""
    label = field
    if field_lists:
        for flist in field_lists:
            for item in flist or []:
                if len(item) >= 2 and item[0] == field:
                    label = item[1]
                    break
            if label != field:
                break
    text = translate_field(label, lang=lang)
    return str(text).replace("_", "\\_")


def translate_value(value: str, lang: str = None) -> str:
    """翻译数据值，未映射则返回原文"""
    if not isinstance(value, str):
        return value
    key = DATA_VALUE_MAP.get(value)
    if key:
        return gettext(key, lang=lang)
    return value


__all__ = [
    "gettext",
    "btn",
    "btn_auto",
    "resolve_lang",
    "resolve_lang_by_user_id",
    "lang_context",
    "I18N",
    "translate_field",
    "format_sort_field",
    "translate_value",
]
