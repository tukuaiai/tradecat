"""期货情绪指标（从 PostgreSQL 读取）"""
import pandas as pd
from datetime import timezone
from typing import Optional, Dict
from ..base import Indicator, IndicatorMeta, register

# 缓存 {interval: {symbol: data}}
_METRICS_CACHE: Dict[str, Dict[str, dict]] = {}
_CACHE_TS: Dict[str, float] = {}


def _load_all_metrics(interval: str = "5m"):
    """批量加载所有币种的最新期货数据"""
    global _METRICS_CACHE, _CACHE_TS
    import time
    import psycopg
    from ...config import config

    # 缓存 60 秒
    if time.time() - _CACHE_TS.get(interval, 0) < 60 and interval in _METRICS_CACHE:
        return

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
                    SELECT DISTINCT ON (symbol) 
                        symbol, {time_col}, sum_open_interest, sum_open_interest_value,
                        count_toptrader_long_short_ratio, sum_toptrader_long_short_ratio,
                        count_long_short_ratio, sum_taker_long_short_vol_ratio
                    FROM market_data.{table}
                    WHERE {time_col} > NOW() - INTERVAL '30 days'
                    ORDER BY symbol, {time_col} DESC
                """)
                _METRICS_CACHE[interval] = {}
                for row in cur.fetchall():
                    _METRICS_CACHE[interval][row[0]] = {
                        "datetime": row[1].replace(tzinfo=timezone.utc) if row[1] else None,
                        "oi": row[2], "oiv": row[3], "ctlsr": row[4],
                        "tlsr": row[5], "lsr": row[6], "tlsvr": row[7],
                    }
                _CACHE_TS[interval] = time.time()
    except Exception:
        pass


def get_latest_metrics(symbol: str, interval: str = "5m") -> Optional[dict]:
    """获取单个币种的最新期货数据"""
    _load_all_metrics(interval)
    return _METRICS_CACHE.get(interval, {}).get(symbol)


def set_metrics_cache(cache: Dict[str, dict], interval: str = "5m"):
    """设置期货数据缓存（用于跨进程传递）"""
    global _METRICS_CACHE, _CACHE_TS
    import time
    _METRICS_CACHE[interval] = cache
    _CACHE_TS[interval] = time.time()


def get_metrics_cache(interval: str = "5m") -> Dict[str, dict]:
    """获取期货数据缓存"""
    _load_all_metrics(interval)
    return _METRICS_CACHE.get(interval, {}).copy()


@register
class FuturesSentiment(Indicator):
    meta = IndicatorMeta(name="期货情绪元数据.py", lookback=1, is_incremental=True)

    def compute(self, df: pd.DataFrame, symbol: str, interval: str) -> pd.DataFrame:
        # 期货数据只有 5m/15m/1h/4h/1d/1w，跳过1m
        if interval == "1m":
            return pd.DataFrame()
        metrics = get_latest_metrics(symbol, interval)
        if not metrics:
            return pd.DataFrame()

        def f(v):
            try:
                return float(v) if v is not None else None
            except Exception:
                return None

        ts = metrics.get("datetime")
        return self._make_result(df, symbol, interval, {
            "持仓张数": f(metrics.get("oi")),
            "持仓金额": f(metrics.get("oiv")),
            "大户多空比样本": f(metrics.get("ctlsr")),
            "大户多空比总和": f(metrics.get("tlsr")),
            "全体多空比样本": f(metrics.get("lsr")),
            "主动成交多空比总和": f(metrics.get("tlsvr")),
            "大户多空比": f(metrics.get("tlsr")),
            "全体多空比": f(metrics.get("lsr")),
            "主动成交多空比": f(metrics.get("tlsvr")),
        }, timestamp=ts)
