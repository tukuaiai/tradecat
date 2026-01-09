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
import logging
import math
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


def render_vpvr_zone_dot(params: Dict, output: str) -> Tuple[object, str]:
    """
    VPVR 价值区点阵图。

    使用聚合后的价值区上下沿与控制点，绘制横向带（VAH–VAL）+ 控制点标记。

    必填：
    - data: [{symbol, value_area_low, value_area_high, poc}]

    可选：
    - coverage: 覆盖率/占比，用于颜色深浅
    - title: 图表标题
    """

    data = params.get("data")
    if not data or not isinstance(data, list):
        raise ValueError("缺少 data 列表")

    records = []
    for item in data:
        try:
            symbol = item["symbol"]
            val_low = float(item.get("value_area_low"))
            val_high = float(item.get("value_area_high"))
            poc = float(item.get("poc"))
        except Exception:
            continue
        coverage = item.get("coverage")
        try:
            coverage = float(coverage) if coverage is not None else None
        except Exception:
            coverage = None
        if val_high <= val_low:
            continue
        records.append((symbol, val_low, val_high, poc, coverage))

    if not records:
        raise ValueError("无有效 VPVR 数据")

    df = pd.DataFrame(records, columns=["symbol", "val_low", "val_high", "poc", "coverage"])
    df.sort_values("poc", inplace=True)
    y_positions = range(len(df))

    if output == "json":
        return (
            {
                "title": params.get("title", "VPVR Value Area"),
                "points": [
                    {
                        "symbol": row.symbol,
                        "value_area_low": row.val_low,
                        "value_area_high": row.val_high,
                        "poc": row.poc,
                        "coverage": row.coverage,
                        "y": idx,
                    }
                    for idx, row in df.reset_index(drop=True).itertuples()
                ],
            },
            "application/json",
        )

    sns.set_theme(style="white")
    fig, ax = plt.subplots(figsize=(12, max(4, len(df) * 0.35)))
    cmap = sns.color_palette("viridis", as_cmap=True)

    for y, row in zip(y_positions, df.itertuples()):
        width = row.val_high - row.val_low
        ax.broken_barh([(row.val_low, width)], (y - 0.25, 0.5), facecolors="lightblue", alpha=0.6)
        color = cmap(row.coverage) if row.coverage is not None else "#1d4ed8"
        ax.scatter(row.poc, y, color=color, s=30, zorder=3)
        ax.text(row.val_high, y, f" POC {row.poc:.4g}", va="center", fontsize=8, color="#111")

    ax.set_xlabel("Price")
    ax.set_yticks(list(y_positions))
    ax.set_yticklabels(df["symbol"])
    ax.set_title(params.get("title", "VPVR Value Area & POC"))
    ax.grid(True, axis="x", linestyle="--", alpha=0.3)
    fig.tight_layout()
    return _fig_to_png(fig), "image/png"


def render_vpvr_zone_grid(params: Dict, output: str) -> Tuple[object, str]:
    """
    VPVR 价值区小卡片网格（横向多卡片）。

    每个币种一张卡：背景矩形 = 价值区 (VAL→VAH)，点 = POC，卡片标题标注币种与覆盖率。

    必填：
    - data: [{symbol, value_area_low, value_area_high, poc, coverage?}]

    可选：
    - cols: 每行卡片数，默认 3
    - title: 总标题
    """

    data = params.get("data")
    if not data or not isinstance(data, list):
        raise ValueError("缺少 data 列表")

    cards = []
    for item in data:
        try:
            symbol = item["symbol"]
            val_low = float(item.get("value_area_low"))
            val_high = float(item.get("value_area_high"))
            poc = float(item.get("poc"))
        except Exception:
            continue
        if val_high <= val_low:
            continue
        cov = item.get("coverage")
        try:
            cov = float(cov) if cov is not None else None
        except Exception:
            cov = None
        cards.append((symbol, val_low, val_high, poc, cov))

    if not cards:
        raise ValueError("无有效 VPVR 数据")

    cols = max(1, int(params.get("cols", 3)))
    rows = math.ceil(len(cards) / cols)
    width = 4 * cols
    height = max(2.8 * rows, 3)

    sns.set_theme(style="white")
    fig, axes = plt.subplots(rows, cols, figsize=(width, height), squeeze=False)
    cmap = sns.color_palette("viridis", as_cmap=True)

    for idx, (symbol, val_low, val_high, poc, cov) in enumerate(cards):
        r, c = divmod(idx, cols)
        ax = axes[r][c]
        band_width = val_high - val_low
        ax.broken_barh([(val_low, band_width)], (0.2, 0.6), facecolors="#bfdbfe", alpha=0.7)
        color = cmap(cov) if cov is not None else "#1d4ed8"
        ax.scatter(poc, 0.5, color=color, s=30, zorder=3)
        ax.text(
            poc,
            0.65,
            f"POC {poc:.4g}",
            ha="center",
            va="bottom",
            fontsize=8,
            color="#0f172a",
        )
        subtitle = f"{symbol}" + (f"  cov {cov:.0%}" if cov is not None else "")
        ax.set_title(subtitle, fontsize=10, pad=6)
        ax.set_yticks([])
        ax.set_ylim(0, 1)
        ax.grid(True, axis="x", linestyle="--", alpha=0.3)
    # 隐藏空白轴
    for idx in range(len(cards), rows * cols):
        r, c = divmod(idx, cols)
        axes[r][c].axis("off")

    fig.suptitle(params.get("title", "VPVR 价值区卡片"), fontsize=12)
    fig.tight_layout(rect=[0, 0, 1, 0.95])

    if output == "json":
        return (
            {
                "title": params.get("title", "VPVR 价值区卡片"),
                "cards": [
                    {
                        "symbol": symbol,
                        "value_area_low": val_low,
                        "value_area_high": val_high,
                        "poc": poc,
                        "coverage": cov,
                    }
                    for (symbol, val_low, val_high, poc, cov) in cards
                ],
                "cols": cols,
            },
            "application/json",
        )

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
    全市场布林带分布图 - 展示各币种价格在布林带中的相对位置。

    每个币种按 %B 值（价格在布林带中的位置）分布：
    - %B < 0: 跌破下轨
    - %B = 0: 在下轨
    - %B = 0.5: 在中轨
    - %B = 1: 在上轨
    - %B > 1: 突破上轨

    必填 data 字段：symbol, percent_b (百分比b)
    可选 data 字段：
      - bandwidth: 带宽，决定圆圈大小（带宽大=波动大）
      - price_change: 涨跌幅，决定边框颜色(红跌绿涨)
      - volume: 成交量，决定圆圈颜色深浅
    """
    data = params.get("data")
    if not data or not isinstance(data, list):
        raise ValueError("缺少 data 列表")

    bands = max(2, int(params.get("bands", 5)))

    df = pd.DataFrame(data)
    required_cols = {"symbol", "percent_b"}
    if not required_cols.issubset(df.columns):
        raise ValueError("data 需包含 symbol, percent_b")

    df = df.dropna(subset=["percent_b"])
    df["percent_b"] = df["percent_b"].astype(float)
    # 过滤无效数据（%B 为 0 且带宽为 0 表示数据不足）
    if "bandwidth" in df.columns:
        df = df[(df["bandwidth"] > 0) | (df["percent_b"] != 0)]

    # 去重：每个币种只保留一条（取最新或第一条）
    df = df.drop_duplicates(subset=["symbol"], keep="first")

    if df.empty:
        raise ValueError("无有效布林带数据")

    # %B 映射到 0-1 范围（允许超出）
    # 原始 %B: 0=下轨, 0.5=中轨, 1=上轨
    # 映射后 y: 0=超卖, 0.5=中轨, 1=超买
    raw_y = df["percent_b"].clip(-0.5, 1.5)  # 允许一定超出
    df["y"] = ((raw_y + 0.5) / 2).clip(0.01, 0.99)  # 归一化到 0-1
    df["y_raw"] = df["percent_b"]

    n = len(df)
    fig_height = min(14, max(10, n * 0.028))

    sns.set_theme(style="white")
    fig, ax = plt.subplots(1, 1, figsize=(16, fig_height), dpi=150)

    # 布林带区域背景色：从超卖（蓝）到超买（红）
    band_colors = ["#1565C0", "#1976D2", "#4CAF50", "#FFA726", "#E53935"]
    if bands != 5:
        cmap = plt.cm.RdYlBu_r  # 红黄蓝反转
        band_colors = [cmap(i / max(1, bands - 1)) for i in range(bands)]

    for i in range(bands):
        y0 = i / bands
        ax.add_patch(plt.Rectangle((0.0, y0), 1.0, 1/bands, facecolor=band_colors[i], alpha=0.85, edgecolor="none"))

    rng = np.random.default_rng(42)

    # 带宽归一化 -> 圆圈大小（带宽大=波动大=圆圈大）
    if "bandwidth" in df.columns:
        bw = df["bandwidth"].fillna(df["bandwidth"].median())
        bw_log = np.log10(bw.clip(lower=0.1) + 1)
        bw_norm = (bw_log - bw_log.min()) / (bw_log.max() - bw_log.min() + 1e-9)
        df["size_factor"] = 0.3 + bw_norm * 1.2  # 0.3 ~ 1.5
    else:
        df["size_factor"] = 1.0

    # 成交量归一化 -> 颜色亮度
    if "volume" in df.columns:
        vol = df["volume"].fillna(df["volume"].median())
        vol_log = np.log10(vol.clip(lower=1))
        vol_norm = (vol_log - vol_log.min()) / (vol_log.max() - vol_log.min() + 1e-9)
        df["vol_factor"] = vol_norm
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
            bin_indices = df[bin_mask].index.tolist()
            for i, idx in enumerate(bin_indices):
                x = (i + 0.5) / bin_count * 0.88 + 0.06
                x += rng.uniform(-0.015, 0.015)
                x_positions.append((idx, x))

    for idx, x in x_positions:
        df.loc[idx, "x"] = x
    df["x"] = df["x"].clip(0.03, 0.97)

    # 绘制圆圈
    base_font = 5.0
    texts = []
    vol_cmap = plt.cm.YlOrRd  # 黄到红：低成交量黄，高成交量红

    for _, row in df.iterrows():
        label = str(row["symbol"]).replace("USDT", "")
        if len(label) > 6:
            label = label[:6] + ".."

        size_factor = row.get("size_factor", 1.0)
        font_size = base_font * (0.8 + size_factor * 0.7)

        vol_factor = row.get("vol_factor", 0.5)
        rgba = vol_cmap(vol_factor)
        point_color = f"#{int(rgba[0]*255):02x}{int(rgba[1]*255):02x}{int(rgba[2]*255):02x}"

        # 涨跌决定边框颜色
        chg = row.get("price_change")
        if chg is not None and chg > 0.005:
            edge_color = "#1a9850"
        elif chg is not None and chg < -0.005:
            edge_color = "#d73027"
        else:
            edge_color = "#ffffff"

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

    # adjustText 微调
    try:
        adjust_text(
            texts,
            x=df["x"].tolist(),
            y=df["y"].tolist(),
            ax=ax,
            expand=(1.03, 1.05),
            force_text=(0.2, 0.3),
            force_static=(0.05, 0.08),
            force_pull=(0.02, 0.02),
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
    # Y 轴标签：%B 值（英文避免字体问题）
    ax.set_yticks([0, 0.25, 0.5, 0.75, 1.0])
    ax.set_yticklabels(["-50%\n(Oversold)", "0%\n(Lower)", "50%\n(Middle)", "100%\n(Upper)", "150%\n(Overbought)"], fontsize=9, color="#333333")
    ax.set_ylabel("Bollinger %B Position", fontsize=10, color="#333333", labelpad=8)

    # 图例
    from matplotlib.lines import Line2D
    legend_elements = [
        Line2D([0], [0], marker='o', color='w', markerfacecolor=band_colors[-1], markersize=10, label='Overbought (>100%)'),
        Line2D([0], [0], marker='o', color='w', markerfacecolor=band_colors[len(band_colors)//2], markersize=10, label='Middle Band (50%)'),
        Line2D([0], [0], marker='o', color='w', markerfacecolor=band_colors[0], markersize=10, label='Oversold (<0%)'),
        Line2D([0], [0], marker='o', color='w', markerfacecolor='#ff6b6b', markersize=11, label='High Volume'),
        Line2D([0], [0], marker='o', color='w', markerfacecolor='#ffffcc', markersize=8, label='Low Volume'),
        Line2D([0], [0], marker='o', color='w', markerfacecolor='#ffcc80', markeredgecolor='#1a9850', markersize=10, markeredgewidth=2, label='Up'),
        Line2D([0], [0], marker='o', color='w', markerfacecolor='#ffcc80', markeredgecolor='#d73027', markersize=10, markeredgewidth=2, label='Down'),
    ]
    ax.legend(handles=legend_elements, loc='lower right', fontsize=9, framealpha=0.9, edgecolor='#cccccc')

    ax.set_xlim(-0.01, 1.01)
    ax.set_ylim(-0.02, 1.02)

    fig.suptitle(params.get("title", "Bollinger Band Distribution"), fontsize=12, color="#1e293b", fontweight="bold", y=0.98)
    fig.tight_layout(rect=[0, 0.02, 0.92, 0.96])

    if output == "json":
        return (
            {
                "title": params.get("title", "Bollinger Band Distribution"),
                "bands": bands,
                "points": [{"symbol": row["symbol"], "percent_b": float(row["y_raw"]), "x": float(row["x"]),
                           "size_factor": float(row.get("size_factor", 1)), "vol_factor": float(row.get("vol_factor", 0.5))}
                          for _, row in df.iterrows()],
            },
            "application/json",
        )

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
            template_id="vpvr-zone-dot",
            name="VPVR 价值区点阵",
            description="使用价值区上下沿 + 控制点绘制横向带和点阵，适合全市场对比",
            outputs=["png", "json"],
            params=[
                "data(list[{symbol, value_area_low, value_area_high, poc, coverage?}])",
                "title?",
            ],
            sample={
                "template_id": "vpvr-zone-dot",
                "output": "png",
                "params": {
                    "data": [
                        {"symbol": "BTCUSDT", "value_area_low": 100, "value_area_high": 105, "poc": 102.5, "coverage": 0.68},
                        {"symbol": "ETHUSDT", "value_area_low": 50, "value_area_high": 52, "poc": 51.2, "coverage": 0.63},
                    ]
                },
            },
        ),
        render_vpvr_zone_dot,
    )
    registry.register(
        TemplateMeta(
            template_id="vpvr-zone-grid",
            name="VPVR 价值区卡片",
            description="横向多卡片：每个币种一条价值区带 + POC 点，方便快速扫描",
            outputs=["png", "json"],
            params=[
                "data(list[{symbol, value_area_low, value_area_high, poc, coverage?}])",
                "cols?(int, default 3)",
                "title?",
            ],
            sample={
                "template_id": "vpvr-zone-grid",
                "output": "png",
                "params": {
                    "cols": 3,
                    "data": [
                        {"symbol": "BTCUSDT", "value_area_low": 100, "value_area_high": 105, "poc": 102.5, "coverage": 0.68},
                        {"symbol": "ETHUSDT", "value_area_low": 50, "value_area_high": 52, "poc": 51.2, "coverage": 0.63},
                        {"symbol": "SOLUSDT", "value_area_low": 8.3, "value_area_high": 9.1, "poc": 8.7, "coverage": 0.7},
                        {"symbol": "XRPUSDT", "value_area_low": 0.5, "value_area_high": 0.56, "poc": 0.53, "coverage": 0.6},
                    ],
                },
            },
        ),
        render_vpvr_zone_grid,
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
    return registry
