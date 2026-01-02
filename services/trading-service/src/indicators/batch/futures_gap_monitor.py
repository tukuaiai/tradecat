"""期货情绪缺口监控 - 检测5m情绪数据缺口"""
import pandas as pd
from datetime import datetime, timezone, timedelta
from typing import List, Dict
from ..base import Indicator, IndicatorMeta, register


def get_metrics_times(symbol: str, limit: int = 240, interval: str = "5m") -> List[datetime]:
    """从 PostgreSQL 获取时间戳列表"""
    import psycopg
    from ...config import config
    
    # 根据周期选择表和列名
    if interval == "5m":
        table = "binance_futures_metrics_5m"
        time_col = "create_time"
    else:
        table = f"binance_futures_metrics_{interval}_last"
        time_col = "bucket"
    
    try:
        with psycopg.connect(config.db_url) as conn:
            with conn.cursor() as cur:
                cur.execute(f"""
                    SELECT {time_col} FROM market_data.{table}
                    WHERE symbol = %s AND {time_col} > NOW() - INTERVAL '30 days'
                    ORDER BY {time_col} DESC
                    LIMIT %s
                """, (symbol, limit))
                rows = cur.fetchall()
                return [r[0].replace(tzinfo=timezone.utc) for r in reversed(rows) if r[0]]
    except:
        return []


def detect_gaps(times: List[datetime], interval_sec: int = 300) -> Dict:
    """检测时间序列中的缺口"""
    if not times:
        return {"已加载根数": 0, "最新时间": None, "缺失根数": None, "首缺口起": None, "首缺口止": None}
    
    times = sorted(set(times))
    missing_segments = []
    for i in range(1, len(times)):
        delta = (times[i] - times[i-1]).total_seconds()
        if delta > interval_sec:
            miss = int(delta // interval_sec) - 1
            gap_start = times[i-1] + timedelta(seconds=interval_sec)
            gap_end = times[i] - timedelta(seconds=interval_sec)
            missing_segments.append((gap_start, gap_end, miss))
    
    total_missing = sum(seg[2] for seg in missing_segments)
    first_gap = missing_segments[0] if missing_segments else (None, None, 0)
    
    return {
        "已加载根数": len(times),
        "最新时间": times[-1].isoformat(),
        "缺失根数": total_missing,
        "首缺口起": first_gap[0].isoformat() if first_gap[0] else None,
        "首缺口止": first_gap[1].isoformat() if first_gap[1] else None,
    }


@register
class FuturesGapMonitor(Indicator):
    meta = IndicatorMeta(name="期货情绪缺口监控.py", lookback=1, is_incremental=False, min_data=1)
    
    def compute(self, df: pd.DataFrame, symbol: str, interval: str) -> pd.DataFrame:
        # 只监控 5m 周期
        if interval != "5m":
            return self._make_insufficient_result(df, symbol, interval, {"信号": "仅支持5m周期"})
        
        times = get_metrics_times(symbol, 240, interval)
        gap_info = detect_gaps(times, 300)
        
        # 不使用 _make_result，直接构建（因为没有数据时间字段）
        row = {"交易对": symbol, **gap_info}
        return pd.DataFrame([row])
