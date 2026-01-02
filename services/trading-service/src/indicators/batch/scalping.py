"""剥头皮信号指标"""
import numpy as np
import pandas as pd
from ..base import Indicator, IndicatorMeta, register


@register
class Scalping(Indicator):
    meta = IndicatorMeta(name="剥头皮信号扫描器.py", lookback=50, is_incremental=False, min_data=20)
    
    def compute(self, df: pd.DataFrame, symbol: str, interval: str) -> pd.DataFrame:
        if not self._check_data(df):
            return self._make_insufficient_result(df, symbol, interval, {"剥头皮信号": None})
        close = df["close"]
        # RSI
        delta = close.diff()
        gain = delta.where(delta > 0, 0).ewm(alpha=1/14, adjust=False).mean()
        loss = (-delta.where(delta < 0, 0)).ewm(alpha=1/14, adjust=False).mean()
        rs = gain / loss.replace(0, np.nan)
        rsi = 100 - (100 / (1 + rs))
        rsi_val = float(rsi.iloc[-1])
        # EMA
        ema9 = close.ewm(span=9, adjust=False).mean()
        ema21 = close.ewm(span=21, adjust=False).mean()
        price = float(close.iloc[-1])
        e9, e21 = float(ema9.iloc[-1]), float(ema21.iloc[-1])
        # 信号
        if rsi_val < 30 and price > e9 > e21:
            signal = "超卖反弹"
        elif rsi_val > 70 and price < e9 < e21:
            signal = "超买回落"
        elif e9 > e21 and rsi_val > 50:
            signal = "多头"
        elif e9 < e21 and rsi_val < 50:
            signal = "空头"
        else:
            signal = "观望"
        return self._make_result(df, symbol, interval, {
            "剥头皮信号": signal,
            "RSI": round(rsi_val, 2),
            "EMA9": round(e9, 6),
            "EMA21": round(e21, 6),
            "当前价格": price,
        })
