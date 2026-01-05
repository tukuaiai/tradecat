"""
模板注册与示例渲染器。

当前仅内置一个示例模板（line-basic），用于验证渲染链路。
后续可在此目录添加更多模板，并在 register_defaults 中注册。
"""

from __future__ import annotations

import io
import logging
from dataclasses import dataclass
from typing import Callable, Dict, Iterable, List, Tuple

import matplotlib
import pandas as pd
import plotly.graph_objects as go
import seaborn as sns

# 使用无界面后端，避免服务器缺乏显示设备时报错
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

logger = logging.getLogger(__name__)


RenderFn = Callable[[Dict, str], Tuple[object, str]]


@dataclass
class TemplateMeta:
    """模板元信息，用于对外展示与路由校验。"""

    template_id: str
    name: str
    description: str
    outputs: List[str]


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


def register_defaults() -> TemplateRegistry:
    """注册内置模板，并返回注册表实例。"""

    registry = TemplateRegistry()
    registry.register(
        TemplateMeta(
            template_id="line-basic",
            name="基础折线图",
            description="示例模板：输入一组数值，输出基础折线图（PNG 或 plotly JSON）。",
            outputs=["png", "json"],
        ),
        render_line_basic,
    )
    return registry
