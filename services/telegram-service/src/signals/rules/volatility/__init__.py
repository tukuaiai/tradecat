"""
波动/通道类规则
"""
from ..base import SignalRule, ConditionType

BOLLINGER_RULES = [
    SignalRule(
        name="突破布林上轨",
        table="布林带扫描器.py",
        category="volatility",
        subcategory="bollinger",
        direction="SELL",
        strength=60,
        priority="medium",
        condition_type=ConditionType.CUSTOM,
        condition_config={"func": lambda p, c: p and (p.get("价格") or 0) < (p.get("上轨价格") or float("inf")) and (c.get("价格") or 0) > (c.get("上轨价格") or 0)},
        message_template="价格突破布林上轨 %b:{b:.2f}",
        fields={"b": "百分比b"}
    ),
    SignalRule(
        name="跌破布林下轨",
        table="布林带扫描器.py",
        category="volatility",
        subcategory="bollinger",
        direction="BUY",
        strength=60,
        priority="medium",
        condition_type=ConditionType.CUSTOM,
        condition_config={"func": lambda p, c: p and (p.get("价格") or float("inf")) > (p.get("下轨价格") or 0) and (c.get("价格") or float("inf")) < (c.get("下轨价格") or float("inf"))},
        message_template="价格跌破布林下轨 %b:{b:.2f}",
        fields={"b": "百分比b"}
    ),
    SignalRule(
        name="布林带收窄",
        table="布林带扫描器.py",
        category="volatility",
        subcategory="bollinger",
        direction="ALERT",
        strength=55,
        priority="low",
        condition_type=ConditionType.CUSTOM,
        condition_config={"func": lambda p, c: p and (p.get("带宽") or 10) > 5 and (c.get("带宽") or 5) < 3},
        message_template="布林带收窄 带宽:{bw:.2f}%",
        fields={"bw": "带宽"}
    ),
    SignalRule(
        name="布林带扩张",
        table="布林带扫描器.py",
        category="volatility",
        subcategory="bollinger",
        direction="ALERT",
        strength=55,
        priority="low",
        condition_type=ConditionType.CUSTOM,
        condition_config={"func": lambda p, c: p and (p.get("带宽") or 0) < 5 and (c.get("带宽") or 0) > 8},
        message_template="布林带扩张 带宽:{bw:.2f}%",
        fields={"bw": "带宽"}
    ),
    SignalRule(
        name="布林%b超买",
        table="布林带扫描器.py",
        category="volatility",
        subcategory="bollinger",
        direction="SELL",
        strength=55,
        priority="low",
        condition_type=ConditionType.THRESHOLD_CROSS_UP,
        condition_config={"field": "百分比b", "threshold": 1.0},
        message_template="布林%b超买: {b:.2f} (> 1.0)",
        fields={"b": "百分比b"}
    ),
]

ATR_RULES = [
    SignalRule(
        name="波动率突增",
        table="ATR波幅扫描器.py",
        category="volatility",
        subcategory="atr",
        direction="ALERT",
        strength=70,
        priority="high",
        condition_type=ConditionType.STATE_CHANGE,
        condition_config={"field": "波动分类", "from_values": ["低波动", "中波动"], "to_values": ["高波动", "极高波动"]},
        message_template="波动率突增: {cls} ATR%:{atr:.2f}%",
        fields={"cls": "波动分类", "atr": "ATR百分比"}
    ),
    SignalRule(
        name="波动率骤降",
        table="ATR波幅扫描器.py",
        category="volatility",
        subcategory="atr",
        direction="ALERT",
        strength=60,
        priority="medium",
        condition_type=ConditionType.STATE_CHANGE,
        condition_config={"field": "波动分类", "from_values": ["高波动", "极高波动"], "to_values": ["低波动"]},
        message_template="波动率骤降: {cls} ATR%:{atr:.2f}%",
        fields={"cls": "波动分类", "atr": "ATR百分比"}
    ),
]

DONCHIAN_RULES = [
    SignalRule(
        name="突破Donchian上轨",
        table="Donchian.py",
        category="volatility",
        subcategory="donchian",
        direction="BUY",
        strength=65,
        priority="medium",
        condition_type=ConditionType.CUSTOM,
        condition_config={"func": lambda p, c: p and (p.get("当前价格") or 0) < (p.get("上轨") or float("inf")) and (c.get("当前价格") or 0) >= (c.get("上轨") or float("inf"))},
        message_template="突破Donchian上轨",
        fields={}
    ),
    SignalRule(
        name="跌破Donchian下轨",
        table="Donchian.py",
        category="volatility",
        subcategory="donchian",
        direction="SELL",
        strength=65,
        priority="medium",
        condition_type=ConditionType.CUSTOM,
        condition_config={"func": lambda p, c: p and (p.get("当前价格") or float("inf")) > (p.get("下轨") or 0) and (c.get("当前价格") or float("inf")) <= (c.get("下轨") or 0)},
        message_template="跌破Donchian下轨",
        fields={}
    ),
]

KELTNER_RULES = [
    SignalRule(
        name="突破Keltner上轨",
        table="Keltner.py",
        category="volatility",
        subcategory="keltner",
        direction="BUY",
        strength=60,
        priority="medium",
        condition_type=ConditionType.CUSTOM,
        condition_config={"func": lambda p, c: p and (p.get("当前价格") or 0) < (p.get("上轨") or float("inf")) and (c.get("当前价格") or 0) >= (c.get("上轨") or float("inf"))},
        message_template="突破Keltner上轨",
        fields={}
    ),
    SignalRule(
        name="跌破Keltner下轨",
        table="Keltner.py",
        category="volatility",
        subcategory="keltner",
        direction="SELL",
        strength=60,
        priority="medium",
        condition_type=ConditionType.CUSTOM,
        condition_config={"func": lambda p, c: p and (p.get("当前价格") or float("inf")) > (p.get("下轨") or 0) and (c.get("当前价格") or float("inf")) <= (c.get("下轨") or 0)},
        message_template="跌破Keltner下轨",
        fields={}
    ),
]

SUPPORT_RESISTANCE_RULES = [
    SignalRule(
        name="接近支撑位",
        table="全量支撑阻力扫描器.py",
        category="volatility",
        subcategory="sr",
        direction="BUY",
        strength=60,
        priority="medium",
        condition_type=ConditionType.CUSTOM,
        condition_config={"func": lambda p, c: (c.get("距支撑百分比") or 100) < 1.5},
        message_template="接近支撑位 距离:{dist:.2f}%",
        fields={"dist": "距支撑百分比"}
    ),
    SignalRule(
        name="接近阻力位",
        table="全量支撑阻力扫描器.py",
        category="volatility",
        subcategory="sr",
        direction="SELL",
        strength=60,
        priority="medium",
        condition_type=ConditionType.CUSTOM,
        condition_config={"func": lambda p, c: (c.get("距阻力百分比") or 100) < 1.5},
        message_template="接近阻力位 距离:{dist:.2f}%",
        fields={"dist": "距阻力百分比"}
    ),
]

VWAP_RULES = [
    SignalRule(
        name="突破VWAP上方",
        table="VWAP离线信号扫描.py",
        category="volatility",
        subcategory="vwap",
        direction="BUY",
        strength=55,
        priority="low",
        condition_type=ConditionType.CUSTOM,
        condition_config={"func": lambda p, c: p and (p.get("偏离百分比") or 0) < 0 and (c.get("偏离百分比") or 0) > 0},
        message_template="价格突破VWAP上方 偏离:{dev:.2f}%",
        fields={"dev": "偏离百分比"}
    ),
    SignalRule(
        name="跌破VWAP下方",
        table="VWAP离线信号扫描.py",
        category="volatility",
        subcategory="vwap",
        direction="SELL",
        strength=55,
        priority="low",
        condition_type=ConditionType.CUSTOM,
        condition_config={"func": lambda p, c: p and (p.get("偏离百分比") or 0) > 0 and (c.get("偏离百分比") or 0) < 0},
        message_template="价格跌破VWAP下方 偏离:{dev:.2f}%",
        fields={"dev": "偏离百分比"}
    ),
]

VOLATILITY_RULES = (
    BOLLINGER_RULES + ATR_RULES + DONCHIAN_RULES +
    KELTNER_RULES + SUPPORT_RESISTANCE_RULES + VWAP_RULES
)
