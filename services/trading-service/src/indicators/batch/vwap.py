"""VWAP离线信号扫描 - 完整复刻"""
import numpy as np
import pandas as pd
from ..base import Indicator, IndicatorMeta, register

WINDOW = 300


@register
class VWAP(Indicator):
    meta = IndicatorMeta(name="VWAP离线信号扫描.py", lookback=300, is_incremental=False, min_data=10)

    def compute(self, df: pd.DataFrame, symbol: str, interval: str) -> pd.DataFrame:
        if not self._check_data(df):
            return self._make_insufficient_result(df, symbol, interval, {"VWAP价格": None})

        window_df = df.tail(WINDOW).copy() if len(df) >= WINDOW else df.copy()
        price = (window_df["high"] + window_df["low"] + window_df["close"]) / 3
        vol = window_df["volume"].replace(0, 1e-9)
        cum_tpv = (price * vol).cumsum()
        cum_vol = vol.cumsum().replace(0, np.nan)
        vwap_series = cum_tpv / cum_vol

        price_std = float(price.std(ddof=0)) if len(price) else 0.0
        vwap_val = float(vwap_series.iloc[-1]) if len(vwap_series) else 0.0
        if not np.isfinite(vwap_val) or vwap_val == 0:
            vwap_val = float(window_df["close"].iloc[-1])

        vwap_upper = vwap_val + price_std
        vwap_lower = vwap_val - price_std

        cur_price = float(window_df["close"].iloc[-1])
        deviation = cur_price - vwap_val
        dev_pct = deviation / vwap_val * 100 if vwap_val else 0

        bandwidth = max(vwap_upper - vwap_lower, 0.0)
        bw_pct = bandwidth / vwap_val * 100 if vwap_val else 0

        quote = df.get("quote_volume", df["volume"] * df["close"])
        turnover = float(quote.iloc[-1]) if not pd.isna(quote.iloc[-1]) else 0

        return self._make_result(df, symbol, interval, {
            "VWAP价格": round(vwap_val, 6),
            "偏离度": round(deviation, 6),
            "偏离百分比": round(dev_pct, 4),
            "成交量加权": float(vol.iloc[-1]),
            "当前价格": cur_price,
            "成交额（USDT）": turnover,
            "VWAP上轨": round(vwap_upper, 6),
            "VWAP下轨": round(vwap_lower, 6),
            "VWAP带宽": round(bandwidth, 6),
            "VWAP带宽百分比": round(bw_pct, 4),
        })
