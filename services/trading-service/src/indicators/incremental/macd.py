"""MACD 柱状指标"""
import pandas as pd
from ..base import Indicator, IndicatorMeta, register


def calc_macd(close: pd.Series):
    ema12 = close.ewm(span=12, adjust=False).mean()
    ema26 = close.ewm(span=26, adjust=False).mean()
    dif = ema12 - ema26
    dea = dif.ewm(span=9, adjust=False).mean()
    macd = 2 * (dif - dea)
    return dif, dea, macd


def get_signal(macd: pd.Series, dif: pd.Series, dea: pd.Series) -> str:
    if len(macd) < 2:
        return "数据不足"
    crossed = ""
    if macd.iloc[-2] <= 0 < macd.iloc[-1]:
        crossed = "零轴上穿"
    elif macd.iloc[-2] >= 0 > macd.iloc[-1]:
        crossed = "零轴下破"
    if dif.iloc[-2] <= dea.iloc[-2] and dif.iloc[-1] > dea.iloc[-1]:
        return "金叉" + (f"/{crossed}" if crossed else "")
    if dif.iloc[-2] >= dea.iloc[-2] and dif.iloc[-1] < dea.iloc[-1]:
        return "死叉" + (f"/{crossed}" if crossed else "")
    return crossed or "延续"


@register
class MACD(Indicator):
    meta = IndicatorMeta(name="MACD柱状扫描器.py", lookback=50, is_incremental=True)

    def compute(self, df: pd.DataFrame, symbol: str, interval: str) -> pd.DataFrame:
        if len(df) < 35:
            return pd.DataFrame()
        dif, dea, macd = calc_macd(df["close"])
        signal = get_signal(macd, dif, dea)
        quote = df.get("quote_volume", df["volume"] * df["close"])
        turnover = float(quote.iloc[-1]) if not pd.isna(quote.iloc[-1]) else 0
        return self._make_result(df, symbol, interval, {
            "信号概述": signal,
            "MACD": round(float(dif.iloc[-1]), 6),
            "MACD信号线": round(float(dea.iloc[-1]), 6),
            "MACD柱状图": round(float(macd.iloc[-1]), 6),
            "DIF": round(float(dif.iloc[-1]), 6),
            "DEA": round(float(dea.iloc[-1]), 6),
            "成交额": turnover,
            "当前价格": float(df["close"].iloc[-1]),
        })
