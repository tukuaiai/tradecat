"""MFI 资金流量指标"""
import numpy as np
import pandas as pd
from ..base import Indicator, IndicatorMeta, register


@register
class MFI(Indicator):
    meta = IndicatorMeta(name="MFI资金流量扫描器.py", lookback=20, is_incremental=False, min_data=15)
    
    def compute(self, df: pd.DataFrame, symbol: str, interval: str) -> pd.DataFrame:
        if not self._check_data(df):
            return self._make_insufficient_result(df, symbol, interval, {"MFI值": None})
        tp = (df["high"] + df["low"] + df["close"]) / 3
        mf = tp * df["volume"]
        direction = np.sign(tp.diff())
        pos = mf.where(direction > 0, 0).rolling(14).sum()
        neg = mf.where(direction < 0, 0).rolling(14).sum().abs()
        mfr = pos / neg.replace(0, np.nan)
        mfi = 100 - (100 / (1 + mfr))
        val = mfi.iloc[-1]
        if np.isnan(val):
            return self._make_insufficient_result(df, symbol, interval, {"MFI值": None})
        return self._make_result(df, symbol, interval, {
            "MFI值": round(float(val), 2),
        })
