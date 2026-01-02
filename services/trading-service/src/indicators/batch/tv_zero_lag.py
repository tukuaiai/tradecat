"""零延迟趋势扫描器 - Zero Lag Trend Signals 完整复刻"""
import numpy as np
import pandas as pd
from ..base import Indicator, IndicatorMeta, register

DEFAULT_LENGTH = 70
DEFAULT_MULT = 1.2
MIN_BARS = DEFAULT_LENGTH * 3 + 5


def _atr(df: pd.DataFrame, length: int) -> pd.Series:
    high, low, close = df["high"], df["low"], df["close"]
    prev_close = close.shift(1)
    tr1 = high - low
    tr2 = (high - prev_close).abs()
    tr3 = (low - prev_close).abs()
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    return tr.ewm(alpha=1 / length, adjust=False).mean()


def _zlema(close: pd.Series, length: int) -> pd.Series:
    lag = int(np.floor((length - 1) / 2))
    shifted = close.shift(lag)
    src = close + (close - shifted)
    return src.ewm(span=length, adjust=False).mean()


def _vol_band(df: pd.DataFrame, length: int, mult: float) -> pd.Series:
    atr = _atr(df, length)
    window = length * 3
    return atr.rolling(window=window, min_periods=window).max() * mult


def _calc_trend(close: pd.Series, basis: pd.Series, band: pd.Series) -> pd.Series:
    trend = 0
    out = []
    for c, b, v in zip(close, basis, band):
        if pd.isna(b) or pd.isna(v):
            out.append(trend)
            continue
        if c > b + v:
            trend = 1
        elif c < b - v:
            trend = -1
        out.append(trend)
    return pd.Series(out, index=close.index)


@register
class TvZeroLag(Indicator):
    meta = IndicatorMeta(name="零延迟趋势扫描器.py", lookback=220, is_incremental=False, min_data=215)

    def compute(self, df: pd.DataFrame, symbol: str, interval: str) -> pd.DataFrame:
        if not self._check_data(df):
            return self._make_insufficient_result(df, symbol, interval, {"信号": None})

        close = df["close"].astype(float)
        basis = _zlema(close, DEFAULT_LENGTH)
        band = _vol_band(df, DEFAULT_LENGTH, DEFAULT_MULT)
        trend_series = _calc_trend(close, basis, band)

        last = int(trend_series.iloc[-1]) if not pd.isna(trend_series.iloc[-1]) else 0
        prev = int(trend_series.iloc[-2]) if len(trend_series) > 1 and not pd.isna(trend_series.iloc[-2]) else 0

        if last > 0 and prev <= 0:
            signal = "买入"
        elif last < 0 and prev >= 0:
            signal = "卖出"
        else:
            signal = "观望"

        direction = "多头" if last > 0 else "空头" if last < 0 else "震荡"

        last_close = close.iloc[-1]
        last_basis = basis.iloc[-1]
        last_band = band.iloc[-1]
        deviation = abs(last_close - last_basis) / last_band * 100 if last_band and not pd.isna(last_band) else None

        upper = last_basis + last_band if not pd.isna(last_basis) and not pd.isna(last_band) else None
        lower = last_basis - last_band if not pd.isna(last_basis) and not pd.isna(last_band) else None

        return self._make_result(df, symbol, interval, {
            "信号": signal,
            "方向": direction,
            "强度": round(deviation, 2) if deviation else None,
            "ZLEMA": round(float(last_basis), 6) if not pd.isna(last_basis) else None,
            "波动带宽": round(float(last_band), 6) if not pd.isna(last_band) else None,
            "上轨": round(float(upper), 6) if upper else None,
            "下轨": round(float(lower), 6) if lower else None,
            "趋势值": last,
        })
