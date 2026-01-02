"""期货情绪聚合表 - 完整复刻原代码"""
import os
import statistics
import pandas as pd
from datetime import datetime, timezone
from typing import Optional, List, Dict, Tuple
from ..base import Indicator, IndicatorMeta, register


def _f(v) -> Optional[float]:
    if v is None: return None
    try: return float(v)
    except: return None


def _linreg_slope(values: List[float]) -> Optional[float]:
    if not values or len(values) < 2: return None
    n = len(values)
    x_sum = (n - 1) * n / 2
    x2_sum = (n - 1) * n * (2 * n - 1) / 6
    y_sum = sum(values)
    xy_sum = sum(i * v for i, v in enumerate(values))
    denom = n * x2_sum - x_sum * x_sum
    return (n * xy_sum - x_sum * y_sum) / denom if denom else None


def _std_over_mean(values: List[float]) -> Optional[float]:
    if not values or len(values) < 2: return None
    mean_v = statistics.fmean(values)
    return statistics.pstdev(values) / mean_v if mean_v else None


def _z_score(latest: float, series: List[float]) -> Optional[float]:
    if series is None or len(series) < 2: return None
    mean_v = statistics.fmean(series)
    std_v = statistics.pstdev(series)
    return (latest - mean_v) / std_v if std_v else 0.0


def _percentile_rank(values: List[float], latest: float) -> Optional[float]:
    if not values: return None
    count = sum(1 for v in values if v is not None and v <= latest)
    total = sum(1 for v in values if v is not None)
    return count / total if total else None


def _尾部连续根数(sign_list: List[int]) -> Optional[int]:
    if not sign_list: return None
    count, last_sign = 0, None
    for s in reversed(sign_list):
        if s == 0:
            count += 1
        elif last_sign is None:
            last_sign, count = s, count + 1
        elif s == last_sign:
            count += 1
        else:
            break
    return (count if last_sign > 0 else -count) if last_sign else 0


def get_metrics_history(symbol: str, limit: int = 100, interval: str = "5m") -> List[dict]:
    """从 PostgreSQL 读取期货情绪历史数据"""
    import psycopg
    from ...config import config
    
    # 根据周期选择表和列名（期货只有 5m/15m/1h/4h/1d/1w）
    if interval == "5m":
        table = "binance_futures_metrics_5m"
        time_col = "create_time"
        closed_col = "is_closed"
    else:
        table = f"binance_futures_metrics_{interval}_last"
        time_col = "bucket"
        closed_col = "complete"
    
    try:
        with psycopg.connect(config.db_url) as conn:
            with conn.cursor() as cur:
                cur.execute(f"""
                    SELECT {time_col}, sum_open_interest, sum_open_interest_value,
                           count_toptrader_long_short_ratio, sum_toptrader_long_short_ratio,
                           count_long_short_ratio, sum_taker_long_short_vol_ratio, {closed_col}
                    FROM market_data.{table}
                    WHERE symbol = %s AND {time_col} > NOW() - INTERVAL '30 days'
                    ORDER BY {time_col} DESC
                    LIMIT %s
                """, (symbol, limit))
                rows = cur.fetchall()
                if not rows:
                    return []
                result = []
                for row in reversed(rows):
                    result.append({
                        "datetime": row[0].replace(tzinfo=timezone.utc) if row[0] else None,
                        "ts": int(row[0].timestamp()) if row[0] else 0,
                        "oi": row[1], "oiv": row[2], "ctlsr": row[3],
                        "tlsr": row[4], "lsr": row[5], "tlsvr": row[6], "x": row[7],
                    })
                return result
    except Exception:
        return []


@register
class FuturesAggregate(Indicator):
    meta = IndicatorMeta(name="期货情绪聚合表.py", lookback=1, is_incremental=False, min_data=1)
    
    def compute(self, df: pd.DataFrame, symbol: str, interval: str) -> pd.DataFrame:
        # 期货数据只有 5m/15m/1h/4h/1d/1w，跳过1m
        if interval == "1m":
            return self._make_insufficient_result(df, symbol, interval, {"信号": "不支持1m周期"})
        history = get_metrics_history(symbol, 240, interval)
        if not history:
            return self._make_insufficient_result(df, symbol, interval, {"信号": None})
        
        latest = history[-1]
        prev = history[-2] if len(history) >= 2 else None
        ts = latest.get("datetime")
        now_ts = datetime.now(timezone.utc)
        
        # 基础数据
        oi = _f(latest.get("oi"))
        oiv = _f(latest.get("oiv"))
        tlsr = _f(latest.get("tlsr"))   # 大户多空比
        lsr = _f(latest.get("lsr"))     # 全体多空比
        tlsvr = _f(latest.get("tlsvr")) # 主动成交多空比
        is_closed = 1 if latest.get("x", False) else 0
        
        # 数据新鲜秒
        freshness = (now_ts - ts).total_seconds() if ts else None
        
        # 持仓变动
        prev_oiv = _f(prev.get("oiv")) if prev else None
        oi_change = oiv - prev_oiv if oiv and prev_oiv else None
        oi_change_pct = oi_change / prev_oiv if oi_change and prev_oiv else None
        
        # 偏离度 (距离1的绝对值)
        top_dev = abs(tlsr - 1) if tlsr else None
        retail_dev = abs(lsr - 1) if lsr else None
        taker_dev = abs(tlsvr - 1) if tlsvr else None
        
        # 情绪差值
        bias_diff = tlsr - lsr if tlsr and lsr else None
        bias_spread = abs(bias_diff) if bias_diff else None
        
        # 窗口统计
        oi_series = [_f(h.get("oiv")) for h in history if _f(h.get("oiv"))]
        top_series = [_f(h.get("tlsr")) for h in history if _f(h.get("tlsr"))]
        retail_series = [_f(h.get("lsr")) for h in history if _f(h.get("lsr"))]
        taker_series = [_f(h.get("tlsvr")) for h in history if _f(h.get("tlsvr"))]
        
        volatility = _std_over_mean(oi_series)
        oi_slope = _linreg_slope(oi_series)
        oi_z = _z_score(oiv, oi_series) if oiv else None
        stability_pct = _percentile_rank(oi_series, volatility) if volatility else None
        
        # OI连续根数
        oi_deltas = []
        for a, b in zip(oi_series[:-1], oi_series[1:]):
            diff = b - a if a and b else 0
            oi_deltas.append(0 if diff == 0 else (1 if diff > 0 else -1))
        oi_streak = _尾部连续根数(oi_deltas)
        
        # 主动连续根数
        taker_signs = [0 if abs(v - 1) < 1e-9 else (1 if v > 1 else -1) for v in taker_series]
        taker_streak = _尾部连续根数(taker_signs)
        
        # 波动率
        top_vol = _std_over_mean(top_series)
        retail_vol = _std_over_mean(retail_series)
        
        # 风险分 (Z分数之和)
        delta_pct_series = [(b - a) / a for a, b in zip(oi_series[:-1], oi_series[1:]) if a and b and a != 0]
        z_delta = _z_score(oi_change_pct, delta_pct_series) if oi_change_pct else None
        top_dev_series = [abs(v - 1) for v in top_series]
        taker_dev_series = [abs(v - 1) for v in taker_series]
        z_top = _z_score(top_dev, top_dev_series) if top_dev else None
        z_taker = _z_score(taker_dev, taker_dev_series) if taker_dev else None
        components = [z for z in (z_delta, z_top, z_taker) if z is not None]
        risk_score = sum(components) if components else None
        
        # 情绪动量
        prev_tlsr = _f(prev.get("tlsr")) if prev else None
        prev_tlsvr = _f(prev.get("tlsvr")) if prev else None
        top_momentum = tlsr - prev_tlsr if tlsr and prev_tlsr else None
        taker_momentum = tlsvr - prev_tlsvr if tlsvr and prev_tlsvr else None
        
        # 翻转信号
        flip_signal = 0
        if prev_tlsr and tlsr:
            if prev_tlsr < 1 < tlsr: flip_signal = 1
            elif prev_tlsr > 1 > tlsr: flip_signal = -1
        
        # 主动跳变幅度
        taker_jump = abs(tlsvr - prev_tlsvr) if tlsvr and prev_tlsvr else None
        
        # 陈旧标记
        period_seconds = {"5m": 300, "15m": 900, "1h": 3600, "4h": 14400, "1d": 86400, "1w": 604800}
        threshold = period_seconds.get(interval, 600) * 3
        stale = 1 if (freshness is None or freshness > threshold) else 0
        
        return self._make_result(df, symbol, interval, {
            "是否闭合": is_closed,
            "数据新鲜秒": freshness,
            "持仓金额": oiv,
            "持仓张数": oi,
            "大户多空比": tlsr,
            "全体多空比": lsr,
            "主动成交多空比": tlsvr,
            "大户样本": None,  # Redis 无此数据
            "持仓变动": oi_change,
            "持仓变动%": oi_change_pct,
            "大户偏离": top_dev,
            "全体偏离": retail_dev,
            "主动偏离": taker_dev,
            "情绪差值": bias_diff,
            "情绪差值绝对值": bias_spread,
            "波动率": volatility,
            "OI连续根数": oi_streak,
            "主动连续根数": taker_streak,
            "风险分": risk_score,
            "市场占比": None,  # 需要全局计算
            "大户波动": top_vol,
            "全体波动": retail_vol,
            "持仓斜率": oi_slope,
            "持仓Z分数": oi_z,
            "大户情绪动量": top_momentum,
            "主动情绪动量": taker_momentum,
            "情绪翻转信号": flip_signal,
            "主动跳变幅度": taker_jump,
            "稳定度分位": stability_pct,
            "贡献度排名": None,  # 需要全局计算
            "陈旧标记": stale,
        }, timestamp=ts)
