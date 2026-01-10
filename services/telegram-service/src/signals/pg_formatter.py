"""
PG 信号模板格式化器
专注于实时预警，简洁有力
"""
from datetime import datetime
from typing import Dict, Any, Optional

# 信号类型配置
SIGNAL_TEMPLATES = {
    # 价格信号
    "price_surge": {
        "icon": "🚀",
        "title": "价格急涨",
        "title_en": "Price Surge",
        "color": "green",
    },
    "price_dump": {
        "icon": "💥",
        "title": "价格急跌",
        "title_en": "Price Dump",
        "color": "red",
    },
    # 成交量信号
    "volume_spike": {
        "icon": "📊",
        "title": "成交量暴增",
        "title_en": "Volume Spike",
        "color": "yellow",
    },
    # 主动买卖信号
    "taker_buy_dominance": {
        "icon": "🟢",
        "title": "主动买入主导",
        "title_en": "Taker Buy Dominance",
        "color": "green",
    },
    "taker_sell_dominance": {
        "icon": "🔴",
        "title": "主动卖出主导",
        "title_en": "Taker Sell Dominance",
        "color": "red",
    },
    # 持仓量信号
    "oi_surge": {
        "icon": "📈",
        "title": "持仓量急增",
        "title_en": "OI Surge",
        "color": "green",
    },
    "oi_dump": {
        "icon": "📉",
        "title": "持仓量急减",
        "title_en": "OI Dump",
        "color": "red",
    },
    # 大户信号
    "top_trader_extreme_long": {
        "icon": "🐋",
        "title": "大户极度看多",
        "title_en": "Whale Extreme Long",
        "color": "yellow",
    },
    "top_trader_extreme_short": {
        "icon": "🐋",
        "title": "大户极度看空",
        "title_en": "Whale Extreme Short",
        "color": "yellow",
    },
    # 主动成交翻转
    "taker_ratio_flip_long": {
        "icon": "🔄",
        "title": "主动成交翻多",
        "title_en": "Taker Flip Long",
        "color": "green",
    },
    "taker_ratio_flip_short": {
        "icon": "🔄",
        "title": "主动成交翻空",
        "title_en": "Taker Flip Short",
        "color": "red",
    },
}

# 方向图标
DIRECTION_ICONS = {
    "BUY": "🟢",
    "SELL": "🔴",
    "ALERT": "⚠️",
}


def fmt_price(val: float) -> str:
    """格式化价格"""
    if val >= 1000:
        return f"${val:,.0f}"
    elif val >= 1:
        return f"${val:.2f}"
    elif val >= 0.01:
        return f"${val:.4f}"
    else:
        return f"${val:.6f}"


def fmt_volume(val: float) -> str:
    """格式化成交额"""
    if val >= 1e9:
        return f"${val/1e9:.2f}B"
    elif val >= 1e6:
        return f"${val/1e6:.1f}M"
    elif val >= 1e3:
        return f"${val/1e3:.0f}K"
    return f"${val:.0f}"


def fmt_pct(val: float, with_sign: bool = True) -> str:
    """格式化百分比"""
    if with_sign and val > 0:
        return f"+{val:.2f}%"
    return f"{val:.2f}%"


def fmt_ratio(val: float) -> str:
    """格式化比率"""
    return f"{val:.2f}"


class PGSignalFormatter:
    """PG 信号格式化器"""
    
    def __init__(self, lang: str = "zh"):
        self.lang = lang
    
    def format(self, signal) -> str:
        """
        格式化 PGSignal 为消息文本
        
        Args:
            signal: PGSignal 对象
        
        Returns:
            格式化后的消息文本
        """
        template = SIGNAL_TEMPLATES.get(signal.signal_type, {})
        icon = template.get("icon", "📊")
        title = template.get("title" if self.lang == "zh" else "title_en", signal.signal_type)
        dir_icon = DIRECTION_ICONS.get(signal.direction, "📊")
        
        # 基础信息
        symbol_clean = signal.symbol.replace("USDT", "")
        time_str = signal.timestamp.strftime("%H:%M:%S")
        
        lines = [
            f"{icon} {title} | {symbol_clean}",
            "",
        ]
        
        # 根据信号类型添加详情
        extra = signal.extra or {}
        
        if signal.signal_type in ["price_surge", "price_dump"]:
            change_pct = extra.get("change_pct", 0)
            lines.extend([
                f"├ 方向: {dir_icon} {signal.direction}",
                f"├ 价格: {fmt_price(signal.price)}",
                f"├ 涨跌: {fmt_pct(change_pct)}",
                f"└ 强度: {self._strength_bar(signal.strength)} {signal.strength}",
            ])
        
        elif signal.signal_type == "volume_spike":
            vol_ratio = extra.get("vol_ratio", 0)
            quote_volume = extra.get("quote_volume", 0)
            lines.extend([
                f"├ 放大: {vol_ratio:.1f}x",
                f"├ 成交额: {fmt_volume(quote_volume)}",
                f"└ 强度: {self._strength_bar(signal.strength)} {signal.strength}",
            ])
        
        elif signal.signal_type in ["taker_buy_dominance", "taker_sell_dominance"]:
            ratio = extra.get("buy_ratio", extra.get("sell_ratio", 0))
            lines.extend([
                f"├ 方向: {dir_icon} {signal.direction}",
                f"├ 占比: {ratio*100:.1f}%",
                f"├ 价格: {fmt_price(signal.price)}",
                f"└ 强度: {self._strength_bar(signal.strength)} {signal.strength}",
            ])
        
        elif signal.signal_type in ["oi_surge", "oi_dump"]:
            oi_change = extra.get("oi_change_pct", 0)
            oi_value = extra.get("oi_value", 0)
            lines.extend([
                f"├ 变化: {fmt_pct(oi_change)}",
                f"├ 持仓: {fmt_volume(oi_value)}",
                f"└ 强度: {self._strength_bar(signal.strength)} {signal.strength}",
            ])
        
        elif signal.signal_type in ["top_trader_extreme_long", "top_trader_extreme_short"]:
            ratio = extra.get("top_trader_ratio", 0)
            lines.extend([
                f"├ 多空比: {fmt_ratio(ratio)}",
                f"├ 方向: {dir_icon} {signal.direction}",
                f"└ 强度: {self._strength_bar(signal.strength)} {signal.strength}",
            ])
        
        elif signal.signal_type in ["taker_ratio_flip_long", "taker_ratio_flip_short"]:
            prev = extra.get("prev_ratio", 0)
            curr = extra.get("curr_ratio", 0)
            lines.extend([
                f"├ 方向: {dir_icon} {signal.direction}",
                f"├ 变化: {fmt_ratio(prev)} → {fmt_ratio(curr)}",
                f"└ 强度: {self._strength_bar(signal.strength)} {signal.strength}",
            ])
        
        else:
            # 通用格式
            lines.extend([
                f"├ 方向: {dir_icon} {signal.direction}",
                f"├ 强度: {self._strength_bar(signal.strength)} {signal.strength}",
                f"└ 详情: {signal.message}",
            ])
        
        # 时间戳
        lines.extend([
            "",
            f"⏰ {time_str}",
        ])
        
        return "\n".join(lines)
    
    def format_simple(self, signal) -> str:
        """简化格式 - 单行"""
        template = SIGNAL_TEMPLATES.get(signal.signal_type, {})
        icon = template.get("icon", "📊")
        dir_icon = DIRECTION_ICONS.get(signal.direction, "📊")
        symbol_clean = signal.symbol.replace("USDT", "")
        
        return f"{icon} {dir_icon} {symbol_clean} | {signal.message}"
    
    def format_batch(self, signals: list) -> str:
        """批量格式化多个信号"""
        if not signals:
            return "暂无信号"
        
        lines = [f"📡 实时信号 ({len(signals)}条)", ""]
        
        for sig in signals[:10]:  # 最多显示10条
            lines.append(self.format_simple(sig))
        
        if len(signals) > 10:
            lines.append(f"... 还有 {len(signals) - 10} 条")
        
        return "\n".join(lines)
    
    @staticmethod
    def _strength_bar(value: int, max_val: int = 100) -> str:
        """生成强度条"""
        pct = min(max(value / max_val, 0), 1)
        filled = int(pct * 10)
        return "█" * filled + "░" * (10 - filled)


# 单例
_formatter: Optional[PGSignalFormatter] = None

def get_pg_formatter(lang: str = "zh") -> PGSignalFormatter:
    """获取格式化器单例"""
    global _formatter
    if _formatter is None:
        _formatter = PGSignalFormatter(lang=lang)
    return _formatter
