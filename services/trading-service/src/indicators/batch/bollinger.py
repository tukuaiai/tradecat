"""布林带指标"""
import numpy as np
import pandas as pd
from ..base import Indicator, IndicatorMeta, register
from ..safe_calc import safe_bollinger


@register
class Bollinger(Indicator):
    meta = IndicatorMeta(name="布林带扫描器.py", lookback=30, is_incremental=False, min_data=5)
    
    def compute(self, df: pd.DataFrame, symbol: str, interval: str) -> pd.DataFrame:
        if not self._check_data(df):
            return self._make_insufficient_result(df, symbol, interval, {
                "带宽": None, "中轨斜率": None, "中轨价格": None,
                "上轨价格": None, "下轨价格": None, "百分比b": None,
                "价格": None, "成交额": None
            })
        
        close = df["close"]
        upper, mid, lower, status = safe_bollinger(close, 20, 2.0, min_period=5)
        
        m, u, l = float(mid.iloc[-1]), float(upper.iloc[-1]), float(lower.iloc[-1])
        if any(map(np.isnan, [m, u, l])) or m == 0:
            return self._make_insufficient_result(df, symbol, interval, {
                "带宽": None, "中轨斜率": None, "中轨价格": None,
                "上轨价格": None, "下轨价格": None, "百分比b": None,
                "价格": None, "成交额": None
            })
        
        bandwidth = (u - l) / m * 100
        pct_b = (float(close.iloc[-1]) - l) / (u - l) if u != l else 0
        half = min(10, len(df) - 1)
        slope = (m - float(mid.iloc[-half])) / half if half > 0 else 0
        quote = df.get("quote_volume", df["volume"] * df["close"])
        turnover = float(quote.iloc[-1]) if not pd.isna(quote.iloc[-1]) else 0
        
        return self._make_result(df, symbol, interval, {
            "带宽": round(bandwidth, 4),
            "中轨斜率": round(slope, 6),
            "中轨价格": round(m, 6),
            "上轨价格": round(u, 6),
            "下轨价格": round(l, 6),
            "百分比b": round(pct_b, 4),
            "价格": float(close.iloc[-1]),
            "成交额": turnover,
        })
