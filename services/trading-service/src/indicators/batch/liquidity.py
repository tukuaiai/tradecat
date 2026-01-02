"""流动性扫描器 - Amihud + Kyle Lambda + 波动率 完整复刻"""
import numpy as np
import pandas as pd
from typing import Tuple
from ..base import Indicator, IndicatorMeta, register

KYLE_WINDOW = 180
AMIHUD_WINDOW = 100
VOLATILITY_WINDOW = 60
LIQUIDITY_WEIGHTS = {"amihud": 0.35, "kyle": 0.30, "volatility": 0.20, "volume": 0.15}


def calculate_amihud_ratio(df: pd.DataFrame) -> float:
    try:
        returns = np.log(df["close"] / df["close"].shift(1))
        abs_return = returns.abs().iloc[-1]
        volume_usd = df["volume"].iloc[-1] * df["close"].iloc[-1]
        if volume_usd == 0 or np.isnan(volume_usd) or np.isnan(abs_return):
            return np.nan
        return abs_return / volume_usd
    except:
        return np.nan


def calculate_amihud_zscore(df: pd.DataFrame, window: int = AMIHUD_WINDOW) -> tuple:
    try:
        ils = []
        for i in range(1, min(window, len(df))):
            ret = abs(np.log(df["close"].iloc[i] / df["close"].iloc[i - 1]))
            vol = df["volume"].iloc[i] * df["close"].iloc[i]
            if vol > 0:
                ils.append(ret / vol)
        if not ils:
            return np.nan, "未知", 0.0
        current_il = calculate_amihud_ratio(df)
        if np.isnan(current_il):
            return np.nan, "未知", 0.0
        mean_il, std_il = np.nanmean(ils), np.nanstd(ils)
        zscore = 0 if std_il == 0 else (current_il - mean_il) / std_il
        score = 100 / (1 + np.exp(zscore))
        level = "优秀" if score >= 80 else "良好" if score >= 65 else "一般" if score >= 50 else "紧张" if score >= 30 else "危险"
        return current_il, level, score
    except:
        return np.nan, "未知", 0.0


def _fit_simple_slope(x: np.ndarray, y: np.ndarray) -> Tuple[float, float]:
    x, y = x.flatten(), y.flatten()
    x_mean, y_mean = np.mean(x), np.mean(y)
    ss_xy = np.sum((x - x_mean) * (y - y_mean))
    ss_xx = np.sum((x - x_mean) ** 2)
    if ss_xx == 0:
        return np.nan, np.nan
    slope = ss_xy / ss_xx
    y_pred = slope * x + y_mean - slope * x_mean
    ss_tot = np.sum((y - y_mean) ** 2)
    ss_res = np.sum((y - y_pred) ** 2)
    r2 = 1 - ss_res / ss_tot if ss_tot != 0 else np.nan
    return slope, r2


def calculate_kyle_lambda(df: pd.DataFrame) -> tuple:
    try:
        if len(df) < 2 or "taker_buy_volume" not in df.columns:
            return np.nan, np.nan
        window = min(KYLE_WINDOW, len(df))
        price_change = df["close"].pct_change().tail(window).values
        order_flow = (2 * df["taker_buy_volume"] - df["volume"]).tail(window).values
        y, x = price_change.reshape(-1, 1), order_flow.reshape(-1, 1)
        mask = ~(np.isnan(y) | np.isnan(x))
        y_clean, x_clean = y[mask], x[mask]
        if len(y_clean) < max(5, window * 0.6):
            return np.nan, np.nan
        return _fit_simple_slope(x_clean, y_clean)
    except:
        return np.nan, np.nan


def calculate_kyle_zscore(df: pd.DataFrame) -> tuple:
    try:
        lambda_val, r_squared = calculate_kyle_lambda(df)
        if np.isnan(lambda_val):
            return np.nan, "未知", 0.0
        zscore = abs(lambda_val) / 0.001
        score = 100 / (1 + np.exp(zscore))
        level = "优秀" if score >= 80 else "良好" if score >= 65 else "一般" if score >= 50 else "紧张" if score >= 30 else "危险"
        return lambda_val, level, score
    except:
        return np.nan, "未知", 0.0


def calculate_volatility_component(df: pd.DataFrame) -> float:
    try:
        returns = np.log(df["close"] / df["close"].shift(1))
        volatility = returns.rolling(VOLATILITY_WINDOW).std().iloc[-1]
        if np.isnan(volatility):
            return 0
        return float(np.clip(100 * np.exp(-volatility / 0.01), 0, 100))
    except:
        return 0


def calculate_volume_component(df: pd.DataFrame) -> float:
    try:
        current_vol = df["volume"].iloc[-1]
        avg_vol = df["volume"].rolling(VOLATILITY_WINDOW).mean().iloc[-1]
        if avg_vol == 0 or np.isnan(avg_vol):
            return 0
        return float(np.clip(100 * (1 - np.exp(-current_vol / avg_vol)), 0, 100))
    except:
        return 0


def calculate_liquidity_score(df: pd.DataFrame) -> tuple:
    try:
        volatility_comp = calculate_volatility_component(df)
        volume_comp = calculate_volume_component(df)
        _, _, amihud_score = calculate_amihud_zscore(df)
        _, _, kyle_score = calculate_kyle_zscore(df)
        score = (LIQUIDITY_WEIGHTS["amihud"] * amihud_score + LIQUIDITY_WEIGHTS["kyle"] * kyle_score +
                 LIQUIDITY_WEIGHTS["volatility"] * volatility_comp + LIQUIDITY_WEIGHTS["volume"] * volume_comp)
        level = "优秀" if score >= 80 else "良好" if score >= 65 else "一般" if score >= 50 else "紧张" if score >= 30 else "危险"
        return score, level, amihud_score, kyle_score, volatility_comp, volume_comp
    except:
        return 0, "未知", 0, 0, 0, 0


@register
class Liquidity(Indicator):
    meta = IndicatorMeta(name="流动性扫描器.py", lookback=200, is_incremental=False, min_data=50)

    def compute(self, df: pd.DataFrame, symbol: str, interval: str) -> pd.DataFrame:
        if not self._check_data(df):
            return self._make_insufficient_result(df, symbol, interval, {"流动性得分": None, "流动性等级": None})

        amihud_il, amihud_level, amihud_score = calculate_amihud_zscore(df)
        kyle_lambda, kyle_level, kyle_score = calculate_kyle_zscore(df)
        liquidity_score, liquidity_level, amihud_comp, kyle_comp, vol_comp, trade_comp = calculate_liquidity_score(df)

        quote = df.get("quote_volume", df["volume"] * df["close"])
        turnover = float(quote.iloc[-1]) if not pd.isna(quote.iloc[-1]) else 0

        return self._make_result(df, symbol, interval, {
            "流动性得分": round(float(liquidity_score if not np.isnan(liquidity_score) else 0), 2),
            "流动性等级": liquidity_level,
            "Amihud得分": round(float(amihud_comp if not np.isnan(amihud_comp) else 0), 2),
            "Kyle得分": round(float(kyle_comp if not np.isnan(kyle_comp) else 0), 2),
            "波动率得分": round(float(vol_comp if not np.isnan(vol_comp) else 0), 2),
            "成交量得分": round(float(trade_comp if not np.isnan(trade_comp) else 0), 2),
            "Amihud原值": round(float(amihud_il if not np.isnan(amihud_il) else 0), 10),
            "Kyle原值": round(float(kyle_lambda if not np.isnan(kyle_lambda) else 0), 10),
            "成交额（USDT）": round(turnover, 2),
            "当前价格": float(df["close"].iloc[-1]),
        })
