"""多空信号扫描器 - Smoothed Heikin Ashi 完整复刻"""
import numpy as np
import pandas as pd
from ..base import Indicator, IndicatorMeta, register

SMOOTH1 = 10
SMOOTH2 = 10


def calculate_smoothed_heikin_ashi(df: pd.DataFrame) -> dict:
    if len(df) < max(SMOOTH1, SMOOTH2) + 10:
        return {"signal": "观望", "strength": 0.0, "direction": "震荡", "color": "red"}

    df_raw = df.copy()
    df_raw["o_smooth"] = df_raw["open"].ewm(span=SMOOTH1, adjust=False).mean()
    df_raw["h_smooth"] = df_raw["high"].ewm(span=SMOOTH1, adjust=False).mean()
    df_raw["l_smooth"] = df_raw["low"].ewm(span=SMOOTH1, adjust=False).mean()
    df_raw["c_smooth"] = df_raw["close"].ewm(span=SMOOTH1, adjust=False).mean()

    ha_close = (df_raw["o_smooth"] + df_raw["h_smooth"] + df_raw["l_smooth"] + df_raw["c_smooth"]) / 4
    ha_open = pd.Series(np.nan, index=df_raw.index)
    ha_open.iloc[0] = (df_raw["o_smooth"].iloc[0] + df_raw["c_smooth"].iloc[0]) / 2
    for i in range(1, len(df_raw)):
        ha_open.iloc[i] = (ha_open.iloc[i - 1] + ha_close.iloc[i - 1]) / 2

    ha_high = pd.concat([df_raw["h_smooth"], ha_open, ha_close], axis=1).max(axis=1)
    ha_low = pd.concat([df_raw["l_smooth"], ha_open, ha_close], axis=1).min(axis=1)

    o2 = ha_open.ewm(span=SMOOTH2, adjust=False).mean()
    h2 = ha_high.ewm(span=SMOOTH2, adjust=False).mean()
    l2 = ha_low.ewm(span=SMOOTH2, adjust=False).mean()
    c2 = ha_close.ewm(span=SMOOTH2, adjust=False).mean()

    is_green = o2 <= c2
    is_red = ~is_green
    red_to_green = is_green.iloc[-1] and is_red.iloc[-2]
    green_to_red = is_red.iloc[-1] and is_green.iloc[-2]

    body_now = abs(o2.iloc[-1] - c2.iloc[-1])
    body_prev = abs(o2.iloc[-2] - c2.iloc[-2])
    slope = (c2.iloc[-1] - c2.iloc[-5]) if len(c2) > 5 else c2.iloc[-1] - c2.iloc[-2]
    slope_strength = max(0, min(1, (slope + 200) / 400))

    strength = 0.0
    if body_prev > 0:
        strength = body_now / body_prev * 100.0
    strength = min(strength + slope_strength * 40, 200.0)

    if red_to_green:
        signal, direction = "买入", "多头"
    elif green_to_red:
        signal, direction = "卖出", "空头"
    else:
        signal = "观望"
        direction = "多头" if is_green.iloc[-1] else "空头"

    return {
        "signal": signal,
        "strength": float(round(strength, 2)),
        "direction": direction,
        "color": "绿色" if is_green.iloc[-1] else "红色",
        "body": float(body_now),
        "wick": float(h2.iloc[-1] - l2.iloc[-1]),
        "ha_open": float(o2.iloc[-1]),
        "ha_close": float(c2.iloc[-1]),
    }


@register
class TvLongShort(Indicator):
    meta = IndicatorMeta(name="多空信号扫描器.py", lookback=120, is_incremental=False, min_data=20)

    def compute(self, df: pd.DataFrame, symbol: str, interval: str) -> pd.DataFrame:
        if not self._check_data(df):
            return self._make_insufficient_result(df, symbol, interval, {"信号": None})

        result = calculate_smoothed_heikin_ashi(df)
        return self._make_result(df, symbol, interval, {
            "信号": result["signal"],
            "方向": result["direction"],
            "强度": result["strength"],
            "颜色": result["color"],
            "实体大小": round(result["body"], 6),
            "影线长度": round(result["wick"], 6),
            "HA开盘": round(result["ha_open"], 6),
            "HA收盘": round(result["ha_close"], 6),
        })
