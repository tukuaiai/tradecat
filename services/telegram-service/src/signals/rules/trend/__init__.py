"""
趋势类规则
"""
from ..base import SignalRule, ConditionType

SUPERTREND_RULES = [
    SignalRule(
        name="SuperTrend翻多",
        table="SuperTrend.py",
        category="trend",
        subcategory="supertrend",
        direction="BUY",
        strength=70,
        priority="high",
        condition_type=ConditionType.STATE_CHANGE,
        condition_config={"field": "方向", "from_values": ["空", "-1", "down"], "to_values": ["多", "1", "up"]},
        message_template="SuperTrend翻多",
        fields={}
    ),
    SignalRule(
        name="SuperTrend翻空",
        table="SuperTrend.py",
        category="trend",
        subcategory="supertrend",
        direction="SELL",
        strength=70,
        priority="high",
        condition_type=ConditionType.STATE_CHANGE,
        condition_config={"field": "方向", "from_values": ["多", "1", "up"], "to_values": ["空", "-1", "down"]},
        message_template="SuperTrend翻空",
        fields={}
    ),
]

PRECISE_TREND_RULES = [
    SignalRule(
        name="精准趋势翻多",
        table="超级精准趋势扫描器.py",
        category="trend",
        subcategory="precise",
        direction="BUY",
        strength=75,
        priority="high",
        condition_type=ConditionType.STATE_CHANGE,
        condition_config={"field": "趋势方向", "from_values": ["空", "down", "-1"], "to_values": ["多", "up", "1"]},
        message_template="精准趋势翻多 强度:{strength}",
        fields={"strength": "趋势强度"}
    ),
    SignalRule(
        name="精准趋势翻空",
        table="超级精准趋势扫描器.py",
        category="trend",
        subcategory="precise",
        direction="SELL",
        strength=75,
        priority="high",
        condition_type=ConditionType.STATE_CHANGE,
        condition_config={"field": "趋势方向", "from_values": ["多", "up", "1"], "to_values": ["空", "down", "-1"]},
        message_template="精准趋势翻空 强度:{strength}",
        fields={"strength": "趋势强度"}
    ),
    SignalRule(
        name="精准趋势强度突破",
        table="超级精准趋势扫描器.py",
        category="trend",
        subcategory="precise",
        direction="ALERT",
        strength=65,
        priority="medium",
        condition_type=ConditionType.THRESHOLD_CROSS_UP,
        condition_config={"field": "趋势强度", "threshold": 80},
        message_template="精准趋势强度突破80: {strength}",
        fields={"strength": "趋势强度"}
    ),
]

ICHIMOKU_RULES = [
    SignalRule(
        name="Ichimoku买入信号",
        table="Ichimoku.py",
        category="trend",
        subcategory="ichimoku",
        direction="BUY",
        strength=70,
        priority="high",
        condition_type=ConditionType.STATE_CHANGE,
        condition_config={"field": "信号", "from_values": ["卖出", "中性", "观望"], "to_values": ["买入"]},
        message_template="Ichimoku买入 强度:{strength}",
        fields={"strength": "强度"}
    ),
    SignalRule(
        name="Ichimoku卖出信号",
        table="Ichimoku.py",
        category="trend",
        subcategory="ichimoku",
        direction="SELL",
        strength=70,
        priority="high",
        condition_type=ConditionType.STATE_CHANGE,
        condition_config={"field": "信号", "from_values": ["买入", "中性", "观望"], "to_values": ["卖出"]},
        message_template="Ichimoku卖出 强度:{strength}",
        fields={"strength": "强度"}
    ),
]

ZERO_LAG_RULES = [
    SignalRule(
        name="零延迟趋势翻多",
        table="零延迟趋势扫描器.py",
        category="trend",
        subcategory="zerolag",
        direction="BUY",
        strength=70,
        priority="high",
        condition_type=ConditionType.STATE_CHANGE,
        condition_config={"field": "方向", "from_values": ["空", "down", "-1"], "to_values": ["多", "up", "1"]},
        message_template="零延迟趋势翻多 强度:{strength}",
        fields={"strength": "强度"}
    ),
    SignalRule(
        name="零延迟趋势翻空",
        table="零延迟趋势扫描器.py",
        category="trend",
        subcategory="zerolag",
        direction="SELL",
        strength=70,
        priority="high",
        condition_type=ConditionType.STATE_CHANGE,
        condition_config={"field": "方向", "from_values": ["多", "up", "1"], "to_values": ["空", "down", "-1"]},
        message_template="零延迟趋势翻空 强度:{strength}",
        fields={"strength": "强度"}
    ),
]

TREND_CLOUD_RULES = [
    SignalRule(
        name="趋势云翻多",
        table="趋势云反转扫描器.py",
        category="trend",
        subcategory="cloud",
        direction="BUY",
        strength=70,
        priority="high",
        condition_type=ConditionType.STATE_CHANGE,
        condition_config={"field": "方向", "from_values": ["空", "down", "-1"], "to_values": ["多", "up", "1"]},
        message_template="趋势云翻多 形态:{shape}",
        fields={"shape": "形态"}
    ),
    SignalRule(
        name="趋势云翻空",
        table="趋势云反转扫描器.py",
        category="trend",
        subcategory="cloud",
        direction="SELL",
        strength=70,
        priority="high",
        condition_type=ConditionType.STATE_CHANGE,
        condition_config={"field": "方向", "from_values": ["多", "up", "1"], "to_values": ["空", "down", "-1"]},
        message_template="趋势云翻空 形态:{shape}",
        fields={"shape": "形态"}
    ),
]

TRENDLINE_RULES = [
    SignalRule(
        name="趋势线翻多",
        table="趋势线榜单.py",
        category="trend",
        subcategory="trendline",
        direction="BUY",
        strength=65,
        priority="medium",
        condition_type=ConditionType.STATE_CHANGE,
        condition_config={"field": "趋势方向", "from_values": ["空", "down", "-1"], "to_values": ["多", "up", "1"]},
        message_template="趋势线翻多 距离:{dist}%",
        fields={"dist": "距离趋势线%"}
    ),
    SignalRule(
        name="趋势线翻空",
        table="趋势线榜单.py",
        category="trend",
        subcategory="trendline",
        direction="SELL",
        strength=65,
        priority="medium",
        condition_type=ConditionType.STATE_CHANGE,
        condition_config={"field": "趋势方向", "from_values": ["多", "up", "1"], "to_values": ["空", "down", "-1"]},
        message_template="趋势线翻空 距离:{dist}%",
        fields={"dist": "距离趋势线%"}
    ),
]

HA_RULES = [
    SignalRule(
        name="多空信号翻多",
        table="多空信号扫描器.py",
        category="trend",
        subcategory="ha",
        direction="BUY",
        strength=65,
        priority="medium",
        condition_type=ConditionType.STATE_CHANGE,
        condition_config={"field": "方向", "from_values": ["空", "down", "-1"], "to_values": ["多", "up", "1"]},
        message_template="多空信号翻多 强度:{strength}",
        fields={"strength": "强度"}
    ),
    SignalRule(
        name="多空信号翻空",
        table="多空信号扫描器.py",
        category="trend",
        subcategory="ha",
        direction="SELL",
        strength=65,
        priority="medium",
        condition_type=ConditionType.STATE_CHANGE,
        condition_config={"field": "方向", "from_values": ["多", "up", "1"], "to_values": ["空", "down", "-1"]},
        message_template="多空信号翻空 强度:{strength}",
        fields={"strength": "强度"}
    ),
]

VOLUME_SIGNAL_RULES = [
    SignalRule(
        name="量能偏向翻多",
        table="量能信号扫描器.py",
        category="trend",
        subcategory="volume_trend",
        direction="BUY",
        strength=60,
        priority="medium",
        condition_type=ConditionType.STATE_CHANGE,
        condition_config={"field": "方向", "from_values": ["空", "down", "-1"], "to_values": ["多", "up", "1"]},
        message_template="量能偏向翻多 多头:{bull}%",
        fields={"bull": "多头比例"}
    ),
    SignalRule(
        name="量能偏向翻空",
        table="量能信号扫描器.py",
        category="trend",
        subcategory="volume_trend",
        direction="SELL",
        strength=60,
        priority="medium",
        condition_type=ConditionType.STATE_CHANGE,
        condition_config={"field": "方向", "from_values": ["多", "up", "1"], "to_values": ["空", "down", "-1"]},
        message_template="量能偏向翻空 空头:{bear}%",
        fields={"bear": "空头比例"}
    ),
]

GC_RULES = [
    SignalRule(
        name="GC点趋势翻多",
        table="G，C点扫描器.py",
        category="trend",
        subcategory="gc",
        direction="BUY",
        strength=65,
        priority="medium",
        condition_type=ConditionType.STATE_CHANGE,
        condition_config={"field": "趋势方向", "from_values": ["空", "down", "-1"], "to_values": ["多", "up", "1"]},
        message_template="GC点趋势翻多 带宽:{score}",
        fields={"score": "带宽评分"}
    ),
    SignalRule(
        name="GC点趋势翻空",
        table="G，C点扫描器.py",
        category="trend",
        subcategory="gc",
        direction="SELL",
        strength=65,
        priority="medium",
        condition_type=ConditionType.STATE_CHANGE,
        condition_config={"field": "趋势方向", "from_values": ["多", "up", "1"], "to_values": ["空", "down", "-1"]},
        message_template="GC点趋势翻空 带宽:{score}",
        fields={"score": "带宽评分"}
    ),
]

TREND_RULES = (
    SUPERTREND_RULES + PRECISE_TREND_RULES + ICHIMOKU_RULES +
    ZERO_LAG_RULES + TREND_CLOUD_RULES + TRENDLINE_RULES +
    HA_RULES + VOLUME_SIGNAL_RULES + GC_RULES
)
