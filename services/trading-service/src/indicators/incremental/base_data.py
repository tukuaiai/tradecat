"""基础数据同步器"""
import math
import pandas as pd
from ..base import Indicator, IndicatorMeta, register


def safe_float(v, default=0):
    if v is None or (isinstance(v, float) and math.isnan(v)):
        return default
    try:
        return float(v)
    except Exception:
        return default


def safe_int(v, default=0):
    if v is None or (isinstance(v, float) and math.isnan(v)):
        return default
    try:
        return int(v)
    except Exception:
        return default


@register
class BaseData(Indicator):
    meta = IndicatorMeta(name="基础数据同步器.py", lookback=1, is_incremental=True)

    def compute(self, df: pd.DataFrame, symbol: str, interval: str) -> pd.DataFrame:
        if df.empty:
            return pd.DataFrame()
        bar = df.iloc[-1]
        o = safe_float(bar.get("open"))
        h = safe_float(bar.get("high"))
        low = safe_float(bar.get("low"))
        c = safe_float(bar.get("close"))
        vol = safe_float(bar.get("volume"))
        quote = safe_float(bar.get("quote_volume"), vol * c)
        trade_count = safe_int(bar.get("trade_count"))
        tbv = safe_float(bar.get("taker_buy_volume"), vol * 0.5)
        tbq = safe_float(bar.get("taker_buy_quote_volume"), quote * 0.5)
        sell_vol = max(vol - tbv, 0)
        sell_quote = max(quote - tbq, 0)
        return self._make_result(df, symbol, interval, {
            "开盘价": o,
            "最高价": h,
            "最低价": low,
            "收盘价": c,
            "当前价格": c,
            "成交量": vol,
            "成交额": quote,
            "振幅": (h - low) / low if low else 0,
            "变化率": (c - o) / o if o else 0,
            "交易次数": trade_count,
            "成交笔数": trade_count,
            "主动买入量": tbv,
            "主动买量": tbv,
            "主动买额": tbq,
            "主动卖出量": sell_vol,
            "主动买卖比": tbv / vol if vol else 0,
            "主动卖出额": sell_quote,
            "资金流向": tbq - sell_quote,
            "平均每笔成交额": quote / trade_count if trade_count else 0,
        })
