"""KDJ 随机指标"""
import pandas as pd
from ..base import Indicator, IndicatorMeta, register


def calc_kdj(df: pd.DataFrame):
    low_n = df["low"].rolling(9, min_periods=9).min()
    high_n = df["high"].rolling(9, min_periods=9).max()
    rsv = (df["close"] - low_n) / (high_n - low_n) * 100
    k = rsv.ewm(alpha=1/3, adjust=False, min_periods=3).mean()
    d = k.ewm(alpha=1/3, adjust=False, min_periods=3).mean()
    j = 3 * k - 2 * d
    return k, d, j


def get_signal(k: pd.Series, d: pd.Series, j: pd.Series) -> str:
    if len(k) < 2:
        return "数据不足"
    if k.iloc[-2] <= d.iloc[-2] and k.iloc[-1] > d.iloc[-1]:
        return "金叉"
    if k.iloc[-2] >= d.iloc[-2] and k.iloc[-1] < d.iloc[-1]:
        return "死叉"
    if j.iloc[-1] > 100:
        return "J>100 极值"
    if j.iloc[-1] < 0:
        return "J<0 极值"
    return "延续"


@register
class KDJ(Indicator):
    meta = IndicatorMeta(name="KDJ随机指标扫描器.py", lookback=50, is_incremental=True)

    def compute(self, df: pd.DataFrame, symbol: str, interval: str) -> pd.DataFrame:
        if len(df) < 40:
            return pd.DataFrame()
        k, d, j = calc_kdj(df)
        if k.isna().iloc[-1] or d.isna().iloc[-1] or j.isna().iloc[-1]:
            return pd.DataFrame()
        signal = get_signal(k, d, j)
        quote = df.get("quote_volume", df["volume"] * df["close"])
        turnover = float(quote.iloc[-1]) if not pd.isna(quote.iloc[-1]) else 0
        return self._make_result(df, symbol, interval, {
            "J值": round(float(j.iloc[-1]), 3),
            "K值": round(float(k.iloc[-1]), 3),
            "D值": round(float(d.iloc[-1]), 3),
            "信号概述": signal,
            "成交额": turnover,
            "当前价格": float(df["close"].iloc[-1]),
        })
