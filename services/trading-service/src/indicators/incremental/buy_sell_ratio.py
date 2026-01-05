"""主动买卖比指标"""
import pandas as pd
from ..base import Indicator, IndicatorMeta, register


@register
class BuySellRatio(Indicator):
    meta = IndicatorMeta(name="主动买卖比扫描器.py", lookback=1, is_incremental=True)

    def compute(self, df: pd.DataFrame, symbol: str, interval: str) -> pd.DataFrame:
        if df.empty or "taker_buy_volume" not in df.columns:
            return pd.DataFrame()
        last = df.iloc[-1]
        vol = float(last.get("volume", 0) or 0)
        if vol <= 0:
            return pd.DataFrame()
        buy = float(last.get("taker_buy_volume", vol * 0.5) or 0)
        sell = max(vol - buy, 0)
        ratio = buy / vol if vol > 0 else 0
        return self._make_result(df, symbol, interval, {
            "主动买量": buy,
            "主动卖量": sell,
            "主动买卖比": ratio,
            "价格": float(last.get("close", 0)),
        })
