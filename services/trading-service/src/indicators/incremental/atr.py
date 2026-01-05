"""ATR 波幅指标"""
import math
import pandas as pd
from ..base import Indicator, IndicatorMeta, register


def calc_atr(df: pd.DataFrame) -> pd.Series:
    prev_close = df["close"].shift(1)
    tr = pd.concat([
        (df["high"] - df["low"]).abs(),
        (df["high"] - prev_close).abs(),
        (df["low"] - prev_close).abs(),
    ], axis=1).max(axis=1)
    return tr.ewm(alpha=1/14, adjust=False, min_periods=14).mean()


@register
class ATR(Indicator):
    meta = IndicatorMeta(name="ATR波幅扫描器.py", lookback=60, is_incremental=True)

    def compute(self, df: pd.DataFrame, symbol: str, interval: str) -> pd.DataFrame:
        if len(df) < 60:
            return pd.DataFrame()
        atr = calc_atr(df)
        atr_val = float(atr.iloc[-1])
        close = float(df["close"].iloc[-1])
        atr_pct = atr_val / close * 100 if close else 0
        mid = df["close"].rolling(20, min_periods=20).mean().iloc[-1]
        if math.isnan(mid):
            return pd.DataFrame()
        upper = mid + 2 * atr_val
        lower = mid - 2 * atr_val
        recent = atr.tail(30).dropna()
        if recent.empty:
            category = "未知"
        else:
            median = recent.median()
            category = "升温" if atr_val > median * 1.1 else "降温" if atr_val < median * 0.9 else "稳定"
        quote = df.get("quote_volume", df["volume"] * df["close"])
        turnover = float(quote.iloc[-1]) if not pd.isna(quote.iloc[-1]) else 0
        return self._make_result(df, symbol, interval, {
            "波动分类": category,
            "ATR百分比": round(atr_pct, 4),
            "上轨": round(upper, 6),
            "中轨": round(mid, 6),
            "下轨": round(lower, 6),
            "成交额": turnover,
            "当前价格": close,
        })
