"""谐波信号扫描器 - 多周期RSI均值 完整复刻（优化版）"""
import numpy as np
import pandas as pd
from ..base import Indicator, IndicatorMeta, register

RSI_PERIODS = list(range(2, 34))  # 2~33


def calc_harmonic(df: pd.DataFrame) -> float:
    """计算谐波值 - 多周期RSI均值"""
    if len(df) < max(RSI_PERIODS) + 2:
        return None
    
    typ_price = (df["high"] + df["low"] + df["close"]) / 3
    delta = typ_price.diff()
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)
    
    rsi_vals = []
    for n in RSI_PERIODS:
        avg_gain = gain.ewm(alpha=1/n, adjust=False).mean().iloc[-1]
        avg_loss = loss.ewm(alpha=1/n, adjust=False).mean().iloc[-1]
        if avg_loss == 0:
            continue
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        if not np.isnan(rsi):
            rsi_vals.append(rsi)
    
    return float(np.mean(rsi_vals)) if rsi_vals else None


@register
class Harmonic(Indicator):
    meta = IndicatorMeta(name="谐波信号扫描器.py", lookback=50, is_incremental=False, min_data=35)

    def compute(self, df: pd.DataFrame, symbol: str, interval: str) -> pd.DataFrame:
        if not self._check_data(df):
            return self._make_insufficient_result(df, symbol, interval, {"谐波值": None})
        val = calc_harmonic(df)
        if val is None:
            return self._make_insufficient_result(df, symbol, interval, {"谐波值": None})
        return self._make_result(df, symbol, interval, {
            "谐波值": round(val, 2),
        })
