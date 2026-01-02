"""
安全指标计算工具
处理数据不足时的动态窗口调整
"""
import numpy as np
import pandas as pd
from typing import Optional, Tuple, Callable

# 各指标最小数据量要求
MIN_DATA_REQUIREMENTS = {
    'RSI': 5,
    'MACD': 10,
    'EMA': 2,
    'SMA': 2,
    'BB': 5,
    'KDJ': 5,
    'ATR': 3,
    'ADX': 10,
    'CCI': 5,
    'MFI': 5,
    'OBV': 2,
    'VWAP': 2,
    'SuperTrend': 10,
    'Ichimoku': 26,
}


def safe_rsi(close: pd.Series, period: int = 14, min_period: int = 5) -> Tuple[pd.Series, str]:
    """
    安全计算 RSI
    返回: (RSI序列, 状态)
    状态: "正常" / "参考值" / "数据不足"
    """
    n = len(close)
    
    if n < min_period:
        return pd.Series([np.nan] * n, index=close.index), "数据不足"
    
    # 动态调整周期
    actual_period = min(period, n - 1)
    status = "正常" if actual_period == period else "参考值"
    
    delta = close.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    
    avg_gain = gain.ewm(alpha=1/actual_period, min_periods=min(actual_period, n-1)).mean()
    avg_loss = loss.ewm(alpha=1/actual_period, min_periods=min(actual_period, n-1)).mean()
    
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    
    return rsi, status


def safe_ema(series: pd.Series, period: int = 20, min_period: int = 2) -> Tuple[pd.Series, str]:
    """安全计算 EMA"""
    n = len(series)
    
    if n < min_period:
        return pd.Series([np.nan] * n, index=series.index), "数据不足"
    
    actual_period = min(period, n)
    status = "正常" if actual_period == period else "参考值"
    
    ema = series.ewm(span=actual_period, adjust=False, min_periods=1).mean()
    return ema, status


def safe_sma(series: pd.Series, period: int = 20, min_period: int = 2) -> Tuple[pd.Series, str]:
    """安全计算 SMA"""
    n = len(series)
    
    if n < min_period:
        return pd.Series([np.nan] * n, index=series.index), "数据不足"
    
    actual_period = min(period, n)
    status = "正常" if actual_period == period else "参考值"
    
    sma = series.rolling(window=actual_period, min_periods=1).mean()
    return sma, status


def safe_macd(close: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9, 
              min_period: int = 10) -> Tuple[pd.Series, pd.Series, pd.Series, str]:
    """
    安全计算 MACD
    返回: (DIF, DEA, MACD柱, 状态)
    """
    n = len(close)
    
    if n < min_period:
        nan_series = pd.Series([np.nan] * n, index=close.index)
        return nan_series, nan_series, nan_series, "数据不足"
    
    # 动态调整周期
    actual_slow = min(slow, n - 1)
    actual_fast = min(fast, actual_slow - 1) if actual_slow > fast else max(2, actual_slow // 2)
    actual_signal = min(signal, n - actual_slow)
    
    status = "正常" if actual_slow == slow else "参考值"
    
    ema_fast = close.ewm(span=actual_fast, adjust=False, min_periods=1).mean()
    ema_slow = close.ewm(span=actual_slow, adjust=False, min_periods=1).mean()
    
    dif = ema_fast - ema_slow
    dea = dif.ewm(span=actual_signal, adjust=False, min_periods=1).mean()
    macd_hist = (dif - dea) * 2
    
    return dif, dea, macd_hist, status


def safe_bollinger(close: pd.Series, period: int = 20, std_dev: float = 2.0,
                   min_period: int = 5) -> Tuple[pd.Series, pd.Series, pd.Series, str]:
    """
    安全计算布林带
    返回: (上轨, 中轨, 下轨, 状态)
    """
    n = len(close)
    
    if n < min_period:
        nan_series = pd.Series([np.nan] * n, index=close.index)
        return nan_series, nan_series, nan_series, "数据不足"
    
    actual_period = min(period, n)
    status = "正常" if actual_period == period else "参考值"
    
    middle = close.rolling(window=actual_period, min_periods=min(3, actual_period)).mean()
    std = close.rolling(window=actual_period, min_periods=min(3, actual_period)).std()
    
    upper = middle + std_dev * std
    lower = middle - std_dev * std
    
    return upper, middle, lower, status


def safe_atr(high: pd.Series, low: pd.Series, close: pd.Series, 
             period: int = 14, min_period: int = 3) -> Tuple[pd.Series, str]:
    """安全计算 ATR"""
    n = len(close)
    
    if n < min_period:
        return pd.Series([np.nan] * n, index=close.index), "数据不足"
    
    actual_period = min(period, n - 1)
    status = "正常" if actual_period == period else "参考值"
    
    prev_close = close.shift(1)
    tr1 = high - low
    tr2 = abs(high - prev_close)
    tr3 = abs(low - prev_close)
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    
    atr = tr.ewm(span=actual_period, adjust=False, min_periods=1).mean()
    return atr, status


def safe_kdj(high: pd.Series, low: pd.Series, close: pd.Series,
             k_period: int = 9, d_period: int = 3, j_smooth: int = 3,
             min_period: int = 5) -> Tuple[pd.Series, pd.Series, pd.Series, str]:
    """
    安全计算 KDJ
    返回: (K, D, J, 状态)
    """
    n = len(close)
    
    if n < min_period:
        nan_series = pd.Series([np.nan] * n, index=close.index)
        return nan_series, nan_series, nan_series, "数据不足"
    
    actual_k = min(k_period, n - 1)
    status = "正常" if actual_k == k_period else "参考值"
    
    lowest_low = low.rolling(window=actual_k, min_periods=1).min()
    highest_high = high.rolling(window=actual_k, min_periods=1).max()
    
    rsv = (close - lowest_low) / (highest_high - lowest_low + 1e-10) * 100
    
    k = rsv.ewm(span=d_period, adjust=False, min_periods=1).mean()
    d = k.ewm(span=j_smooth, adjust=False, min_periods=1).mean()
    j = 3 * k - 2 * d
    
    return k, d, j, status


def get_min_data_requirement(indicator_name: str) -> int:
    """获取指标最小数据量要求"""
    return MIN_DATA_REQUIREMENTS.get(indicator_name.upper(), 5)


def check_data_sufficient(data_len: int, indicator_name: str) -> Tuple[bool, str]:
    """检查数据是否充足"""
    min_req = get_min_data_requirement(indicator_name)
    if data_len < min_req:
        return False, f"数据不足(需要{min_req}条,实际{data_len}条)"
    return True, "正常"
