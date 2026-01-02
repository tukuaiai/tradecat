"""成交量比率指标"""
import math
import pandas as pd
from ..base import Indicator, IndicatorMeta, register


@register
class VolumeRatio(Indicator):
    meta = IndicatorMeta(name="成交量比率扫描器.py", lookback=30, is_incremental=False, min_data=25)
    
    def compute(self, df: pd.DataFrame, symbol: str, interval: str) -> pd.DataFrame:
        if not self._check_data(df):
            return self._make_insufficient_result(df, symbol, interval, {"量比": None, "信号概述": None})
        vol = df["volume"]
        avg = vol.rolling(20, min_periods=20).mean()
        ratio = vol / avg
        cur = ratio.iloc[-1]
        if math.isnan(cur) or math.isinf(cur):
            return self._make_insufficient_result(df, symbol, interval, {"量比": None, "信号概述": None})
        if cur > 5:
            signal = "极值放量"
        elif cur > 2:
            signal = "异常放量"
        elif cur > 1:
            signal = "放量"
        elif cur < 0.7:
            signal = "缩量"
        else:
            signal = "正常"
        quote = df.get("quote_volume", df["volume"] * df["close"])
        turnover = float(quote.iloc[-1]) if not pd.isna(quote.iloc[-1]) else 0
        return self._make_result(df, symbol, interval, {
            "量比": round(float(cur), 4),
            "信号概述": signal,
            "成交额": turnover,
            "当前价格": float(df["close"].iloc[-1]),
        })
