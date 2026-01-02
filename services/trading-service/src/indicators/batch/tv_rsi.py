"""智能RSI扫描器 - 多周期RSI与背离检测完整复刻"""
import numpy as np
import pandas as pd
from typing import Dict, Optional, Tuple
from ..base import Indicator, IndicatorMeta, register
from ..safe_calc import safe_rsi, safe_ema, safe_atr

RSI_PERIODS = [7, 14, 21]
EMA_TREND_PERIOD = 34
ATR_PERIOD = 14
MIN_DATA = 15  # 最小数据量


def calc_rsi(series: pd.Series, period: int) -> pd.Series:
    """兼容旧接口"""
    rsi, _ = safe_rsi(series, period, min_period=3)
    return rsi


def calc_dynamic_threshold(atr_normalized: float) -> Tuple[float, float]:
    base_overbought, base_oversold = 70, 30
    volatility_factor = 1.0 + (atr_normalized - 0.5) * 0.2
    overbought = min(80, base_overbought * volatility_factor)
    oversold = max(20, base_oversold / volatility_factor)
    return overbought, oversold


def detect_divergence(df: pd.DataFrame, rsi: pd.Series, lookback: int = 50) -> Tuple[str, float]:
    if len(df) < lookback or rsi.isna().sum() > len(rsi) * 0.1:
        return "none", 0.0
    recent_data = df.tail(lookback).copy()
    recent_rsi = rsi.tail(lookback)
    price_highs, price_lows = [], []
    rsi_highs, rsi_lows = [], []

    for i in range(5, len(recent_data) - 5):
        price_window = recent_data["high"].iloc[i-5:i+6]
        if recent_data["high"].iloc[i] == price_window.max():
            price_highs.append(recent_data["high"].iloc[i])
            rsi_highs.append(recent_rsi.iloc[i])
        price_window_low = recent_data["low"].iloc[i-5:i+6]
        if recent_data["low"].iloc[i] == price_window_low.min():
            price_lows.append(recent_data["low"].iloc[i])
            rsi_lows.append(recent_rsi.iloc[i])

    if len(price_highs) >= 2 and len(price_lows) >= 2:
        if price_highs[-1] > price_highs[-2] and rsi_highs[-1] < rsi_highs[-2]:
            strength = (rsi_highs[-2] - rsi_highs[-1]) / rsi_highs[-2] * 100
            return "顶背离", min(strength, 100.0)
        if price_lows[-1] < price_lows[-2] and rsi_lows[-1] > rsi_lows[-2]:
            strength = (rsi_lows[-1] - rsi_lows[-2]) / rsi_lows[-2] * 100
            return "底背离", min(strength, 100.0)
    return "无背离", 0.0


def evaluate_rsi_state(df: pd.DataFrame, rsi_7: pd.Series, rsi_14: pd.Series, 
                       rsi_21: pd.Series, overbought: float, oversold: float) -> Dict:
    current_rsi_7 = rsi_7.iloc[-1]
    current_rsi_14 = rsi_14.iloc[-1]
    current_rsi_21 = rsi_21.iloc[-1]
    rsi_values = [current_rsi_7, current_rsi_14, current_rsi_21]
    valid_rsi = [v for v in rsi_values if not np.isnan(v)]

    if not valid_rsi:
        return {"signal": "观望", "direction": "震荡", "strength": 0.0, "rsi_avg": 0.0, "position": "中性"}

    rsi_avg = np.mean(valid_rsi)
    close = df["close"]
    ema = close.ewm(span=EMA_TREND_PERIOD, adjust=False).mean()
    trend = "bullish" if close.iloc[-1] > ema.iloc[-1] else "bearish"

    in_oversold = sum(1 for v in valid_rsi if v < oversold)
    in_overbought = sum(1 for v in valid_rsi if v > overbought)

    if trend == "bullish":
        if in_oversold >= 2:
            signal, direction, position = "买入", "多头", "超卖区"
        elif in_overbought >= 2:
            signal, direction, position = "观望", "震荡", "超买区"
        else:
            signal, direction, position = "观望", "震荡", "中性区"
    else:
        if in_overbought >= 2:
            signal, direction, position = "卖出", "空头", "超买区"
        elif in_oversold >= 2:
            signal, direction, position = "观望", "震荡", "超卖区"
        else:
            signal, direction, position = "观望", "震荡", "中性区"

    if signal == "买入":
        strength = (oversold - rsi_avg) / oversold * 100
    elif signal == "卖出":
        strength = (rsi_avg - overbought) / (100 - overbought) * 100
    else:
        strength = abs(50 - rsi_avg) / 50 * 100
    strength = max(0.0, min(100.0, abs(strength)))

    return {"signal": signal, "direction": direction, "strength": strength, 
            "rsi_avg": round(rsi_avg, 2), "trend": trend, "position": position}


@register
class TvRSI(Indicator):
    meta = IndicatorMeta(name="智能RSI扫描器.py", lookback=100, is_incremental=False)

    def compute(self, df: pd.DataFrame, symbol: str, interval: str) -> pd.DataFrame:
        # 动态最小数据量：至少需要最大RSI周期+5
        min_required = max(RSI_PERIODS) + 5
        
        if len(df) < MIN_DATA:
            # 数据太少，返回带状态的空结果
            return self._make_result(df, symbol, interval, {
                "信号": "数据不足",
                "方向": "未知",
                "强度": 0,
                "RSI均值": None,
                "RSI7": None,
                "RSI14": None,
                "RSI21": None,
                "位置": "未知",
                "背离": "未知",
                "超买阈值": 70,
                "超卖阈值": 30,
            })

        high, low, close = df["high"], df["low"], df["close"]
        
        # 使用安全计算 ATR
        atr, atr_status = safe_atr(high, low, close, ATR_PERIOD, min_period=3)
        if atr_status == "数据不足":
            atr_normalized = pd.Series([0.5] * len(df), index=df.index)
        else:
            atr_normalized = (atr - atr.min()) / (atr.max() - atr.min() + 1e-10)
        
        current_atr_norm = atr_normalized.iloc[-1] if not np.isnan(atr_normalized.iloc[-1]) else 0.5
        overbought, oversold = calc_dynamic_threshold(current_atr_norm)

        # 使用安全计算 RSI
        rsi_7, status_7 = safe_rsi(close, RSI_PERIODS[0], min_period=3)
        rsi_14, status_14 = safe_rsi(close, RSI_PERIODS[1], min_period=3)
        rsi_21, status_21 = safe_rsi(close, RSI_PERIODS[2], min_period=3)

        rsi_state = evaluate_rsi_state(df, rsi_7, rsi_14, rsi_21, overbought, oversold)
        
        # 背离检测需要更多数据
        if len(df) >= 50:
            divergence_type, divergence_strength = detect_divergence(df, rsi_14, lookback=50)
        else:
            divergence_type, divergence_strength = "数据不足", 0.0

        final_signal = rsi_state["signal"]
        if divergence_type == "底背离" and rsi_state["direction"] == "多头":
            final_signal = "买入"
            rsi_state["strength"] = min(100.0, rsi_state["strength"] + divergence_strength * 0.5)
        elif divergence_type == "顶背离" and rsi_state["direction"] == "空头":
            final_signal = "卖出"
            rsi_state["strength"] = min(100.0, rsi_state["strength"] + divergence_strength * 0.5)

        # 标记参考值状态
        data_status = "参考值" if any(s == "参考值" for s in [status_7, status_14, status_21]) else ""

        return self._make_result(df, symbol, interval, {
            "信号": final_signal + (f"({data_status})" if data_status else ""),
            "方向": rsi_state["direction"],
            "强度": round(rsi_state["strength"], 2),
            "RSI均值": rsi_state["rsi_avg"],
            "RSI7": round(float(rsi_7.iloc[-1]), 2) if not np.isnan(rsi_7.iloc[-1]) else None,
            "RSI14": round(float(rsi_14.iloc[-1]), 2) if not np.isnan(rsi_14.iloc[-1]) else None,
            "RSI21": round(float(rsi_21.iloc[-1]), 2) if not np.isnan(rsi_21.iloc[-1]) else None,
            "位置": rsi_state["position"],
            "背离": divergence_type,
            "超买阈值": round(overbought, 2),
            "超卖阈值": round(oversold, 2),
        })
