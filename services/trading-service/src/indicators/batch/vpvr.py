"""VPVR排行生成器 - 完整复刻原代码"""
import pandas as pd
from dataclasses import dataclass
from typing import List
from ..base import Indicator, IndicatorMeta, register


@dataclass(slots=True)
class 成交密度桶:
    下沿价格: float
    上沿价格: float
    总成交量: float = 0.0
    主动买量: float = 0.0
    主动卖量: float = 0.0

    @property
    def 中心价格(self) -> float:
        return (self.下沿价格 + self.上沿价格) / 2


def _钳制比例(v: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, v))


def _提取节点(桶集合: List[成交密度桶], 条件) -> tuple:
    return tuple(桶.中心价格 for 桶 in 桶集合 if 条件(桶))


def _计算价值区(桶集合: List[成交密度桶], 控制点索引: int, 覆盖目标: float, 总成交量: float):
    left = right = 控制点索引
    当前覆盖 = 桶集合[控制点索引].总成交量 / 总成交量
    while 当前覆盖 < 覆盖目标 and (left > 0 or right < len(桶集合) - 1):
        左值 = 桶集合[left - 1].总成交量 if left > 0 else -1
        右值 = 桶集合[right + 1].总成交量 if right < len(桶集合) - 1 else -1
        if 左值 >= 右值 and left > 0:
            left -= 1
            当前覆盖 += 左值 / 总成交量
        elif right < len(桶集合) - 1:
            right += 1
            当前覆盖 += 右值 / 总成交量
        else:
            break
    return 桶集合[left].下沿价格, 桶集合[right].上沿价格, 当前覆盖


@register
class VPVR(Indicator):
    meta = IndicatorMeta(name="VPVR排行生成器.py", lookback=200, is_incremental=False, min_data=5)

    def compute(self, df: pd.DataFrame, symbol: str, interval: str) -> pd.DataFrame:
        桶数量 = 48
        价值区占比 = 0.7
        高节点系数 = 0.7
        低节点系数 = 0.25

        if not self._check_data(df):
            return self._make_insufficient_result(df, symbol, interval, {"控制点价格": None})

        价格下限 = float(df["low"].min())
        价格上限 = float(df["high"].max())
        if 价格上限 <= 价格下限:
            调整 = max(价格下限 * 0.001, 1e-6)
            价格上限 += 调整
            价格下限 -= 调整

        桶宽 = (价格上限 - 价格下限) / 桶数量
        桶集合: List[成交密度桶] = [
            成交密度桶(价格下限 + i * 桶宽, 价格下限 + (i + 1) * 桶宽) for i in range(桶数量)
        ]

        总成交量 = 0.0
        for _, row in df.iterrows():
            成交量 = float(row.get("volume", 0.0) or 0.0)
            if 成交量 <= 0:
                continue
            主动买 = float(row.get("taker_buy_volume", 成交量 * 0.5) or 成交量 * 0.5)
            主动卖 = max(成交量 - 主动买, 0.0)
            典型价 = (row["high"] + row["low"] + row["close"]) / 3
            相对 = (典型价 - 价格下限) / (价格上限 - 价格下限)
            索引 = min(max(int(相对 * 桶数量), 0), 桶数量 - 1)
            桶 = 桶集合[索引]
            桶.总成交量 += 成交量
            桶.主动买量 += 主动买
            桶.主动卖量 += 主动卖
            总成交量 += 成交量

        if 总成交量 <= 0:
            return self._make_insufficient_result(df, symbol, interval, {"控制点价格": None})

        控制点索引 = max(range(桶数量), key=lambda i: 桶集合[i].总成交量)
        控制点桶 = 桶集合[控制点索引]
        价值区下沿, 价值区上沿, 覆盖率 = _计算价值区(
            桶集合, 控制点索引, _钳制比例(价值区占比, 0.1, 0.95), 总成交量
        )
        高阈值 = 控制点桶.总成交量 * max(高节点系数, 0.1)
        低阈值 = 控制点桶.总成交量 * max(min(低节点系数, 高节点系数), 0.05)
        高节点 = _提取节点(桶集合, lambda 桶: 桶.总成交量 >= 高阈值)
        低节点 = _提取节点(桶集合, lambda 桶: 0 < 桶.总成交量 <= 低阈值)

        last_price = float(df["close"].iloc[-1])
        if last_price > 价值区上沿:
            价值区位置 = "价值区上方"
        elif last_price < 价值区下沿:
            价值区位置 = "价值区下方"
        else:
            价值区位置 = "价值区内"

        return self._make_result(df, symbol, interval, {
            "VPVR价格": round(控制点桶.中心价格, 6),
            "成交量分布": round(控制点桶.总成交量, 2),
            "价值区下沿": round(价值区下沿, 6),
            "价值区上沿": round(价值区上沿, 6),
            "价值区宽度": round(价值区上沿 - 价值区下沿, 6),
            "价值区宽度百分比": round((价值区上沿 - 价值区下沿) / 控制点桶.中心价格 * 100, 4) if 控制点桶.中心价格 else 0,
            "价值区覆盖率": round(覆盖率 * 100, 2),
            "高成交节点": ",".join(str(round(p, 2)) for p in 高节点),
            "低成交节点": ",".join(str(round(p, 2)) for p in 低节点),
            "价值区位置": 价值区位置,
        })


# ============ 可视化专用方法 ============

def compute_vpvr_distribution(df: pd.DataFrame, bins: int = 48) -> dict:
    """
    计算 VPVR 成交量分布，供可视化使用。
    
    Args:
        df: K线数据，需包含 high, low, close, volume 列
        bins: 价格分桶数量，默认 48（与指标计算一致）
    
    Returns:
        {
            "bin_centers": [价格中心点列表],
            "volumes": [对应成交量列表],
            "poc_price": 控制点价格,
            "poc_volume": 控制点成交量,
            "va_low": 价值区下沿,
            "va_high": 价值区上沿,
            "ohlc": {"open": x, "high": x, "low": x, "close": x}
        }
    """
    if df is None or len(df) < 5:
        return None
    
    价格下限 = float(df["low"].min())
    价格上限 = float(df["high"].max())
    if 价格上限 <= 价格下限:
        调整 = max(价格下限 * 0.001, 1e-6)
        价格上限 += 调整
        价格下限 -= 调整
    
    桶宽 = (价格上限 - 价格下限) / bins
    桶集合: List[成交密度桶] = [
        成交密度桶(价格下限 + i * 桶宽, 价格下限 + (i + 1) * 桶宽) for i in range(bins)
    ]
    
    总成交量 = 0.0
    for _, row in df.iterrows():
        成交量 = float(row.get("volume", 0.0) or 0.0)
        if 成交量 <= 0:
            continue
        典型价 = (row["high"] + row["low"] + row["close"]) / 3
        相对 = (典型价 - 价格下限) / (价格上限 - 价格下限)
        索引 = min(max(int(相对 * bins), 0), bins - 1)
        桶集合[索引].总成交量 += 成交量
        总成交量 += 成交量
    
    if 总成交量 <= 0:
        return None
    
    # 控制点
    控制点索引 = max(range(bins), key=lambda i: 桶集合[i].总成交量)
    控制点桶 = 桶集合[控制点索引]
    
    # 价值区
    价值区下沿, 价值区上沿, _ = _计算价值区(桶集合, 控制点索引, 0.7, 总成交量)
    
    # OHLC
    ohlc = {
        "open": float(df["open"].iloc[0]),
        "high": float(df["high"].max()),
        "low": float(df["low"].min()),
        "close": float(df["close"].iloc[-1]),
    }
    
    return {
        "bin_centers": [桶.中心价格 for 桶 in 桶集合],
        "volumes": [桶.总成交量 for 桶 in 桶集合],
        "poc_price": 控制点桶.中心价格,
        "poc_volume": 控制点桶.总成交量,
        "va_low": 价值区下沿,
        "va_high": 价值区上沿,
        "ohlc": ohlc,
    }


def compute_vpvr_ridge_data(
    symbol: str,
    interval: str = "1h",
    periods: int = 10,
    lookback: int = 200,
    bins: int = 48,
    db_url: str = None,
) -> dict:
    """
    计算 VPVR 山脊图数据，供可视化使用。
    
    直接读取对应 interval 的物化视图（如 candles_1h），避免从 1m 聚合。
    
    Args:
        symbol: 交易对，如 BTCUSDT
        interval: K线周期，如 1h, 4h, 1d（需有对应物化视图）
        periods: 山脊周期数量（T-0 为最新）
        lookback: 每个周期的 K 线数量（默认 200）
        bins: 价格分桶数量（默认 48）
        db_url: 数据库连接串
    
    Returns:
        periods[0] = T-0 = 最新周期，periods[1] = T-1 = 更早，以此类推
        每个 period 的 OHLC 与其分布使用同一时间窗口
    """
    import os
    import logging
    logger = logging.getLogger(__name__)
    
    # 参数校验
    if periods <= 0 or lookback <= 0 or bins <= 0:
        logger.warning("参数无效: periods=%s, lookback=%s, bins=%s", periods, lookback, bins)
        return None
    
    try:
        import psycopg2
    except ImportError:
        logger.error("psycopg2 未安装")
        return None
    
    if db_url is None:
        db_url = os.environ.get("DATABASE_URL", "postgresql://postgres:postgres@localhost:5433/market_data")
    
    # interval 对应的物化视图表名
    table_map = {
        "1m": "candles_1m", "5m": "candles_5m", "15m": "candles_15m", 
        "30m": "candles_30m", "1h": "candles_1h", "2h": "candles_2h",
        "4h": "candles_4h", "6h": "candles_6h", "8h": "candles_8h",
        "12h": "candles_12h", "1d": "candles_1d", "3d": "candles_3d", "1w": "candles_1w",
    }
    table_name = table_map.get(interval)
    if not table_name:
        logger.warning("不支持的 interval: %s", interval)
        return None
    
    total_candles = periods * lookback  # 需要 periods * lookback 根 K 线
    logger.debug("VPVR ridge: symbol=%s, interval=%s, periods=%s, lookback=%s, bins=%s, total=%s",
                 symbol, interval, periods, lookback, bins, total_candles)
    
    try:
        # 连接超时 3s，查询超时 5s
        with psycopg2.connect(db_url, connect_timeout=3) as conn:
            with conn.cursor() as cur:
                cur.execute("SET statement_timeout = '5s'")
                
                # 直接读物化视图，按时间倒序（最新在前）
                cur.execute(f"""
                    SELECT bucket_ts, open, high, low, close, volume
                    FROM market_data.{table_name}
                    WHERE symbol = %s
                    ORDER BY bucket_ts DESC
                    LIMIT %s
                """, (symbol, total_candles))
                rows = cur.fetchall()
    except Exception as e:
        logger.error("数据库查询失败: %s", e)
        return None
    
    if len(rows) < total_candles:
        logger.warning("数据不足: 需要 %s 条，实际 %s 条", total_candles, len(rows))
        return None
    
    # rows 已按时间倒序：rows[0] = 最新，rows[1] = 次新...
    # 每个周期用不重叠的 lookback 根 K 线
    # T-0: OHLC = rows[0], VPVR = rows[0:lookback]
    # T-1: OHLC = rows[lookback], VPVR = rows[lookback:2*lookback]
    # T-i: OHLC = rows[i*lookback], VPVR = rows[i*lookback:(i+1)*lookback]
    result_periods = []
    for i in range(periods):
        start = i * lookback
        end = start + lookback
        if end > len(rows):
            break
        
        # 该周期的 K 线切片
        chunk = rows[start:end]
        
        # OHLC 用该周期第一根（最新的那根）
        kline_row = chunk[0]
        ohlc = {
            "open": float(kline_row[1]),
            "high": float(kline_row[2]),
            "low": float(kline_row[3]),
            "close": float(kline_row[4]),
        }
        
        # VPVR 用整个切片（反转为时间正序）
        vpvr_rows = chunk[::-1]
        
        df = pd.DataFrame(vpvr_rows, columns=["bucket_ts", "open", "high", "low", "close", "volume"])
        for col in ["open", "high", "low", "close", "volume"]:
            df[col] = df[col].astype(float)
        
        # 检查成交量是否为 0
        total_vol = df["volume"].sum()
        if total_vol <= 0:
            logger.debug("周期 T-%s 成交量为 0，跳过", i)
            continue
        
        dist = compute_vpvr_distribution(df, bins)
        if dist:
            dist["label"] = f"T-{i}"
            dist["ohlc"] = ohlc  # 使用该周期对应的单根 K 线 OHLC
            result_periods.append(dist)
    
    if not result_periods:
        logger.warning("无有效周期数据")
        return None
    
    return {
        "symbol": symbol,
        "interval": interval,
        "lookback": lookback,
        "periods": result_periods,  # T-0 在前（最新），T-n 在后（更早）
    }
