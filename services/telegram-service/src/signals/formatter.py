"""
信号模板格式化器
生成完整的信号推送消息
"""
from typing import Dict, Optional, Any
from datetime import datetime
import time

from cards.i18n import gettext as _t


def strength_bar(value: float, max_val: float = 100) -> str:
    """生成强度条"""
    if value is None:
        return "░░░░░░░░░░"
    pct = min(max(value / max_val, 0), 1)
    filled = int(pct * 10)
    return "█" * filled + "░" * (10 - filled)


def fmt_price(val: Any) -> str:
    """格式化价格"""
    if val is None:
        return "-"
    try:
        v = float(val)
        if v >= 1000:
            return f"${v:,.0f}"
        elif v >= 1:
            return f"${v:.2f}"
        else:
            return f"${v:.4f}"
    except Exception:
        return str(val)


def fmt_pct(val: Any, with_sign: bool = True) -> str:
    """格式化百分比"""
    if val is None:
        return "-"
    try:
        v = float(val)
        if with_sign and v > 0:
            return f"+{v:.2f}%"
        return f"{v:.2f}%"
    except Exception:
        return str(val)


def fmt_vol(val: Any) -> str:
    """格式化成交额"""
    if val is None:
        return "-"
    try:
        v = float(val)
        if v >= 1e9:
            return f"${v/1e9:.2f}B"
        elif v >= 1e6:
            return f"${v/1e6:.1f}M"
        elif v >= 1e3:
            return f"${v/1e3:.0f}K"
        return f"${v:.0f}"
    except Exception:
        return str(val)


def fmt_num(val: Any, decimals: int = 2) -> str:
    """格式化数字"""
    if val is None:
        return "-"
    try:
        v = float(val)
        if decimals == 0:
            return f"{v:,.0f}"
        return f"{v:.{decimals}f}"
    except Exception:
        return str(val)


def fmt_change(prev: Any, curr: Any) -> str:
    """格式化变化百分比"""
    if prev is None or curr is None:
        return ""
    try:
        p, c = float(prev), float(curr)
        if p == 0:
            return ""
        pct = (c - p) / abs(p) * 100
        if pct > 0:
            return f"(+{pct:.1f}%)"
        return f"({pct:.1f}%)"
    except Exception:
        return ""


def fmt_arrow(prev: Any, curr: Any) -> str:
    """格式化前值箭头"""
    if prev is None:
        return str(curr) if curr is not None else "-"
    return f"{prev} ⏩ {curr}"


class SignalFormatter:
    """信号格式化器"""

    def __init__(self):
        self.last_trigger: Dict[str, float] = {}  # {rule_symbol_tf: timestamp}

    def format_signal(
        self,
        symbol: str,
        direction: str,
        rule_name: str,
        timeframe: str,
        strength: int,
        curr_data: Dict[str, Dict[str, Any]],
        prev_data: Optional[Dict[str, Dict[str, Any]]] = None,
        rule_message: str = "",
        lang: str = "zh_CN"
    ) -> str:
        """
        格式化完整信号消息
        
        Args:
            symbol: 交易对
            direction: BUY/SELL/ALERT
            rule_name: 规则名称
            timeframe: 周期
            strength: 强度 0-100
            curr_data: 当前数据 {table: {field: value}}
            prev_data: 前值数据 {table: {field: value}}
            lang: 语言代码
            rule_message: 规则消息
        """
        icon = {"BUY": "🟢", "SELL": "🔴", "ALERT": "⚠️"}.get(direction, "📊")

        # 获取各表数据
        basic = curr_data.get("基础数据同步器.py", {})
        basic_prev = (prev_data or {}).get("基础数据同步器.py", {})
        futures = curr_data.get("期货情绪聚合表.py", {})
        futures_prev = (prev_data or {}).get("期货情绪聚合表.py", {})
        rsi = curr_data.get("智能RSI扫描器.py", {})
        rsi_prev = (prev_data or {}).get("智能RSI扫描器.py", {})
        kdj = curr_data.get("KDJ随机指标扫描器.py", {})
        curr_data.get("MACD柱状扫描器.py", {})
        (prev_data or {}).get("MACD柱状扫描器.py", {})
        boll = curr_data.get("布林带扫描器.py", {})
        obv = curr_data.get("OBV能量潮扫描器.py", {})
        obv_prev = (prev_data or {}).get("OBV能量潮扫描器.py", {})
        cvd = curr_data.get("CVD信号排行榜.py", {})
        vol_ratio = curr_data.get("成交量比率扫描器.py", {})
        vol_ratio_prev = (prev_data or {}).get("成交量比率扫描器.py", {})
        sr = curr_data.get("全量支撑阻力扫描器.py", {})
        st = curr_data.get("SuperTrend.py", {})
        st_prev = (prev_data or {}).get("SuperTrend.py", {})
        precise = curr_data.get("超级精准趋势扫描器.py", {})
        curr_data.get("Ichimoku.py", {})
        smc = curr_data.get("大资金操盘扫描器.py", {})
        pattern = curr_data.get("K线形态扫描器.py", {})
        atr = curr_data.get("ATR波幅扫描器.py", {})
        atr_prev = (prev_data or {}).get("ATR波幅扫描器.py", {})
        liquidity = curr_data.get("流动性扫描器.py", {})
        scalp = curr_data.get("剥头皮信号扫描器.py", {})

        # 构建消息
        lines = [f"{icon} {direction} {symbol}", ""]

        # 💰 行情
        price = basic.get("当前价格") or basic.get("收盘价")
        price_prev = basic_prev.get("当前价格") or basic_prev.get("收盘价")
        lines.append(_t("signal.section.market", None, lang=lang))
        lines.append(f"├ 价格: {fmt_price(price_prev)} ⏩ {fmt_price(price)} {fmt_change(price_prev, price)}")
        lines.append(f"├ 振幅: {fmt_pct(basic.get('振幅'), False)}")

        ratio = basic.get("主动买卖比")
        ratio_prev = basic_prev.get("主动买卖比")
        ratio_label = "买盘主导" if (ratio or 1) > 1.1 else ("卖盘主导" if (ratio or 1) < 0.9 else "均衡")
        lines.append(f"├ 买卖比: {fmt_num(ratio_prev)} ⏩ {fmt_num(ratio)} {fmt_change(ratio_prev, ratio)} {ratio_label}")
        lines.append(f"├ 成交额: {fmt_vol(basic.get('成交额'))}")
        lines.append(f"├ 净流入: {fmt_vol(basic.get('资金流向'))}")
        lines.append(f"└ 交易次数: {fmt_num(basic.get('交易次数'), 0)}")
        lines.append("")

        # 📊 合约
        if futures:
            lines.append(_t("signal.section.futures", None, lang=lang))
            lines.append(f"├ 持仓: {fmt_vol(futures.get('持仓金额'))} ({fmt_pct(futures.get('持仓变动%'))})")

            big_ratio = futures.get("大户多空比")
            big_prev = futures_prev.get("大户多空比")
            lines.append(f"├ 大户多空: {fmt_num(big_prev)} ⏩ {fmt_num(big_ratio)} {fmt_change(big_prev, big_ratio)}")

            all_ratio = futures.get("全体多空比")
            all_prev = futures_prev.get("全体多空比")
            lines.append(f"├ 全体多空: {fmt_num(all_prev)} ⏩ {fmt_num(all_ratio)} {fmt_change(all_prev, all_ratio)}")

            taker = futures.get("主动成交多空比")
            taker_prev = futures_prev.get("主动成交多空比")
            lines.append(f"├ 主动多空: {fmt_num(taker_prev)} ⏩ {fmt_num(taker)} {fmt_change(taker_prev, taker)}")

            lines.append(f"├ 情绪差值: {fmt_num(futures.get('情绪差值'))}")
            lines.append(f"├ 风险分: {strength_bar(futures.get('风险分'))} {fmt_num(futures.get('风险分'), 0)}")
            lines.append(f"├ OI连续: {futures.get('OI连续根数')}根")
            lines.append(f"└ 情绪动量: 大户{fmt_num(futures.get('大户情绪动量'))} 主动{fmt_num(futures.get('主动情绪动量'))}")
            lines.append("")

        # 📉 动量
        lines.append(_t("signal.section.momentum", None, lang=lang))
        adx = curr_data.get("ADX.py", {})
        adx_val = adx.get("ADX")
        di_label = "+DI>-DI" if (adx.get("正向DI") or 0) > (adx.get("负向DI") or 0) else "-DI>+DI"
        lines.append(f"├ ADX: {strength_bar(adx_val, 50)} {fmt_num(adx_val)} {di_label}")

        cci = curr_data.get("CCI.py", {})
        lines.append(f"├ CCI: {fmt_num(cci.get('CCI'))}")

        wr = curr_data.get("WilliamsR.py", {})
        lines.append(f"├ WR: {fmt_num(wr.get('WilliamsR'))}")

        mfi = curr_data.get("MFI资金流量扫描器.py", {})
        lines.append(f"├ MFI: {strength_bar(mfi.get('MFI值'))} {fmt_num(mfi.get('MFI值'))}")

        lines.append(f"├ KDJ: J={fmt_num(kdj.get('J值'))} K={fmt_num(kdj.get('K值'))} D={fmt_num(kdj.get('D值'))}")

        if rsi:
            rsi7 = rsi.get("RSI7")
            rsi7_prev = rsi_prev.get("RSI7")
            lines.append(f"├ RSI7: {fmt_num(rsi7_prev)} ⏩ {fmt_num(rsi7)} {fmt_change(rsi7_prev, rsi7)}")
            lines.append(f"├ RSI位置: {rsi.get('位置', '-')}")
            lines.append(f"└ RSI背离: {rsi.get('背离', '无')}")
        lines.append("")

        # 📊 量价
        lines.append(_t("signal.section.volume", None, lang=lang))
        obv_val = obv.get("OBV值")
        obv_prev_val = obv_prev.get("OBV值")
        lines.append(f"├ OBV: {fmt_num(obv_prev_val)} ⏩ {fmt_num(obv_val)} {fmt_change(obv_prev_val, obv_val)}")
        lines.append(f"├ CVD: {fmt_num(cvd.get('CVD值'))}")

        vr = vol_ratio.get("量比")
        vr_prev = vol_ratio_prev.get("量比")
        vr_label = "放量" if (vr or 0) > 1.5 else ("缩量" if (vr or 0) < 0.7 else "")
        lines.append(f"├ 量比: {fmt_num(vr_prev)} ⏩ {fmt_num(vr)} {fmt_change(vr_prev, vr)} {vr_label}")

        ha = curr_data.get("多空信号扫描器.py", {})
        bull = ha.get("多头比例") or 50
        lines.append(f"└ 多空力量: {'多' if bull > 50 else '空'}{strength_bar(bull if bull > 50 else 100-bull)} {fmt_num(bull, 0)}%")
        lines.append("")

        # 📍 关键位
        lines.append(_t("signal.section.levels", None, lang=lang))
        lines.append(f"├ 支撑: {fmt_price(sr.get('支撑位'))} (距{fmt_pct(sr.get('距支撑百分比'), False)})")
        lines.append(f"├ 阻力: {fmt_price(sr.get('阻力位'))} (距{fmt_pct(sr.get('距阻力百分比'), False)})")
        lines.append(f"└ 布林%b: {fmt_num(boll.get('百分比b'))}")
        lines.append("")

        # 📈 趋势
        lines.append(_t("signal.section.trend", None, lang=lang))
        st_dir = st.get("方向")
        st_prev_dir = st_prev.get("方向")
        lines.append(f"├ SuperTrend: {st_prev_dir} ⏩ {st_dir}" if st_prev_dir != st_dir else f"├ SuperTrend: {st_dir}")

        lines.append(f"├ 精准趋势: {precise.get('趋势方向')} {strength_bar(precise.get('趋势强度'))} {fmt_num(precise.get('趋势强度'), 0)}")
        lines.append(f"└ 量能偏向: {precise.get('量能偏向', '-')}")
        lines.append("")

        # 🏦 智能资金
        if smc:
            lines.append("🏦 智能资金")
            lines.append(f"├ 偏向: {smc.get('偏向', '-')}")
            ob_up = smc.get("订单块上沿")
            ob_down = smc.get("订单块下沿")
            if ob_up and ob_down:
                lines.append(f"├ 订单块: {fmt_price(ob_down)}-{fmt_price(ob_up)}")
            lines.append(f"├ 缺口: {smc.get('缺口类型', '-')}")
            lines.append(f"├ 结构: {smc.get('结构事件', '-')}")
            lines.append(f"└ 评分: {strength_bar(smc.get('评分'))} {fmt_num(smc.get('评分'), 0)}")
            lines.append("")

        # 🕯️ K线形态
        if pattern and pattern.get("形态类型"):
            lines.append("🕯️ K线形态")
            lines.append(f"├ 形态: {pattern.get('形态类型', '-')}")
            lines.append(f"├ 数量: {pattern.get('检测数量', 0)}个")
            lines.append(f"└ 强度: {strength_bar(pattern.get('强度'))} {fmt_num(pattern.get('强度'), 0)}")
            lines.append("")

        # ⚡ 波动
        lines.append("⚡ 波动")
        atr_pct = atr.get("ATR百分比")
        atr_pct_prev = atr_prev.get("ATR百分比")
        lines.append(f"├ ATR%: {fmt_pct(atr_pct_prev, False)} ⏩ {fmt_pct(atr_pct, False)} {fmt_change(atr_pct_prev, atr_pct)}")
        lines.append(f"├ 波动: {atr.get('波动分类', '-')}")
        lines.append(f"└ 流动性: {strength_bar(liquidity.get('流动性得分'))} {fmt_num(liquidity.get('流动性得分'), 0)}")
        lines.append("")

        # 🎯 剥头皮
        if scalp:
            lines.append("🎯 剥头皮")
            lines.append(f"├ 信号: {scalp.get('剥头皮信号', '-')}")
            lines.append(f"└ RSI: {fmt_num(scalp.get('RSI'))}")
            lines.append("")

        # 📌 信号详情
        lines.append(f"📌 {rule_name}")
        lines.append(f"├ 周期: {timeframe}")
        lines.append(f"├ 强度: {strength_bar(strength)} {strength}")
        if rule_message:
            lines.append(f"└ 📝 {rule_message}")
        lines.append("")

        # 时间
        now = datetime.now()
        lines.append(f"⏰ {now.strftime('%Y-%m-%d %H:%M')}")

        # 上次触发
        key = f"{rule_name}_{symbol}_{timeframe}"
        last = self.last_trigger.get(key)
        if last:
            delta = int(time.time() - last)
            hours = delta // 3600
            mins = (delta % 3600) // 60
            lines.append(f"🔄 上次触发: {hours}h{mins}m前")

        self.last_trigger[key] = time.time()

        return "\n".join(lines)

    def format_simple(
        self,
        symbol: str,
        direction: str,
        rule_name: str,
        timeframe: str,
        strength: int,
        price: float,
        message: str
    ) -> str:
        """简化版信号格式"""
        icon = {"BUY": "🟢", "SELL": "🔴", "ALERT": "⚠️"}.get(direction, "📊")

        return f"""
{icon} {direction} | {symbol}

📌 {rule_name}
⏱ 周期: {timeframe}
💰 价格: {fmt_price(price)}
📊 强度: {strength_bar(strength)} {strength}%

💬 {message}
"""


# 单例
_formatter: Optional[SignalFormatter] = None

def get_formatter() -> SignalFormatter:
    global _formatter
    if _formatter is None:
        _formatter = SignalFormatter()
    return _formatter
