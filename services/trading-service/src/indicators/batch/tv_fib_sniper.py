"""量能斐波狙击扫描器 - VWMA Fibonacci Bands 完整复刻"""
import numpy as np
import pandas as pd
from typing import Dict
from ..base import Indicator, IndicatorMeta, register

LENGTH = 200
MULT = 3.0
FIB_RATIOS = [0.236, 0.382, 0.5, 0.618, 0.764, 1.0]


def calculate_vwma(src: pd.Series, volume: pd.Series, length: int) -> pd.Series:
    vol_sum = volume.rolling(window=length).sum()
    price_vol = (src * volume).rolling(window=length).sum()
    return price_vol / vol_sum


def calculate_fibonacci_bands(df: pd.DataFrame) -> Dict:
    if len(df) < LENGTH + 10:
        return {"signal": "观望", "strength": 0.0, "direction": "震荡", "position": "数据不足"}

    src = (df["high"] + df["low"] + df["close"]) / 3  # hlc3
    price = df["close"]
    volume = df["volume"] if "volume" in df.columns else pd.Series(np.ones(len(df)))
    basis = calculate_vwma(src, volume, LENGTH)
    dev = MULT * src.rolling(window=LENGTH).std()

    channels = {}
    for idx, ratio in enumerate(FIB_RATIOS):
        channels[f"upper_{idx}"] = basis + ratio * dev
        channels[f"lower_{idx}"] = basis - ratio * dev

    latest_price = price.iloc[-1]
    latest_basis = basis.iloc[-1]
    latest_dev = dev.iloc[-1]
    if np.isnan(latest_basis) or np.isnan(latest_dev):
        return {"signal": "观望", "strength": 0.0, "direction": "震荡", "position": "等待"}

    distance = abs(latest_price - latest_basis) / max(latest_dev, 1e-9) * 100
    prev_price = price.iloc[-2]
    signal, direction = "观望", "震荡"
    strength = 0.0
    price_zone = "中间"

    def _zone_name(idx: int, side: str) -> str:
        return f"{'上' if side == 'upper' else '下'}通道({FIB_RATIOS[idx]})"

    if latest_price >= latest_basis:
        direction = "多头"
        for idx in range(len(FIB_RATIOS) - 1, -1, -1):
            upper = channels[f"upper_{idx}"].iloc[-1]
            lower = channels[f"upper_{idx + 1}"].iloc[-1] if idx < len(FIB_RATIOS) - 1 else latest_basis
            if lower <= latest_price <= upper:
                price_zone = _zone_name(idx, "upper")
                break
    else:
        direction = "空头"
        for idx in range(len(FIB_RATIOS) - 1, -1, -1):
            lower = channels[f"lower_{idx}"].iloc[-1]
            upper = channels[f"lower_{idx + 1}"].iloc[-1] if idx < len(FIB_RATIOS) - 1 else latest_basis
            if lower <= latest_price <= upper:
                price_zone = _zone_name(idx, "lower")
                break

    for idx in range(len(FIB_RATIOS)):
        upper = channels[f"upper_{idx}"].iloc[-1]
        lower = channels[f"lower_{idx}"].iloc[-1]
        if prev_price <= upper and latest_price > upper:
            signal = "买入"
            strength = (idx + 1) * (1 + min(distance / 50, 1))
            direction = "多头"
            break
        if prev_price >= lower and latest_price < lower:
            signal = "卖出"
            strength = (idx + 1) * (1 + min(distance / 50, 1))
            direction = "空头"
            break

    if signal == "观望":
        strength = min(distance / 10, 6.0)

    return {"signal": signal, "strength": round(float(strength), 2), "direction": direction,
            "position": price_zone, "basis": float(latest_basis)}


@register
class TvFibSniper(Indicator):
    meta = IndicatorMeta(name="量能斐波狙击扫描器.py", lookback=220, is_incremental=False, min_data=210)

    def compute(self, df: pd.DataFrame, symbol: str, interval: str) -> pd.DataFrame:
        if not self._check_data(df):
            return self._make_insufficient_result(df, symbol, interval, {"信号": None})

        result = calculate_fibonacci_bands(df)
        return self._make_result(df, symbol, interval, {
            "信号": result["signal"],
            "方向": result["direction"],
            "强度": result["strength"],
            "价格区域": result["position"],
            "VWMA基准": round(result["basis"], 6),
        })
