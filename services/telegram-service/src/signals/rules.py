"""
信号规则配置
定义各种信号触发条件
"""

# 信号规则列表
SIGNAL_RULES = [
    # ==================== RSI 信号 ====================
    {
        "name": "RSI超卖反弹",
        "table": "智能RSI扫描器.py",
        "condition": lambda prev, curr: prev and prev.get('RSI6', 100) < 30 and curr.get('RSI6', 0) > 30,
        "direction": "BUY",
        "strength": 70,
        "message": "RSI6 从超卖区({prev_val:.1f})回升至{curr_val:.1f}",
        "fields": {"prev_val": "RSI6", "curr_val": "RSI6"}
    },
    {
        "name": "RSI超买回落",
        "table": "智能RSI扫描器.py",
        "condition": lambda prev, curr: prev and prev.get('RSI6', 0) > 70 and curr.get('RSI6', 100) < 70,
        "direction": "SELL",
        "strength": 70,
        "message": "RSI6 从超买区({prev_val:.1f})回落至{curr_val:.1f}",
        "fields": {"prev_val": "RSI6", "curr_val": "RSI6"}
    },
    
    # ==================== MACD 信号 ====================
    {
        "name": "MACD金叉",
        "table": "MACD柱状扫描器.py",
        "condition": lambda prev, curr: (
            prev and 
            prev.get('DIF', 0) < prev.get('DEA', 0) and 
            curr.get('DIF', 0) > curr.get('DEA', 0)
        ),
        "direction": "BUY",
        "strength": 65,
        "message": "MACD金叉: DIF({dif:.4f})上穿DEA({dea:.4f})",
        "fields": {"dif": "DIF", "dea": "DEA"}
    },
    {
        "name": "MACD死叉",
        "table": "MACD柱状扫描器.py",
        "condition": lambda prev, curr: (
            prev and 
            prev.get('DIF', 0) > prev.get('DEA', 0) and 
            curr.get('DIF', 0) < curr.get('DEA', 0)
        ),
        "direction": "SELL",
        "strength": 65,
        "message": "MACD死叉: DIF({dif:.4f})下穿DEA({dea:.4f})",
        "fields": {"dif": "DIF", "dea": "DEA"}
    },
    {
        "name": "MACD柱状图转正",
        "table": "MACD柱状扫描器.py",
        "condition": lambda prev, curr: prev and prev.get('MACD柱状图', 0) < 0 and curr.get('MACD柱状图', 0) > 0,
        "direction": "BUY",
        "strength": 55,
        "message": "MACD柱状图由负转正",
        "fields": {}
    },
    
    # ==================== KDJ 信号 ====================
    {
        "name": "KDJ金叉",
        "table": "KDJ随机指标扫描器.py",
        "condition": lambda prev, curr: (
            prev and 
            prev.get('K值', 0) < prev.get('D值', 0) and 
            curr.get('K值', 0) > curr.get('D值', 0) and
            curr.get('J值', 100) < 80  # J值不在超买区
        ),
        "direction": "BUY",
        "strength": 60,
        "message": "KDJ金叉: K({k:.1f})上穿D({d:.1f}), J={j:.1f}",
        "fields": {"k": "K值", "d": "D值", "j": "J值"}
    },
    {
        "name": "KDJ超卖",
        "table": "KDJ随机指标扫描器.py",
        "condition": lambda prev, curr: curr.get('J值', 100) < 0,
        "direction": "BUY",
        "strength": 75,
        "message": "KDJ超卖: J值={j:.1f}",
        "fields": {"j": "J值"}
    },
    
    # ==================== 布林带信号 ====================
    {
        "name": "布林带下轨突破",
        "table": "布林带扫描器.py",
        "condition": lambda prev, curr: (
            prev and 
            prev.get('当前价格', 0) > prev.get('下轨', 0) and 
            curr.get('当前价格', 0) < curr.get('下轨', float('inf'))
        ),
        "direction": "BUY",  # 超卖可能反弹
        "strength": 60,
        "message": "价格跌破布林带下轨",
        "fields": {}
    },
    {
        "name": "布林带上轨突破",
        "table": "布林带扫描器.py",
        "condition": lambda prev, curr: (
            prev and 
            prev.get('当前价格', 0) < prev.get('上轨', float('inf')) and 
            curr.get('当前价格', 0) > curr.get('上轨', 0)
        ),
        "direction": "SELL",  # 超买可能回落
        "strength": 60,
        "message": "价格突破布林带上轨",
        "fields": {}
    },
    
    # ==================== ATR 波动信号 ====================
    {
        "name": "波动率突增",
        "table": "ATR波幅扫描器.py",
        "condition": lambda prev, curr: (
            prev and 
            prev.get('波动分类') == '低波动' and 
            curr.get('波动分类') in ['高波动', '极高波动']
        ),
        "direction": "ALERT",
        "strength": 80,
        "message": "波动率突增: {prev_class} → {curr_class}",
        "fields": {"prev_class": "波动分类", "curr_class": "波动分类"}
    },
    
    # ==================== 趋势信号 ====================
    {
        "name": "SuperTrend翻多",
        "table": "SuperTrend.py",
        "condition": lambda prev, curr: prev and prev.get('趋势') == '空' and curr.get('趋势') == '多',
        "direction": "BUY",
        "strength": 70,
        "message": "SuperTrend趋势翻多",
        "fields": {}
    },
    {
        "name": "SuperTrend翻空",
        "table": "SuperTrend.py",
        "condition": lambda prev, curr: prev and prev.get('趋势') == '多' and curr.get('趋势') == '空',
        "direction": "SELL",
        "strength": 70,
        "message": "SuperTrend趋势翻空",
        "fields": {}
    },
]

# 监控的周期
TIMEFRAMES = ['1h', '4h', '1d']

# 信号冷却时间（秒），同一币种同一信号在此时间内不重复触发
SIGNAL_COOLDOWN = 3600  # 1小时

# 最小成交额过滤（USDT）
MIN_VOLUME = 100000
