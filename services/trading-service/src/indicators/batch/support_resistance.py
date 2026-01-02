"""支撑阻力指标"""
import pandas as pd
from ..base import Indicator, IndicatorMeta, register


@register
class SupportResistance(Indicator):
    meta = IndicatorMeta(name="全量支撑阻力扫描器.py", lookback=100, is_incremental=False, min_data=20)
    
    def compute(self, df: pd.DataFrame, symbol: str, interval: str) -> pd.DataFrame:
        if not self._check_data(df):
            return self._make_insufficient_result(df, symbol, interval, {"支撑位": None, "阻力位": None})
        high, low, close = df["high"], df["low"], df["close"]
        price = float(close.iloc[-1])
        # 简单支撑阻力：近期高低点
        support = float(low.tail(20).min())
        resistance = float(high.tail(20).max())
        # ATR
        prev_close = close.shift(1)
        tr = pd.concat([(high - low).abs(), (high - prev_close).abs(), (low - prev_close).abs()], axis=1).max(axis=1)
        atr = float(tr.ewm(alpha=1/14, adjust=False).mean().iloc[-1])
        dist_support = (price - support) / price * 100 if price else 0
        dist_resistance = (resistance - price) / price * 100 if price else 0
        dist_key = min(abs(dist_support), abs(dist_resistance))
        return self._make_result(df, symbol, interval, {
            "支撑位": round(support, 6),
            "阻力位": round(resistance, 6),
            "当前价格": price,
            "ATR": round(atr, 6),
            "距支撑百分比": round(dist_support, 4),
            "距阻力百分比": round(dist_resistance, 4),
            "距关键位百分比": round(dist_key, 4),
        })
