"""大资金操盘扫描器 - Smart Money Concepts 完整复刻"""
import pandas as pd
import numpy as np
from dataclasses import dataclass
from typing import Dict, List, Optional, Sequence
from ..base import Indicator, IndicatorMeta, register

PIVOT = 5


@dataclass
class StructureState:
    bias: str
    event: str
    score: float
    swing_high: Optional[float]
    swing_low: Optional[float]


def calc_atr(close: pd.Series, period: int = 14) -> float:
    returns = close.pct_change().abs()
    return float(returns.ewm(span=period).mean().iloc[-1] * close.iloc[-1])


def normalize_strength(value: float, range_tuple: tuple) -> float:
    lo, hi = range_tuple
    if hi == lo:
        return 0.5
    return max(0, min(1, (value - lo) / (hi - lo)))


def identify_swing_points(df: pd.DataFrame, pivot: int) -> List[Dict]:
    """识别摆动高低点（向量化优化）"""
    points = []
    n = len(df)
    if n < pivot * 2 + 1:
        return points
    
    high = df["high"].values
    low = df["low"].values
    
    # 使用滚动窗口找局部极值
    for idx in range(pivot, n - pivot):
        window_high = high[idx - pivot : idx + pivot + 1]
        window_low = low[idx - pivot : idx + pivot + 1]
        
        if high[idx] >= window_high.max():
            points.append({"index": idx, "price": float(high[idx]), "type": "high"})
        if low[idx] <= window_low.min():
            points.append({"index": idx, "price": float(low[idx]), "type": "low"})
    
    return points


def evaluate_structure(df: pd.DataFrame, pivots: Sequence[Dict]) -> StructureState:
    ema = df["close"].ewm(span=34, adjust=False).mean()
    bias = "bull" if df["close"].iloc[-1] >= ema.iloc[-1] else "bear"
    swing_high = next((p["price"] for p in reversed(pivots) if p["type"] == "high"), None)
    swing_low = next((p["price"] for p in reversed(pivots) if p["type"] == "low"), None)
    close = df["close"].iloc[-1]

    event = "区间震荡"
    score = 0.0
    if swing_high and close > swing_high:
        event = "多头突破"
        score += 3.5
    if swing_low and close < swing_low:
        event = "空头突破"
        score -= 3.5
    if bias == "bull" and swing_low and close < swing_low:
        event = "结构反转向下"
        score -= 4.5
    elif bias == "bear" and swing_high and close > swing_high:
        event = "结构反转向上"
        score += 4.5

    atr = calc_atr(df["close"], period=14)
    anchor = swing_low if bias == "bull" else swing_high
    if anchor:
        distance = (close - anchor) if bias == "bull" else (anchor - close)
        score += normalize_strength(distance, (-atr * 2, atr * 2)) * 0.2

    return StructureState(bias=bias, event=event, score=score, swing_high=swing_high, swing_low=swing_low)


def detect_order_block(df: pd.DataFrame, bias: str) -> Dict:
    recent = df.tail(8)
    block = {"type": "无", "upper": 0.0, "lower": 0.0}
    if bias == "bull":
        bearish = recent[recent["close"] < recent["open"]]
        if not bearish.empty:
            candle = bearish.iloc[-1]
            block = {"type": "多头订单块", "upper": float(max(candle["open"], candle["close"])),
                     "lower": float(min(candle["low"], candle["open"]))}
    else:
        bullish = recent[recent["close"] > recent["open"]]
        if not bullish.empty:
            candle = bullish.iloc[-1]
            block = {"type": "空头订单块", "upper": float(max(candle["open"], candle["high"])),
                     "lower": float(min(candle["open"], candle["close"]))}
    return block


def detect_fvg(df: pd.DataFrame) -> Optional[Dict]:
    if len(df) < 5:
        return None
    for offset in range(2, 6):
        i = len(df) - offset
        if i - 2 < 0:
            break
        high_prev = df["high"].iloc[i - 2]
        low_prev = df["low"].iloc[i - 2]
        high_curr = df["high"].iloc[i]
        low_curr = df["low"].iloc[i]
        if df["low"].iloc[i - 1] > high_prev and low_curr > high_prev:
            return {"type": "多头缺口", "gap_top": low_curr, "gap_bottom": high_prev}
        if df["high"].iloc[i - 1] < low_prev and high_curr < low_prev:
            return {"type": "空头缺口", "gap_top": low_prev, "gap_bottom": high_curr}
    return None


def calc_zone(df: pd.DataFrame, lookback: int) -> Dict:
    recent = df.tail(min(lookback, len(df)))
    high = recent["high"].max()
    low = recent["low"].min()
    mid = (high + low) / 2
    close = recent["close"].iloc[-1]
    if close >= high:
        zone = "极端溢价"
    elif close >= mid:
        zone = "溢价区"
    elif close <= low:
        zone = "极端折价"
    elif close <= mid:
        zone = "折价区"
    else:
        zone = "均衡区"
    return {"zone": zone, "high": float(high), "low": float(low), "mid": float(mid)}


def combine_signal(structure: StructureState, order_block: Dict, fvg: Optional[Dict], zone: Dict) -> Dict:
    score = structure.score
    if order_block["type"] == "多头订单块":
        score += 1.5
    elif order_block["type"] == "空头订单块":
        score -= 1.5
    if fvg:
        score += 1.2 if fvg["type"] == "多头缺口" else -1.2
    if structure.bias == "bull" and zone["zone"].startswith("折价"):
        score += 1.0
    if structure.bias == "bear" and zone["zone"].startswith("溢价"):
        score -= 1.0

    direction = "多头" if score >= 0 else "空头"
    if score >= 5:
        signal = "买入"
    elif score <= -5:
        signal = "卖出"
    else:
        signal = "观望"
    return {"signal": signal, "direction": direction, "score": round(score, 2)}


@register
class TvBigMoney(Indicator):
    meta = IndicatorMeta(name="大资金操盘扫描器.py", lookback=250, is_incremental=False, min_data=50)

    def compute(self, df: pd.DataFrame, symbol: str, interval: str) -> pd.DataFrame:
        if not self._check_data(df):
            return self._make_insufficient_result(df, symbol, interval, {"信号": None})

        pivots = identify_swing_points(df, PIVOT)
        structure = evaluate_structure(df, pivots)
        order_block = detect_order_block(df, structure.bias)
        fvg = detect_fvg(df)
        zone = calc_zone(df, 100)
        result = combine_signal(structure, order_block, fvg, zone)

        return self._make_result(df, symbol, interval, {
            "信号": result["signal"],
            "方向": result["direction"],
            "评分": result["score"],
            "结构事件": structure.event,
            "偏向": "多头" if structure.bias == "bull" else "空头",
            "订单块": order_block["type"],
            "订单块上沿": order_block["upper"],
            "订单块下沿": order_block["lower"],
            "缺口类型": fvg["type"] if fvg else "无",
            "价格区域": zone["zone"],
            "摆动高点": structure.swing_high,
            "摆动低点": structure.swing_low,
        })
