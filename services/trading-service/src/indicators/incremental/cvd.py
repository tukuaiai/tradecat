"""CVD 主动成交差指标"""
import pandas as pd
from ..base import Indicator, IndicatorMeta, register


@register
class CVD(Indicator):
    meta = IndicatorMeta(name="CVD信号排行榜.py", lookback=400, is_incremental=True)

    def compute(self, df: pd.DataFrame, symbol: str, interval: str) -> pd.DataFrame:
        if "taker_buy_volume" not in df.columns or len(df) < 2:
            return pd.DataFrame()
        vol = df["volume"].astype(float).fillna(0.0)
        buy = df["taker_buy_volume"].astype(float).fillna(vol * 0.5)
        sell = (vol - buy).clip(lower=0.0)
        delta = buy - sell
        cvd = delta.cumsum()
        window = min(360, len(cvd) - 1) if len(cvd) > 1 else 1
        base = cvd.iloc[-window] if window < len(cvd) else cvd.iloc[0]
        change = (cvd.iloc[-1] - base) / (abs(base) + 1e-9)
        return self._make_result(df, symbol, interval, {
            "CVD值": float(cvd.iloc[-1]),
            "变化率": float(change),
        })
