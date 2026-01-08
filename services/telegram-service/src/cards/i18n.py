"""排行榜卡片与信号模块的轻量 i18n 辅助。

复用全局 gettext 配置，并按用户/Telegram 语言选择翻译。
仅做只读操作，不写入用户偏好文件。
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Optional
from telegram import InlineKeyboardButton

from libs.common.i18n import build_i18n_from_env

PROJECT_ROOT = Path(__file__).resolve().parents[2]
LOCALE_STORE = PROJECT_ROOT / "data" / "user_locale.json"
I18N = build_i18n_from_env()

_user_locale_map: dict[str, str] = {}

def _load_user_locale_map() -> dict[str, str]:
    global _user_locale_map
    if _user_locale_map:
        return _user_locale_map
    if LOCALE_STORE.exists():
        try:
            _user_locale_map = json.loads(LOCALE_STORE.read_text(encoding="utf-8"))
        except Exception:
            _user_locale_map = {}
    else:
        _user_locale_map = {}
    return _user_locale_map


def resolve_lang(update=None, lang: Optional[str] = None) -> str:
    """解析语言：显式 lang > 用户偏好文件 > Telegram 语言 > 默认。"""
    if lang:
        return I18N.resolve(lang)
    _load_user_locale_map()
    user_id = getattr(getattr(update, "effective_user", None), "id", None)
    if user_id is not None:
        pref = _user_locale_map.get(str(user_id))
        if pref:
            return I18N.resolve(pref)
    tg_lang = getattr(getattr(update, "effective_user", None), "language_code", None)
    if tg_lang:
        return I18N.resolve(tg_lang)
    return I18N.resolve(None)


def gettext(message_id: str, update=None, lang: Optional[str] = None, **kwargs) -> str:
    resolved = resolve_lang(update, lang)
    try:
        return I18N.gettext(message_id, lang=resolved, **kwargs)
    except Exception:
        return message_id


def btn(update, key: str, callback: str, *, active: bool = False, prefix: str = "✅") -> InlineKeyboardButton:
    text = gettext(key, update=update)
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
}


def btn_auto(update, label: str, callback: str, *, active: bool = False, prefix: str = "✅") -> InlineKeyboardButton:
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
        text = gettext(key, update=update)
    else:
        # 若传入的 label 本身是 key（带 .），尝试翻译；否则原文回退
        text = gettext(clean_label, update=update) if "." in clean_label else clean_label
    
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


def translate_field(label: str, lang: str = None) -> str:
    """翻译字段名，优先查 BUTTON_KEY_MAP，再查 SNAPSHOT_FIELD_MAP，未映射则返回原文"""
    key = BUTTON_KEY_MAP.get(label) or SNAPSHOT_FIELD_MAP.get(label)
    if key:
        return gettext(key, lang=lang)
    return label


__all__ = ["gettext", "btn", "btn_auto", "resolve_lang", "I18N", "translate_field"]
