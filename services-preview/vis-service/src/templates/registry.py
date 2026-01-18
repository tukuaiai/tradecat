"""
模板注册与示例渲染器。

内置 4 个即用模板：
- line-basic：基础折线（示例）
- kline-basic：K 线 + 均线 + 量能
- macd: 价格 + MACD
- equity-drawdown: 权益曲线 + 回撤
"""

from __future__ import annotations

import io
import json
import logging
import math
import os
import re
from datetime import datetime, timezone
from functools import lru_cache
from pathlib import Path
from typing import Callable, Dict, Iterable, List, Tuple

import matplotlib
import mplfinance as mpf
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import seaborn as sns
from adjustText import adjust_text
from pydantic import BaseModel

# 使用无界面后端，避免服务器缺乏显示设备时报错
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

logger = logging.getLogger(__name__)


RenderFn = Callable[[Dict, str], Tuple[object, str]]


class TemplateMeta(BaseModel):
    """模板元信息，用于对外展示与路由校验。"""

    template_id: str
    name: str
    description: str
    outputs: List[str]
    params: List[str]
    sample: Dict


class TemplateRegistry:
    """简单的内存模板注册表。"""

    def __init__(self) -> None:
        self._templates: Dict[str, Tuple[TemplateMeta, RenderFn]] = {}

    def register(self, meta: TemplateMeta, render_fn: RenderFn) -> None:
        if meta.template_id in self._templates:
            raise ValueError(f"模板重复注册: {meta.template_id}")
        self._templates[meta.template_id] = (meta, render_fn)
        logger.info("已注册模板: %s", meta.template_id)

    def list(self) -> Iterable[TemplateMeta]:
        return (meta for meta, _ in self._templates.values())

    def get(self, template_id: str) -> Tuple[TemplateMeta, RenderFn] | None:
        return self._templates.get(template_id)


def render_line_basic(params: Dict, output: str) -> Tuple[object, str]:
    """
    基础折线图模板。

    输入参数：
    - series: 数值列表，必填
    - title: 图表标题，可选
    """

    series = params.get("series")
    if not series:
        raise ValueError("缺少参数 series（数值列表）")

    title = params.get("title", "Line Chart")
    df = pd.DataFrame({"y": series})
    df["x"] = df.index

    if output == "json":
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=df["x"], y=df["y"], mode="lines+markers", name="series"))
        fig.update_layout(title=title, template="plotly_white")
        return fig.to_dict(), "application/json"

    # 默认输出 PNG
    sns.set_theme(style="whitegrid")
    fig, ax = plt.subplots(figsize=(8, 4))
    ax.plot(df["x"], df["y"], color="#2563eb", linewidth=1.8)
    ax.scatter(df["x"], df["y"], color="#1d4ed8", s=10)
    ax.set_title(title)
    ax.set_xlabel("index")
    ax.set_ylabel("value")
    fig.tight_layout()

    buffer = io.BytesIO()
    fig.savefig(buffer, format="png", dpi=160, bbox_inches="tight")
    plt.close(fig)
    buffer.seek(0)
    return buffer.read(), "image/png"


def _fig_to_png(fig) -> bytes:
    """通用 PNG 导出。"""

    buffer = io.BytesIO()
    fig.savefig(buffer, format="png", dpi=160, bbox_inches="tight")
    plt.close(fig)
    buffer.seek(0)
    return buffer.read()


def render_kline_basic(params: Dict, output: str) -> Tuple[object, str]:
    """
    基础 K 线图（含均线、量能）。

    必填：
    - open, high, low, close: 等长数列
    可选：
    - volume: 数列
    - ma_periods: 均线周期列表（默认 [7, 25]）
    - title: 标题
    - timestamps: 时间戳字符串数组（可选，长度一致则用于 X 轴）
    """

    required = ["open", "high", "low", "close"]
    for key in required:
        if key not in params:
            raise ValueError(f"缺少参数 {key}")

    df = pd.DataFrame(
        {
            "Open": params["open"],
            "High": params["high"],
            "Low": params["low"],
            "Close": params["close"],
        }
    )

    if "volume" in params:
        df["Volume"] = params["volume"]

    if "timestamps" in params and len(params["timestamps"]) == len(df):
        df.index = pd.to_datetime(params["timestamps"])
    else:
        df.index = pd.RangeIndex(len(df))

    ma_periods = params.get("ma_periods", [7, 25])
    title = params.get("title", "Kline")

    if output == "json":
        fig = go.Figure(
            data=[
                go.Candlestick(
                    x=df.index,
                    open=df["Open"],
                    high=df["High"],
                    low=df["Low"],
                    close=df["Close"],
                    name="Kline",
                )
            ]
        )
        for period in ma_periods:
            if period < len(df):
                fig.add_trace(
                    go.Scatter(
                        x=df.index,
                        y=df["Close"].rolling(period).mean(),
                        mode="lines",
                        name=f"MA{period}",
                    )
                )
        if "Volume" in df:
            fig.add_trace(
                go.Bar(x=df.index, y=df["Volume"], name="Volume", yaxis="y2", opacity=0.3)
            )
            fig.update_layout(
                yaxis2=dict(overlaying="y", side="right", showgrid=False, title="Volume")
            )
        fig.update_layout(title=title, template="plotly_white")
        return fig.to_dict(), "application/json"

    mpf_kwargs = {
        "type": "candle",
        "style": "yahoo",
        "mav": [p for p in ma_periods if p < len(df)],
        "volume": "Volume" in df.columns,
        "title": title,
        "returnfig": True,
        "figratio": (16, 9),
        "figscale": 1.1,
    }
    fig, _ = mpf.plot(df, **mpf_kwargs)
    return _fig_to_png(fig), "image/png"


# ==================== 多周期K线包络（复用外部模板） ====================
_INTERVAL_PATTERN = re.compile(r"^(\d+)([smhdwM])$")
_INTERVAL_UNIT_SECONDS = {"s": 1, "m": 60, "h": 3600, "d": 86400, "w": 604800, "M": 2592000}
_ALLOWED_INTERVALS = {
    "1m", "3m", "5m", "15m", "30m",
    "1h", "2h", "4h", "6h", "8h", "12h",
    "1d", "3d", "1w", "1M",
}
_DEFAULT_RANGE_DAYS = 30


def _parse_range_days(val: object) -> int | None:
    """解析 range 参数，支持 '30d'/'7'/'90D' 等。"""
    if val is None:
        return None
    if isinstance(val, (int, float)):
        return int(val)
    text = str(val).strip().lower()
    if text.endswith("d"):
        text = text[:-1]
    if not text:
        return None
    try:
        return int(float(text))
    except ValueError:
        return None


def _select_intervals_by_span(span_ms: int) -> List[str]:
    """根据时间跨度选择可视周期层级（LOD）。"""
    days = max(span_ms / 86400000, 0.0)
    if days > 180:
        return ["1d", "4h"]
    if days > 60:
        return ["1d", "4h", "1h"]
    if days > 14:
        return ["4h", "1h", "15m"]
    if days > 3:
        return ["1h", "15m", "5m"]
    return ["15m", "5m", "1m"]


def _normalize_interval(interval: str) -> str:
    """标准化周期字符串，并确保在允许列表内。"""
    match = _INTERVAL_PATTERN.match(str(interval).strip())
    if not match:
        raise ValueError(f"无效周期: {interval}")
    value, unit = match.groups()
    value = int(value)
    if unit == "M":
        normalized = f"{value}M"
    else:
        normalized = f"{value}{unit.lower()}"
    if normalized not in _ALLOWED_INTERVALS:
        raise ValueError(f"不支持的周期: {normalized}")
    return normalized


def _interval_seconds(interval: str) -> int:
    """返回周期秒数。"""
    match = _INTERVAL_PATTERN.match(interval)
    if not match:
        raise ValueError(f"无效周期: {interval}")
    value, unit = match.groups()
    return int(value) * _INTERVAL_UNIT_SECONDS[unit]


def _interval_table(interval: str) -> str:
    """周期到视图表名映射。"""
    if interval.endswith("M"):
        return '"candles_1M"'
    return f"candles_{interval}"


@lru_cache(maxsize=2)
def _load_envelope_template() -> str:
    """加载外部包络可视化 HTML 模板（原样复用）。"""
    template_path = Path(__file__).resolve().parents[4] / "libs" / "external" / "Financial-Fractal-KLine-main" / "multi_period_kline_static.html"
    if not template_path.exists():
        raise ValueError(f"未找到模板文件: {template_path}")
    return template_path.read_text(encoding="utf-8")


def _replace_embedded_payload(html: str, payload: Dict, title: str | None = None, lead: str | None = None) -> str:
    """将 payload 注入模板中的 embedded-klines 节点。"""
    payload_json = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
    html = re.sub(
        r'(<script type="application/json" id="embedded-klines">)(.*?)(</script>)',
        rf"\1{payload_json}\3",
        html,
        flags=re.S,
    )
    if title:
        html = re.sub(r"(<h1>)(.*?)(</h1>)", rf"\1{title}\3", html, count=1, flags=re.S)
    if lead:
        html = re.sub(r'(<p class="lead">)(.*?)(</p>)', rf"\1{lead}\3", html, count=1, flags=re.S)
    return html


def _fetch_multi_interval_klines(params: Dict) -> Dict:
    """按时间窗口逐周期查询 TimescaleDB，构造包络可视化数据。"""
    from core.settings import get_settings
    import psycopg2

    symbol = params.get("symbol")
    if not symbol:
        raise ValueError("缺少参数 symbol")
    symbol = str(symbol).upper()

    exchange = params.get("exchange") or os.environ.get("BINANCE_WS_DB_EXCHANGE") or os.environ.get("DB_EXCHANGE") or "binance_futures_um"
    intervals_param = params.get("intervals")

    if intervals_param and str(intervals_param).strip().lower() != "auto":
        if isinstance(intervals_param, str):
            intervals = [s.strip() for s in intervals_param.split(",") if s.strip()]
        else:
            intervals = list(intervals_param)
    else:
        intervals = []

    limit = int(params.get("limit", 500))
    if limit <= 0:
        raise ValueError("limit 必须 > 0")

    end_ms = params.get("end_time") or params.get("endTime")
    start_ms = params.get("start_time") or params.get("startTime")
    range_days = _parse_range_days(params.get("range_days") or params.get("rangeDays") or params.get("range"))

    settings = get_settings()
    if not settings.database_url:
        raise ValueError("未配置 DATABASE_URL / VIS_SERVICE_DATABASE_URL")

    with psycopg2.connect(settings.database_url) as conn:
        if end_ms is None:
            with conn.cursor() as cur:
                candidates = []
                if intervals:
                    candidates = list(intervals)
                else:
                    candidates = ["1m", "5m", "15m", "1h", "4h", "1d"]
                resolved_base = None
                for interval in candidates:
                    table = _interval_table(interval)
                    try:
                        cur.execute(
                            f"SELECT MAX(bucket_ts) FROM market_data.{table} WHERE symbol = %s AND exchange = %s",
                            (symbol, exchange),
                        )
                        row = cur.fetchone()
                    except Exception as exc:  # noqa: BLE001
                        logger.warning("读取 %s 失败: %s", table, exc)
                        continue
                    if row and row[0] is not None:
                        end_ms = int(row[0].timestamp() * 1000)
                        resolved_base = interval
                        break
                if end_ms is None:
                    if "1m" not in candidates:
                        table = _interval_table("1m")
                        try:
                            cur.execute(
                                f"SELECT MAX(bucket_ts) FROM market_data.{table} WHERE symbol = %s AND exchange = %s",
                                (symbol, exchange),
                            )
                            row = cur.fetchone()
                            if row and row[0] is not None:
                                end_ms = int(row[0].timestamp() * 1000)
                                resolved_base = "1m"
                        except Exception as exc:  # noqa: BLE001
                            logger.warning("读取 %s 失败: %s", table, exc)
                    if end_ms is None:
                        raise ValueError(f"无可用数据: {symbol} {exchange} ({','.join(candidates)})")
                if resolved_base:
                    base_interval = resolved_base

        if start_ms is None:
            if range_days is None:
                range_days = _DEFAULT_RANGE_DAYS
            start_ms = int(end_ms - (range_days * 86400000))

        if start_ms > end_ms:
            start_ms, end_ms = end_ms, start_ms

        span_ms = end_ms - start_ms

        if not intervals:
            intervals = _select_intervals_by_span(span_ms)

        intervals = [_normalize_interval(iv) for iv in intervals]
        if not intervals:
            raise ValueError("intervals 为空")

        base_interval = params.get("base_interval")
        if base_interval:
            base_interval = _normalize_interval(base_interval)
            if base_interval not in intervals:
                intervals.insert(0, base_interval)
        base_interval = base_interval or min(intervals, key=_interval_seconds)

        payload = {
            "symbol": symbol,
            "exchange": exchange,
            "fetchedAt": datetime.now(timezone.utc).isoformat(),
            "source": "TimescaleDB",
            "intervals": intervals,
            "klines": {},
        }

        has_any = False
        for interval in intervals:
            table = _interval_table(interval)
            interval_ms = _interval_seconds(interval) * 1000
            try:
                with conn.cursor() as cur:
                    cur.execute(
                        f"""
                        SELECT bucket_ts, open, high, low, close, volume
                        FROM market_data.{table}
                        WHERE symbol = %s
                          AND exchange = %s
                          AND bucket_ts >= to_timestamp(%s / 1000.0)
                          AND bucket_ts <= to_timestamp(%s / 1000.0)
                        ORDER BY bucket_ts ASC
                        """,
                        (symbol, exchange, start_ms, end_ms),
                    )
                    rows = cur.fetchall()
            except Exception as exc:  # noqa: BLE001
                logger.warning("查询 %s 失败: %s", table, exc)
                rows = []

            series = []
            for bucket_ts, open_v, high_v, low_v, close_v, volume_v in rows:
                open_time = int(bucket_ts.timestamp() * 1000)
                series.append(
                    {
                        "openTime": open_time,
                        "open": float(open_v),
                        "high": float(high_v),
                        "low": float(low_v),
                        "close": float(close_v),
                        "volume": float(volume_v) if volume_v is not None else 0.0,
                        "closeTime": int(open_time + interval_ms - 1),
                    }
                )

            payload["klines"][interval] = series
            if series:
                has_any = True

    if not has_any:
        raise ValueError(f"无可用数据: {symbol} {exchange} ({','.join(intervals)})")

    return payload


def render_kline_envelope(params: Dict, output: str) -> Tuple[object, str]:
    """
    多周期 K 线包络（复用 Financial-Fractal-KLine 的前端逻辑）。

    必填：
    - symbol: 交易对

    可选：
    - intervals: 周期列表或逗号分隔字符串（默认 5m,1h,4h,1d）
    - base_interval: 用于计算窗口的基准周期
    - limit: 基准周期根数（默认 500）
    - startTime/endTime: 毫秒时间戳窗口
    - exchange: 交易所（默认 Binance）
    - title/lead: HTML 标题与说明
    """
    payload = _fetch_multi_interval_klines(params)

    if output == "json":
        return payload, "application/json"

    html = _load_envelope_template()
    title = params.get("title")
    lead = params.get("lead")
    html = _replace_embedded_payload(html, payload, title=title, lead=lead)
    return html, "text/html; charset=utf-8"


def render_macd(params: Dict, output: str) -> Tuple[object, str]:
    """
    价格 + MACD 双面板。

    必填：
    - close: 收盘价序列
    可选：
    - fast: 快线周期（默认12）
    - slow: 慢线周期（默认26）
    - signal: 信号线周期（默认9）
    - title: 标题
    """

    close = params.get("close")
    if not close:
        raise ValueError("缺少参数 close")
    fast = int(params.get("fast", 12))
    slow = int(params.get("slow", 26))
    signal = int(params.get("signal", 9))
    title = params.get("title", "MACD")

    s = pd.Series(close)
    ema_fast = s.ewm(span=fast, adjust=False).mean()
    ema_slow = s.ewm(span=slow, adjust=False).mean()
    macd_line = ema_fast - ema_slow
    signal_line = macd_line.ewm(span=signal, adjust=False).mean()
    hist = macd_line - signal_line
    x = list(range(len(s)))

    if output == "json":
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=x, y=s, mode="lines", name="Close"))
        fig.add_trace(go.Bar(x=x, y=hist, name="Hist", marker_color="rgba(99,102,241,0.5)"))
        fig.add_trace(go.Scatter(x=x, y=macd_line, mode="lines", name="MACD"))
        fig.add_trace(go.Scatter(x=x, y=signal_line, mode="lines", name="Signal"))
        fig.update_layout(title=title, template="plotly_white")
        return fig.to_dict(), "application/json"

    sns.set_theme(style="whitegrid")
    fig, axes = plt.subplots(2, 1, sharex=True, figsize=(10, 6), gridspec_kw={"height_ratios": [2, 1]})
    axes[0].plot(x, s, color="#2563eb", linewidth=1.6, label="Close")
    axes[0].set_title(title)
    axes[0].legend()

    axes[1].bar(x, hist, color="#a5b4fc", alpha=0.8, label="Hist")
    axes[1].plot(x, macd_line, color="#111827", linewidth=1.2, label="MACD")
    axes[1].plot(x, signal_line, color="#ef4444", linewidth=1.2, label="Signal")
    axes[1].legend()
    fig.tight_layout()
    return _fig_to_png(fig), "image/png"


def render_equity_drawdown(params: Dict, output: str) -> Tuple[object, str]:
    """
    权益曲线 + 回撤面板。

    必填：
    - equity: 权益序列
    可选：
    - title: 标题
    - timestamps: 时间索引
    """

    equity = params.get("equity")
    if not equity:
        raise ValueError("缺少参数 equity")
    title = params.get("title", "Equity & Drawdown")

    s = pd.Series(equity)
    roll_max = s.cummax()
    drawdown = (s - roll_max) / roll_max
    x = params.get("timestamps")
    if x and len(x) == len(s):
        x_axis = pd.to_datetime(x)
    else:
        x_axis = list(range(len(s)))

    if output == "json":
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=x_axis, y=s, mode="lines", name="Equity"))
        fig.add_trace(
            go.Scatter(
                x=x_axis,
                y=drawdown,
                mode="lines",
                name="Drawdown",
                fill="tozeroy",
                fillcolor="rgba(239,68,68,0.25)",
            )
        )
        fig.update_layout(title=title, template="plotly_white")
        return fig.to_dict(), "application/json"

    sns.set_theme(style="whitegrid")
    fig, axes = plt.subplots(2, 1, sharex=True, figsize=(10, 6), gridspec_kw={"height_ratios": [2, 1]})
    axes[0].plot(x_axis, s, color="#10b981", linewidth=1.6, label="Equity")
    axes[0].set_title(title)
    axes[0].legend()

    axes[1].fill_between(x_axis, drawdown, 0, color="#fca5a5")
    axes[1].plot(x_axis, drawdown, color="#ef4444", linewidth=1.2, label="Drawdown")
    axes[1].legend()
    fig.tight_layout()
    return _fig_to_png(fig), "image/png"


def _build_bin_edges(prices: List[float], bins: int, mode: str) -> np.ndarray:
    """根据模式构建统一的 bin 边界。"""

    arr = np.asarray(prices, dtype=float)
    arr = arr[np.isfinite(arr)]
    if arr.size == 0:
        raise ValueError("无有效价格数据")

    if mode == "percentile":
        edges = np.percentile(arr, np.linspace(0, 100, bins + 1))
    else:
        median = np.median(arr)
        span = abs(median) * 0.05 if median != 0 else 1.0
        edges = np.linspace(median - span, median + span, bins + 1)

    # 防止重复边界导致直方图异常
    edges = np.maximum.accumulate(edges)
    for i in range(1, len(edges)):
        if edges[i] <= edges[i - 1]:
            edges[i] = edges[i - 1] + 1e-9
    return edges


def render_market_vpvr_heat(params: Dict, output: str) -> Tuple[object, str]:
    """
    全市场 VPVR 热力图。

    必填：
    - data: [{symbol, price/list or close/list, volume/list}, ...]

    可选：
    - bins: 分桶数，默认 40
    - bin_mode: percentile|relative，默认 percentile
    - top_n: 仅保留成交量总和前 N 个
    - scale: linear|log，默认 linear
    """

    data = params.get("data")
    if not data or not isinstance(data, list):
        raise ValueError("缺少 data 列表")

    bins = int(params.get("bins", 40))
    bin_mode = params.get("bin_mode", "percentile")
    scale = params.get("scale", "linear")
    top_n = params.get("top_n")

    # 收集全部价格用于统一分桶
    all_prices: List[float] = []
    prepared: List[Tuple[str, np.ndarray, np.ndarray]] = []
    for item in data:
        symbol = item.get("symbol")
        prices = item.get("price") or item.get("close") or []
        volumes = item.get("volume") or item.get("volumes") or []
        if not symbol or not prices or not volumes:
            continue
        if len(prices) != len(volumes):
            continue
        p_arr = np.asarray(prices, dtype=float)
        v_arr = np.asarray(volumes, dtype=float)
        mask = np.isfinite(p_arr) & np.isfinite(v_arr) & (v_arr > 0)
        p_arr = p_arr[mask]
        v_arr = v_arr[mask]
        if p_arr.size == 0:
            continue
        all_prices.extend(p_arr.tolist())
        prepared.append((symbol, p_arr, v_arr))

    if not prepared:
        raise ValueError("无有效的价格/成交量数据")

    edges = _build_bin_edges(all_prices, bins=bins, mode=bin_mode)

    rows = []
    symbols = []
    total_volumes = []
    for symbol, p_arr, v_arr in prepared:
        hist, _ = np.histogram(p_arr, bins=edges, weights=v_arr)
        total = hist.sum()
        if total <= 0:
            continue
        total_volumes.append((symbol, total))
        rows.append(hist / total)
        symbols.append(symbol)

    if not rows:
        raise ValueError("无有效聚合结果")

    # 按总成交量排序、截断 top_n
    if top_n:
        order = sorted(total_volumes, key=lambda x: x[1], reverse=True)[: int(top_n)]
        keep = {s for s, _ in order}
        mask_rows = [i for i, s in enumerate(symbols) if s in keep]
        rows = [rows[i] for i in mask_rows]
        symbols = [symbols[i] for i in mask_rows]

    mat = np.vstack(rows)
    if scale == "log":
        mat = np.log10(mat + 1e-9)

    # 生成列标签
    col_labels = []
    for i in range(len(edges) - 1):
        col_labels.append(f"{edges[i]:.4g}-{edges[i+1]:.4g}")

    if output == "json":
        fig = go.Figure(
            data=go.Heatmap(
                z=mat,
                x=col_labels,
                y=symbols,
                colorscale="Viridis",
                colorbar=dict(title="vol% (log)" if scale == "log" else "vol%"),
            )
        )
        fig.update_layout(
            title=params.get("title", "Market VPVR"),
            xaxis_title="Price bins",
            yaxis_title="Symbol",
            template="plotly_white",
        )
        return fig.to_dict(), "application/json"

    sns.set_theme(style="white")
    fig, ax = plt.subplots(figsize=(12, max(4, len(symbols) * 0.4)))
    sns.heatmap(
        mat,
        ax=ax,
        yticklabels=symbols,
        xticklabels=False,
        cmap="viridis",
        cbar_kws={"label": "vol% (log)" if scale == "log" else "vol%"},
    )
    ax.set_title(params.get("title", "Market VPVR"))
    ax.set_xlabel("Price bins")
    ax.set_ylabel("Symbol")
    fig.tight_layout()
    return _fig_to_png(fig), "image/png"

def render_vpvr_zone_strip(params: Dict, output: str) -> Tuple[object, str]:
    """
    VPVR 价值区分布图。

    每个币种按当前价格在自身价值区的相对位置(0-100%)分布。

    必填 data 字段：symbol, price, value_area_low, value_area_high
    可选 data 字段：
      - market_cap: 市值，决定圆圈大小
      - volume: 成交量，决定圆圈颜色深浅
      - price_change: 涨跌幅，决定颜色(红跌绿涨)
    """
    data = params.get("data")
    if not data or not isinstance(data, list):
        raise ValueError("缺少 data 列表")

    bands = max(2, int(params.get("bands", 6)))

    df = pd.DataFrame(data)
    required_cols = {"symbol", "price", "value_area_low", "value_area_high"}
    if not required_cols.issubset(df.columns):
        raise ValueError("data 需包含 symbol, price, value_area_low, value_area_high")

    df = df.dropna(subset=["price", "value_area_low", "value_area_high"])
    df["span"] = (df["value_area_high"] - df["value_area_low"]).astype(float)
    df = df[df["span"] > 0]
    if df.empty:
        raise ValueError("无有效 VPVR 数据")

    # 每个币种在自身价值区的相对位置 (0-1)
    raw_y = (df["price"] - df["value_area_low"]) / df["span"]
    df["y"] = raw_y.clip(0.01, 0.99)
    df["y_raw"] = raw_y.clip(0, 1)

    n = len(df)
    fig_height = min(14, max(10, n * 0.028))

    sns.set_theme(style="white")
    fig, ax = plt.subplots(1, 1, figsize=(16, fig_height), dpi=150)

    # 更丰富的背景色带
    band_colors = ["#4a148c", "#1a237e", "#006064", "#1b5e20", "#f9a825", "#ff6f00"]
    if bands != 6:
        cmap = plt.cm.viridis
        band_colors = [cmap(i / max(1, bands - 1)) for i in range(bands)]

    for i in range(bands):
        y0 = i / bands
        ax.add_patch(plt.Rectangle((0.0, y0), 1.0, 1/bands, facecolor=band_colors[i], alpha=0.85, edgecolor="none"))

    rng = np.random.default_rng(42)

    # 市值归一化 -> 圆圈大小 (平方根归一化，保留差异)
    if "market_cap" in df.columns:
        mc = df["market_cap"].fillna(df["market_cap"].median())
        mc_sqrt = np.sqrt(mc.clip(lower=1))
        mc_norm = (mc_sqrt - mc_sqrt.min()) / (mc_sqrt.max() - mc_sqrt.min() + 1e-9)
        df["size_factor"] = 0.3 + mc_norm * 1.2  # 0.3 ~ 1.5
    else:
        df["size_factor"] = 1.0

    # 成交量归一化 -> 颜色亮度
    if "volume" in df.columns:
        vol = df["volume"].fillna(df["volume"].median())
        vol_log = np.log10(vol.clip(lower=1))
        vol_norm = (vol_log - vol_log.min()) / (vol_log.max() - vol_log.min() + 1e-9)
        df["vol_factor"] = vol_norm  # 0 ~ 1
    else:
        df["vol_factor"] = 0.5

    # 智能初始布局
    df = df.sort_values("y").reset_index(drop=True)
    y_bins = pd.cut(df["y"], bins=25, labels=False)
    df["y_bin"] = y_bins.fillna(0).astype(int)

    x_positions = []
    for bin_id in range(25):
        bin_mask = df["y_bin"] == bin_id
        bin_count = bin_mask.sum()
        if bin_count > 0:
            # 层内均匀分布
            bin_indices = df[bin_mask].index.tolist()
            for i, idx in enumerate(bin_indices):
                x = (i + 0.5) / bin_count * 0.88 + 0.06
                x += rng.uniform(-0.015, 0.015)  # 小抖动
                x_positions.append((idx, x))

    for idx, x in x_positions:
        df.loc[idx, "x"] = x
    df["x"] = df["x"].clip(0.03, 0.97)

    # 绘制圆圈 - 参数调大
    # 绘制圆圈 - v13 参数
    base_font = 5.0
    texts = []

    vol_cmap = plt.cm.RdYlGn  # 红到绿：低成交量红，高成交量绿

    for _, row in df.iterrows():
        label = str(row["symbol"]).replace("USDT", "")
        if len(label) > 6:
            label = label[:6] + ".."

        # 市值决定大小
        size_factor = row.get("size_factor", 1.0)
        font_size = base_font * (0.8 + size_factor * 0.7)

        # 成交量决定填充颜色
        vol_factor = row.get("vol_factor", 0.5)
        rgba = vol_cmap(vol_factor)  # 0=红, 1=绿
        point_color = f"#{int(rgba[0]*255):02x}{int(rgba[1]*255):02x}{int(rgba[2]*255):02x}"

        # 涨跌决定边框颜色
        chg = row.get("price_change")
        if chg is not None and chg > 0.005:
            edge_color = "#1a9850"
        elif chg is not None and chg < -0.005:
            edge_color = "#d73027"
        else:
            edge_color = "#ffffff"

        # 边框宽度
        edge_width = 1.0 + size_factor * 1.2

        txt = ax.text(
            row["x"], row["y"], label,
            ha="center", va="center",
            fontsize=font_size,
            color="#1a1a1a",
            fontweight="bold",
            zorder=4,
            bbox=dict(boxstyle="circle,pad=0.4", facecolor=point_color, edgecolor=edge_color, linewidth=edge_width, alpha=0.92),
        )
        texts.append(txt)

    # adjustText 微调 - 更紧凑，限制迭代
    try:
        adjust_text(
            texts,
            x=df["x"].tolist(),
            y=df["y"].tolist(),
            ax=ax,
            expand=(1.03, 1.05),  # 更紧凑
            force_text=(0.2, 0.3),  # 减小推力
            force_static=(0.05, 0.08),
            force_pull=(0.02, 0.02),  # 增加回拉力
            arrowprops=dict(arrowstyle="-", color="#666666", lw=0.3, alpha=0.4),
            time_lim=1.5,
            only_move={"text": "xy"},
        )
    except Exception as e:
        logger.warning("adjustText failed: %s", e)

    # 样式
    for spine in ["top", "right", "bottom"]:
        ax.spines[spine].set_visible(False)
    ax.spines["left"].set_color("#444444")
    ax.spines["left"].set_linewidth(1.2)

    ax.set_xticks([])
    ax.set_yticks([0, 0.2, 0.4, 0.6, 0.8, 1.0])
    ax.set_yticklabels(["0%", "20%", "40%", "60%", "80%", "100%"], fontsize=9, color="#333333")
    ax.set_ylabel("Position in Value Area", fontsize=10, color="#333333", labelpad=8)

    # 图例 - matplotlib 原生方案
    from matplotlib.lines import Line2D
    legend_elements = [
        Line2D([0], [0], marker='o', color='w', markerfacecolor=band_colors[-1], markersize=10, label='Overbought'),
        Line2D([0], [0], marker='o', color='w', markerfacecolor=band_colors[len(band_colors)//2], markersize=10, label='POC Zone'),
        Line2D([0], [0], marker='o', color='w', markerfacecolor=band_colors[0], markersize=10, label='Oversold'),
        Line2D([0], [0], marker='o', color='w', markerfacecolor='#b71c1c', markersize=11, label='High Vol'),
        Line2D([0], [0], marker='o', color='w', markerfacecolor='#ffffcc', markersize=8, label='Low Vol'),
        Line2D([0], [0], marker='o', color='w', markerfacecolor='#ffcc80', markeredgecolor='#1a9850', markersize=10, markeredgewidth=2, label='Up'),
        Line2D([0], [0], marker='o', color='w', markerfacecolor='#ffcc80', markeredgecolor='#d73027', markersize=10, markeredgewidth=2, label='Down'),
    ]
    ax.legend(handles=legend_elements, loc='lower right', fontsize=9, framealpha=0.9, edgecolor='#cccccc')

    ax.set_xlim(-0.01, 1.01)
    ax.set_ylim(-0.02, 1.02)

    fig.suptitle(params.get("title", "VPVR Zone Distribution"), fontsize=12, color="#1e293b", fontweight="bold", y=0.98)
    fig.tight_layout(rect=[0, 0.02, 0.92, 0.96])

    if output == "json":
        return (
            {
                "title": params.get("title", "VPVR Zone Distribution"),
                "bands": bands,
                "points": [{"symbol": row["symbol"], "position": float(row["y_raw"]), "x": float(row["x"]),
                           "size_factor": float(row.get("size_factor", 1)), "vol_factor": float(row.get("vol_factor", 0.5))}
                          for _, row in df.iterrows()],
            },
            "application/json",
        )

    return _fig_to_png(fig), "image/png"


def _fetch_ridge_data_from_db(symbol: str, interval: str, periods: int = 10, lookback: int = 200, bins: int = 48) -> Tuple[List[Dict], List[Dict]]:
    """从 trading-service 的 VPVR 计算方法获取山脊图数据。

    Returns:
        (ridge_data, ohlc_data): ridge_data=[{period, prices, volumes}], ohlc_data=[{period, open, high, low, close}]
    """
    import os
    import sys

    # 添加 trading-service 路径
    trading_service_path = os.path.join(os.path.dirname(__file__), "../../../../services/trading-service/src")
    if trading_service_path not in sys.path:
        sys.path.insert(0, os.path.abspath(trading_service_path))

    try:
        from indicators.batch.vpvr import compute_vpvr_ridge_data
    except ImportError as e:
        logger.warning("无法导入 VPVR 计算方法: %s", e)
        return [], []

    result = compute_vpvr_ridge_data(symbol, interval, periods, lookback, bins)
    if not result or not result.get("periods"):
        return [], []

    ridge_data = []
    ohlc_data = []
    for p in result["periods"]:
        ridge_data.append({
            "period": p["label"],
            "distribution": [{"price": c, "volume": v} for c, v in zip(p["bin_centers"], p["volumes"])],
        })
        ohlc_data.append({
            "period": p["label"],
            "open": p["ohlc"]["open"],
            "high": p["ohlc"]["high"],
            "low": p["ohlc"]["low"],
            "close": p["ohlc"]["close"],
        })

    return ridge_data, ohlc_data


def render_vpvr_ridge(params: Dict, output: str) -> Tuple[object, str]:
    """
    VPVR 山脊图 - 展示成交量分布随时间演变。

    方式1 - 直接传数据：
    - data: [{period, distribution: [{price, volume}]}]

    方式2 - 从数据库获取：
    - symbol: 交易对，如 BTCUSDT
    - interval: 周期，如 1h, 5m
    - periods: 周期数量，默认 10
    - lookback: 每个周期的 K 线数量，默认 200（与 trading-service VPVR 一致）

    可选：
    - title: 标题
    - bins: 价格分桶数，默认 48（与 trading-service VPVR 一致）
    - overlap: 山脊重叠度，默认 0.5
    - colormap: 颜色映射，默认 viridis
    - show_ohlc: 是否显示 OHLC 价格线，默认 True
    """
    data = params.get("data")
    ohlc_data = params.get("ohlc_data", [])

    bins = int(params.get("bins", 48))  # 与 trading-service VPVR 一致

    # 如果没有 data，尝试从数据库获取
    if not data and params.get("symbol"):
        symbol = params["symbol"]
        interval = params.get("interval", "1h")
        periods_count = int(params.get("periods", 10))
        lookback = int(params.get("lookback", 200))  # 与 trading-service VPVR 一致
        data, ohlc_data = _fetch_ridge_data_from_db(symbol, interval, periods_count, lookback, bins)
        if not data:
            raise ValueError(f"无法获取 {symbol} {interval} 数据")

    if not data or not isinstance(data, list):
        raise ValueError("缺少 data 列表或 symbol 参数")
    overlap = float(params.get("overlap", 0.5))
    cmap_name = params.get("colormap", "viridis")
    show_ohlc = params.get("show_ohlc", True)

    # 自动生成标题
    if params.get("symbol"):
        default_title = f"{params['symbol']} VPVR Ridge - {params.get('interval', '1h')} x {params.get('periods', 10)}"
    else:
        default_title = "VPVR Ridge Plot"
    title = params.get("title", default_title)

    # 解析数据，构建每个时间段的价格-成交量分布
    periods = []
    distributions = []

    for item in data:
        period = item.get("period", str(len(periods)))

        if "distribution" in item:
            dist = item["distribution"]
            prices = [d["price"] for d in dist]
            volumes = [d["volume"] for d in dist]
        elif "prices" in item and "volumes" in item:
            prices = np.array(item["prices"], dtype=float)
            volumes = np.array(item["volumes"], dtype=float)
            if len(prices) != len(volumes) or len(prices) == 0:
                continue
        else:
            continue

        periods.append(period)
        distributions.append((prices, volumes))

    if not distributions:
        raise ValueError("无有效的分布数据")

    # 反转顺序：让 T-0（最新）在底部，T-n（最早）在顶部
    periods = periods[::-1]
    distributions = distributions[::-1]
    if ohlc_data:
        ohlc_data = ohlc_data[::-1]

    # 计算全局价格范围
    all_prices = np.concatenate([d[0] for d in distributions])
    price_min, price_max = np.nanmin(all_prices), np.nanmax(all_prices)
    bin_edges = np.linspace(price_min, price_max, bins + 1)
    bin_centers = (bin_edges[:-1] + bin_edges[1:]) / 2

    # 计算每个时间段的成交量分布
    histograms = []
    for prices, volumes in distributions:
        hist, _ = np.histogram(prices, bins=bin_edges, weights=volumes)
        hist = hist / (hist.max() + 1e-9)
        histograms.append(hist)

    n_periods = len(periods)

    if output == "json":
        return (
            {
                "title": title,
                "periods": periods,
                "bin_centers": bin_centers.tolist(),
                "distributions": [h.tolist() for h in histograms],
                "ohlc": ohlc_data,
            },
            "application/json",
        )

    # 使用 joypy 绘制标准山脊图
    import joypy
    import pandas as pd
    from matplotlib import cm

    # 构建 DataFrame：每行是一个价格点，包含周期标签和成交量
    df_rows = []
    for period, hist in zip(periods, histograms):
        for price, vol in zip(bin_centers, hist):
            # 按成交量重复价格点，模拟分布
            count = int(vol * 100) + 1
            for _ in range(count):
                df_rows.append({"period": period, "price": price})

    df = pd.DataFrame(df_rows)

    # joypy.joyplot 绘制
    fig, axes = joypy.joyplot(
        df,
        by="period",
        column="price",
        colormap=cm.get_cmap(cmap_name),
        overlap=overlap,
        linewidth=1,
        linecolor="white",
        fade=True,
        figsize=(12, max(6, n_periods * 0.8)),
        grid="y",
        xlabels=True,
        ylabels=True,
        legend=False,
    )

    # 添加标题和 X 轴标签
    fig.suptitle(title, fontsize=12, fontweight="bold", y=0.98)
    axes[-1].set_xlabel("Price", fontsize=10)

    # 添加 OHLC 价格线（4 条线连接各山脊子图）
    if show_ohlc and ohlc_data and len(ohlc_data) == n_periods:
        # joypy axes: axes[0] 是顶部子图，axes[-1] 是底部 X 轴
        # 每个子图的基线 y=0，山脊向上延伸
        # 需要在 figure 坐标系上绘制跨子图的线条

        # 提取 OHLC 数据
        opens = [d["open"] for d in ohlc_data]
        highs = [d["high"] for d in ohlc_data]
        lows = [d["low"] for d in ohlc_data]
        closes = [d["close"] for d in ohlc_data]

        # 获取每个子图的中心 y 位置（figure 坐标）
        y_positions = []
        for i, ax in enumerate(axes[:-1]):  # 排除最后一个（X 轴）
            bbox = ax.get_position()
            y_center = bbox.y0 + bbox.height * 0.3  # 山脊底部偏上一点
            y_positions.append(y_center)

        # 获取 x 轴范围（数据坐标 -> figure 坐标）
        main_ax = axes[-1]  # 底部轴共享 x 轴
        xlim = main_ax.get_xlim()

        def price_to_fig_x(price):
            """将价格转换为 figure x 坐标"""
            bbox = main_ax.get_position()
            rel = (price - xlim[0]) / (xlim[1] - xlim[0])
            return bbox.x0 + rel * bbox.width

        # OHLC 线条颜色和样式
        ohlc_styles = [
            ("open", opens, "#2196F3", "-", 1.5),      # 蓝色 - 开盘价
            ("high", highs, "#4CAF50", "--", 1.2),     # 绿色虚线 - 最高价
            ("low", lows, "#F44336", "--", 1.2),       # 红色虚线 - 最低价
            ("close", closes, "#FF9800", "-", 1.5),   # 橙色 - 收盘价
        ]

        # 在 figure 坐标系上绘制线条
        from matplotlib.lines import Line2D
        for name, prices, color, linestyle, linewidth in ohlc_styles:
            x_coords = [price_to_fig_x(p) for p in prices]
            line = Line2D(
                x_coords, y_positions,
                color=color, linestyle=linestyle, linewidth=linewidth,
                alpha=0.8, transform=fig.transFigure, zorder=10
            )
            fig.add_artist(line)
            # 添加端点标记
            for x, y in zip(x_coords, y_positions):
                fig.add_artist(plt.Circle(
                    (x, y), 0.006, color=color, transform=fig.transFigure, zorder=11
                ))

        # 更新图例
        from matplotlib.patches import Patch
        legend_elements = [
            Patch(facecolor=cm.get_cmap(cmap_name)(0.0), label=f'{periods[0]} (oldest)'),
            Patch(facecolor=cm.get_cmap(cmap_name)(1.0), label=f'{periods[-1]} (newest)'),
            Line2D([0], [0], color="#2196F3", linestyle="-", linewidth=1.5, label='Open'),
            Line2D([0], [0], color="#4CAF50", linestyle="--", linewidth=1.2, label='High'),
            Line2D([0], [0], color="#F44336", linestyle="--", linewidth=1.2, label='Low'),
            Line2D([0], [0], color="#FF9800", linestyle="-", linewidth=1.5, label='Close'),
        ]
        axes[0].legend(handles=legend_elements, loc='upper right', fontsize=7, framealpha=0.9, ncol=2)
    else:
        # 无 OHLC 时的简单图例
        from matplotlib.patches import Patch
        legend_elements = [
            Patch(facecolor=cm.get_cmap(cmap_name)(0.0), label=f'{periods[0]} (oldest)'),
            Patch(facecolor=cm.get_cmap(cmap_name)(1.0), label=f'{periods[-1]} (newest)'),
        ]
        axes[0].legend(handles=legend_elements, loc='upper right', fontsize=8, framealpha=0.9)

    return _fig_to_png(fig), "image/png"


def render_bb_zone_strip(params: Dict, output: str) -> Tuple[object, str]:
    """
    全市场布林带分布图 - 九宫格矩阵。

    Y轴：%B 值（价格在布林带中的位置）
    X轴：带宽（波动率）分3区 - 收窄/正常/扩张

    九宫格解读：
    - 左上：收窄+超买 → 向上突破前兆
    - 右上：扩张+超买 → 疯狂追涨
    - 左下：收窄+超卖 → 向下突破前兆
    - 右下：扩张+超卖 → 恐慌抛售

    必填 data 字段：symbol, percent_b, bandwidth
    可选 data 字段：
      - price_change: 涨跌幅，决定边框颜色(红跌绿涨)
      - volume: 成交量，决定圆圈颜色深浅
    """
    data = params.get("data")
    if not data or not isinstance(data, list):
        raise ValueError("缺少 data 列表")

    y_bands = max(2, int(params.get("bands", 5)))  # Y轴分区数
    x_bands = 3  # X轴固定3区：收窄/正常/扩张

    df = pd.DataFrame(data)
    required_cols = {"symbol", "percent_b", "bandwidth"}
    if not required_cols.issubset(df.columns):
        raise ValueError("data 需包含 symbol, percent_b, bandwidth")

    df = df.dropna(subset=["percent_b", "bandwidth"])
    df["percent_b"] = df["percent_b"].astype(float)
    df["bandwidth"] = df["bandwidth"].astype(float)
    df = df[df["bandwidth"] > 0]
    df = df.drop_duplicates(subset=["symbol"], keep="first")

    if df.empty:
        raise ValueError("无有效布林带数据")

    # Y轴：%B 映射到 0-1
    raw_y = df["percent_b"].clip(-0.5, 1.5)
    df["y"] = ((raw_y + 0.5) / 2).clip(0.02, 0.98)
    df["y_raw"] = df["percent_b"]

    # X轴：带宽按分位数分3区
    bw = df["bandwidth"]
    q33 = bw.quantile(0.33)
    q66 = bw.quantile(0.66)

    def bw_to_x_zone(b):
        if b <= q33:
            return 0  # 收窄
        elif b <= q66:
            return 1  # 正常
        else:
            return 2  # 扩张

    df["x_zone"] = df["bandwidth"].apply(bw_to_x_zone)

    # 带宽归一化用于圆圈大小
    bw_log = np.log10(bw.clip(lower=0.1) + 1)
    bw_norm = (bw_log - bw_log.min()) / (bw_log.max() - bw_log.min() + 1e-9)
    df["size_factor"] = 0.4 + bw_norm * 1.0

    # 成交量归一化 -> 颜色
    if "volume" in df.columns:
        vol = df["volume"].fillna(df["volume"].median())
        vol_log = np.log10(vol.clip(lower=1))
        vol_norm = (vol_log - vol_log.min()) / (vol_log.max() - vol_log.min() + 1e-9)
        df["vol_factor"] = vol_norm
    else:
        df["vol_factor"] = 0.5

    n = len(df)
    fig_height = min(14, max(10, n * 0.025))

    sns.set_theme(style="white")
    fig, ax = plt.subplots(1, 1, figsize=(16, fig_height), dpi=150)

    # Y轴背景色带
    y_band_colors = ["#1565C0", "#1976D2", "#4CAF50", "#FFA726", "#E53935"]
    if y_bands != 5:
        cmap = plt.cm.RdYlBu_r
        y_band_colors = [cmap(i / max(1, y_bands - 1)) for i in range(y_bands)]

    for i in range(y_bands):
        y0 = i / y_bands
        for j in range(x_bands):
            x0 = j / x_bands
            ax.add_patch(plt.Rectangle(
                (x0, y0), 1/x_bands, 1/y_bands,
                facecolor=y_band_colors[i], alpha=0.75, edgecolor="white", linewidth=0.5
            ))

    # X轴分区线和标签
    for i in range(1, x_bands):
        ax.axvline(x=i/x_bands, color="white", linewidth=2, alpha=0.9)

    # 贪心算法防重叠布局 v3
    def get_radius(size_factor):
        return 0.015 + size_factor * 0.008  # 缩小气泡

    def check_overlap(x1, y1, r1, placed_list):
        """检查与所有已放置气泡的重叠数"""
        count = 0
        for px, py, pr in placed_list:
            dx = (x1 - px) * 1.5
            dy = y1 - py
            dist = (dx**2 + dy**2) ** 0.5
            if dist < (r1 + pr) * 0.95:
                count += 1
        return count

    df["x"] = 0.5
    df["y_final"] = df["y"]

    for zone in range(x_bands):
        zone_mask = df["x_zone"] == zone
        zone_indices = df[zone_mask].index.tolist()
        if not zone_indices:
            continue

        zone_x_start = zone / x_bands + 0.02
        zone_x_end = (zone + 1) / x_bands - 0.02

        # 按 size_factor 降序（大气泡优先放）
        zone_df = df.loc[zone_indices].sort_values("size_factor", ascending=False)
        zone_placed = []

        # X 方向搜索点（更密集）
        x_grid = np.linspace(zone_x_start + 0.015, zone_x_end - 0.015, 30)
        # Y 方向偏移（更大范围）
        y_offsets = [0] + [d * s for d in range(1, 25) for s in [-0.01, 0.01]]

        for idx in zone_df.index:
            row = df.loc[idx]
            target_y = row["y"]
            radius = get_radius(row["size_factor"])

            best_pos = None
            best_score = float("inf")

            for try_x in x_grid:
                for y_off in y_offsets:
                    try_y = target_y + y_off
                    if try_y < 0.02 or try_y > 0.98:
                        continue

                    overlap = check_overlap(try_x, try_y, radius, zone_placed)
                    score = overlap * 100 + abs(y_off) * 10 + abs(try_x - (zone_x_start + zone_x_end)/2) * 2

                    if score < best_score:
                        best_score = score
                        best_pos = (try_x, try_y)

                    if overlap == 0:
                        break
                if best_score == 0:
                    break

            if best_pos:
                df.loc[idx, "x"] = best_pos[0]
                df.loc[idx, "y_final"] = best_pos[1]
                zone_placed.append((best_pos[0], best_pos[1], radius))
            else:
                df.loc[idx, "x"] = (zone_x_start + zone_x_end) / 2
                df.loc[idx, "y_final"] = target_y
                zone_placed.append(((zone_x_start + zone_x_end) / 2, target_y, radius))

    df["y"] = df["y_final"]
    df["x"] = df["x"].clip(0.02, 0.98)

    # 绘制气泡
    base_font = 4.0  # 缩小字体
    texts = []
    vol_cmap = plt.cm.YlOrRd

    for _, row in df.iterrows():
        label = str(row["symbol"]).replace("USDT", "")
        if len(label) > 5:
            label = label[:5] + ".."

        size_factor = row.get("size_factor", 1.0)
        font_size = base_font * (0.75 + size_factor * 0.4)  # 缩小

        vol_factor = row.get("vol_factor", 0.5)
        rgba = vol_cmap(vol_factor)
        point_color = f"#{int(rgba[0]*255):02x}{int(rgba[1]*255):02x}{int(rgba[2]*255):02x}"

        chg = row.get("price_change")
        if chg is not None and chg > 0.005:
            edge_color = "#1a9850"
        elif chg is not None and chg < -0.005:
            edge_color = "#d73027"
        else:
            edge_color = "#ffffff"

        edge_width = 0.8 + size_factor * 0.6

        txt = ax.text(
            row["x"], row["y"], label,
            ha="center", va="center",
            fontsize=font_size,
            color="#1a1a1a",
            fontweight="bold",
            zorder=4,
            bbox=dict(boxstyle="circle,pad=0.25", facecolor=point_color, edgecolor=edge_color, linewidth=edge_width, alpha=0.92),
        )
        texts.append(txt)

    # adjustText
    try:
        adjust_text(
            texts, x=df["x"].tolist(), y=df["y"].tolist(), ax=ax,
            expand=(1.02, 1.03), force_text=(0.15, 0.2), force_static=(0.03, 0.05),
            force_pull=(0.01, 0.01), time_lim=1.2, only_move={"text": "xy"},
            arrowprops=dict(arrowstyle="-", color="#666666", lw=0.3, alpha=0.3),
        )
    except Exception as e:
        logger.warning("adjustText failed: %s", e)

    # 样式
    for spine in ax.spines.values():
        spine.set_visible(False)

    # Y轴标签
    ax.set_yticks([0.1, 0.3, 0.5, 0.7, 0.9])
    ax.set_yticklabels(["Oversold\n(<0%)", "Lower\n(0-25%)", "Middle\n(50%)", "Upper\n(75-100%)", "Overbought\n(>100%)"], fontsize=9, color="#333")
    ax.set_ylabel("Bollinger %B", fontsize=11, color="#333", labelpad=10)

    # X轴标签
    ax.set_xticks([1/6, 3/6, 5/6])
    ax.set_xticklabels(["Squeeze\n(Narrowing)", "Normal", "Expansion\n(Volatile)"], fontsize=10, color="#333")
    ax.set_xlabel("Bandwidth (Volatility)", fontsize=11, color="#333", labelpad=10)

    # 图例
    from matplotlib.lines import Line2D
    legend_elements = [
        Line2D([0], [0], marker='o', color='w', markerfacecolor='#ff6b6b', markersize=10, label='High Volume'),
        Line2D([0], [0], marker='o', color='w', markerfacecolor='#ffffcc', markersize=8, label='Low Volume'),
        Line2D([0], [0], marker='o', color='w', markerfacecolor='#ffcc80', markeredgecolor='#1a9850', markersize=9, markeredgewidth=2, label='Rising'),
        Line2D([0], [0], marker='o', color='w', markerfacecolor='#ffcc80', markeredgecolor='#d73027', markersize=9, markeredgewidth=2, label='Falling'),
    ]
    ax.legend(handles=legend_elements, loc='upper left', fontsize=9, framealpha=0.9, edgecolor='#ccc')

    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)

    fig.suptitle(params.get("title", "Bollinger Band Matrix"), fontsize=13, color="#1e293b", fontweight="bold", y=0.98)
    fig.tight_layout(rect=[0, 0.03, 1, 0.95])

    if output == "json":
        return (
            {
                "title": params.get("title", "Bollinger Band Matrix"),
                "y_bands": y_bands,
                "x_zones": ["squeeze", "normal", "expansion"],
                "bandwidth_thresholds": {"q33": float(q33), "q66": float(q66)},
                "points": [{"symbol": row["symbol"], "percent_b": float(row["y_raw"]), "bandwidth": float(row["bandwidth"]),
                           "x_zone": int(row["x_zone"]), "x": float(row["x"]), "y": float(row["y"])}
                          for _, row in df.iterrows()],
            },
            "application/json",
        )

    return _fig_to_png(fig), "image/png"


# ============================================================
# 日内分析图表 (Intraday Analysis Charts)
# ============================================================

def render_intraday_volume_heatmap(params: Dict, output: str) -> Tuple[object, str]:
    """日内成交量热力图 - X轴:小时(0-23), Y轴:币种, 颜色:成交量"""
    data = params.get("data")
    if not data or not isinstance(data, list):
        raise ValueError("缺少 data 列表")
    
    df = pd.DataFrame(data)
    if not {"symbol", "hour", "volume"}.issubset(df.columns):
        raise ValueError("data 需包含 symbol, hour, volume")
    
    df["hour"] = df["hour"].astype(int)
    df["volume"] = df["volume"].astype(float)
    
    pivot = df.pivot_table(index="symbol", columns="hour", values="volume", aggfunc="sum", fill_value=0)
    for h in range(24):
        if h not in pivot.columns:
            pivot[h] = 0
    pivot = pivot.reindex(columns=sorted(pivot.columns))
    
    top_n = int(params.get("top_n", 30))
    row_sums = pivot.sum(axis=1).sort_values(ascending=False)
    pivot = pivot.loc[row_sums.head(top_n).index]
    
    normalize = params.get("normalize", "row")
    if normalize == "row":
        pivot = pivot.div(pivot.max(axis=1) + 1e-10, axis=0)
    elif normalize == "all":
        pivot = pivot / (pivot.max().max() + 1e-10)
    
    if output == "json":
        return {"title": params.get("title", "Intraday Volume Heatmap"), "symbols": pivot.index.tolist(),
                "hours": list(range(24)), "values": pivot.values.tolist()}, "application/json"
    
    fig_height = max(6, len(pivot) * 0.25)
    fig, ax = plt.subplots(figsize=(14, fig_height))
    sns.heatmap(pivot, ax=ax, cmap="YlOrRd", linewidths=0.5, linecolor="#f0f0f0",
                cbar_kws={"label": "Volume (normalized)", "shrink": 0.6})
    ax.set_xlabel("Hour (UTC)", fontsize=11)
    ax.set_ylabel("Symbol", fontsize=11)
    ax.set_title(params.get("title", "Intraday Volume Heatmap"), fontsize=13, fontweight="bold")
    for h in [8, 14, 20]:
        ax.axvline(x=h, color="#333", linestyle="--", alpha=0.3, linewidth=1)
    fig.tight_layout()
    return _fig_to_png(fig), "image/png"


def render_intraday_volatility(params: Dict, output: str) -> Tuple[object, str]:
    """日内波动率曲线 - 展示不同时段的平均波动率"""
    data = params.get("data")
    if not data:
        raise ValueError("缺少 data")
    
    if isinstance(data, dict):
        df = pd.DataFrame({"hour": data.get("hours", list(range(24))),
                          "volatility": data.get("volatilities", [0]*24),
                          "volume": data.get("volumes", [0]*24)})
    else:
        df = pd.DataFrame(data)
    
    if "hour" not in df.columns or "volatility" not in df.columns:
        raise ValueError("data 需包含 hour, volatility")
    
    df = df.groupby("hour").agg({"volatility": "mean", "volume": "sum"}).reset_index().sort_values("hour")
    symbol = params.get("symbol", "")
    
    if output == "json":
        return {"title": params.get("title", f"Intraday Volatility {symbol}".strip()),
                "hours": df["hour"].tolist(), "volatility": df["volatility"].tolist(),
                "volume": df["volume"].tolist() if "volume" in df.columns else None}, "application/json"
    
    fig, ax1 = plt.subplots(figsize=(12, 5))
    ax1.fill_between(df["hour"], df["volatility"], alpha=0.3, color="#e74c3c")
    ax1.plot(df["hour"], df["volatility"], color="#c0392b", linewidth=2, marker="o", markersize=5)
    ax1.set_xlabel("Hour (UTC)", fontsize=11)
    ax1.set_ylabel("Volatility (%)", fontsize=11, color="#c0392b")
    ax1.tick_params(axis="y", labelcolor="#c0392b")
    ax1.set_xlim(-0.5, 23.5)
    ax1.set_xticks(range(24))
    
    if params.get("show_volume", True) and "volume" in df.columns and df["volume"].sum() > 0:
        ax2 = ax1.twinx()
        ax2.bar(df["hour"], df["volume"], alpha=0.3, color="#3498db", width=0.6)
        ax2.set_ylabel("Volume", fontsize=11, color="#3498db")
        ax2.tick_params(axis="y", labelcolor="#3498db")
    
    high_vol_hours = df.nlargest(3, "volatility")["hour"].tolist()
    for h in high_vol_hours:
        ax1.axvline(x=h, color="#e74c3c", linestyle="--", alpha=0.5, linewidth=1)
    
    ax1.set_title(params.get("title", f"Intraday Volatility {symbol}".strip()), fontsize=13, fontweight="bold")
    ax1.grid(axis="y", alpha=0.3)
    fig.tight_layout()
    return _fig_to_png(fig), "image/png"


def render_taker_ratio_heatmap(params: Dict, output: str) -> Tuple[object, str]:
    """主动买卖比热力图 - 蓝=买压, 红=卖压"""
    data = params.get("data")
    if not data or not isinstance(data, list):
        raise ValueError("缺少 data 列表")
    
    df = pd.DataFrame(data)
    if not {"symbol", "hour", "taker_buy_ratio"}.issubset(df.columns):
        raise ValueError("data 需包含 symbol, hour, taker_buy_ratio")
    
    df["hour"] = df["hour"].astype(int)
    df["taker_buy_ratio"] = df["taker_buy_ratio"].astype(float)
    
    pivot = df.pivot_table(index="symbol", columns="hour", values="taker_buy_ratio", aggfunc="mean", fill_value=0.5)
    for h in range(24):
        if h not in pivot.columns:
            pivot[h] = 0.5
    pivot = pivot.reindex(columns=sorted(pivot.columns))
    
    top_n = int(params.get("top_n", 30))
    row_std = pivot.std(axis=1).sort_values(ascending=False)
    pivot = pivot.loc[row_std.head(top_n).index]
    
    if output == "json":
        return {"title": params.get("title", "Taker Buy Ratio Heatmap"), "symbols": pivot.index.tolist(),
                "hours": list(range(24)), "values": pivot.values.tolist()}, "application/json"
    
    fig_height = max(6, len(pivot) * 0.25)
    fig, ax = plt.subplots(figsize=(14, fig_height))
    sns.heatmap(pivot, ax=ax, cmap="RdBu", center=0.5, vmin=0.3, vmax=0.7,
                linewidths=0.5, linecolor="#f0f0f0", cbar_kws={"label": "Taker Buy Ratio", "shrink": 0.6})
    ax.set_xlabel("Hour (UTC)", fontsize=11)
    ax.set_ylabel("Symbol", fontsize=11)
    ax.set_title(params.get("title", "Taker Buy Ratio Heatmap (Blue=Buy, Red=Sell)"), fontsize=13, fontweight="bold")
    fig.tight_layout()
    return _fig_to_png(fig), "image/png"


def render_long_short_ratio(params: Dict, output: str) -> Tuple[object, str]:
    """多空比时序图 - 大户/散户/主动成交三线"""
    data = params.get("data")
    if not data or not isinstance(data, list):
        raise ValueError("缺少 data 列表")
    
    df = pd.DataFrame(data)
    if "time" not in df.columns:
        raise ValueError("data 需包含 time 字段")
    
    df["time"] = pd.to_datetime(df["time"])
    df = df.sort_values("time")
    symbol = params.get("symbol", "")
    
    if output == "json":
        result = {"title": params.get("title", f"Long/Short Ratio {symbol}".strip()),
                  "time": df["time"].dt.strftime("%Y-%m-%d %H:%M").tolist()}
        for col in ["top_trader_ratio", "global_ratio", "taker_ratio"]:
            if col in df.columns:
                result[col] = df[col].tolist()
        return result, "application/json"
    
    fig, ax = plt.subplots(figsize=(14, 6))
    colors = {"top_trader_ratio": "#e74c3c", "global_ratio": "#3498db", "taker_ratio": "#2ecc71"}
    labels = {"top_trader_ratio": "Top Traders", "global_ratio": "All Traders", "taker_ratio": "Taker"}
    for col, color in colors.items():
        if col in df.columns:
            ax.plot(df["time"], df[col], color=color, linewidth=1.5, label=labels[col], alpha=0.8)
    ax.axhline(y=1.0, color="#666", linestyle="--", alpha=0.5, linewidth=1, label="Balance (1.0)")
    ax.set_xlabel("Time", fontsize=11)
    ax.set_ylabel("Long/Short Ratio", fontsize=11)
    ax.set_title(params.get("title", f"Long/Short Ratio {symbol}".strip()), fontsize=13, fontweight="bold")
    ax.legend(loc="upper right", fontsize=9)
    ax.grid(axis="y", alpha=0.3)
    fig.autofmt_xdate(rotation=45)
    fig.tight_layout()
    return _fig_to_png(fig), "image/png"


def render_cvd_cumulative(params: Dict, output: str) -> Tuple[object, str]:
    """CVD累计图 - 日内累计买卖量差"""
    data = params.get("data")
    if not data:
        raise ValueError("缺少 data")
    
    if isinstance(data, dict):
        df = pd.DataFrame({"time": data.get("times", []), "cvd": data.get("cvd_values", []),
                          "price": data.get("prices", [None] * len(data.get("times", [])))})
    else:
        df = pd.DataFrame(data)
    
    if "time" not in df.columns or "cvd" not in df.columns:
        raise ValueError("data 需包含 time, cvd")
    
    df["time"] = pd.to_datetime(df["time"])
    df = df.sort_values("time")
    symbol = params.get("symbol", "")
    show_price = params.get("show_price", False) and "price" in df.columns
    
    if output == "json":
        result = {"title": params.get("title", f"CVD {symbol}".strip()),
                  "time": df["time"].dt.strftime("%Y-%m-%d %H:%M").tolist(), "cvd": df["cvd"].tolist()}
        if show_price:
            result["price"] = df["price"].tolist()
        return result, "application/json"
    
    fig, ax1 = plt.subplots(figsize=(14, 6))
    cvd = df["cvd"]
    ax1.fill_between(df["time"], cvd, where=(cvd >= 0), color="#2ecc71", alpha=0.4, label="Buying Pressure")
    ax1.fill_between(df["time"], cvd, where=(cvd < 0), color="#e74c3c", alpha=0.4, label="Selling Pressure")
    ax1.plot(df["time"], cvd, color="#333", linewidth=1.2)
    ax1.axhline(y=0, color="#666", linestyle="-", alpha=0.5, linewidth=1)
    ax1.set_xlabel("Time", fontsize=11)
    ax1.set_ylabel("CVD (Cumulative Volume Delta)", fontsize=11)
    
    if show_price and df["price"].notna().any():
        ax2 = ax1.twinx()
        ax2.plot(df["time"], df["price"], color="#f39c12", linewidth=1.5, alpha=0.7, label="Price")
        ax2.set_ylabel("Price", fontsize=11, color="#f39c12")
        ax2.tick_params(axis="y", labelcolor="#f39c12")
    
    ax1.set_title(params.get("title", f"CVD (Cumulative Volume Delta) {symbol}".strip()), fontsize=13, fontweight="bold")
    ax1.legend(loc="upper left", fontsize=9)
    ax1.grid(axis="y", alpha=0.3)
    fig.autofmt_xdate(rotation=45)
    fig.tight_layout()
    return _fig_to_png(fig), "image/png"


def render_oi_change(params: Dict, output: str) -> Tuple[object, str]:
    """持仓量变化图 - OI + Price 双轴"""
    data = params.get("data")
    if not data or not isinstance(data, list):
        raise ValueError("缺少 data 列表")
    
    df = pd.DataFrame(data)
    if "time" not in df.columns or "oi" not in df.columns:
        raise ValueError("data 需包含 time, oi")
    
    df["time"] = pd.to_datetime(df["time"])
    df = df.sort_values("time")
    df["oi_change"] = df["oi"].diff().fillna(0)
    
    symbol = params.get("symbol", "")
    show_price = params.get("show_price", True) and "price" in df.columns
    
    if output == "json":
        result = {"title": params.get("title", f"Open Interest {symbol}".strip()),
                  "time": df["time"].dt.strftime("%Y-%m-%d %H:%M").tolist(),
                  "oi": df["oi"].tolist(), "oi_change": df["oi_change"].tolist()}
        if show_price:
            result["price"] = df["price"].tolist()
        return result, "application/json"
    
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 8), gridspec_kw={"height_ratios": [2, 1]}, sharex=True)
    
    ax1.plot(df["time"], df["oi"], color="#9b59b6", linewidth=2, label="Open Interest")
    ax1.set_ylabel("Open Interest", fontsize=11, color="#9b59b6")
    ax1.tick_params(axis="y", labelcolor="#9b59b6")
    ax1.legend(loc="upper left", fontsize=9)
    
    if show_price and df["price"].notna().any():
        ax1_price = ax1.twinx()
        ax1_price.plot(df["time"], df["price"], color="#f39c12", linewidth=1.5, alpha=0.7, label="Price")
        ax1_price.set_ylabel("Price", fontsize=11, color="#f39c12")
        ax1_price.tick_params(axis="y", labelcolor="#f39c12")
        ax1_price.legend(loc="upper right", fontsize=9)
    
    colors = ["#2ecc71" if x >= 0 else "#e74c3c" for x in df["oi_change"]]
    ax2.bar(df["time"], df["oi_change"], color=colors, alpha=0.7, width=0.02)
    ax2.axhline(y=0, color="#666", linestyle="-", alpha=0.5, linewidth=1)
    ax2.set_ylabel("OI Change", fontsize=11)
    ax2.set_xlabel("Time", fontsize=11)
    
    ax1.set_title(params.get("title", f"Open Interest {symbol}".strip()), fontsize=13, fontweight="bold")
    ax1.grid(axis="y", alpha=0.3)
    ax2.grid(axis="y", alpha=0.3)
    fig.autofmt_xdate(rotation=45)
    fig.tight_layout()
    return _fig_to_png(fig), "image/png"


def register_defaults() -> TemplateRegistry:
    """注册内置模板，并返回注册表实例。"""

    registry = TemplateRegistry()
    registry.register(
        TemplateMeta(
            template_id="line-basic",
            name="基础折线图",
            description="示例模板：输入一组数值，输出基础折线图（PNG 或 plotly JSON）。",
            outputs=["png", "json"],
            params=["series(list[float])", "title?"],
            sample={"template_id": "line-basic", "output": "png", "params": {"series": [1, 3, 2, 5, 4]}},
        ),
        render_line_basic,
    )
    registry.register(
        TemplateMeta(
            template_id="kline-basic",
            name="K线+均线+量能",
            description="金融行情图：OHLC 必填，均线周期可选，支持量能",
            outputs=["png", "json"],
            params=[
                "open(list[float])",
                "high(list[float])",
                "low(list[float])",
                "close(list[float])",
                "volume?(list[float])",
                "ma_periods?(list[int])",
                "timestamps?(list[str])",
                "title?",
            ],
            sample={
                "template_id": "kline-basic",
                "output": "png",
                "params": {
                    "open": [10, 11, 12, 12.5, 12.2],
                    "high": [11, 12, 12.6, 13, 12.8],
                    "low": [9.8, 10.5, 11.5, 12, 12],
                    "close": [10.5, 11.8, 12.3, 12.7, 12.1],
                    "volume": [100, 120, 130, 90, 110],
                    "ma_periods": [3],
                    "title": "示例K线",
                },
            },
        ),
        render_kline_basic,
    )
    registry.register(
        TemplateMeta(
            template_id="kline-envelope",
            name="多周期K线包络",
            description="复用 Financial-Fractal-KLine 的多周期包络可视化（HTML/JSON）",
            outputs=["html", "json"],
            params=[
                "symbol(str)",
                "intervals?(list[str] | str)",
                "base_interval?(str)",
                "limit?(int)",
                "startTime?(int)",
                "endTime?(int)",
                "exchange?(str)",
                "title?(str)",
                "lead?(str)",
            ],
            sample={
                "template_id": "kline-envelope",
                "output": "html",
                "params": {
                    "symbol": "BTCUSDT",
                    "intervals": ["5m", "1h", "4h", "1d"],
                    "limit": 500,
                },
            },
        ),
        render_kline_envelope,
    )
    registry.register(
        TemplateMeta(
            template_id="macd",
            name="价格 + MACD",
            description="双面板显示收盘价与 MACD/Signal/Hist",
            outputs=["png", "json"],
            params=["close(list[float])", "fast?(int)", "slow?(int)", "signal?(int)", "title?"],
            sample={
                "template_id": "macd",
                "output": "png",
                "params": {"close": [1, 2, 3, 2.5, 3.2, 3.8, 3.5], "title": "示例MACD"},
            },
        ),
        render_macd,
    )
    registry.register(
        TemplateMeta(
            template_id="equity-drawdown",
            name="权益+回撤",
            description="上方权益曲线，下方回撤百分比阴影",
            outputs=["png", "json"],
            params=["equity(list[float])", "timestamps?(list[str])", "title?"],
            sample={
                "template_id": "equity-drawdown",
                "output": "png",
                "params": {"equity": [100, 105, 103, 110, 107, 120]},
            },
        ),
        render_equity_drawdown,
    )
    registry.register(
        TemplateMeta(
            template_id="market-vpvr-heat",
            name="全市场 VPVR 热力图",
            description="价格分桶的成交量占比热力图，X=价格区间，Y=币种",
            outputs=["png", "json"],
            params=[
                "data(list[ {symbol, price|close: list, volume|volumes: list} ])",
                "bins?(int, default 40)",
                "bin_mode?(percentile|relative)",
                "top_n?(int)",
                "scale?(linear|log)",
                "title?",
            ],
            sample={
                "template_id": "market-vpvr-heat",
                "output": "png",
                "params": {
                    "bins": 20,
                    "data": [
                        {"symbol": "BTCUSDT", "close": [100, 101, 102, 101.5], "volume": [10, 12, 9, 11]},
                        {"symbol": "ETHUSDT", "close": [50, 51, 50.5, 52], "volume": [8, 9, 7, 10]},
                    ],
                },
            },
        ),
        render_market_vpvr_heat,
    )
    registry.register(
        TemplateMeta(
            template_id="vpvr-zone-strip",
            name="VPVR 条带散点",
            description="按价值区位置分布，使用 adjustText 自动防重叠，支持涨跌/量比着色",
            outputs=["png", "json"],
            params=[
                "data(list[{symbol, price, value_area_low, value_area_high, price_change?, volume_change?}])",
                "bands?(int, default 5)",
                "title?",
            ],
            sample={
                "template_id": "vpvr-zone-strip",
                "output": "png",
                "params": {
                    "bands": 5,
                    "data": [
                        {"symbol": "ETHUSDT", "price": 1620, "value_area_low": 1500, "value_area_high": 1700, "price_change": 0.03},
                        {"symbol": "BTCUSDT", "price": 34500, "value_area_low": 33000, "value_area_high": 36000, "price_change": -0.05},
                        {"symbol": "SOLUSDT", "price": 135, "value_area_low": 120, "value_area_high": 140, "volume_change": 2.0},
                    ],
                },
            },
        ),
        render_vpvr_zone_strip,
    )
    registry.register(
        TemplateMeta(
            template_id="vpvr-ridge",
            name="VPVR 山脊图",
            description="展示成交量分布随时间演变，支持 OHLC 价格线叠加",
            outputs=["png", "json"],
            params=[
                "symbol(str)",
                "interval?(str, default 1h)",
                "periods?(int, default 10)",
                "lookback?(int, default 200)",
                "bins?(int, default 48)",
                "overlap?(float, default 0.5)",
                "colormap?(str, default viridis)",
                "show_ohlc?(bool, default True)",
                "title?",
            ],
            sample={
                "template_id": "vpvr-ridge",
                "output": "png",
                "params": {
                    "symbol": "BTCUSDT",
                    "interval": "1h",
                    "periods": 10,
                    "show_ohlc": True,
                },
            },
        ),
        render_vpvr_ridge,
    )
    registry.register(
        TemplateMeta(
            template_id="bb-zone-strip",
            name="布林带分布图",
            description="全市场布林带 %B 位置分布，展示各币种在布林带中的相对位置（超买/超卖）",
            outputs=["png", "json"],
            params=[
                "data(list[{symbol, percent_b, bandwidth?, price_change?, volume?}])",
                "bands?(int, default 5)",
                "title?",
            ],
            sample={
                "template_id": "bb-zone-strip",
                "output": "png",
                "params": {
                    "bands": 5,
                    "data": [
                        {"symbol": "BTCUSDT", "percent_b": 0.85, "bandwidth": 15.5, "price_change": 0.02},
                        {"symbol": "ETHUSDT", "percent_b": 0.45, "bandwidth": 20.3, "price_change": -0.01},
                        {"symbol": "SOLUSDT", "percent_b": 0.12, "bandwidth": 25.8, "price_change": -0.03},
                    ],
                },
            },
        ),
        render_bb_zone_strip,
    )
    # 日内分析图表
    registry.register(
        TemplateMeta(
            template_id="intraday-volume-heatmap",
            name="日内成交量热力图",
            description="展示各币种在24小时内的成交量分布，识别活跃交易时段",
            outputs=["png", "json"],
            params=["data(list[{symbol, hour, volume}])", "top_n?(int, default 30)", "normalize?(row/all/none)", "title?"],
            sample={"template_id": "intraday-volume-heatmap", "output": "png",
                    "params": {"top_n": 10, "data": [{"symbol": "BTCUSDT", "hour": 0, "volume": 1000},
                                                     {"symbol": "BTCUSDT", "hour": 8, "volume": 2500}]}},
        ),
        render_intraday_volume_heatmap,
    )
    registry.register(
        TemplateMeta(
            template_id="intraday-volatility",
            name="日内波动率曲线",
            description="展示24小时内各时段的平均波动率，识别最佳交易时段",
            outputs=["png", "json"],
            params=["data(list[{hour, volatility, volume?}])", "symbol?(str)", "show_volume?(bool)", "title?"],
            sample={"template_id": "intraday-volatility", "output": "png",
                    "params": {"symbol": "BTCUSDT", "data": [{"hour": 0, "volatility": 0.5}, {"hour": 8, "volatility": 1.2}]}},
        ),
        render_intraday_volatility,
    )
    registry.register(
        TemplateMeta(
            template_id="taker-ratio-heatmap",
            name="主动买卖比热力图",
            description="展示各币种各时段的主动买入占比，蓝色=买压，红色=卖压",
            outputs=["png", "json"],
            params=["data(list[{symbol, hour, taker_buy_ratio}])", "top_n?(int, default 30)", "title?"],
            sample={"template_id": "taker-ratio-heatmap", "output": "png",
                    "params": {"data": [{"symbol": "BTCUSDT", "hour": 0, "taker_buy_ratio": 0.55}]}},
        ),
        render_taker_ratio_heatmap,
    )
    registry.register(
        TemplateMeta(
            template_id="long-short-ratio",
            name="多空比时序图",
            description="展示大户/散户/主动成交三线多空比变化",
            outputs=["png", "json"],
            params=["data(list[{time, top_trader_ratio?, global_ratio?, taker_ratio?}])", "symbol?(str)", "title?"],
            sample={"template_id": "long-short-ratio", "output": "png",
                    "params": {"symbol": "BTCUSDT", "data": [{"time": "2024-01-01 00:00", "top_trader_ratio": 1.2, "global_ratio": 1.1}]}},
        ),
        render_long_short_ratio,
    )
    registry.register(
        TemplateMeta(
            template_id="cvd-cumulative",
            name="CVD累计图",
            description="累计成交量差 (Cumulative Volume Delta)，判断多空主导力量",
            outputs=["png", "json"],
            params=["data(list[{time, cvd, price?}])", "symbol?(str)", "show_price?(bool)", "title?"],
            sample={"template_id": "cvd-cumulative", "output": "png",
                    "params": {"symbol": "BTCUSDT", "data": [{"time": "2024-01-01 00:00", "cvd": 100}, {"time": "2024-01-01 01:00", "cvd": 250}]}},
        ),
        render_cvd_cumulative,
    )
    registry.register(
        TemplateMeta(
            template_id="oi-change",
            name="持仓量变化图",
            description="展示持仓量 (Open Interest) 随时间变化，配合价格判断趋势强度",
            outputs=["png", "json"],
            params=["data(list[{time, oi, price?}])", "symbol?(str)", "show_price?(bool)", "title?"],
            sample={"template_id": "oi-change", "output": "png",
                    "params": {"symbol": "BTCUSDT", "data": [{"time": "2024-01-01 00:00", "oi": 50000, "price": 42000}]}},
        ),
        render_oi_change,
    )
    return registry
