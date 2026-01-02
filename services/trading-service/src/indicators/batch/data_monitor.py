"""数据监控 - 检查K线数据完整性"""
import pandas as pd
from datetime import datetime, timezone, timedelta
from ..base import Indicator, IndicatorMeta, register


def _calc_expected_bars(interval: str, days: int = 7) -> int:
    """计算指定天数内应有的K线数量"""
    minutes_map = {"1m": 1, "5m": 5, "15m": 15, "1h": 60, "4h": 240, "1d": 1440, "1w": 10080}
    mins = minutes_map.get(interval, 5)
    return (days * 24 * 60) // mins


@register
class DataMonitor(Indicator):
    meta = IndicatorMeta(name="数据监控.py", lookback=1, is_incremental=False, min_data=1)
    
    def compute(self, df: pd.DataFrame, symbol: str, interval: str) -> pd.DataFrame:
        if df.empty:
            return self._make_insufficient_result(df, symbol, interval, {"已加载K线": 0})
        
        loaded = len(df)
        latest = df.index[-1] if hasattr(df.index[-1], 'isoformat') else None
        
        # 只对 1m 计算缺口
        expected = None
        gap = None
        if interval == "1m":
            expected = _calc_expected_bars(interval, 7)
            gap = max(0, expected - loaded)
        
        return self._make_result(df, symbol, interval, {
            "已加载根数": loaded,
            "最新时间": latest.isoformat() if latest else None,
            "本周应有根数": expected,
            "缺口": gap,
        })
