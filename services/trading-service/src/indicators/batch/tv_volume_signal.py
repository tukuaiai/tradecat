"""量能信号扫描器 - Madrid Moving Average Ribbon 完整复刻"""
import pandas as pd
from typing import Dict
from ..base import Indicator, IndicatorMeta, register

MA_PERIODS = [5, 10, 15, 20, 25, 30, 35, 40, 45, 50, 55, 60, 65, 70, 75, 80, 90, 100]


def calculate_ribbon(df: pd.DataFrame) -> Dict:
    if len(df) < MA_PERIODS[-1]:
        return {"signal": "观望", "strength": 0.0, "direction": "震荡"}

    close = df["close"]
    ma_lines = {period: close.ewm(span=period, adjust=False).mean() for period in MA_PERIODS}
    ma_last = {period: ma_lines[period].iloc[-1] for period in MA_PERIODS}
    ma100 = ma_last[100]
    current = close.iloc[-1]

    bullish_count = sum(1 for period in MA_PERIODS 
                        if ma_last[period] > ma100 and ma_lines[period].diff().iloc[-1] > 0)
    bearish_count = sum(1 for period in MA_PERIODS 
                        if ma_last[period] < ma100 and ma_lines[period].diff().iloc[-1] < 0)

    bullish_ratio = bullish_count / len(MA_PERIODS)
    bearish_ratio = bearish_count / len(MA_PERIODS)

    if bullish_ratio >= 0.7:
        signal, direction = "买入", "多头"
        strength = bullish_ratio * 10
    elif bearish_ratio >= 0.7:
        signal, direction = "卖出", "空头"
        strength = bearish_ratio * 10
    else:
        signal = "观望"
        direction = "多头" if current > ma100 else "空头"
        strength = abs((current - ma100) / ma100) * 5

    return {"signal": signal, "strength": round(float(strength), 3), "direction": direction,
            "bullish_ratio": round(bullish_ratio, 2), "bearish_ratio": round(bearish_ratio, 2),
            "ma100": ma100}


@register
class TvVolumeSignal(Indicator):
    meta = IndicatorMeta(name="量能信号扫描器.py", lookback=200, is_incremental=False, min_data=100)

    def compute(self, df: pd.DataFrame, symbol: str, interval: str) -> pd.DataFrame:
        if not self._check_data(df):
            return self._make_insufficient_result(df, symbol, interval, {"信号": None})

        result = calculate_ribbon(df)
        return self._make_result(df, symbol, interval, {
            "信号": result["signal"],
            "方向": result["direction"],
            "强度": result["strength"],
            "多头比例": result["bullish_ratio"],
            "空头比例": result["bearish_ratio"],
            "MA100": round(result["ma100"], 6),
        })
