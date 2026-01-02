"""超级精准趋势扫描器 - Zero Lag Trend Signals 完整复刻
参数：length=70, multiplier=1.2
基线：ZLEMA(close + (close - close[lag]), length)，lag = floor((length-1)/2)
波动带：highest(ATR(length), length*3) * multiplier（ATR 使用 Wilder RMA）
"""
import numpy as np
import pandas as pd
from typing import Optional
from ..base import Indicator, IndicatorMeta, register

DEFAULT_LENGTH = 70
DEFAULT_MULT = 1.2
DEFAULT_LAG = (DEFAULT_LENGTH - 1) // 2
HIGHEST_WIN = DEFAULT_LENGTH * 3


def _rma(series: pd.Series, length: int) -> pd.Series:
    """Wilder RMA，与 ta.rma/ta.atr 一致"""
    alpha = 1 / length
    vals = []
    prev = np.nan
    for i, v in enumerate(series):
        if i == 0:
            prev = v
        else:
            prev = alpha * v + (1 - alpha) * prev
        vals.append(prev)
    return pd.Series(vals, index=series.index)


def _atr_wilder(df: pd.DataFrame, length: int = DEFAULT_LENGTH) -> pd.Series:
    high, low, close = df["high"], df["low"], df["close"]
    prev_close = close.shift(1)
    tr = pd.concat([
        (high - low).abs(),
        (high - prev_close).abs(),
        (low - prev_close).abs(),
    ], axis=1).max(axis=1)
    return _rma(tr, length)


def _zlema(close: pd.Series, length: int = DEFAULT_LENGTH, lag: int = DEFAULT_LAG) -> pd.Series:
    src = close + (close - close.shift(lag))
    return src.ewm(span=length, adjust=False).mean()


@register
class SuperTrend(Indicator):
    meta = IndicatorMeta(name="超级精准趋势扫描器.py", lookback=280, is_incremental=False, min_data=70)

    def compute(self, df: pd.DataFrame, symbol: str, interval: str) -> pd.DataFrame:
        # 周线放宽到 70 根
        min_bars = DEFAULT_LENGTH + HIGHEST_WIN
        if str(interval).lower() == "1w":
            min_bars = DEFAULT_LENGTH
        if len(df) < min_bars:
            return self._make_insufficient_result(df, symbol, interval, {"信号": None})

        close = df["close"]
        zlema = _zlema(close, DEFAULT_LENGTH, DEFAULT_LAG)
        atr = _atr_wilder(df, DEFAULT_LENGTH)
        vol_band = atr.rolling(HIGHEST_WIN, min_periods=1).max() * DEFAULT_MULT

        trend = [0] * len(close)
        last_cross_idx: Optional[int] = None
        for i in range(1, len(close)):
            upper = zlema.iloc[i] + vol_band.iloc[i]
            lower = zlema.iloc[i] - vol_band.iloc[i]
            if close.iloc[i - 1] <= upper and close.iloc[i] > upper:
                trend[i] = 1
                if trend[i] != trend[i - 1]:
                    last_cross_idx = i
            elif close.iloc[i - 1] >= lower and close.iloc[i] < lower:
                trend[i] = -1
                if trend[i] != trend[i - 1]:
                    last_cross_idx = i
            else:
                trend[i] = trend[i - 1]

        upper_last = zlema.iloc[-1] + vol_band.iloc[-1]
        lower_last = zlema.iloc[-1] - vol_band.iloc[-1]
        trend_band = lower_last if trend[-1] == 1 else upper_last
        atr_last = float(vol_band.iloc[-1])
        band_gap = float((close.iloc[-1] - trend_band) / atr_last) if atr_last else None

        if last_cross_idx is None:
            trend_duration = len(close)
            last_cross_ts = df.index[0]
        else:
            trend_duration = len(close) - last_cross_idx
            last_cross_ts = df.index[last_cross_idx]

        # 量能偏向
        window = df.tail(20)
        up_vol = window.loc[window["close"] > window["open"], "volume"].sum()
        down_vol = window.loc[window["close"] < window["open"], "volume"].sum()
        avg_vol = (up_vol + down_vol) / 2 if (up_vol + down_vol) != 0 else np.nan
        delta_volume = float((up_vol - down_vol) / avg_vol) if avg_vol and not np.isnan(avg_vol) else None

        return self._make_result(df, symbol, interval, {
            "趋势方向": "多" if trend[-1] == 1 else "空",
            "趋势持续根数": int(trend_duration),
            "趋势强度": round(band_gap, 4) if band_gap else None,
            "趋势带": round(float(trend_band), 6),
            "最近翻转时间": last_cross_ts.isoformat() if hasattr(last_cross_ts, "isoformat") else str(last_cross_ts),
            "量能偏向": round(delta_volume, 4) if delta_volume else None,
        })
