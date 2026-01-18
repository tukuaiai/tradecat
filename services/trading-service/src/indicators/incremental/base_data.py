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
        tbv_raw = bar.get("taker_buy_volume")
        tbq_raw = bar.get("taker_buy_quote_volume")

        # ---- 主动买数据兜底策略 ----
        # 优先使用现成字段；仅在能推导时估算，避免“对半分”造成净流=0的假象
        tbv = safe_float(tbv_raw, None)
        tbq = safe_float(tbq_raw, None)

        # 若仅有量或额，尝试用价格推算另一项
        if tbq is None and tbv is not None and c:
            tbq = tbv * c
        if tbv is None and tbq is not None and c:
            tbv = tbq / c

        # 若仍缺失，不伪造：保持 None，后续格式化为 "-"
        if tbv is None:
            tbv = None
        if tbq is None:
            tbq = None

        if tbv is not None and tbq is not None:
            sell_vol = max(vol - tbv, 0)
            sell_quote = max(quote - tbq, 0)
            buy_ratio = tbv / vol if vol else 0
            net_flow = tbq - sell_quote
        else:
            sell_vol = None
            sell_quote = None
            buy_ratio = None
            net_flow = None

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
            "主动买卖比": buy_ratio,
            "主动卖出额": sell_quote,
            "资金流向": net_flow,
            "平均每笔成交额": quote / trade_count if trade_count else 0,
        })
