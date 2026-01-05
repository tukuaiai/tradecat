"""OBV 能量潮指标"""
import numpy as np
import pandas as pd
from ..base import Indicator, IndicatorMeta, register


@register
class OBV(Indicator):
    meta = IndicatorMeta(name="OBV能量潮扫描器.py", lookback=50, is_incremental=True)

    def compute(self, df: pd.DataFrame, symbol: str, interval: str) -> pd.DataFrame:
        if len(df) < 32:
            return pd.DataFrame()
        direction = np.sign(df["close"].diff()).fillna(0)
        obv = (direction * df["volume"]).cumsum()
        window = min(30, len(obv) - 1)
        base = obv.iloc[-window] if window > 0 else obv.iloc[0]
        change = (obv.iloc[-1] - base) / max(abs(base), 1e-9)
        return self._make_result(df, symbol, interval, {
            "OBV值": float(obv.iloc[-1]),
            "OBV变化率": float(change),
        })
