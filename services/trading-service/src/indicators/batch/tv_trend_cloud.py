"""趋势云反转扫描器 - SMMA200 + K线反转形态完整复刻"""
import numpy as np
import pandas as pd
from ..base import Indicator, IndicatorMeta, register


def calculate_smma(src: pd.Series, length: int) -> pd.Series:
    smma = pd.Series(np.nan, index=src.index)
    sma_first = src.rolling(window=length).mean()
    smma.iloc[length - 1] = sma_first.iloc[length - 1]
    for i in range(length, len(src)):
        smma.iloc[i] = (smma.iloc[i - 1] * (length - 1) + src.iloc[i]) / length
    return smma


def detect_3line_strike(df: pd.DataFrame) -> str:
    if len(df) < 4:
        return "HOLD"
    if (df["close"].iloc[-4] < df["open"].iloc[-4]
        and df["close"].iloc[-3] < df["open"].iloc[-3]
        and df["close"].iloc[-2] < df["open"].iloc[-2]
        and df["close"].iloc[-1] > df["open"].iloc[-2]):
        return "BUY"
    if (df["close"].iloc[-4] > df["open"].iloc[-4]
        and df["close"].iloc[-3] > df["open"].iloc[-3]
        and df["close"].iloc[-2] > df["open"].iloc[-2]
        and df["close"].iloc[-1] < df["open"].iloc[-2]):
        return "SELL"
    return "HOLD"


def detect_engulfing(df: pd.DataFrame) -> str:
    if len(df) < 2:
        return "HOLD"
    prev, curr = df.iloc[-2], df.iloc[-1]
    if curr["open"] <= prev["close"] and curr["open"] < prev["open"] and curr["close"] > prev["open"]:
        return "BUY"
    if curr["open"] >= prev["close"] and curr["open"] > prev["open"] and curr["close"] < prev["open"]:
        return "SELL"
    return "HOLD"


@register
class TvTrendCloud(Indicator):
    meta = IndicatorMeta(name="趋势云反转扫描器.py", lookback=220, is_incremental=False, min_data=200)

    def compute(self, df: pd.DataFrame, symbol: str, interval: str) -> pd.DataFrame:
        if not self._check_data(df):
            return self._make_insufficient_result(df, symbol, interval, {"信号": None})

        close = df["close"]
        smma200 = calculate_smma(close, 200)
        ema2 = close.ewm(span=2, adjust=False).mean()

        signal_3ls = detect_3line_strike(df)
        signal_eng = detect_engulfing(df)

        trend_up = ema2.iloc[-1] > smma200.iloc[-1]
        trend_down = ema2.iloc[-1] < smma200.iloc[-1]

        body_size = abs(df["close"].iloc[-1] - df["open"].iloc[-1])
        avg_body = df.apply(lambda row: abs(row["close"] - row["open"]), axis=1).iloc[-15:].mean()
        strength = (body_size / avg_body * 100) if avg_body else 0.0

        if (signal_3ls == "BUY" or signal_eng == "BUY") and trend_up:
            signal, direction = "买入", "多头"
        elif (signal_3ls == "SELL" or signal_eng == "SELL") and trend_down:
            signal, direction = "卖出", "空头"
        elif trend_up:
            drift = (close.iloc[-1] - smma200.iloc[-1]) / smma200.iloc[-1] * 100
            signal, direction, strength = "观望", "多头", min(drift, 5.0)
        elif trend_down:
            drift = (smma200.iloc[-1] - close.iloc[-1]) / smma200.iloc[-1] * 100
            signal, direction, strength = "观望", "空头", min(drift, 5.0)
        else:
            signal, direction, strength = "观望", "震荡", 0.0

        # 形态检测
        pattern = "无"
        if signal_3ls != "HOLD":
            pattern = "三线打击"
        elif signal_eng != "HOLD":
            pattern = "吞没形态"

        return self._make_result(df, symbol, interval, {
            "信号": signal,
            "方向": direction,
            "强度": round(strength, 2),
            "形态": pattern,
            "SMMA200": round(float(smma200.iloc[-1]), 6) if not pd.isna(smma200.iloc[-1]) else None,
            "EMA2": round(float(ema2.iloc[-1]), 6),
        })
